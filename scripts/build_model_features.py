# -*- coding: utf-8 -*-
"""
build_model_features.py

职责：
1. 读取 JD-data 的基础数据：
   - fundamental_features.csv
   - 个股 daily_clean.csv
   - 指数 clean.csv
   - 代理层 clean.csv
   - 港股交易日历
2. 以港股交易日为 asof_date 主轴，构建 model_features.csv
3. 严格采用 as-of 对齐：
   - 每个 asof_date 只能吃到该日及以前可见的基本面锚点
   - 默认以 report_date <= asof_date 做首版近似锚定
4. 输出正式模型消费表：
   data_model/02618.HK/model_features.csv

说明：
- 本脚本是 V1 首版构建器，目标是先把“统一消费表”稳定落地
- 当前不负责标签生成
- 当前不负责训练
- 当前不负责预测
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


# =========================
# 基础路径与配置
# =========================

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SYMBOL = "02618.HK"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data_model" / DEFAULT_SYMBOL
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "model_features.csv"

CALENDAR_FILE = REPO_ROOT / "calendar" / "hk_trade_calendar.csv"
FUNDAMENTAL_FILE = REPO_ROOT / "data_fundamental" / DEFAULT_SYMBOL / "fundamental_features.csv"
STOCK_DAILY_FILE = REPO_ROOT / "data_clean" / DEFAULT_SYMBOL / "daily_clean.csv"

INDEX_FILES = {
    "HSI": REPO_ROOT / "data_clean" / "HSI" / "hsi_clean.csv",
    "HKTECH": REPO_ROOT / "data_clean" / "HKTECH" / "hktech_clean.csv",
    "HSCEI": REPO_ROOT / "data_clean" / "HSCEI" / "hscei_clean.csv",
}

PROXY_FILES = {
    "9618": REPO_ROOT / "data_clean" / "9618.HK" / "daily_clean.csv",
    "3690": REPO_ROOT / "data_clean" / "3690.HK" / "daily_clean.csv",
    "9988": REPO_ROOT / "data_clean" / "9988.HK" / "daily_clean.csv",
    "2057": REPO_ROOT / "data_clean" / "2057.HK" / "daily_clean.csv",
    "1519": REPO_ROOT / "data_clean" / "1519.HK" / "daily_clean.csv",
}

FUNDAMENTAL_NUMERIC_COLUMNS = [
    "revenue",
    "gross_profit",
    "gross_margin",
    "net_profit",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "current_assets",
    "current_liabilities",
    "borrowings",
    "lease_liabilities",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "free_cash_inflow",
    "capex_net",
    "net_cash",
    "working_capital",
    "debt_to_asset_ratio",
    "lease_burden_ratio",
    "trade_receivables",
    "contract_assets",
    "inventories",
    "trade_payables",
    "receivables_ratio",
    "contract_assets_ratio",
    "inventory_ratio",
    "payables_ratio",
    "supplier_finance_arrangements",
    "supplier_finance_ratio",
    "receivables_over_6m_ratio",
    "receivables_over_12m_ratio",
    "payables_over_12m_ratio",
    "receivables_loss_allowance_ratio",
    "free_cash_flow_margin",
    "capex_intensity",
    "operating_cash_flow_margin",
    "cash_conversion_quality_score",
    "revenue_jd_group",
    "revenue_external",
    "revenue_integrated_supply_chain",
    "revenue_external_integrated_supply_chain",
    "revenue_other_customers",
    "external_revenue_ratio",
    "jd_group_revenue_ratio",
    "integrated_supply_chain_revenue_ratio",
    "external_isc_revenue_ratio",
    "warehouse_count",
    "external_isc_customer_count",
    "external_isc_arpc",
    "external_isc_customer_yoy",
    "external_isc_arpc_yoy",
]

FUNDAMENTAL_META_COLUMNS = [
    "report_date",
    "period_type",
    "quality_flag",
    "data_version",
]

FINAL_COLUMNS_ORDER = [
    # 身份层
    "symbol",
    "asof_date",
    "trade_year",
    "trade_month",
    "trade_dayofweek",
    # 财报锚点层
    "fundamental_anchor_date",
    "fundamental_anchor_period_type",
    "fundamental_lag_days",
    "fundamental_quality_flag",
    "fundamental_data_version",
    # 基本面慢变量层
    *FUNDAMENTAL_NUMERIC_COLUMNS,
    # 个股市场层
    "stock_close",
    "stock_ret_1d",
    "stock_ret_5d",
    "stock_ret_20d",
    "stock_vol_5d",
    "stock_vol_20d",
    # 指数收益层
    "hsi_ret_1d",
    "hsi_ret_5d",
    "hsi_ret_20d",
    "hktech_ret_1d",
    "hktech_ret_5d",
    "hktech_ret_20d",
    "hscei_ret_1d",
    "hscei_ret_5d",
    "hscei_ret_20d",
    # 相对强弱
    "alpha_hsi_5d",
    "alpha_hktech_5d",
    "alpha_hscei_5d",
    "alpha_hsi_20d",
    "alpha_hktech_20d",
    "alpha_hscei_20d",
    # 代理层
    "ret_9618_1d",
    "ret_9618_5d",
    "ret_9618_20d",
    "ret_3690_1d",
    "ret_3690_5d",
    "ret_3690_20d",
    "ret_9988_1d",
    "ret_9988_5d",
    "ret_9988_20d",
    "ret_2057_1d",
    "ret_2057_5d",
    "ret_2057_20d",
    "ret_1519_1d",
    "ret_1519_5d",
    "ret_1519_20d",
    "alpha_vs_9618_5d",
    "alpha_vs_3690_5d",
    "alpha_vs_9988_5d",
    "alpha_vs_2057_5d",
    "alpha_vs_1519_5d",
    # 质量控制
    "row_quality_flag",
    "missing_ratio",
    "feature_count_total",
    "feature_count_nonnull",
    "build_version",
    "built_at",
]

BUILD_VERSION = "model_features_v1.0"


# =========================
# 工具函数
# =========================

def read_csv_safe(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"缺少文件: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)


def standardize_date_col(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    if date_col not in df.columns:
        raise ValueError(f"缺少日期列: {date_col}")
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
    df = df[df[date_col].notna()].copy()
    return df


def find_first_existing_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def normalize_symbol_column(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    df = df.copy()
    if "symbol" not in df.columns:
        df["symbol"] = symbol
    return df


def make_return_features(df: pd.DataFrame, prefix: str, close_col: str = "close") -> pd.DataFrame:
    """
    给任意按日期排序的行情表增加收益与波动字段。
    """
    if df.empty:
        return df

    df = df.copy()
    df = df.sort_values("date").reset_index(drop=True)

    if close_col not in df.columns:
        raise ValueError(f"缺少 close 列: {close_col}")

    df[f"{prefix}_ret_1d"] = df[close_col].pct_change(1)
    df[f"{prefix}_ret_5d"] = df[close_col].pct_change(5)
    df[f"{prefix}_ret_20d"] = df[close_col].pct_change(20)

    if prefix == "stock":
        df[f"{prefix}_vol_5d"] = df[f"{prefix}_ret_1d"].rolling(5).std()
        df[f"{prefix}_vol_20d"] = df[f"{prefix}_ret_1d"].rolling(20).std()

    return df


def quality_rank(flag: str) -> int:
    """
    质量等级排序：
    CONFIRMED > PARTIAL > RAW > 其他
    """
    mapping = {
        "CONFIRMED": 3,
        "PARTIAL": 2,
        "RAW": 1,
    }
    return mapping.get(str(flag).upper(), 0)


def derive_row_quality_flag(missing_ratio: float, fundamental_quality_flag: str) -> str:
    f = str(fundamental_quality_flag).upper()
    if f == "CONFIRMED" and missing_ratio <= 0.10:
        return "PASS"
    if f in {"CONFIRMED", "PARTIAL"} and missing_ratio <= 0.25:
        return "PARTIAL"
    return "REVIEW"


def safe_div(a: float, b: float) -> float:
    if pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan
    return a / b


# =========================
# 数据加载
# =========================

def load_calendar() -> pd.DataFrame:
    df = read_csv_safe(CALENDAR_FILE, required=True)

    date_col = find_first_existing_column(
        df,
        ["trade_date", "date", "calendar_date"]
    )
    if date_col is None:
        raise ValueError("hk_trade_calendar.csv 未找到日期列")

    df = standardize_date_col(df, date_col)
    df = df.rename(columns={date_col: "date"})

    # 兼容不同字段命名
    is_open_col = find_first_existing_column(df, ["is_open", "open", "is_trade_day"])
    if is_open_col is not None:
        df = df[df[is_open_col].astype(str).isin(["1", "True", "true", "TRUE"])].copy()

    df = df[["date"]].drop_duplicates().sort_values("date").reset_index(drop=True)
    return df


def load_fundamental(symbol: str) -> pd.DataFrame:
    df = read_csv_safe(FUNDAMENTAL_FILE, required=True)
    df = standardize_date_col(df, "report_date")

    if "symbol" in df.columns:
        df = df[df["symbol"] == symbol].copy()
    else:
        df["symbol"] = symbol

    # 首版保留 annual / semiannual / quarter，但优先级 annual > semiannual > quarter
    period_rank_map = {
        "annual": 3,
        "semiannual": 2,
        "quarter": 1,
    }
    df["period_rank"] = df["period_type"].map(period_rank_map).fillna(0)

    if "quality_flag" not in df.columns:
        df["quality_flag"] = "UNKNOWN"
    if "data_version" not in df.columns:
        df["data_version"] = ""

    keep_cols = ["symbol"] + FUNDAMENTAL_META_COLUMNS + ["period_rank"]
    for col in FUNDAMENTAL_NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
        keep_cols.append(col)

    df = df[keep_cols].copy()
    df = df.sort_values(["report_date", "period_rank"]).reset_index(drop=True)
    return df


def load_daily_like(path: Path, symbol: Optional[str] = None) -> pd.DataFrame:
    df = read_csv_safe(path, required=True)

    date_col = find_first_existing_column(df, ["date", "trade_date"])
    if date_col is None:
        raise ValueError(f"{path.name} 未找到 date/trade_date 列")
    df = standardize_date_col(df, date_col)
    df = df.rename(columns={date_col: "date"})

    if symbol is not None:
        df = normalize_symbol_column(df, symbol)

    close_col = find_first_existing_column(df, ["close", "adj_close", "Close"])
    if close_col is None:
        raise ValueError(f"{path.name} 未找到 close 列")
    if close_col != "close":
        df = df.rename(columns={close_col: "close"})

    df = df.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return df


# =========================
# 基本面对齐
# =========================

def build_fundamental_anchor_map(calendar_df: pd.DataFrame, fundamental_df: pd.DataFrame) -> pd.DataFrame:
    """
    对每个交易日，找到 report_date <= asof_date 的最近一条基本面记录。
    若同一 report_date 有多条，则优先：
    period_rank 高者优先，quality_flag 高者优先。
    """
    if fundamental_df.empty:
        raise ValueError("fundamental_features.csv 为空，无法构建 model_features")

    f = fundamental_df.copy()
    f["quality_rank"] = f["quality_flag"].map(quality_rank)

    # 同一个 report_date 下保留最优记录
    f = (
        f.sort_values(["report_date", "period_rank", "quality_rank"], ascending=[True, False, False])
         .drop_duplicates(subset=["report_date"], keep="first")
         .reset_index(drop=True)
    )

    base = calendar_df.copy()
    base = base.rename(columns={"date": "asof_date"})

    # merge_asof 要求排序
    left = base.sort_values("asof_date").reset_index(drop=True)
    right = f.sort_values("report_date").reset_index(drop=True)

    merged = pd.merge_asof(
        left,
        right,
        left_on="asof_date",
        right_on="report_date",
        direction="backward",
        allow_exact_matches=True,
    )

    merged = merged.rename(
        columns={
            "report_date": "fundamental_anchor_date",
            "period_type": "fundamental_anchor_period_type",
            "quality_flag": "fundamental_quality_flag",
            "data_version": "fundamental_data_version",
        }
    )

    merged["fundamental_lag_days"] = (
        merged["asof_date"] - merged["fundamental_anchor_date"]
    ).dt.days

    return merged


# =========================
# 市场特征拼接
# =========================

def prepare_stock_features(stock_df: pd.DataFrame) -> pd.DataFrame:
    df = make_return_features(stock_df, prefix="stock", close_col="close")
    keep = ["date", "close", "stock_ret_1d", "stock_ret_5d", "stock_ret_20d", "stock_vol_5d", "stock_vol_20d"]
    df = df[keep].rename(columns={"date": "asof_date", "close": "stock_close"})
    return df


def prepare_index_features(index_df: pd.DataFrame, key: str) -> pd.DataFrame:
    prefix_map = {
        "HSI": "hsi",
        "HKTECH": "hktech",
        "HSCEI": "hscei",
    }
    prefix = prefix_map[key]
    tmp = make_return_features(index_df, prefix=prefix, close_col="close")
    keep = ["date", f"{prefix}_ret_1d", f"{prefix}_ret_5d", f"{prefix}_ret_20d"]
    return tmp[keep].rename(columns={"date": "asof_date"})


def prepare_proxy_features(proxy_df: pd.DataFrame, code: str) -> pd.DataFrame:
    prefix = f"ret_{code}"
    tmp = make_return_features(proxy_df, prefix=prefix, close_col="close")
    keep = ["date", f"{prefix}_ret_1d", f"{prefix}_ret_5d", f"{prefix}_ret_20d"]
    renamed = {
        "date": "asof_date",
        f"{prefix}_ret_1d": f"ret_{code}_1d",
        f"{prefix}_ret_5d": f"ret_{code}_5d",
        f"{prefix}_ret_20d": f"ret_{code}_20d",
    }
    return tmp[keep].rename(columns=renamed)


# =========================
# 主流程
# =========================

def build_model_features(symbol: str, start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
    calendar_df = load_calendar()
    fundamental_df = load_fundamental(symbol)
    stock_df = load_daily_like(STOCK_DAILY_FILE, symbol=symbol)

    if start_date:
        start_ts = pd.to_datetime(start_date).normalize()
        calendar_df = calendar_df[calendar_df["date"] >= start_ts].copy()

    if end_date:
        end_ts = pd.to_datetime(end_date).normalize()
        calendar_df = calendar_df[calendar_df["date"] <= end_ts].copy()

    if calendar_df.empty:
        raise ValueError("过滤日期后，交易日历为空")

    # 以个股行情实际存在日期做进一步约束，避免空交易日样本泛滥
    stock_available_dates = set(stock_df["date"].dropna().tolist())
    calendar_df = calendar_df[calendar_df["date"].isin(stock_available_dates)].copy()

    if calendar_df.empty:
        raise ValueError("交易日历与个股行情无交集，无法生成样本")

    base_df = build_fundamental_anchor_map(calendar_df, fundamental_df)
    base_df["symbol"] = symbol

    # 时间衍生字段
    base_df["trade_year"] = base_df["asof_date"].dt.year
    base_df["trade_month"] = base_df["asof_date"].dt.month
    base_df["trade_dayofweek"] = base_df["asof_date"].dt.dayofweek

    # 个股特征
    stock_features = prepare_stock_features(stock_df)
    out = base_df.merge(stock_features, on="asof_date", how="left")

    # 指数特征
    for idx_key, idx_path in INDEX_FILES.items():
        idx_df = load_daily_like(idx_path)
        idx_feat = prepare_index_features(idx_df, idx_key)
        out = out.merge(idx_feat, on="asof_date", how="left")

    # 相对强弱
    out["alpha_hsi_5d"] = out["stock_ret_5d"] - out["hsi_ret_5d"]
    out["alpha_hktech_5d"] = out["stock_ret_5d"] - out["hktech_ret_5d"]
    out["alpha_hscei_5d"] = out["stock_ret_5d"] - out["hscei_ret_5d"]

    out["alpha_hsi_20d"] = out["stock_ret_20d"] - out["hsi_ret_20d"]
    out["alpha_hktech_20d"] = out["stock_ret_20d"] - out["hktech_ret_20d"]
    out["alpha_hscei_20d"] = out["stock_ret_20d"] - out["hscei_ret_20d"]

    # 代理层特征
    for proxy_code, proxy_path in PROXY_FILES.items():
        proxy_df = load_daily_like(proxy_path)
        proxy_feat = prepare_proxy_features(proxy_df, proxy_code)
        out = out.merge(proxy_feat, on="asof_date", how="left")
        out[f"alpha_vs_{proxy_code}_5d"] = out["stock_ret_5d"] - out[f"ret_{proxy_code}_5d"]

    # 质量控制
    feature_cols_for_missing = [
        c for c in FINAL_COLUMNS_ORDER
        if c not in {
            "symbol",
            "asof_date",
            "trade_year",
            "trade_month",
            "trade_dayofweek",
            "fundamental_anchor_date",
            "fundamental_anchor_period_type",
            "fundamental_lag_days",
            "fundamental_quality_flag",
            "fundamental_data_version",
            "row_quality_flag",
            "missing_ratio",
            "feature_count_total",
            "feature_count_nonnull",
            "build_version",
            "built_at",
        }
    ]

    out["feature_count_total"] = len(feature_cols_for_missing)
    out["feature_count_nonnull"] = out[feature_cols_for_missing].notna().sum(axis=1)
    out["missing_ratio"] = 1.0 - out["feature_count_nonnull"] / out["feature_count_total"]

    out["row_quality_flag"] = out.apply(
        lambda r: derive_row_quality_flag(
            missing_ratio=float(r["missing_ratio"]),
            fundamental_quality_flag=str(r.get("fundamental_quality_flag", "")),
        ),
        axis=1,
    )

    out["build_version"] = BUILD_VERSION
    out["built_at"] = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # 强制列存在
    for col in FINAL_COLUMNS_ORDER:
        if col not in out.columns:
            out[col] = np.nan

    out = out[FINAL_COLUMNS_ORDER].sort_values(["symbol", "asof_date"]).reset_index(drop=True)

    # 最后去重保护
    out = out.drop_duplicates(subset=["symbol", "asof_date"], keep="last").reset_index(drop=True)

    return out


# =========================
# CLI
# =========================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build model_features.csv for JD-data")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="证券代码，首版默认 02618.HK")
    parser.add_argument("--start-date", default=None, help="起始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", default=None, help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_FILE),
        help="输出文件路径，默认 data_model/02618.HK/model_features.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.symbol != DEFAULT_SYMBOL:
        raise ValueError("首版脚本当前仅支持 02618.HK，请勿直接扩展到其它 symbol 后不验收")

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model_df = build_model_features(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    model_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[OK] model_features 已生成: {output_path}")
    print(f"[OK] rows={len(model_df)}")
    if not model_df.empty:
        print(
            "[OK] date_range="
            f"{model_df['asof_date'].min()} -> {model_df['asof_date'].max()}"
        )
        print(
            "[OK] row_quality_flag_counts="
            f"{model_df['row_quality_flag'].value_counts(dropna=False).to_dict()}"
        )


if __name__ == "__main__":
    main()
