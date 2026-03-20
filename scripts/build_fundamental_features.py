# -*- coding: utf-8 -*-
"""
build_fundamental_features.py

作用：
1. 读取摘要层：
   data_fundamental/<symbol>/fundamental_quarterly.csv

2. 读取标准财报明细层：
   data_fundamental/<symbol>/fundamental_statement_items.csv

3. 将 statement_items 按 item_code 透视为宽表

4. 与 quarterly 按主键合并

5. 生成下游消费层：
   data_fundamental/<symbol>/fundamental_features.csv

V1 设计原则：
- 不伪造 Q1 / Q3 缺失项
- 明细层优先用于派生计算
- 摘要层保留解释价值
- 比例字段统一输出为“百分数数值”，例如 9.1 表示 9.1%
- 金额统一默认为 RMB / million_rmb
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


DEFAULT_SYMBOL = "02618.HK"
DATA_VERSION = "V1"

PRIMARY_KEYS = ["symbol", "report_date", "period_type"]

QUARTERLY_FILE = "fundamental_quarterly.csv"
STATEMENT_ITEMS_FILE = "fundamental_statement_items.csv"
FEATURES_FILE = "fundamental_features.csv"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def ensure_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for col in columns:
        if col not in df.columns:
            df[col] = np.nan
    return df


def to_numeric_if_possible(df: pd.DataFrame, exclude: Optional[Iterable[str]] = None) -> pd.DataFrame:
    exclude_set = set(exclude or [])
    for col in df.columns:
        if col in exclude_set:
            continue
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def first_notnull(series: pd.Series):
    non_null = series.dropna()
    return non_null.iloc[0] if len(non_null) > 0 else np.nan


def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_columns(df, PRIMARY_KEYS)
    for col in PRIMARY_KEYS:
        df[col] = df[col].astype(str).str.strip()
    return df


def load_quarterly(base_dir: Path) -> pd.DataFrame:
    path = base_dir / QUARTERLY_FILE
    df = safe_read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=PRIMARY_KEYS)

    df = normalize_keys(df)

    # 避免后续 merge 出现缺列
    keep_cols = [
        "symbol",
        "report_date",
        "period_type",
        "revenue",
        "gross_profit",
        "gross_margin",
        "net_profit",
        "non_ifrs_profit",
        "non_ifrs_ebitda",
        "total_assets",
        "total_liabilities",
        "total_equity",
        "operating_cash_flow",
        "external_customer_revenue",
        "integrated_supply_chain_revenue",
        "warehouse_count",
        "warehouse_gfa",
        "overseas_warehouse_area",
        "employee_count",
        "quality_flag",
    ]
    df = ensure_columns(df, keep_cols)
    df = to_numeric_if_possible(df, exclude=PRIMARY_KEYS + ["quality_flag"])
    return df


def load_statement_items(base_dir: Path) -> pd.DataFrame:
    path = base_dir / STATEMENT_ITEMS_FILE
    df = safe_read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=PRIMARY_KEYS)

    required_cols = PRIMARY_KEYS + ["item_code", "value"]
    df = ensure_columns(df, required_cols)
    df = normalize_keys(df)
    df["item_code"] = df["item_code"].astype(str).str.strip()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def pivot_statement_items(df_items: pd.DataFrame) -> pd.DataFrame:
    if df_items.empty:
        return pd.DataFrame(columns=PRIMARY_KEYS)

    pivot = (
        df_items.pivot_table(
            index=PRIMARY_KEYS,
            columns="item_code",
            values="value",
            aggfunc=first_notnull,
        )
        .reset_index()
    )

    pivot.columns.name = None
    return pivot


def pct(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator * 100.0


def coalesce(*values):
    for v in values:
        if pd.notna(v):
            return v
    return np.nan


def derive_row(row: pd.Series) -> pd.Series:
    revenue = row.get("revenue", np.nan)
    total_assets = coalesce(row.get("total_assets"), row.get("total_assets_q", np.nan))
    total_liabilities = coalesce(row.get("total_liabilities"), row.get("total_liabilities_q", np.nan))
    total_equity = coalesce(row.get("total_equity"), row.get("total_equity_q", np.nan))
    operating_cash_flow = coalesce(row.get("operating_cash_flow"), row.get("operating_cash_flow_q", np.nan))

    cash_and_cash_equivalents = row.get("cash_and_cash_equivalents", np.nan)
    restricted_cash = coalesce(row.get("restricted_cash", np.nan), 0.0)
    term_deposits = coalesce(row.get("term_deposits", np.nan), 0.0)
    borrowings = row.get("borrowings", np.nan)

    current_assets = row.get("current_assets", np.nan)
    current_liabilities = row.get("current_liabilities", np.nan)
    lease_liabilities = row.get("lease_liabilities", np.nan)
    trade_receivables = row.get("trade_receivables", np.nan)
    contract_assets = row.get("contract_assets", np.nan)
    inventories = row.get("inventories", np.nan)
    trade_payables = row.get("trade_payables", np.nan)
    supplier_finance_arrangements = row.get("supplier_finance_arrangements", np.nan)
    receivables_6_to_12m = row.get("receivables_6_to_12m", np.nan)
    receivables_over_12m = row.get("receivables_over_12m", np.nan)
    payables_over_12m = row.get("payables_over_12m", np.nan)
    receivables_loss_allowance = row.get("receivables_loss_allowance", np.nan)
    free_cash_inflow = row.get("free_cash_inflow", np.nan)
    capex_net = row.get("capex_net", np.nan)

    revenue_external = row.get("revenue_external", np.nan)
    external_customer_revenue = row.get("external_customer_revenue", np.nan)
    revenue_jd_group = row.get("revenue_jd_group", np.nan)
    revenue_integrated_supply_chain = row.get("revenue_integrated_supply_chain", np.nan)
    integrated_supply_chain_revenue = row.get("integrated_supply_chain_revenue", np.nan)
    revenue_external_integrated_supply_chain = row.get("revenue_external_integrated_supply_chain", np.nan)

    # 统一回填核心摘要字段（仅在摘要层缺失时回填）
    row["total_assets"] = total_assets
    row["total_liabilities"] = total_liabilities
    row["total_equity"] = total_equity
    row["operating_cash_flow"] = operating_cash_flow

    # 派生
    if pd.notna(cash_and_cash_equivalents) and pd.notna(borrowings):
        row["net_cash"] = cash_and_cash_equivalents + restricted_cash + term_deposits - borrowings
    else:
        row["net_cash"] = np.nan

    row["working_capital"] = (
        current_assets - current_liabilities
        if pd.notna(current_assets) and pd.notna(current_liabilities)
        else np.nan
    )

    row["debt_to_asset_ratio"] = pct(total_liabilities, total_assets)
    row["lease_burden_ratio"] = pct(lease_liabilities, total_liabilities)
    row["receivables_ratio"] = pct(trade_receivables, revenue)
    row["contract_assets_ratio"] = pct(contract_assets, revenue)
    row["inventory_ratio"] = pct(inventories, revenue)

    # V1：按收入口径
    row["payables_ratio"] = pct(trade_payables, revenue)
    row["supplier_finance_ratio"] = pct(supplier_finance_arrangements, trade_payables)

    if pd.notna(trade_receivables) and trade_receivables > 0:
        overdue_6m = coalesce(receivables_6_to_12m, 0.0) + coalesce(receivables_over_12m, 0.0)
        row["receivables_over_6m_ratio"] = overdue_6m / trade_receivables * 100.0
    else:
        row["receivables_over_6m_ratio"] = np.nan

    row["receivables_over_12m_ratio"] = pct(receivables_over_12m, trade_receivables)
    row["payables_over_12m_ratio"] = pct(payables_over_12m, trade_payables)
    row["receivables_loss_allowance_ratio"] = pct(receivables_loss_allowance, trade_receivables)
    row["free_cash_flow_margin"] = pct(free_cash_inflow, revenue)
    row["capex_intensity"] = pct(capex_net, revenue)
    row["operating_cash_flow_margin"] = pct(operating_cash_flow, revenue)

    if pd.notna(row["operating_cash_flow_margin"]) and pd.notna(row["receivables_ratio"]):
        row["cash_conversion_quality_score"] = row["operating_cash_flow_margin"] - row["receivables_ratio"]
    else:
        row["cash_conversion_quality_score"] = np.nan

    # 收入结构
    revenue_external_preferred = coalesce(revenue_external, external_customer_revenue)
    revenue_integrated_preferred = coalesce(revenue_integrated_supply_chain, integrated_supply_chain_revenue)

    row["external_revenue_ratio"] = pct(revenue_external_preferred, revenue)
    row["jd_group_revenue_ratio"] = pct(revenue_jd_group, revenue)
    row["integrated_supply_chain_revenue_ratio"] = pct(revenue_integrated_preferred, revenue)
    row["external_isc_revenue_ratio"] = pct(revenue_external_integrated_supply_chain, revenue)

    return row


def compute_yoy(df: pd.DataFrame, value_col: str, out_col: str) -> pd.DataFrame:
    if value_col not in df.columns:
        df[out_col] = np.nan
        return df

    df[out_col] = np.nan

    for symbol, group_idx in df.groupby("symbol").groups.items():
        g = df.loc[group_idx].copy()
        g["report_date_dt"] = pd.to_datetime(g["report_date"], errors="coerce")
        g = g.sort_values(["period_type", "report_date_dt"])

        yoy_values = {}
        for period_type, gp in g.groupby("period_type"):
            gp = gp.sort_values("report_date_dt")
            vals = gp[value_col]
            prev = vals.shift(1)
            yoy = np.where((prev.notna()) & (prev != 0) & vals.notna(), (vals - prev) / prev * 100.0, np.nan)
            for idx, v in zip(gp.index, yoy):
                yoy_values[idx] = v

        for idx, v in yoy_values.items():
            df.at[idx, out_col] = v

    return df


def label_working_capital_pressure(row: pd.Series) -> str:
    wc = row.get("working_capital", np.nan)
    rr = row.get("receivables_ratio", np.nan)

    if pd.notna(wc) and wc < 0:
        return "HIGH_PRESSURE"
    if pd.notna(wc) and wc >= 0 and pd.notna(rr) and rr > 20:
        return "WATCH"
    if pd.notna(wc):
        return "NORMAL"
    return ""


def label_receivables_quality(row: pd.Series) -> str:
    r12 = row.get("receivables_over_12m_ratio", np.nan)
    if pd.isna(r12):
        return ""
    if r12 >= 10:
        return "WEAK"
    if r12 >= 5:
        return "WATCH"
    return "GOOD"


def label_supplier_finance_usage(row: pd.Series) -> str:
    s = row.get("supplier_finance_ratio", np.nan)
    if pd.isna(s):
        return ""
    if s >= 20:
        return "HIGH"
    if s >= 10:
        return "MEDIUM"
    return "LOW"


def label_cash_flow_quality(row: pd.Series) -> str:
    fcf = row.get("free_cash_flow_margin", np.nan)
    ocf = row.get("operating_cash_flow_margin", np.nan)
    non_ifrs_profit = row.get("non_ifrs_profit", np.nan)

    if pd.notna(fcf) and fcf < 0 and pd.notna(non_ifrs_profit) and non_ifrs_profit > 0:
        return "PROFIT_CASH_DIVERGENCE"
    if pd.notna(ocf) and ocf > 0 and pd.notna(fcf) and fcf > 0:
        return "GOOD"
    if pd.notna(ocf) or pd.notna(fcf):
        return "REVIEW"
    return ""


def label_customer_structure(row: pd.Series) -> str:
    ext_ratio = row.get("external_revenue_ratio", np.nan)
    jd_ratio = row.get("jd_group_revenue_ratio", np.nan)

    if pd.notna(ext_ratio) and ext_ratio >= 60:
        return "EXTERNAL_DOMINANT"
    if pd.notna(jd_ratio) and jd_ratio >= 40:
        return "JD_GROUP_DEPENDENT"
    if pd.notna(ext_ratio) or pd.notna(jd_ratio):
        return "BALANCED"
    return ""


def label_globalization_phase(row: pd.Series) -> str:
    overseas_area = row.get("overseas_warehouse_area", np.nan)
    if pd.notna(overseas_area) and overseas_area > 0:
        return "GLOBALIZING"
    return "DOMESTIC_CORE"


def add_network_expansion_tag(df: pd.DataFrame) -> pd.DataFrame:
    if "warehouse_count" not in df.columns:
        df["network_expansion_tag"] = ""
        return df

    df["network_expansion_tag"] = ""
    for symbol, idxs in df.groupby("symbol").groups.items():
        g = df.loc[idxs].copy()
        g["report_date_dt"] = pd.to_datetime(g["report_date"], errors="coerce")
        g = g.sort_values(["period_type", "report_date_dt"])

        for period_type, gp in g.groupby("period_type"):
            gp = gp.sort_values("report_date_dt")
            prev = gp["warehouse_count"].shift(1)
            cur = gp["warehouse_count"]
            for i in gp.index:
                p = prev.loc[i]
                c = cur.loc[i]
                if pd.isna(c):
                    tag = ""
                elif pd.notna(p):
                    if c > p:
                        tag = "EXPANDING"
                    elif c == p:
                        tag = "STABLE"
                    else:
                        tag = "REVIEW"
                else:
                    tag = "REVIEW"
                df.at[i, "network_expansion_tag"] = tag
    return df


def build_feature_note(row: pd.Series) -> str:
    notes: List[str] = []

    if row.get("quality_flag", "") == "REVIEW":
        notes.append("存在口径或来源需复核")
    if row.get("period_type", "") in {"quarter"} and (
        pd.isna(row.get("current_assets", np.nan)) or pd.isna(row.get("current_liabilities", np.nan))
    ):
        notes.append("季度口径可能未披露完整资产负债表")
    if pd.notna(row.get("free_cash_flow_margin", np.nan)) and row["free_cash_flow_margin"] < 0:
        notes.append("自由现金流率为负")
    if pd.notna(row.get("receivables_over_12m_ratio", np.nan)) and row["receivables_over_12m_ratio"] >= 10:
        notes.append("长账龄应收占比较高")

    return "；".join(notes)


def assign_row_quality_flag(row: pd.Series) -> str:
    review_needed = False

    revenue_external = row.get("revenue_external", np.nan)
    external_customer_revenue = row.get("external_customer_revenue", np.nan)
    if pd.notna(revenue_external) and pd.notna(external_customer_revenue):
        if abs(revenue_external - external_customer_revenue) > 1e-6:
            review_needed = True

    core_fields = [
        row.get("revenue", np.nan),
        row.get("total_assets", np.nan),
        row.get("total_liabilities", np.nan),
        row.get("trade_receivables", np.nan),
        row.get("free_cash_flow_margin", np.nan),
    ]
    available_count = sum(pd.notna(v) for v in core_fields)

    if review_needed:
        return "REVIEW"
    if available_count >= 4:
        return "CONFIRMED"
    if available_count >= 2:
        return "PARTIAL"
    return "RAW"


def finalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    ordered_cols = [
        # 主键
        "symbol",
        "report_date",
        "period_type",
        # 直接保留字段
        "revenue",
        "gross_profit",
        "gross_margin",
        "net_profit",
        "non_ifrs_profit",
        "non_ifrs_ebitda",
        "total_assets",
        "total_liabilities",
        "total_equity",
        "operating_cash_flow",
        "external_customer_revenue",
        "integrated_supply_chain_revenue",
        "warehouse_count",
        "warehouse_gfa",
        "overseas_warehouse_area",
        "employee_count",
        # 明细层补充字段
        "cash_and_cash_equivalents",
        "restricted_cash",
        "term_deposits",
        "trade_receivables",
        "contract_assets",
        "inventories",
        "trade_payables",
        "borrowings",
        "lease_liabilities",
        "current_assets",
        "current_liabilities",
        "investing_cash_flow",
        "financing_cash_flow",
        "free_cash_inflow",
        "capex_net",
        "revenue_jd_group",
        "revenue_external",
        "revenue_integrated_supply_chain",
        "revenue_external_integrated_supply_chain",
        "revenue_other_customers",
        "external_isc_customer_count",
        "external_isc_arpc",
        "receivables_within_3m",
        "receivables_3_to_6m",
        "receivables_6_to_12m",
        "receivables_over_12m",
        "receivables_loss_allowance",
        "payables_within_3m",
        "payables_3_to_6m",
        "payables_6_to_12m",
        "payables_over_12m",
        "supplier_finance_arrangements",
        # 派生字段
        "net_cash",
        "working_capital",
        "debt_to_asset_ratio",
        "lease_burden_ratio",
        "receivables_ratio",
        "contract_assets_ratio",
        "inventory_ratio",
        "payables_ratio",
        "supplier_finance_ratio",
        "receivables_over_6m_ratio",
        "receivables_over_12m_ratio",
        "payables_over_12m_ratio",
        "receivables_loss_allowance_ratio",
        "free_cash_flow_margin",
        "capex_intensity",
        "operating_cash_flow_margin",
        "cash_conversion_quality_score",
        "external_revenue_ratio",
        "jd_group_revenue_ratio",
        "integrated_supply_chain_revenue_ratio",
        "external_isc_revenue_ratio",
        "external_isc_customer_yoy",
        "external_isc_arpc_yoy",
        # 标签字段
        "working_capital_pressure_tag",
        "receivables_quality_tag",
        "supplier_finance_usage_tag",
        "cash_flow_quality_tag",
        "customer_structure_tag",
        "globalization_phase_tag",
        "network_expansion_tag",
        "feature_note",
        # 元数据
        "data_version",
        "quality_flag",
        "source_summary",
        "updated_at",
    ]

    df = ensure_columns(df, ordered_cols)
    return df[ordered_cols]


def build_features(base_dir: Path) -> pd.DataFrame:
    quarterly = load_quarterly(base_dir)
    items = load_statement_items(base_dir)
    items_pivot = pivot_statement_items(items)

    # 避免和透视表的同名字段冲突时丢信息
    duplicate_cols = [c for c in ["total_assets", "total_liabilities", "total_equity", "operating_cash_flow"] if c in quarterly.columns]
    quarterly = quarterly.rename(columns={c: f"{c}_q" for c in duplicate_cols})

    df = quarterly.merge(items_pivot, on=PRIMARY_KEYS, how="left")

    # 恢复摘要字段目标列
    for c in ["total_assets", "total_liabilities", "total_equity", "operating_cash_flow"]:
        if c not in df.columns:
            df[c] = np.nan

    df = df.apply(derive_row, axis=1)

    # 同比字段
    df = compute_yoy(df, "external_isc_customer_count", "external_isc_customer_yoy")
    df = compute_yoy(df, "external_isc_arpc", "external_isc_arpc_yoy")

    # 标签
    df["working_capital_pressure_tag"] = df.apply(label_working_capital_pressure, axis=1)
    df["receivables_quality_tag"] = df.apply(label_receivables_quality, axis=1)
    df["supplier_finance_usage_tag"] = df.apply(label_supplier_finance_usage, axis=1)
    df["cash_flow_quality_tag"] = df.apply(label_cash_flow_quality, axis=1)
    df["customer_structure_tag"] = df.apply(label_customer_structure, axis=1)
    df["globalization_phase_tag"] = df.apply(label_globalization_phase, axis=1)
    df = add_network_expansion_tag(df)

    # 元数据
    df["data_version"] = DATA_VERSION
    df["source_summary"] = "fundamental_quarterly+fundamental_statement_items"
    df["updated_at"] = now_iso()

    # 行级质量标记和说明
    df["quality_flag"] = df.apply(assign_row_quality_flag, axis=1)
    df["feature_note"] = df.apply(build_feature_note, axis=1)

    # 排序
    df["report_date_dt"] = pd.to_datetime(df["report_date"], errors="coerce")
    df = df.sort_values(["symbol", "report_date_dt", "period_type"]).drop(columns=["report_date_dt"])

    # 去重
    df = df.drop_duplicates(subset=PRIMARY_KEYS, keep="last")

    # 输出列顺序
    df = finalize_columns(df)
    return df


def save_features(df: pd.DataFrame, base_dir: Path) -> Path:
    output_path = base_dir / FEATURES_FILE
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建下游可消费的企业基本面特征表 fundamental_features.csv")
    parser.add_argument(
        "--symbol",
        default=DEFAULT_SYMBOL,
        help=f"股票代码目录，默认 {DEFAULT_SYMBOL}",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="仓库根目录，默认当前目录",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    base_dir = root / "data_fundamental" / args.symbol

    if not base_dir.exists():
        raise FileNotFoundError(f"目标目录不存在: {base_dir}")

    df = build_features(base_dir)
    output_path = save_features(df, base_dir)

    print("=" * 80)
    print("fundamental_features 构建完成")
    print(f"symbol: {args.symbol}")
    print(f"rows: {len(df)}")
    print(f"output: {output_path}")
    print("=" * 80)

    if len(df) > 0:
        preview_cols = [c for c in [
            "symbol",
            "report_date",
            "period_type",
            "revenue",
            "net_cash",
            "working_capital",
            "debt_to_asset_ratio",
            "receivables_ratio",
            "free_cash_flow_margin",
            "quality_flag",
        ] if c in df.columns]
        print(df[preview_cols].tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
