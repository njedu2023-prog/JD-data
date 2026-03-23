# -*- coding: utf-8 -*-
"""Train baseline models for JD-data.

Outputs a baseline model evaluation JSON file for 02618.HK:
- data_model/02618.HK/baseline_model_v1.json

Models:
- Regression: Ridge regression for y_ret_1d
- Classification: Logistic regression for y_up_1d

Metrics:
- Regression: MAE, RMSE, IC
- Classification: Accuracy, F1, ROC AUC, Brier score

Benchmarks:
- Regression: constant random-walk baseline (predict 0)
- Classification: constant majority class baseline

Time split:
- sorted by asof_date, use first 80% as train, last 20% as test
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
    brier_score_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_FILE = REPO_ROOT / "data_model" / "02618.HK" / "model_dataset.csv"
OUTPUT_FILE = REPO_ROOT / "data_model" / "02618.HK" / "baseline_model_v1.json"

TARGET_REG = "y_ret_1d"
TARGET_CLS = "y_up_1d"


@dataclass
class Split:
    train_idx: np.ndarray
    test_idx: np.ndarray


@dataclass
class EvalRegression:
    mae: float
    rmse: float
    ic: Optional[float]


@dataclass
class EvalClassification:
    accuracy: float
    f1: float
    roc_auc: Optional[float]
    brier: float


def _pearson_ic(y_true: np.ndarray, y_pred: np.ndarray) -> Optional[float]:
    if len(y_true) < 2:
        return None
    x = np.asarray(y_true, dtype=float)
    y = np.asarray(y_pred, dtype=float)
    if np.allclose(np.std(x), 0) or np.allclose(np.std(y), 0):
        return 0.0
    corr = np.corrcoef(x, y)[0, 1]
    if np.isnan(corr):
        return None
    return float(corr)


def _time_split(n: int, train_ratio: float = 0.8) -> Split:
    if n < 2:
        raise ValueError("Not enough rows for split")
    split = int(n * train_ratio)
    split = max(1, min(n - 1, split))
    train_idx = np.arange(split)
    test_idx = np.arange(split, n)
    return Split(train_idx=train_idx, test_idx=test_idx)


def _select_features(df: pd.DataFrame) -> List[str]:
    # numeric features only
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    # remove targets and known non-features
    exclude_prefixes = ["y_"]
    exclude_names = {
        TARGET_REG,
        TARGET_CLS,
        "feature_count_total",
        "feature_count_nonnull",
        "missing_ratio",
        "build_version",
    }

    features: List[str] = []
    for col in numeric_cols:
        if col in exclude_names:
            continue
        if any(col.startswith(p) for p in exclude_prefixes):
            continue
        features.append(col)

    if not features:
        raise ValueError("No numeric features available after exclusion")

    return features


def train_regression(df: pd.DataFrame) -> Dict[str, object]:
    target = df[TARGET_REG].to_numpy()
    mask = np.isfinite(target)
    df = df.loc[mask].copy()
    target = target[mask]

    df = df.sort_values("asof_date").reset_index(drop=True)
    features = _select_features(df)

    X = df[features].to_numpy()
    y = df[TARGET_REG].to_numpy()

    # fill NaNs
    X = np.nan_to_num(X, nan=0.0)

    split = _time_split(len(y), train_ratio=0.8)

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.0, random_state=42))
        ]
    )

    pipeline.fit(X[split.train_idx], y[split.train_idx])
    y_pred = pipeline.predict(X[split.test_idx])

    mae = float(mean_absolute_error(y[split.test_idx], y_pred))
    rmse = float(math.sqrt(mean_squared_error(y[split.test_idx], y_pred)))
    ic = _pearson_ic(y[split.test_idx], y_pred)

    # baseline: predict 0
    base_pred = np.zeros_like(y[split.test_idx])
    mae_base = float(mean_absolute_error(y[split.test_idx], base_pred))
    rmse_base = float(math.sqrt(mean_squared_error(y[split.test_idx], base_pred)))

    return {
        "meta": {
            "rows": int(len(df)),
            "train_rows": int(len(split.train_idx)),
            "test_rows": int(len(split.test_idx)),
            "feature_cols": features,
        },
        "model": {
            "type": "Ridge",
            "alpha": 1.0,
        },
        "metrics": EvalRegression(mae=mae, rmse=rmse, ic=ic).__dict__,
        "benchmark_random_walk": EvalRegression(mae=mae_base, rmse=rmse_base, ic=0.0).__dict__,
    }


def train_classification(df: pd.DataFrame) -> Dict[str, object]:
    target = df[TARGET_CLS].to_numpy()
    mask = np.isfinite(target)
    df = df.loc[mask].copy()
    target = target[mask]

    df[TARGET_CLS] = df[TARGET_CLS].astype(int)

    df = df.sort_values("asof_date").reset_index(drop=True)
    features = _select_features(df)

    X = df[features].to_numpy()
    y = df[TARGET_CLS].to_numpy(dtype=int)

    X = np.nan_to_num(X, nan=0.0)

    split = _time_split(len(y), train_ratio=0.8)

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("logreg", LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)),
        ]
    )

    pipeline.fit(X[split.train_idx], y[split.train_idx])
    y_prob = pipeline.predict_proba(X[split.test_idx])[:, 1]
    y_pred_cls = (y_prob >= 0.5).astype(int)

    acc = float(accuracy_score(y[split.test_idx], y_pred_cls))
    f1 = float(f1_score(y[split.test_idx], y_pred_cls))
    try:
        roc = float(roc_auc_score(y[split.test_idx], y_prob))
    except Exception:
        roc = None
    brier = float(brier_score_loss(y[split.test_idx], y_prob))

    # baseline: majority class probability from train set
    majority = int(np.round(np.mean(y[split.train_idx])))
    base_prob = float(np.mean(y[split.train_idx]))
    base_pred = np.full_like(y[split.test_idx], majority)
    base_prob_vec = np.full_like(y_prob, base_prob, dtype=float)

    acc_base = float(accuracy_score(y[split.test_idx], base_pred))
    f1_base = float(f1_score(y[split.test_idx], base_pred))
    try:
        roc_base = float(roc_auc_score(y[split.test_idx], base_prob_vec))
    except Exception:
        roc_base = None
    brier_base = float(brier_score_loss(y[split.test_idx], base_prob_vec))

    return {
        "meta": {
            "rows": int(len(df)),
            "train_rows": int(len(split.train_idx)),
            "test_rows": int(len(split.test_idx)),
            "feature_cols": features,
            "majority_class_train": majority,
        },
        "model": {
            "type": "LogisticRegression",
            "solver": "lbfgs",
            "max_iter": 1000,
        },
        "metrics": EvalClassification(
            accuracy=acc, f1=f1, roc_auc=roc, brier=brier
        ).__dict__,
        "benchmark_majority": EvalClassification(
            accuracy=acc_base, f1=f1_base, roc_auc=roc_base, brier=brier_base
        ).__dict__,
    }


def main() -> None:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Missing dataset file: {DATASET_FILE}")

    df = pd.read_csv(DATASET_FILE)
    if "asof_date" not in df.columns:
        raise ValueError("model_dataset.csv must contain asof_date")

    df["asof_date"] = pd.to_datetime(df["asof_date"], errors="coerce")
    df = df[df["asof_date"].notna()].copy()

    results = {
        "regression": train_regression(df.copy()),
        "classification": train_classification(df.copy()),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[OK] baseline model report written:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
