# -*- coding: utf-8 -*-
"""
build_fundamental_features.py

作用：
1. 读取摘要层：
   data_fundamental/<symbol>/fundamental_quarterly.csv

2. 读取标准财报明细层：
   data_fundamental/<symbol>/fundamental_statement_items.csv

3. 以 quarterly 为骨架行，以 statement_items 为事实底表，
   按 report_date + period_type + item_code 逐行消费映射

4. 生成下游消费层：
   data_fundamental/<symbol>/fundamental_features.csv

V2.2 设计原则：
- 当前主线第一优先：打透 2021–2025 annual 行映射
- 不回退旧话题，不重复验证 workflow
- 不再只依赖简单 pivot merge，而是显式做行级消费
- annual / semiannual / quarter 三类 period_type 统一归一
- statement_items 若存在重复记录，按质量优先级择优
- 比例字段统一输出为“百分数数值”，例如 9.1 表示 9.1%
- statement_items 金额字段统一标准化到 million RMB 后再进入 features
- 修复 quality_flag 误判：不再把 external_customer_revenue 与 revenue_external 视为同口径冲突字段
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


DEFAULT_SYMBOL = "02618.HK"
DATA_VERSION = "V2.2"

PRIMARY_KEYS = ["symbol", "report_date", "period_type"]

QUARTERLY_FILE = "fundamental_quarterly.csv"
STATEMENT_ITEMS_FILE = "fundamental_statement_items.csv"
FEATURES_FILE = "fundamental_features.csv"

TARGET_ITEM_COLUMNS = [
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
    # 兼容 item 层直接写入的摘要字段
    "total_assets",
    "total_liabilities",
    "total_equity",
    "operating_cash_flow",
    "revenue",
]

CORE_SUMMARY_COLUMNS = [
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

QUALITY_SCORE_MAP = {
    "CONFIRMED": 4,
    "HIGH": 4,
    "PARTIAL": 3,
    "MEDIUM": 3,
    "RAW": 2,
    "LOW": 2,
    "REVIEW": 1,
    "UNKNOWN": 0,
    "": 0,
}

AMOUNT_ITEM_COLUMNS = {
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
    "total_assets",
    "total_liabilities",
    "total_equity",
    "operating_cash_flow",
    "revenue",
}

NON_AMOUNT_ITEM_COLUMNS = {
    "external_isc_customer_count",
    "external_isc_arpc",
}


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


def normalize_report_date_value(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    dt = pd.to_datetime(text, errors="coerce")
    if pd.isna(dt):
        return text
    return dt.strftime("%Y-%m-%d")


def normalize_period_type_value(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    if text in {"annual", "fy", "full_year", "year", "yearly"}:
        return "annual"
    if text in {"semiannual", "semi-annual", "semi_annual", "interim", "h1", "half_year", "half-year"}:
        return "semiannual"
    if text in {"quarter", "quarterly", "q1", "q2", "q3", "q4"}:
        return "quarter"
    return text


def normalize_item_code_value(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_columns(df, PRIMARY_KEYS)
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["report_date"] = df["report_date"].apply(normalize_report_date_value)
    df["period_type"] = df["period_type"].apply(normalize_period_type_value)
    return df


def normalize_unit_text(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = text.replace(" ", "")
    text = text.replace("’", "'")
    text = text.replace("人民币", "rmb")
    return text


def is_amount_item(item_code: str) -> bool:
    return item_code in AMOUNT_ITEM_COLUMNS


def normalize_amount_to_million_rmb(value, unit, currency, item_code: str):
    """
    统一把金额类 item 转成 million RMB。
    非金额类 item 原值保留。
    """
    if pd.isna(value):
        return np.nan

    if item_code in NON_AMOUNT_ITEM_COLUMNS:
        return value

    if not is_amount_item(item_code):
        return value

    unit_text = normalize_unit_text(unit)
    currency_text = str(currency).strip().upper() if pd.notna(currency) else ""

    if unit_text in {
        "rmb'000",
        "rmb000",
        "cny'000",
        "cny000",
        "thousandrmb",
        "thousandcny",
        "rmbthousand",
        "cnythousand",
    }:
        return value / 1000.0

    if unit_text in {
        "rmbmillion",
        "millionrmb",
        "cnymillion",
        "millioncny",
        "rmbmn",
        "cnymn",
        "million",
    }:
        return value

    if unit_text in {
        "rmbbillion",
        "billionrmb",
        "cnybillion",
        "billioncny",
        "rmbbn",
        "cnybn",
        "billion",
    }:
        return value * 1000.0

    if "customer" in unit_text or "customers" in unit_text:
        return value

    if currency_text in {"CNY", "RMB"} and unit_text == "":
        return value

    return value


def load_quarterly(base_dir: Path) -> pd.DataFrame:
    path = base_dir / QUARTERLY_FILE
    df = safe_read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=PRIMARY_KEYS)

    df = normalize_keys(df)
    df = ensure_columns(df, CORE_SUMMARY_COLUMNS)
    df = to_numeric_if_possible(df, exclude=PRIMARY_KEYS + ["quality_flag"])
    return df


def load_statement_items(base_dir: Path) -> pd.DataFrame:
    path = base_dir / STATEMENT_ITEMS_FILE
    df = safe_read_csv(path)
    if df.empty:
        return pd.DataFrame(columns=PRIMARY_KEYS)

    required_cols = PRIMARY_KEYS + [
        "statement_type",
        "item_code",
        "value",
        "unit",
        "currency",
        "quality_flag",
        "source_doc",
        "source_page",
        "source_section",
        "note",
    ]
    df = ensure_columns(df, required_cols)
    df = normalize_keys(df)
    df["item_code"] = df["item_code"].apply(normalize_item_code_value)
    df["statement_type"] = df["statement_type"].astype(str).str.strip().str.lower()
    df["quality_flag"] = df["quality_flag"].fillna("").astype(str).str.strip().str.upper()
    df["source_doc"] = df["source_doc"].fillna("").astype(str).str.strip()
    df["source_section"] = df["source_section"].fillna("").astype(str).str.strip()
    df["note"] = df["note"].fillna("").astype(str).str.strip()
    df["unit"] = df["unit"].fillna("").astype(str).str.strip()
    df["currency"] = df["currency"].fillna("").astype(str).str.strip().str.upper()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df["normalized_value"] = df.apply(
        lambda row: normalize_amount_to_million_rmb(
            value=row.get("value", np.nan),
            unit=row.get("unit", ""),
            currency=row.get("currency", ""),
            item_code=row.get("item_code", ""),
        ),
        axis=1,
    )
    return df


def pct(numerator, denominator):
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator * 100.0


def coalesce(*values):
    for v in values:
        if pd.notna(v):
            return v
    return np.nan


def score_item_record(row: pd.Series) -> float:
    """
    statement_items 存在重复时择优逻辑：
    1. normalized_value 非空优先
    2. quality_flag 高优先
    3. source_doc / source_section 有追溯优先
    4. note 中若出现 rounded / narrative / estimated 等，降权
    """
    score = 0.0

    if pd.notna(row.get("normalized_value", np.nan)):
        score += 100.0

    qf = str(row.get("quality_flag", "")).upper().strip()
    score += QUALITY_SCORE_MAP.get(qf, 0) * 10.0

    source_doc = str(row.get("source_doc", "")).strip()
    source_section = str(row.get("source_section", "")).strip()
    if source_doc:
        score += 3.0
    if source_section:
        score += 2.0

    note = str(row.get("note", "")).lower()
    if any(token in note for token in ["rounded", "narrative", "estimated", "estimate", "approx"]):
        score -= 3.0

    statement_type = str(row.get("statement_type", "")).lower()
    if statement_type in {"balance_sheet", "income_statement", "cash_flow", "note"}:
        score += 1.0

    return score


def build_best_item_records(df_items: pd.DataFrame) -> pd.DataFrame:
    if df_items.empty:
        return df_items.copy()

    df = df_items.copy()
    df["record_score"] = df.apply(score_item_record, axis=1)
    df = df.sort_values(
        by=["symbol", "report_date", "period_type", "item_code", "record_score"],
        ascending=[True, True, True, True, False],
    )
    df = df.drop_duplicates(subset=["symbol", "report_date", "period_type", "item_code"], keep="first")
    return df


def build_item_lookup(df_items: pd.DataFrame) -> Dict[Tuple[str, str, str, str], Dict[str, object]]:
    """
    key = (symbol, report_date, period_type, item_code)
    """
    lookup: Dict[Tuple[str, str, str, str], Dict[str, object]] = {}
    if df_items.empty:
        return lookup

    best_df = build_best_item_records(df_items)
    for _, row in best_df.iterrows():
        key = (
            str(row["symbol"]).strip(),
            normalize_report_date_value(row["report_date"]),
            normalize_period_type_value(row["period_type"]),
            normalize_item_code_value(row["item_code"]),
        )
        lookup[key] = {
            "raw_value": row.get("value", np.nan),
            "value": row.get("normalized_value", np.nan),
            "unit": row.get("unit", ""),
            "currency": row.get("currency", ""),
            "quality_flag": row.get("quality_flag", ""),
            "source_doc": row.get("source_doc", ""),
            "source_section": row.get("source_section", ""),
            "source_page": row.get("source_page", np.nan),
            "note": row.get("note", ""),
            "record_score": row.get("record_score", 0.0),
        }
    return lookup


def get_item_record(
    lookup: Dict[Tuple[str, str, str, str], Dict[str, object]],
    symbol: str,
    report_date: str,
    period_type: str,
    item_code: str,
) -> Optional[Dict[str, object]]:
    key = (
        str(symbol).strip(),
        normalize_report_date_value(report_date),
        normalize_period_type_value(period_type),
        normalize_item_code_value(item_code),
    )
    return lookup.get(key)


def consume_statement_items_into_feature_rows(
    df_features: pd.DataFrame,
    lookup: Dict[Tuple[str, str, str, str], Dict[str, object]],
) -> pd.DataFrame:
    if df_features.empty:
        return df_features

    df = df_features.copy()

    for col in TARGET_ITEM_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    df["item_quality_score_sum"] = 0.0
    df["item_quality_score_avg"] = np.nan
    df["mapped_item_count"] = 0
    df["mapped_item_nonnull_count"] = 0
    df["mapped_item_codes"] = ""
    df["item_source_docs"] = ""

    consumed_doc_list: List[str] = []
    consumed_code_list: List[str] = []
    avg_scores: List[float] = []
    quality_sums: List[float] = []
    mapped_counts: List[int] = []
    mapped_nonnull_counts: List[int] = []

    for idx, row in df.iterrows():
        symbol = row["symbol"]
        report_date = row["report_date"]
        period_type = row["period_type"]

        used_codes: List[str] = []
        used_docs: List[str] = []
        score_values: List[float] = []
        nonnull_count = 0
        mapped_count = 0

        for item_code in TARGET_ITEM_COLUMNS:
            rec = get_item_record(lookup, symbol, report_date, period_type, item_code)
            if rec is None:
                continue

            mapped_count += 1
            used_codes.append(item_code)

            value = rec.get("value", np.nan)
            if pd.notna(value):
                df.at[idx, item_code] = value
                nonnull_count += 1

            record_score = float(rec.get("record_score", 0.0) or 0.0)
            score_values.append(record_score)

            source_doc = str(rec.get("source_doc", "")).strip()
            if source_doc:
                used_docs.append(source_doc)

        mapped_counts.append(mapped_count)
        mapped_nonnull_counts.append(nonnull_count)
        quality_sums.append(float(np.sum(score_values)) if score_values else 0.0)
        avg_scores.append(float(np.mean(score_values)) if score_values else np.nan)
        consumed_code_list.append("|".join(sorted(set(used_codes))))
        consumed_doc_list.append("|".join(sorted(set(used_docs))))

    df["mapped_item_count"] = mapped_counts
    df["mapped_item_nonnull_count"] = mapped_nonnull_counts
    df["item_quality_score_sum"] = quality_sums
    df["item_quality_score_avg"] = avg_scores
    df["mapped_item_codes"] = consumed_code_list
    df["item_source_docs"] = consumed_doc_list

    return df


def derive_row(row: pd.Series) -> pd.Series:
    revenue = coalesce(row.get("revenue", np.nan), row.get("revenue_q", np.nan))
    total_assets = coalesce(row.get("total_assets", np.nan), row.get("total_assets_q", np.nan))
    total_liabilities = coalesce(row.get("total_liabilities", np.nan), row.get("total_liabilities_q", np.nan))
    total_equity = coalesce(row.get("total_equity", np.nan), row.get("total_equity_q", np.nan))
    operating_cash_flow = coalesce(row.get("operating_cash_flow", np.nan), row.get("operating_cash_flow_q", np.nan))

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

    row["revenue"] = revenue
    row["total_assets"] = total_assets
    row["total_liabilities"] = total_liabilities
    row["total_equity"] = total_equity
    row["operating_cash_flow"] = operating_cash_flow

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

    for _, group_idx in df.groupby("symbol").groups.items():
        g = df.loc[group_idx].copy()
        g["report_date_dt"] = pd.to_datetime(g["report_date"], errors="coerce")

        yoy_values = {}
        for period_type, gp in g.groupby("period_type"):
            gp = gp.sort_values("report_date_dt")
            vals = gp[value_col]
            prev = vals.shift(1)
            yoy = np.where(
                (prev.notna()) & (prev != 0) & vals.notna(),
                (vals - prev) / prev * 100.0,
                np.nan,
            )
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
    for _, idxs in df.groupby("symbol").groups.items():
        g = df.loc[idxs].copy()
        g["report_date_dt"] = pd.to_datetime(g["report_date"], errors="coerce")

        for _, gp in g.groupby("period_type"):
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


def has_implausible_ratio(row: pd.Series) -> bool:
    suspicious_cols = [
        "receivables_ratio",
        "contract_assets_ratio",
        "inventory_ratio",
        "payables_ratio",
        "free_cash_flow_margin",
        "capex_intensity",
        "operating_cash_flow_margin",
        "external_revenue_ratio",
        "jd_group_revenue_ratio",
        "integrated_supply_chain_revenue_ratio",
        "external_isc_revenue_ratio",
    ]
    for col in suspicious_cols:
        v = row.get(col, np.nan)
        if pd.notna(v) and abs(v) > 1000:
            return True
    return False


def annual_core_completeness_score(row: pd.Series) -> int:
    core_fields = [
        row.get("revenue", np.nan),
        row.get("total_assets", np.nan),
        row.get("total_liabilities", np.nan),
        row.get("trade_receivables", np.nan),
        row.get("trade_payables", np.nan),
        row.get("current_assets", np.nan),
        row.get("current_liabilities", np.nan),
        row.get("cash_and_cash_equivalents", np.nan),
        row.get("borrowings", np.nan),
        row.get("free_cash_flow_margin", np.nan),
        row.get("external_revenue_ratio", np.nan),
        row.get("jd_group_revenue_ratio", np.nan),
    ]
    return int(sum(pd.notna(v) for v in core_fields))


def annual_note_completeness_score(row: pd.Series) -> int:
    note_fields = [
        row.get("contract_assets", np.nan),
        row.get("receivables_within_3m", np.nan),
        row.get("receivables_3_to_6m", np.nan),
        row.get("receivables_6_to_12m", np.nan),
        row.get("receivables_over_12m", np.nan),
        row.get("receivables_loss_allowance", np.nan),
        row.get("payables_within_3m", np.nan),
        row.get("payables_3_to_6m", np.nan),
        row.get("payables_6_to_12m", np.nan),
        row.get("payables_over_12m", np.nan),
        row.get("supplier_finance_arrangements", np.nan),
    ]
    return int(sum(pd.notna(v) for v in note_fields))


def has_material_data_conflict(row: pd.Series) -> bool:
    """
    这里只保留真正更稳的冲突判定：
    1. total_assets 与 total_liabilities + total_equity 严重不平
    2. revenue_jd_group + revenue_external 明显大幅偏离 revenue
    不再拿 external_customer_revenue 与 revenue_external 直接比较。
    """
    total_assets = row.get("total_assets", np.nan)
    total_liabilities = row.get("total_liabilities", np.nan)
    total_equity = row.get("total_equity", np.nan)

    if pd.notna(total_assets) and pd.notna(total_liabilities) and pd.notna(total_equity):
        base = max(abs(total_assets), 1.0)
        rel_gap = abs(total_assets - (total_liabilities + total_equity)) / base
        if rel_gap > 0.05:
            return True

    revenue = row.get("revenue", np.nan)
    revenue_jd_group = row.get("revenue_jd_group", np.nan)
    revenue_external = row.get("revenue_external", np.nan)

    if pd.notna(revenue) and pd.notna(revenue_jd_group) and pd.notna(revenue_external):
        base = max(abs(revenue), 1.0)
        rel_gap = abs((revenue_jd_group + revenue_external) - revenue) / base
        if rel_gap > 0.08:
            return True

    return False


def build_feature_note(row: pd.Series) -> str:
    notes: List[str] = []

    period_type = row.get("period_type", "")
    quality_flag = row.get("quality_flag", "")

    if quality_flag == "REVIEW":
        notes.append("存在口径或来源需复核")
    if quality_flag == "RAW":
        notes.append("核心字段到位率偏低")

    if period_type == "quarter" and (
        pd.isna(row.get("current_assets", np.nan)) or pd.isna(row.get("current_liabilities", np.nan))
    ):
        notes.append("季度口径可能未披露完整资产负债表")

    if pd.notna(row.get("free_cash_flow_margin", np.nan)) and row["free_cash_flow_margin"] < 0:
        notes.append("自由现金流率为负")

    if pd.notna(row.get("receivables_over_12m_ratio", np.nan)) and row["receivables_over_12m_ratio"] >= 10:
        notes.append("长账龄应收占比较高")

    if has_implausible_ratio(row):
        notes.append("存在异常比例值，需复核单位或口径")

    if period_type == "annual":
        core_score = annual_core_completeness_score(row)
        note_score = annual_note_completeness_score(row)
        if core_score >= 9 and note_score < 3:
            notes.append("annual 主干字段已通，但附注字段覆盖仍偏薄")
        elif core_score >= 9 and note_score < 6:
            notes.append("annual 附注字段覆盖中等，仍可继续补齐")

    return "；".join(notes)


def assign_row_quality_flag(row: pd.Series) -> str:
    """
    V2.2 逻辑：
    1. 若出现异常比例爆炸，直接 REVIEW
    2. 若出现真正的资产/收入对账冲突，REVIEW
    3. annual 行按覆盖率判 CONFIRMED / PARTIAL / RAW
    4. 非 annual 行保持偏保守，但不乱报 REVIEW
    """
    if has_implausible_ratio(row):
        return "REVIEW"

    if has_material_data_conflict(row):
        return "REVIEW"

    period_type = row.get("period_type", "")
    item_quality_avg = row.get("item_quality_score_avg", np.nan)
    mapped_nonnull_count = int(row.get("mapped_item_nonnull_count", 0) or 0)

    if period_type == "annual":
        core_score = annual_core_completeness_score(row)
        note_score = annual_note_completeness_score(row)

        if core_score >= 9 and mapped_nonnull_count >= 20 and pd.notna(item_quality_avg) and item_quality_avg >= 100:
            return "CONFIRMED"

        if core_score >= 7 and mapped_nonnull_count >= 10:
            return "PARTIAL"

        return "RAW"

    available_count = sum(
        pd.notna(v)
        for v in [
            row.get("revenue", np.nan),
            row.get("gross_profit", np.nan),
            row.get("net_profit", np.nan),
            row.get("operating_cash_flow", np.nan),
            row.get("total_assets", np.nan),
            row.get("total_liabilities", np.nan),
        ]
    )

    if available_count >= 5:
        return "PARTIAL"
    if available_count >= 3:
        return "RAW"
    return "RAW"


def finalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    ordered_cols = [
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
        "working_capital_pressure_tag",
        "receivables_quality_tag",
        "supplier_finance_usage_tag",
        "cash_flow_quality_tag",
        "customer_structure_tag",
        "globalization_phase_tag",
        "network_expansion_tag",
        "feature_note",
        "mapped_item_count",
        "mapped_item_nonnull_count",
        "item_quality_score_sum",
        "item_quality_score_avg",
        "mapped_item_codes",
        "item_source_docs",
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
    item_lookup = build_item_lookup(items)

    if quarterly.empty:
        df = pd.DataFrame(columns=PRIMARY_KEYS)
    else:
        df = quarterly.copy()

    duplicate_cols = [
        c for c in ["revenue", "total_assets", "total_liabilities", "total_equity", "operating_cash_flow"]
        if c in df.columns
    ]
    if duplicate_cols:
        df = df.rename(columns={c: f"{c}_q" for c in duplicate_cols})

    for c in ["revenue", "total_assets", "total_liabilities", "total_equity", "operating_cash_flow"]:
        if c not in df.columns:
            df[c] = np.nan

    df = consume_statement_items_into_feature_rows(df, item_lookup)
    df = df.apply(derive_row, axis=1)

    df = compute_yoy(df, "external_isc_customer_count", "external_isc_customer_yoy")
    df = compute_yoy(df, "external_isc_arpc", "external_isc_arpc_yoy")

    df["working_capital_pressure_tag"] = df.apply(label_working_capital_pressure, axis=1)
    df["receivables_quality_tag"] = df.apply(label_receivables_quality, axis=1)
    df["supplier_finance_usage_tag"] = df.apply(label_supplier_finance_usage, axis=1)
    df["cash_flow_quality_tag"] = df.apply(label_cash_flow_quality, axis=1)
    df["customer_structure_tag"] = df.apply(label_customer_structure, axis=1)
    df["globalization_phase_tag"] = df.apply(label_globalization_phase, axis=1)
    df = add_network_expansion_tag(df)

    df["data_version"] = DATA_VERSION
    df["source_summary"] = "fundamental_quarterly+fundamental_statement_items"
    df["updated_at"] = now_iso()

    df["quality_flag"] = df.apply(assign_row_quality_flag, axis=1)
    df["feature_note"] = df.apply(build_feature_note, axis=1)

    df["report_date_dt"] = pd.to_datetime(df["report_date"], errors="coerce")
    period_rank = {"annual": 1, "semiannual": 2, "quarter": 3}
    df["period_rank"] = df["period_type"].map(period_rank).fillna(9)
    df = df.sort_values(["symbol", "report_date_dt", "period_rank"]).drop(columns=["report_date_dt", "period_rank"])

    df = df.drop_duplicates(subset=PRIMARY_KEYS, keep="last")
    df = finalize_columns(df)
    return df


def save_features(df: pd.DataFrame, base_dir: Path) -> Path:
    output_path = base_dir / FEATURES_FILE
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建下游可消费的企业基本面特征表 fundamental_features.csv")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help=f"股票代码目录，默认 {DEFAULT_SYMBOL}")
    parser.add_argument("--root", default=".", help="仓库根目录，默认当前目录")
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
        preview_cols = [
            c for c in [
                "symbol",
                "report_date",
                "period_type",
                "revenue",
                "cash_and_cash_equivalents",
                "trade_receivables",
                "trade_payables",
                "net_cash",
                "working_capital",
                "debt_to_asset_ratio",
                "receivables_ratio",
                "free_cash_flow_margin",
                "external_revenue_ratio",
                "jd_group_revenue_ratio",
                "mapped_item_nonnull_count",
                "quality_flag",
            ] if c in df.columns
        ]
        print(df[preview_cols].tail(12).to_string(index=False))


if __name__ == "__main__":
    main()
