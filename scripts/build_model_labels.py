# -*- coding: utf-8 -*-
"""Build model labels for JD-data.

Outputs
- data_model/02618.HK/model_labels.csv
- data_model/02618.HK/model_dataset.csv (features + labels)

Primary targets (V1)
- y_ret_1d, y_ret_5d, y_ret_20d
- y_up_1d

Assumptions
- base daily close from data_clean/02618.HK/daily_clean.csv
- merge on asof_date with model_features.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SYMBOL = "02618.HK"

daily_path = REPO_ROOT / "data_clean" / SYMBOL / "daily_clean.csv"
feat_path = REPO_ROOT / "data_model" / SYMBOL / "model_features.csv"
labels_path = REPO_ROOT / "data_model" / SYMBOL / "model_labels.csv"
dataset_path = REPO_ROOT / "data_model" / SYMBOL / "model_dataset.csv"


def standardize_date(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.copy()
    df[col] = pd.to_datetime(df[col], errors="coerce").dt.normalize()
    df = df[df[col].notna()].copy()
    return df


def build_labels(df: pd.DataFrame) -> pd.DataFrame:
    """df has columns date, close."""
    df = df.sort_values("date").reset_index(drop=True)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    out = df[["date"]].copy()
    out = out.rename(columns={"date": "asof_date"})

    close = df["close"].values

    def forward_ret(k: int) -> np.ndarray:
        y = np.full(len(close), np.nan)
        y[:-k] = close[k:] / close[:-k] - 1.0
        return y

    out["y_ret_1d"] = forward_ret(1)
    out["y_ret_5d"] = forward_ret(5)
    out["y_ret_20d"] = forward_ret(20)
    out["y_up_1d"] = (out["y_ret_1d"] > 0).astype(float)

    out["label_version"] = "model_labels_v1"
    out["built_at"] = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return out


def build_dataset(feat_df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
    feat_df = feat_df.copy()
    feat_df["asof_date"] = pd.to_datetime(feat_df["asof_date"], errors="coerce").dt.normalize()

    out = feat_df.merge(labels_df, on="asof_date", how="left")
    out = out.sort_values(["symbol", "asof_date"]).reset_index(drop=True)
    return out


def main() -> None:
    daily_df = pd.read_csv(daily_path)

    # daily_clean is symbol-specific directory; keep defensive filter
    if "symbol" in daily_df.columns:
        daily_df = daily_df[daily_df["symbol"] == SYMBOL].copy()

    daily_df = standardize_date(daily_df, "date")

    labels_df = build_labels(daily_df)
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    labels_df.to_csv(labels_path, index=False, encoding="utf-8-sig")

    feat_df = pd.read_csv(feat_path)
    dataset_df = build_dataset(feat_df, labels_df)
    dataset_df.to_csv(dataset_path, index=False, encoding="utf-8-sig")

    print(f"[OK] labels rows={len(labels_df)}")
    print(f"[OK] dataset rows={len(dataset_df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default=SYMBOL)
    args = parser.parse_args()
    if args.symbol != SYMBOL:
        raise ValueError("首版脚本仅支持 02618.HK")

    main()
