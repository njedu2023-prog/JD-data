import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)
from scipy.stats import pearsonr


DATASET_PATH = Path("data_model/02618.HK/model_dataset.csv")
OUTPUT_DIR = Path("data_model/02618.HK")
REPORT_FILE = OUTPUT_DIR / "baseline_eval_v1.json"


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["asof_date"] = pd.to_datetime(df["asof_date"])
    return df


def time_split(df: pd.DataFrame, test_ratio: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("asof_date").reset_index(drop=True)
    n = len(df)
    n_test = max(50, int(n * test_ratio))
    n_test = min(n - 1, n_test)
    n_train = n - n_test

    train = df.iloc[:n_train].copy()
    test = df.iloc[n_train:].copy()
    return train, test


def select_feature_columns(df: pd.DataFrame) -> list[str]:
    label_cols = {"y_ret_1d", "y_ret_5d", "y_ret_20d", "y_up_1d", "label_version"}
    id_cols = {"symbol", "asof_date"}

    drop_cols = list((label_cols | id_cols) & set(df.columns))
    feature_df = df.drop(columns=drop_cols, errors="ignore")

    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    return numeric_cols


def clean_xy(df: pd.DataFrame, feature_cols: list[str], target_col: str):
    X = df[feature_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    y = df[target_col].astype(float).values
    return X, y


def regression_metrics(y_true, y_pred) -> dict:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    try:
        ic = float(pearsonr(y_true, y_pred)[0])
    except Exception:
        ic = float("nan")
    return {"MAE": mae, "RMSE": rmse, "IC": ic}


def classification_metrics(y_true, y_prob) -> dict:
    y_pred = (y_prob >= 0.5).astype(int)
    acc = float(accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred))
    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auc = float("nan")
    brier = float(brier_score_loss(y_true, y_prob))
    return {"Accuracy": acc, "F1": f1, "AUC": auc, "Brier": brier}


def random_walk_regression_baseline(y_true) -> dict:
    mae = float(np.mean(np.abs(y_true)))
    rmse = float(np.sqrt(np.mean(np.square(y_true))))
    return {"MAE": mae, "RMSE": rmse, "IC": 0.0}


def constant_prob_baseline(y_true, prob: float) -> dict:
    y_prob = np.full_like(y_true, prob, dtype=float)
    return classification_metrics(y_true, y_prob)


def main():
    df = load_dataset(DATASET_PATH)
    feature_cols = select_feature_columns(df)
    train_df, test_df = time_split(df)

    report = {
        "report_version": "baseline_eval_v1",
        "built_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": {
            "n_rows": int(len(df)),
            "n_features": int(len(feature_cols)),
            "train_rows": int(len(train_df)),
            "test_rows": int(len(test_df)),
        },
    }

    # Regression: y_ret_1d
    report["regression"] = {"target": "y_ret_1d", "models": {}}
    X_train, y_train = clean_xy(train_df, feature_cols, "y_ret_1d")
    X_test, y_test = clean_xy(test_df, feature_cols, "y_ret_1d")

    report["regression"]["models"]["random_walk"] = random_walk_regression_baseline(y_test)

    reg = LinearRegression()
    reg.fit(X_train, y_train)
    y_pred = reg.predict(X_test)
    report["regression"]["models"]["linear_regression"] = regression_metrics(y_test, y_pred)

    # Classification: y_up_1d
    report["classification"] = {"target": "y_up_1d", "models": {}}
    X_train_cls, y_train_cls = clean_xy(train_df, feature_cols, "y_up_1d")
    X_test_cls, y_test_cls = clean_xy(test_df, feature_cols, "y_up_1d")

    base_prob = float(np.mean(y_train_cls))
    report["classification"]["models"]["constant_mean_prob"] = constant_prob_baseline(y_test_cls, base_prob)

    cls = LogisticRegression(max_iter=200, n_jobs=-1)
    cls.fit(X_train_cls, y_train_cls)
    y_prob = cls.predict_proba(X_test_cls)[:, 1]
    report["classification"]["models"]["logistic_regression"] = classification_metrics(y_test_cls, y_prob)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
