# -*- coding: utf-8 -*-
"""
validate_fundamental_table.py

用途：
1. 校验 data_fundamental 下的 fundamental_quarterly.csv 是否符合基础质量要求
2. 检查表头、主键、必填字段、枚举字段、日期字段、数值字段、布尔字段
3. 适合作为本地/CI/GitHub Actions 的质量闸门

默认校验路径：
data_fundamental/02618.HK/fundamental_quarterly.csv

可选命令：
python scripts/validate_fundamental_table.py
python scripts/validate_fundamental_table.py --file data_fundamental/02618.HK/fundamental_quarterly.csv
python scripts/validate_fundamental_table.py --root .
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple


EXPECTED_HEADERS: List[str] = [
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

PRIMARY_KEY_FIELDS: Tuple[str, str, str] = ("symbol", "report_date", "period_type")

REQUIRED_FIELDS: Tuple[str, ...] = (
    "symbol",
    "company_name_zh",
    "report_date",
    "announce_date",
    "period_type",
    "fiscal_year",
    "fiscal_period",
    "currency",
    "unit",
    "source_type",
    "source_title",
    "ingest_time",
    "data_version",
    "quality_flag",
    "is_manual_verified",
)

ALLOWED_PERIOD_TYPES: Set[str] = {"quarter", "semiannual", "annual"}
ALLOWED_CURRENCIES: Set[str] = {"rmb", "hkd", "usd"}
ALLOWED_QUALITY_FLAGS: Set[str] = {"OK", "REVIEW", "WARN", "ERROR"}
ALLOWED_BOOLEAN_VALUES: Set[str] = {"0", "1", "true", "false", "TRUE", "FALSE"}

DATE_FIELDS: Tuple[str, ...] = (
    "report_date",
    "announce_date",
    "verified_time",
)

DATETIME_FIELDS: Tuple[str, ...] = (
    "ingest_time",
)

INTEGER_LIKE_FIELDS: Tuple[str, ...] = (
    "fiscal_year",
    "major_event_flag",
    "guidance_change_flag",
    "is_manual_verified",
    "integrated_supply_chain_clients",
    "warehouse_count",
    "warehouse_area",
    "cloud_warehouse_count",
)

NUMERIC_FIELDS: Tuple[str, ...] = (
    "revenue",
    "revenue_yoy",
    "revenue_qoq",
    "core_business_revenue",
    "supply_chain_revenue",
    "external_customer_revenue",
    "other_revenue",
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
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "free_cash_flow",
    "capex",
    "cash_and_equivalents",
    "restricted_cash",
    "total_assets",
    "total_liabilities",
    "total_equity",
    "current_assets",
    "current_liabilities",
    "interest_bearing_debt",
    "net_cash",
    "debt_to_asset_ratio",
    "inventory",
    "inventory_turnover_days",
    "accounts_receivable",
    "accounts_receivable_turnover_days",
    "accounts_payable",
    "accounts_payable_turnover_days",
    "working_capital",
    "working_capital_change",
    "county_coverage_ratio",
    "market_cap",
    "ps_ttm",
    "pe_ttm",
    "pb",
    "ev_to_ebitda",
)

SOURCE_URL_OPTIONAL = True


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    infos: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        self.infos.append(message)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate fundamental quarterly CSV.")
    parser.add_argument(
        "--root",
        default=".",
        help="仓库根目录，默认当前目录",
    )
    parser.add_argument(
        "--file",
        default="data_fundamental/02618.HK/fundamental_quarterly.csv",
        help="待校验 CSV 相对路径",
    )
    return parser.parse_args()


def is_blank(value: Optional[str]) -> bool:
    return value is None or str(value).strip() == ""


def normalize(value: Optional[str]) -> str:
    return "" if value is None else str(value).strip()


def is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_valid_datetime(value: str) -> bool:
    try:
        # 兼容 Z 结尾
        value2 = value.replace("Z", "+00:00")
        datetime.fromisoformat(value2)
        return True
    except ValueError:
        return False


def is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_integer_like(value: str) -> bool:
    try:
        f = float(value)
        return f.is_integer()
    except ValueError:
        return False


def load_csv(csv_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def validate_headers(headers: Sequence[str], result: ValidationResult) -> None:
    actual = list(headers)
    expected = list(EXPECTED_HEADERS)

    missing = [h for h in expected if h not in actual]
    extra = [h for h in actual if h not in expected]

    if missing:
        result.add_error(f"表头缺失字段: {missing}")

    if extra:
        result.add_warning(f"表头存在额外字段: {extra}")

    if actual != expected:
        result.add_warning("表头顺序与 EXPECTED_HEADERS 不完全一致。")
    else:
        result.add_info("表头顺序校验通过。")


def validate_required_fields(row: Dict[str, str], row_num: int, result: ValidationResult) -> None:
    for field_name in REQUIRED_FIELDS:
        if is_blank(row.get(field_name)):
            result.add_error(f"第 {row_num} 行必填字段为空: {field_name}")


def validate_enum_fields(row: Dict[str, str], row_num: int, result: ValidationResult) -> None:
    period_type = normalize(row.get("period_type"))
    if period_type and period_type not in ALLOWED_PERIOD_TYPES:
        result.add_error(f"第 {row_num} 行 period_type 非法: {period_type}")

    currency = normalize(row.get("currency"))
    if currency and currency not in ALLOWED_CURRENCIES:
        result.add_warning(f"第 {row_num} 行 currency 不在推荐集合内: {currency}")

    quality_flag = normalize(row.get("quality_flag"))
    if quality_flag and quality_flag not in ALLOWED_QUALITY_FLAGS:
        result.add_error(f"第 {row_num} 行 quality_flag 非法: {quality_flag}")

    for field_name in ("major_event_flag", "guidance_change_flag", "is_manual_verified"):
        value = normalize(row.get(field_name))
        if value and value not in ALLOWED_BOOLEAN_VALUES:
            result.add_error(f"第 {row_num} 行 {field_name} 不是允许布尔值: {value}")


def validate_date_fields(row: Dict[str, str], row_num: int, result: ValidationResult) -> None:
    for field_name in DATE_FIELDS:
        value = normalize(row.get(field_name))
        if value and not is_valid_date(value):
            result.add_error(f"第 {row_num} 行 {field_name} 日期格式错误，应为 YYYY-MM-DD: {value}")

    for field_name in DATETIME_FIELDS:
        value = normalize(row.get(field_name))
        if value and not is_valid_datetime(value):
            result.add_error(f"第 {row_num} 行 {field_name} 时间格式错误，应为 ISO-8601: {value}")


def validate_numeric_fields(row: Dict[str, str], row_num: int, result: ValidationResult) -> None:
    for field_name in NUMERIC_FIELDS:
        value = normalize(row.get(field_name))
        if value and not is_numeric(value):
            result.add_error(f"第 {row_num} 行 {field_name} 不是合法数值: {value}")

    for field_name in INTEGER_LIKE_FIELDS:
        value = normalize(row.get(field_name))
        if value and not is_integer_like(value):
            result.add_warning(f"第 {row_num} 行 {field_name} 建议为整数口径，当前值: {value}")


def validate_primary_key(rows: Sequence[Dict[str, str]], result: ValidationResult) -> None:
    seen: Dict[Tuple[str, str, str], int] = {}
    for idx, row in enumerate(rows, start=2):
        key = tuple(normalize(row.get(f)) for f in PRIMARY_KEY_FIELDS)
        if any(is_blank(v) for v in key):
            result.add_error(f"第 {idx} 行主键字段不完整: {PRIMARY_KEY_FIELDS} -> {key}")
            continue

        if key in seen:
            result.add_error(
                f"主键重复: 第 {seen[key]} 行 与 第 {idx} 行 重复，主键={key}"
            )
        else:
            seen[key] = idx

    result.add_info(f"主键去重检查完成，共检查 {len(rows)} 行数据。")


def validate_semantic_rules(row: Dict[str, str], row_num: int, result: ValidationResult) -> None:
    fiscal_year = normalize(row.get("fiscal_year"))
    report_date = normalize(row.get("report_date"))
    fiscal_period = normalize(row.get("fiscal_period"))
    period_type = normalize(row.get("period_type"))
    source_url = normalize(row.get("source_url"))
    verified_time = normalize(row.get("verified_time"))
    is_manual_verified = normalize(row.get("is_manual_verified"))

    if fiscal_year and report_date and is_valid_date(report_date):
        report_year = report_date[:4]
        if fiscal_year != report_year:
            result.add_warning(
                f"第 {row_num} 行 fiscal_year={fiscal_year} 与 report_date 年份={report_year} 不一致"
            )

    if period_type == "quarter" and fiscal_period and not fiscal_period.startswith("Q"):
        result.add_warning(f"第 {row_num} 行 quarter 记录的 fiscal_period 建议写成 Q1/Q2/Q3/Q4，当前为: {fiscal_period}")

    if period_type == "semiannual" and fiscal_period and fiscal_period not in {"H1", "H2"}:
        result.add_warning(f"第 {row_num} 行 semiannual 记录的 fiscal_period 建议为 H1/H2，当前为: {fiscal_period}")

    if period_type == "annual" and fiscal_period and fiscal_period != "FY":
        result.add_warning(f"第 {row_num} 行 annual 记录的 fiscal_period 建议为 FY，当前为: {fiscal_period}")

    if not SOURCE_URL_OPTIONAL and is_blank(source_url):
        result.add_error(f"第 {row_num} 行 source_url 不能为空")

    if is_manual_verified in {"1", "true", "TRUE"} and is_blank(verified_time):
        result.add_warning(f"第 {row_num} 行 is_manual_verified=1，但 verified_time 为空")

    if is_manual_verified in {"0", "false", "FALSE"} and not is_blank(verified_time):
        result.add_warning(f"第 {row_num} 行 is_manual_verified=0，但 verified_time 有值")


def validate_rows(rows: Sequence[Dict[str, str]], result: ValidationResult) -> None:
    if not rows:
        result.add_error("CSV 无数据行，至少应有 1 行数据。")
        return

    for row_num, row in enumerate(rows, start=2):
        validate_required_fields(row, row_num, result)
        validate_enum_fields(row, row_num, result)
        validate_date_fields(row, row_num, result)
        validate_numeric_fields(row, row_num, result)
        validate_semantic_rules(row, row_num, result)


def print_result(result: ValidationResult, csv_path: Path, row_count: int) -> None:
    print("=" * 80)
    print("fundamental 表校验结果")
    print("=" * 80)
    print(f"文件: {csv_path}")
    print(f"数据行数: {row_count}")
    print(f"错误数: {len(result.errors)}")
    print(f"警告数: {len(result.warnings)}")
    print(f"提示数: {len(result.infos)}")
    print("-" * 80)

    if result.infos:
        print("[INFO]")
        for msg in result.infos:
            print(f"- {msg}")
        print("-" * 80)

    if result.warnings:
        print("[WARN]")
        for msg in result.warnings:
            print(f"- {msg}")
        print("-" * 80)

    if result.errors:
        print("[ERROR]")
        for msg in result.errors:
            print(f"- {msg}")
        print("-" * 80)

    if result.ok:
        print("结论: 校验通过。")
    else:
        print("结论: 校验失败。")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    csv_path = (root / args.file).resolve()

    result = ValidationResult()

    if not csv_path.exists():
        result.add_error(f"文件不存在: {csv_path}")
        print_result(result, csv_path, 0)
        return 1

    if not csv_path.is_file():
        result.add_error(f"目标不是文件: {csv_path}")
        print_result(result, csv_path, 0)
        return 1

    try:
        headers, rows = load_csv(csv_path)
    except Exception as exc:
        result.add_error(f"读取 CSV 失败: {exc}")
        print_result(result, csv_path, 0)
        return 1

    validate_headers(headers, result)
    validate_primary_key(rows, result)
    validate_rows(rows, result)
    print_result(result, csv_path, len(rows))

    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
