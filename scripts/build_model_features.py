# -*- coding: utf-8 -*-
"""
build_model_features.py

职责：
1. 读取 JD-data 的基础数据：
   - fundamental_features.csv
   - 个股 daily_clean.csv
   - 指数 clean.csv
   - 代理层 clean.csv
   - 港股交易日历（仅辅助校验，不再作为唯一主轴）
2. 以个股实际可用交易日为 asof_date 主轴，构建 model_features.csv
3. 严格采用 as-of 对齐：
   - 每个 asof_date 只能吃到该日及以前可见的基本面锚点
4. 输出正式模型消费表：
   data_model/02618.HK/model_features.csv

V2.3 核心修复：
1. 保持“以个股实际交易日为主轴”的历史全覆盖逻辑
2. 保持已完成的首轮修剪：
   - 移除 ret_1519_* 与 alpha_vs_1519_5d
   - 不再加载 1519.HK 代理层
3. 按当前主线继续做“特征修剪收口”：
   - 移除高缺失且弱信号特征：
     external_isc_customer_yoy
     external_isc_arpc_yoy
     receivables_loss_allowance_ratio
     contract_assets
     contract_assets_ratio

说明：
- 当前不负责标签生成
- 当前不负责训练
- 当前不负责预测
- 当前只负责稳定生成模型消费母表
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional

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

# 已按当前主线移除 1519
PROXY_FILES = {
    "9618": REPO_ROOT / "data_clean" / "9618.HK" / "daily_clean.csv",
    "3690": REPO_ROOT / "data_clean" / "3690.HK" / "daily_clean.csv",
    "9988": REPO_ROOT / "data_clean" / "9988.HK" / "daily_clean.csv",
    "2057": REPO_ROOT / "data_clean" / "2057.HK" / "daily_clean.csv",
}

BUILD_VERSION = "model_features_v2.3"

# 数值基本面字段
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
    "inventories",
    "trade_payables",
    "receivables_ratio",
    "inventory_ratio",
    "payables_ratio",
    "supplier_finance_arrangements",
    "supplier_finance_ratio",
    "receivables_over_6m_ratio",
    "receivables_over_12m_ratio",
    "payables_over_12m_ratio",
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
]

FUNDAMENTAL_META_COLUMNS = [
    "report_date",
    "period_type",
    "quality_flag",
    "data_version",
]

# 关键字段闸门
CRITICAL_FUNDAMENTAL_FIELDS = [
    "revenue",
    "gross_margin",
    "net_profit",
    "total_assets",
    "total_liabilities",
    "operating_cash_flow",
    "debt_to_asset_ratio",
    "revenue_external",
    "revenue_jd_group",
    "warehouse_count",
]

# 更偏“慢变量核心”的关键字段
ANCHOR_STRENGTH_FIELDS = [
    "revenue",
    "gross_profit",
    "gross_margin",
    "net_profit",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "operating_cash_flow",
    "net_cash",
    "debt_to_asset_ratio",
    "external_revenue_ratio",
    "jd_group_revenue_ratio",
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
    "fundamental_anchor_score",
    "fundamental_critical_nonnull_count",
    "fundamental_critical_nonnull_ratio",
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
    # 代理层（已移除 1519）
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
    "alpha_vs_9618_5d",
    "alpha_vs_3690_5d",
    "alpha_vs_9988_5d",
    "alpha_vs_2057_5d",
    # 质量控制
    "row_quality_flag",
    "missing_ratio",
    "feature_count_total",
    "feature_count_nonnull",
    "build_version",
    "built_at",
]


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
    mapping = {
        "CONFIRMED": 3,
        "PARTIAL": 2,
        "RAW": 1,
    }
    return mapping.get(str(flag).upper(), 0)


def period_rank(period_type: str) -> int:
    mapping = {
        "annual": 3,
        "semiannual": 2,
        "quarter": 1,
    }
    return mapping.get(str(period_type).lower(), 0)


def count_nonnull_fields(row: pd.Series, cols: List[str]) -> int:
    count = 0
    for col in cols:
        if col in row.index and pd.notna(row[col]):
            count += 1
    return count


def calc_anchor_strength_score(row: pd.Series) -> float:
    """
    锚点选择综合分：
    1. 质量优先
    2. 周期优先
    3. 关键字段越全越优
    4. 慢变量核心越全越优
    """
    q_rank = quality_rank(str(row.get("quality_flag", "UNKNOWN")))
    p_rank = period_rank(str(row.get("period_type", "unknown")))

    critical_nonnull = count_nonnull_fields(row, CRITICAL_FUNDAMENTAL_FIELDS)
    anchor_strength = count_nonnull_fields(row, ANCHOR_STRENGTH_FIELDS)

    score = (
        q_rank * 1000
        + p_rank * 100
        + critical_nonnull * 10
        + anchor_strength
    )
    return float(score)


def derive_row_quality_flag(
    missing_ratio: float,
    fundamental_quality_flag: str,
    fundamental_anchor_period_type: str,
    critical_nonnull_ratio: float,
) -> str:
    f = str(fundamental_quality_flag).upper()
    p = str(fundamental_anchor_period_type).lower()

    if (
        f == "CONFIRMED"
        and critical_nonnull_ratio >= 0.90
        and missing_ratio <= 0.10
    ):
        return "PASS"

    if (
        f in {"CONFIRMED", "PARTIAL"}
        and critical_nonnull_ratio >= 0.60
        and missing_ratio <= 0.25
    ):
        return "PARTIAL"

    if p == "quarter" and (f == "RAW" or critical_nonnull_ratio < 0.60):
        return "REVIEW"

    return "REVIEW"


# =========================
# 数据加载
# =========================

def load_calendar(required: bool = False) -> pd.DataFrame:
    df = read_csv_safe(CALENDAR_FILE, required=required)
    if df.empty:
        return df

    date_col = find_first_existing_column(df, ["trade_date", "date", "calendar_date"])
    if date_col is None:
        raise ValueError("hk_trade_calendar.csv 未找到日期列")

    df = standardize_date_col(df, date_col)
    df = df.rename(columns={date_col: "date"})

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

    if "period_type" not in df.columns:
        df["period_type"] = "unknown"
    if "quality_flag" not in df.columns:
        df["quality_flag"] = "UNKNOWN"
    if "data_version" not in df.columns:
        df["data_version"] = "UNKNOWN"

    keep_cols = ["symbol"] + FUNDAMENTAL_META_COLUMNS
    for col in FUNDAMENTAL_NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
        keep_cols.append(col)

    df = df[keep_cols].copy()

    df["quality_rank"] = df["quality_flag"].map(quality_rank)
    df["period_rank"] = df["period_type"].map(period_rank)

    df["critical_nonnull_count"] = df.apply(
        lambda r: count_nonnull_fields(r, CRITICAL_FUNDAMENTAL_FIELDS),
        axis=1,
    )
    df["critical_nonnull_ratio"] = df["critical_nonnull_count"] / len(CRITICAL_FUNDAMENTAL_FIELDS)

    df["anchor_score"] = df.apply(calc_anchor_strength_score, axis=1)

    df = df.sort_values(
        ["report_date", "anchor_score", "quality_rank", "period_rank"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)

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


def resolve_asof_dates(
    stock_df: pd.DataFrame,
    start_date: Optional[str],
    end_date: Optional[str],
) -> pd.DataFrame:
    """
    正式母表主轴改为：个股实际可用交易日。
    这样不会再被不完整的 hk_trade_calendar.csv 截断历史。
    """
    if stock_df.empty:
        raise ValueError("个股行情为空，无法生成样本")

    asof_df = stock_df[["date"]].drop_duplicates().sort_values("date").reset_index(drop=True)

    if start_date:
        start_ts = pd.to_datetime(start_date).normalize()
        asof_df = asof_df[asof_df["date"] >= start_ts].copy()

    if end_date:
        end_ts = pd.to_datetime(end_date).normalize()
        asof_df = asof_df[asof_df["date"] <= end_ts].copy()

    if asof_df.empty:
        raise ValueError("过滤日期后，个股可用交易日为空")

    return asof_df.rename(columns={"date": "asof_date"}).reset_index(drop=True)


def print_calendar_coverage_diagnostics(asof_df: pd.DataFrame) -> None:
    calendar_df = load_calendar(required=False)
    if calendar_df.empty:
        print("[WARN] hk_trade_calendar.csv 缺失或为空：已直接使用个股交易日作为主轴")
        return

    calendar_dates = set(calendar_df["date"].tolist())
    asof_dates = set(asof_df["asof_date"].tolist())
    missing_in_calendar = sorted(asof_dates - calendar_dates)

    if not missing_in_calendar:
        print("[OK] calendar 覆盖了全部个股交易日")
        return

    missing_years = sorted({d.year for d in missing_in_calendar})
    print(
        "[WARN] hk_trade_calendar.csv 未覆盖全部个股交易日，"
        f"缺失 {len(missing_in_calendar)} 个日期，涉及年份: {missing_years}；"
        "已改为直接使用个股交易日主轴，避免历史被截断"
    )


# =========================
# 锚点选择 V2
# =========================

def select_best_fundamental_anchor(candidates: pd.DataFrame) -> Optional[pd.Series]:
    if candidates.empty:
        return None

    ranked = candidates.sort_values(
        ["anchor_score", "quality_rank", "period_rank", "report_date"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    return ranked.iloc[0]


def build_fundamental_anchor_map(asof_df: pd.DataFrame, fundamental_df: pd.DataFrame) -> pd.DataFrame:
    if fundamental_df.empty:
        raise ValueError("fundamental_features.csv 为空，无法构建 model_features")

    rows = []
    f = fundamental_df.copy().sort_values("report_date").reset_index(drop=True)

    for asof_date in asof_df["asof_date"].tolist():
        candidates = f[f["report_date"] <= asof_date].copy()
        best = select_best_fundamental_anchor(candidates)

        if best is None:
            row = {
                "asof_date": asof_date,
                "fundamental_anchor_date": pd.NaT,
                "fundamental_anchor_period_type": np.nan,
                "fundamental_lag_days": np.nan,
                "fundamental_quality_flag": np.nan,
                "fundamental_data_version": np.nan,
                "fundamental_anchor_score": np.nan,
                "fundamental_critical_nonnull_count": np.nan,
                "fundamental_critical_nonnull_ratio": np.nan,
            }
            for col in FUNDAMENTAL_NUMERIC_COLUMNS:
                row[col] = np.nan
            rows.append(row)
            continue

        row = {
            "asof_date": asof_date,
            "fundamental_anchor_date": best["report_date"],
            "fundamental_anchor_period_type": best["period_type"],
            "fundamental_lag_days": (asof_date - best["report_date"]).days,
            "fundamental_quality_flag": best["quality_flag"],
            "fundamental_data_version": best["data_version"],
            "fundamental_anchor_score": best["anchor_score"],
            "fundamental_critical_nonnull_count": best["critical_nonnull_count"],
            "fundamental_critical_nonnull_ratio": best["critical_nonnull_ratio"],
        }

        for col in FUNDAMENTAL_NUMERIC_COLUMNS:
            row[col] = best[col] if col in best.index else np.nan

        rows.append(row)

    return pd.DataFrame(rows)


# =========================
# 市场特征拼接
# =========================

def prepare_stock_features(stock_df: pd.DataFrame) -> pd.DataFrame:
    df = make_return_features(stock_df, prefix="stock", close_col="close")
    keep = [
        "date",
        "close",
        "stock_ret_1d",
        "stock_ret_5d",
        "stock_ret_20d",
        "stock_vol_5d",
        "stock_vol_20d",
    ]
    return df[keep].rename(columns={"date": "asof_date", "close": "stock_close"})


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
    fundamental_df = load_fundamental(symbol)
    stock_df = load_daily_like(STOCK_DAILY_FILE, symbol=symbol)

    asof_df = resolve_asof_dates(
        stock_df=stock_df,
        start_date=start_date,
        end_date=end_date,
    )
    print_calendar_coverage_diagnostics(asof_df)

    base_df = build_fundamental_anchor_map(asof_df, fundamental_df)
    base_df["symbol"] = symbol

    base_df["trade_year"] = base_df["asof_date"].dt.year
    base_df["trade_month"] = base_df["asof_date"].dt.month
    base_df["trade_dayofweek"] = base_df["asof_date"].dt.dayofweek

    stock_features = prepare_stock_features(stock_df)
    out = base_df.merge(stock_features, on="asof_date", how="left")

    for idx_key, idx_path in INDEX_FILES.items():
        idx_df = load_daily_like(idx_path)
        idx_feat = prepare_index_features(idx_df, idx_key)
        out = out.merge(idx_feat, on="asof_date", how="left")

    out["alpha_hsi_5d"] = out["stock_ret_5d"] - out["hsi_ret_5d"]
    out["alpha_hktech_5d"] = out["stock_ret_5d"] - out["hktech_ret_5d"]
    out["alpha_hscei_5d"] = out["stock_ret_5d"] - out["hscei_ret_5d"]

    out["alpha_hsi_20d"] = out["stock_ret_20d"] - out["hsi_ret_20d"]
    out["alpha_hktech_20d"] = out["stock_ret_20d"] - out["hktech_ret_20d"]
    out["alpha_hscei_20d"] = out["stock_ret_20d"] - out["hscei_ret_20d"]

    for proxy_code, proxy_path in PROXY_FILES.items():
        proxy_df = load_daily_like(proxy_path)
        proxy_feat = prepare_proxy_features(proxy_df, proxy_code)
        out = out.merge(proxy_feat, on="asof_date", how="left")
        out[f"alpha_vs_{proxy_code}_5d"] = out["stock_ret_5d"] - out[f"ret_{proxy_code}_5d"]

    exclude_cols = {
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
        "fundamental_anchor_score",
        "fundamental_critical_nonnull_count",
        "fundamental_critical_nonnull_ratio",
        "row_quality_flag",
        "missing_ratio",
        "feature_count_total",
        "feature_count_nonnull",
        "build_version",
        "built_at",
    }

    feature_cols_for_missing = [c for c in FINAL_COLUMNS_ORDER if c not in exclude_cols]

    out["feature_count_total"] = len(feature_cols_for_missing)
    out["feature_count_nonnull"] = out[feature_cols_for_missing].notna().sum(axis=1)
    out["missing_ratio"] = 1.0 - out["feature_count_nonnull"] / out["feature_count_total"]

    out["row_quality_flag"] = out.apply(
        lambda r: derive_row_quality_flag(
            missing_ratio=float(r["missing_ratio"]),
            fundamental_quality_flag=str(r.get("fundamental_quality_flag", "UNKNOWN")),
            fundamental_anchor_period_type=str(r.get("fundamental_anchor_period_type", "unknown")),
            critical_nonnull_ratio=float(
                r.get("fundamental_critical_nonnull_ratio")
                if pd.notna(r.get("fundamental_critical_nonnull_ratio"))
                else 0.0
            ),
        ),
        axis=1,
    )

    out["build_version"] = BUILD_VERSION
    out["built_at"] = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for col in FINAL_COLUMNS_ORDER:
        if col not in out.columns:
            out[col] = np.nan

    out = out[FINAL_COLUMNS_ORDER].sort_values(["symbol", "asof_date"]).reset_index(drop=True)
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
        print(
            "[OK] anchor_period_counts="
            f"{model_df['fundamental_anchor_period_type'].value_counts(dropna=False).to_dict()}"
        )
        print(
            "[OK] fundamental_quality_counts="
            f"{model_df['fundamental_quality_flag'].value_counts(dropna=False).to_dict()}"
        )


if __name__ == "__main__":
    main()
