# -*- coding: utf-8 -*-
"""
init_fundamental_consumer_tables.py

作用：
1. 创建 data_fundamental/<symbol>/fundamental_statement_items.csv 空表头
2. 创建 data_fundamental/<symbol>/fundamental_features.csv 空表头

默认 symbol = 02618.HK
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


DEFAULT_SYMBOL = "02618.HK"


STATEMENT_ITEMS_COLUMNS = [
    "symbol",
    "report_date",
    "period_type",
    "statement_type",
    "item_code",
    "item_name_cn",
    "item_name_en",
    "value",
    "unit",
    "currency",
    "source_doc",
    "source_page",
    "source_section",
    "is_derived",
    "quality_flag",
    "note",
    "updated_at",
]


FEATURES_COLUMNS = [
    # 主键字段
    "symbol",
    "report_date",
    "period_type",

    # 直接保留字段（来自 fundamental_quarterly.csv）
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

    # 明细层补充字段（来自 fundamental_statement_items.csv）
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

    # 派生特征字段
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

    # 标签 / 解释字段
    "working_capital_pressure_tag",
    "receivables_quality_tag",
    "supplier_finance_usage_tag",
    "cash_flow_quality_tag",
    "customer_structure_tag",
    "globalization_phase_tag",
    "network_expansion_tag",
    "feature_note",

    # 元数据字段
    "data_version",
    "quality_flag",
    "source_summary",
    "updated_at",
]


def write_empty_csv(path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def parse_args():
    parser = argparse.ArgumentParser(description="初始化企业基本面消费层两张空表头")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help=f"股票代码目录，默认 {DEFAULT_SYMBOL}")
    parser.add_argument("--root", default=".", help="仓库根目录，默认当前目录")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    base_dir = root / "data_fundamental" / args.symbol

    statement_items_path = base_dir / "fundamental_statement_items.csv"
    features_path = base_dir / "fundamental_features.csv"

    write_empty_csv(statement_items_path, STATEMENT_ITEMS_COLUMNS)
    write_empty_csv(features_path, FEATURES_COLUMNS)

    print("=" * 80)
    print("初始化完成")
    print(f"symbol: {args.symbol}")
    print(f"created: {statement_items_path}")
    print(f"created: {features_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
