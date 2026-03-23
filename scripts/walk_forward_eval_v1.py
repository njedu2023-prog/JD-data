# -*- coding: utf-8 -*-
"""
Walk-forward validation for JD-data baseline models.

Outputs:
- data_model/02618.HK/walk_forward_eval_v1.json

Minimal, reproducible settings:
- sort by asof_date
- expanding train window
- fixed test_size per fold
- Ridge: y_ret_1d
- LogisticRegression: y_up_1d
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
OUTPUT_FILE = REPO_ROOT / "data_model" / "02618.HK" / "walk_forward_eval_v1.json"

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


def _select_features(df: pd.DataFrame) -> List[str]:
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    exclude_names = {
        TARGET_REG,
        TARGET_CLS,
        "feature_count_total",
        "feature_count_nonnull",
        "missing_ratio",
        "build_version",
    }
    features = [c for c in numeric_cols if c not in exclude_names and not c.startswith("y_")]
    if not features:
        raise ValueError("No numeric features available after exclusion")
    return features


def _walk_forward_splits(
    n: int, min_train: int, test_size: int, step: Optional[int] = None
) -> List[Split]:
    if n < min_train + test_size:
        raise ValueError("Not enough rows for walk-forward validation")
    if step is None:
        step = test_size

    splits: List[Split] = []
    train_end = min_train

    while train_end + test_size <= n:
        splits.append(
            Split(
                train_idx=np.arange(train_end),
                test_idx=np.arange(train_end, train_end + test_size),
            )
        )
        train_end += step

    return splits


def _nanmean(values: List[Optional[float]]) -> Optional[float]:
    arr = np.array([v for v in values if v is not None], dtype=float)
    if arr.size == 0:
        return None
    return float(np.nanmean(arr))


def _nanstd(values: List[Optional[float]]) -> Optional[float]:
    arr = np.array([v for v in values if v is not None], dtype=float)
    if arr.size == 0:
        return None
    return float(np.nanstd(arr))


def train_regression_fold(df: pd.DataFrame, split: Split, features: List[str]) -> Dict[str, Any]:
    y = df[TARGET_REG].to_numpy()
    X = np.nan_to_num(df[features].to_numpy(), nan=0.0)

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.0, random_state=42)),
        ]
    )

    pipeline.fit(X[split.train_idx], y[split.train_idx])
    y_pred = pipeline.predict(X[split.test_idx])

    mae = mean_absolute_error(y[split.test_idx], y_pred)
    rmse = math.sqrt(mean_squared_error(y[split.test_idx], y_pred))
    ic = _pearson_ic(y[split.test_idx], y_pred)

    base_pred = np.zeros_like(y[split.test_idx])
    mae_base = mean_absolute_error(y[split.test_idx], base_pred)
    rmse_base = math.sqrt(mean_squared_error(y[split.test_idx], base_pred))

    return {
        "ridge": asdict(EvalRegression(mae=float(mae), rmse=float(rmse), ic=ic)),
        "random_walk": asdict(EvalRegression(mae=float(mae_base), rmse=float(rmse_base), ic=0.0)),
    }


def train_classification_fold(df: pd.DataFrame, split: Split, features: List[str]) -> Dict[str, Any]:
    y = df[TARGET_CLS].astype(int).to_numpy()
    X = np.nan_to_num(df[features].to_numpy(), nan=0.0)

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("logreg", LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)),
        ]
    )

    pipeline.fit(X[split.train_idx], y[split.train_idx])
    y_prob = pipeline.predict_proba(X[split.test_idx])[:, 1]
    y_pred_cls = (y_prob >= 0.5).astype(int)

    acc = accuracy_score(y[split.test_idx], y_pred_cls)
    f1 = f1_score(y[split.test_idx], y_pred_cls)
    try:
        roc = roc_auc_score(y[split.test_idx], y_prob)
    except Exception:
        roc = None
    brier = brier_score_loss(y[split.test_idx], y_prob)

    base_prob = float(np.mean(y[split.train_idx]))
    majority = 1 if base_prob > 0.5 else 0
    base_pred = np.full_like(y[split.test_idx], majority)
    base_prob_vec = np.full_like(y_prob, base_prob, dtype=float)

    acc_base = accuracy_score(y[split.test_idx], base_pred)
    f1_base = f1_score(y[split.test_idx], base_pred)
    try:
        roc_base = roc_auc_score(y[split.test_idx], base_prob_vec)
    except Exception:
        roc_base = None
    brier_base = brier_score_loss(y[split.test_idx], base_prob_vec)

    return {
        "logistic": asdict(
            EvalClassification(
                accuracy=float(acc), f1=float(f1), roc_auc=roc, brier=float(brier)
            )
        ),
        "majority": asdict(
            EvalClassification(
                accuracy=float(acc_base),
                f1=float(f1_base),
                roc_auc=roc_base,
                brier=float(brier_base),
            )
        ),
        "majority_class_train": majority,
        "majority_prob_train": base_prob,
    }


def _to_serializable(obj: Any) -> Any:
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return obj


def main() -> None:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Missing dataset file: {DATASET_FILE}")

    df = pd.read_csv(DATASET_FILE)
    if "asof_date" not in df.columns:
        raise ValueError("model_dataset.csv must contain asof_date")

    df["asof_date"] = pd.to_datetime(df["asof_date"], errors="coerce")
    df = df[df["asof_date"].notna()].copy().sort_values("asof_date")

    mask = np.isfinite(df[TARGET_REG]) & np.isfinite(df[TARGET_CLS])
    df = df.loc[mask].copy().reset_index(drop=True)

    # Keep minimal window settings for reproducibility.
    min_train = 500
    test_size = 60
    step = 60

    features = _select_features(df)
    splits = _walk_forward_splits(len(df), min_train=min_train, test_size=test_size, step=step)

    regression_folds: List[Dict[str, Any]] = []
    classification_folds: List[Dict[str, Any]] = []

    for fold_id, split in enumerate(splits, start=1):
        fold_meta = {
            "fold_id": fold_id,
            "train_rows": int(len(split.train_idx)),
            "test_rows": int(len(split.test_idx)),
            "train_start": df["asof_date"].iloc[split.train_idx[0]].date().isoformat(),
            "train_end": df["asof_date"].iloc[split.train_idx[-1]].date().isoformat(),
            "test_start": df["asof_date"].iloc[split.test_idx[0]].date().isoformat(),
            "test_end": df["asof_date"].iloc[split.test_idx[-1]].date().isoformat(),
        }

        regression_folds.append({"meta": fold_meta, "metrics": train_regression_fold(df, split, features)})
        classification_folds.append({"meta": fold_meta, "metrics": train_classification_fold(df, split, features)})

    def _agg(folds: List[Dict[str, Any]], bucket: str, key: str, agg_func):
        vals = [fold["metrics"][bucket].get(key) for fold in folds]
        return agg_func(vals)

    output = {
        "report_version": "walk_forward_eval_v1",
        "built_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "dataset": {
            "file": str(DATASET_FILE.relative_to(REPO_ROOT)),
            "rows": int(len(df)),
            "asof_date_start": df["asof_date"].min().date().isoformat(),
            "asof_date_end": df["asof_date"].max().date().isoformat(),
            "build_version_unique": sorted(df["build_version"].dropna().unique().tolist())
            if "build_version" in df.columns
            else None,
        },
        "params": {"min_train": min_train, "test_size": test_size, "step": step},
        "features": {"count": len(features), "names": features},
        "regression": {
            "summary": {
                "ridge_mean": {
                    "mae": _agg(regression_folds, "ridge", "mae", _nanmean),
                    "rmse": _agg(regression_folds, "ridge", "rmse", _nanmean),
                    "ic": _agg(regression_folds, "ridge", "ic", _nanmean),
                },
                "ridge_std": {
                    "mae": _agg(regression_folds, "ridge", "mae", _nanstd),
                    "rmse": _agg(regression_folds, "ridge", "rmse", _nanstd),
                    "ic": _agg(regression_folds, "ridge", "ic", _nanstd),
                },
                "random_walk_mean": {
                    "mae": _agg(regression_folds, "random_walk", "mae", _nanmean),
                    "rmse": _agg(regression_folds, "random_walk", "rmse", _nanmean),
                    "ic": _agg(regression_folds, "random_walk", "ic", _nanmean),
                },
                "random_walk_std": {
                    "mae": _agg(regression_folds, "random_walk", "mae", _nanstd),
                    "rmse": _agg(regression_folds, "random_walk", "rmse", _nanstd),
                    "ic": _agg(regression_folds, "random_walk", "ic", _nanstd),
                },
            },
            "folds": regression_folds,
        },
        "classification": {
            "summary": {
                "logistic_mean": {
                    "accuracy": _agg(classification_folds, "logistic", "accuracy", _nanmean),
                    "f1": _agg(classification_folds, "logistic", "f1", _nanmean),
                    "roc_auc": _agg(classification_folds, "logistic", "roc_auc", _nanmean),
                    "brier": _agg(classification_folds, "logistic", "brier", _nanmean),
                },
                "logistic_std": {
                    "accuracy": _agg(classification_folds, "logistic", "accuracy", _nanstd),
                    "f1": _agg(classification_folds, "logistic", "f1", _nanstd),
                    "roc_auc": _agg(classification_folds, "logistic", "roc_auc", _nanstd),
                    "brier": _agg(classification_folds, "logistic", "brier", _nanstd),
                },
                "majority_mean": {
                    "accuracy": _agg(classification_folds, "majority", "accuracy", _nanmean),
                    "f1": _agg(classification_folds, "majority", "f1", _nanmean),
                    "roc_auc": _agg(classification_folds, "majority", "roc_auc", _nanmean),
                    "brier": _agg(classification_folds, "majority", "brier", _nanmean),
                },
                "majority_std": {
                    "accuracy": _agg(classification_folds, "majority", "accuracy", _nanstd),
                    "f1": _agg(classification_folds, "majority", "f1", _nanstd),
                    "roc_auc": _agg(classification_folds, "majority", "roc_auc", _nanstd),
                    "brier": _agg(classification_folds, "majority", "brier", _nanstd),
                },
            },
            "folds": classification_folds,
        },
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=_to_serializable),
        encoding="utf-8",
    )

    print(f"[OK] walk-forward evaluation written: {OUTPUT_FILE} ({len(regression_folds)} folds)")


if __name__ == "__main__":
    main()
