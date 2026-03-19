# -*- coding: utf-8 -*-
"""
初始化京东物流基本面数据底座

作用：
1. 创建 data_fundamental/02618.HK/ 目录
2. 创建 fundamental_quarterly.csv 并写入首版表头
3. 创建 ingest_log.csv 并写入首版表头
4. 创建 source_docs/.gitkeep
5. 默认不覆盖已有文件，避免误伤历史数据

建议运行方式：
python scripts/init_fundamental_table.py
"""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNDAMENTAL_DIR = REPO_ROOT / "data_fundamental" / "02618.HK"
SOURCE_DOCS_DIR = FUNDAMENTAL_DIR / "source_docs"

FUNDAMENTAL_CSV = FUNDAMENTAL_DIR / "fundamental_quarterly.csv"
INGEST_LOG_CSV = FUNDAMENTAL_DIR / "ingest_log.csv"
GITKEEP_FILE = SOURCE_DOCS_DIR / ".gitkeep"


FUNDAMENTAL_HEADERS = [
    "symbol",
    "company_name_zh",
    "company_name_en",
    "report_date",
    "announce_date",
    "period_type",
    "fiscal_year",
    "fiscal_period",
    "currency",
    "unit",
    "revenue",
    "revenue_yoy",
    "revenue_qoq",
    "core_business_revenue",
    "supply_chain_revenue",
    "external_customer_revenue",
    "other_revenue",
    "revenue_growth_quality_note",
    "gross_profit",
    "gross_margin",
    "operating_profit",
    "operating_margin",
    "net_profit",
    "net_profit_yoy",
    "net_profit_qoq",
    "net_margin",
    "adj_net_profit",
    "adj_net_profit_yoy",
    "ebitda",
    "ebitda_margin",
    "adj_ebitda",
    "adj_ebitda_margin",
    "profit_quality_note",
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "free_cash_flow",
    "capex",
    "cash_and_equivalents",
    "restricted_cash",
    "cash_flow_quality_note",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "current_assets",
    "current_liabilities",
    "interest_bearing_debt",
    "net_cash",
    "debt_to_asset_ratio",
    "balance_sheet_quality_note",
    "inventory",
    "inventory_turnover_days",
    "accounts_receivable",
    "accounts_receivable_turnover_days",
    "accounts_payable",
    "accounts_payable_turnover_days",
    "working_capital",
    "working_capital_change",
    "efficiency_note",
    "integrated_supply_chain_clients",
    "warehouse_count",
    "warehouse_area",
    "cloud_warehouse_count",
    "county_coverage_ratio",
    "delivery_network_note",
    "fulfillment_scale_note",
    "market_cap",
    "ps_ttm",
    "pe_ttm",
    "pb",
    "ev_to_ebitda",
    "valuation_note",
    "major_event_flag",
    "major_event_type",
    "major_event_note",
    "management_guidance",
    "guidance_change_flag",
    "guidance_note",
    "source_type",
    "source_url",
    "source_title",
    "ingest_time",
    "data_version",
    "quality_flag",
    "quality_note",
    "is_manual_verified",
    "verified_by",
    "verified_time",
]

INGEST_LOG_HEADERS = [
    "ingest_time",
    "symbol",
    "report_date",
    "period_type",
    "source_file",
    "source_type",
    "source_url",
    "action",
    "rows_affected",
    "status",
    "message",
    "operator",
]


def ensure_dir(path: Path) -> None:
    """确保目录存在。"""
    path.mkdir(parents=True, exist_ok=True)


def write_csv_header_if_not_exists(path: Path, headers: list[str]) -> bool:
    """
    如果文件不存在，则创建并写入表头。
    返回值：
    - True: 本次新创建
    - False: 文件已存在，未改动
    """
    if path.exists():
        return False

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
    return True


def create_gitkeep_if_not_exists(path: Path) -> bool:
    """
    如果 .gitkeep 不存在，则创建。
    返回值：
    - True: 本次新创建
    - False: 文件已存在，未改动
    """
    if path.exists():
        return False

    path.write_text("", encoding="utf-8")
    return True


def main() -> None:
    print("=" * 72)
    print("初始化京东物流基本面数据底座")
    print("=" * 72)
    print(f"仓库根目录: {REPO_ROOT}")
    print(f"目标目录:   {FUNDAMENTAL_DIR}")
    print("")

    # 1) 创建目录
    ensure_dir(FUNDAMENTAL_DIR)
    ensure_dir(SOURCE_DOCS_DIR)
    print(f"[OK] 目录已确认: {FUNDAMENTAL_DIR}")
    print(f"[OK] 目录已确认: {SOURCE_DOCS_DIR}")

    # 2) 创建 fundamental_quarterly.csv
    created_fundamental = write_csv_header_if_not_exists(
        FUNDAMENTAL_CSV,
        FUNDAMENTAL_HEADERS,
    )
    if created_fundamental:
        print(f"[NEW] 已创建主表: {FUNDAMENTAL_CSV}")
    else:
        print(f"[SKIP] 主表已存在，未覆盖: {FUNDAMENTAL_CSV}")

    # 3) 创建 ingest_log.csv
    created_ingest_log = write_csv_header_if_not_exists(
        INGEST_LOG_CSV,
        INGEST_LOG_HEADERS,
    )
    if created_ingest_log:
        print(f"[NEW] 已创建入库日志表: {INGEST_LOG_CSV}")
    else:
        print(f"[SKIP] 入库日志表已存在，未覆盖: {INGEST_LOG_CSV}")

    # 4) 创建 source_docs/.gitkeep
    created_gitkeep = create_gitkeep_if_not_exists(GITKEEP_FILE)
    if created_gitkeep:
        print(f"[NEW] 已创建占位文件: {GITKEEP_FILE}")
    else:
        print(f"[SKIP] 占位文件已存在，未覆盖: {GITKEEP_FILE}")

    print("")
    print("=" * 72)
    print("初始化完成")
    print("=" * 72)
    print("建议下一步：")
    print("1. 新增 fundamental_quarterly_dictionary.md")
    print("2. 新增字段来源映射表文档")
    print("3. 后续再补一个 ingest_fundamental_from_excel.py 导入脚本")
    print("")


if __name__ == "__main__":
    main()
