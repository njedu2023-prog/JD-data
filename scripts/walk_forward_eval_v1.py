# -*- coding: utf-8 -*-
"""Walk-forward validation for JD-data baseline models.

Outputs walk-forward evaluation JSON file for 02618.HK:
- data_model/02618.HK/walk_forward_eval_v1.json

Strategy (minimal but reproducible):
- Sorting by asof_date
- Walk-forward expanding window
- Fixed test window size per fold
- Ridge for regression target y_ret_1d
- Logistic regression for classification target y_up_1d

Metrics:
- Regression: MAE, RMSE, IC (Pearson correlation)
- Classification: Accuracy, F1, ROC AUC, Brier score

Benchmarks:
- Regression: random-walk (predict 0)
- Classification: majority class from train set
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
e    if len(y_true) < 2:
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


def _walk_forward_splits(n: int, min_train: int, test_size: int, step: Optional[int] = None) -> List[Split]:
    if n < min_train + test_size:
        raise ValueError("Not enough rows for walk-forward validation")
    if step is None:
        step = test_size

    splits: List[Split] = []
    train_end = min_train

    while train_end + test_size <= n:
        train_idx = np.arange(train_end)
        test_idx = np.arange(train_end, train_end + test_size)
        splits.append(Split(train_idx=train_idx, test_idx=test_idx))

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

    X = df[features].to_numpy()
    X = np.nan_to_num(X, nan=0.0)

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.0, random_state=42)),
        ]
    )

    pipeline.fit(X[split.train_idx], y[split.train_idx])
    y_pred = pipeline.predict(X[split.test_idx])

    mae = float(mean_absolute_error(y[split.test_idx], y_pred))
    rmse = float(math.sqrt(mean_squared_error(y[split.test_idx], y_pred)))
    ic = _pearson_ic(y[split.test_idx], y_pred)

    base_pred = np.zeros_like(y[split.test_idx])
    mae_base = float(mean_absolute_error(y[split.test_idx], base_pred))
    rmse_base = float(math.sqrt(mean_squared_error(y[split.test_idx], base_pred)))

    return {
        "ridge": asdict(EvalRegression(mae=mae, rmse=rmse, ic=ic)),
        "random_walk": asdict(EvalRegression(mae=mae_base, rmse=rmse_base, ic=0.0)),
    }


def train_classification_fold(df: pd.DataFrame, split: Split, features: List[str]) -> Dict[str, Any]:
    y = df[TARGET_CLS].astype(int).to_numpy(dtype=int)

    X = df[features].to_numpy()
    X = np.nan_to_num(X, nan=0.0)

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

    base_prob = float(np.mean(y[split.train_idx]))
    majority = int(round(base_prob))

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
        "logistic": asdict(EvalClassification(accuracy=acc, f1=f1, roc_auc=roc, brier=brier)),
        "majority": asdict(
            EvalClassification(
                accuracy=acc_base,
                f1=f1_base,
                roc_auc=roc_base,
                brier=brier_base,
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
    df = df[df["asof_date"].notna()].copy()

    df = df.sort_values("asof_date").reset_index(drop=True)

    # Minimal pipeline settings (keep simple for reproducibility).
    min_train = 500
    test_size = 60
    step = 60

    features = _select_features(df)

    df_reg = df[np.isfinite(df[TARGET_REG])].copy().reset_index(drop=True)
    df_cls = df[np.isfinite(df[TARGET_CLS])].copy().reset_index(drop=True)

    if len(df_reg) != len(df_cls):
        # Inconsistent labels should be rare; still allow but warn.
        print(
            f"[WARN] different row counts after label filtering: regression={len(df_reg)}, classification={len(df_cls)}"
        )

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

        reg_metrics = train_regression_fold(df_reg, split, features)
        cls_metrics = train_classification_fold(df_cls, split, features)

        regression_folds.append({"meta": fold_meta, "metrics": reg_metrics})
        classification_folds.append({"meta": fold_meta, "metrics": cls_metrics})

    def _aggregate_reg(key: str, agg_func) -> Optional[float]:
        vals = [fold["metrics"]["ridge"].get(key) for fold in regression_folds]
        return agg_func(vals)

    def _aggregate_reg_base(key: str, agg_func) -> Optional[float]:
        vals = [fold["metrics"]["random_walk"].get(key) for fold in regression_folds]
        return agg_func(vals)

    def _aggregate_cls(key: str, agg_func) -> Optional[float]:
        vals = [fold["metrics"]["logistic"].get(key) for fold in classification_folds]
        return agg_func(vals)

    def _aggregate_cls_base(key: str, agg_func) -> Optional[float]:
        vals = [fold["metrics"]["majority"].get(key) for fold in classification_folds]
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
                    "mae": _aggregate_reg("mae", _nanmean),
                    "rmse": _aggregate_reg("rmse", _nanmean),
                    "ic": _aggregate_reg("ic", _nanmean),
                },
                "ridge_std": {
                    "mae": _aggregate_reg("mae", _nanstd),
                    "rmse": _aggregate_reg("rmse", _nanstd),
                    "ic": _aggregate_reg("ic", _nanstd),
                },
                "random_walk_mean": {
                    "mae": _aggregate_reg_base("mae", _nanmean),
                    "rmse": _aggregate_reg_base("rmse", _nanmean),
                    "ic": _aggregate_reg_base("ic", _nanmean),
                },
                "random_walk_std": {
                    "mae": _aggregate_reg_base("mae", _nanstd),
                    "rmse": _aggregate_reg_base("rmse", _nanstd),
                    "ic": _aggregate_reg_base("ic", _nanstd),
                },
            },
            "folds": regression_folds,
        },
        "classification": {
            "summary": {
                "logistic_mean": {
                    "accuracy": _aggregate_cls("accuracy", _nanmean),
                    "f1": _aggregate_cls("f1", _nanmean),
                    "roc_auc": _aggregate_cls("roc_auc", _nanmean),
                    "brier": _aggregate_cls("brier", _nanmean),
                },
                "logistic_std": {
                    "accuracy": _aggregate_cls("accuracy", _nanstd),
                    "f1": _aggregate_cls("f1", _nanstd),
                    "roc_auc": _aggregate_cls("roc_auc", _nanstd),
                    "brier": _aggregate_cls("brier", _nanstd),
                },
                "majority_mean": {
                    "accuracy": _aggregate_cls_base("accuracy", _nanmean),
                    "f1": _aggregate_cls_base("f1", _nanmean),
                    "roc_auc": _aggregate_cls_base("roc_auc", _nanmean),
                    "brier": _aggregate_cls_base("brier", _nanmean),
                },
                "majority_std": {
                    "accuracy": _aggregate_cls_base("accuracy", _nanstd),
                    "f1": _aggregate_cls_base("f1", _nanstd),
                    "roc_auc": _aggregate_cls_base("roc_auc", _nanstd),
                    "brier": _aggregate_cls_base("brier", _nanstd),
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

    print(
        f"[OK] walk-forward evaluation written: {OUTPUT_FILE} ({len(regression_folds)} folds)"
    )


if __name__ == "__main__":
    main()
