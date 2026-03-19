# -*- coding: utf-8 -*-
"""
京东物流基本面主表：最小可用导入脚手架（V1 Stub）

作用：
1. 读取待导入 JSON 文件（记录列表）
2. 按主键 symbol + report_date + period_type 对 fundamental_quarterly.csv 执行 upsert
3. 自动补写 ingest_time / data_version / quality_flag 等治理字段
4. 写入 ingest_log.csv 留痕
5. 为后续 Excel / PDF / 文档抽取后的结构化结果提供统一落库入口

当前定位：
- 这是“导入骨架”，不是最终智能抽取器
- 当前只负责“结构化记录 -> 主表”
- 后续可再加：Excel 解析、公告抽取、字段校验增强、公式字段补算

建议运行：
python scripts/ingest_fundamental_stub.py --input temp_fundamental_records.json

输入 JSON 示例：
[
  {
    "symbol": "02618.HK",
    "report_date": "2025-09-30",
    "announce_date": "2025-11-13",
    "period_type": "quarter",
    "fiscal_year": 2025,
    "fiscal_period": "Q3",
    "currency": "rmb",
    "unit": "million_rmb",
    "revenue": 55100,
    "revenue_yoy": 0.241,
    "supply_chain_revenue": 30100,
    "external_customer_revenue": 8900,
    "net_profit": 2000,
    "gross_margin": 0.091,
    "adj_ebitda_margin": 0.097,
    "warehouse_count": 1600,
    "cloud_warehouse_count": 2000,
    "warehouse_area": 34000000,
    "major_event_flag": 1,
    "major_event_type": "acquisition",
    "major_event_note": "以2.7亿美元收购本地即时配送业务",
    "management_guidance": "继续强化一体化供应链与最后一公里能力",
    "source_type": "interim_report",
    "source_url": "https://example.com/report",
    "source_title": "京东物流2025年三季报",
    "quality_note": "部分字段待人工复核",
    "is_manual_verified": 0
  }
]
"""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = REPO_ROOT / "data_fundamental" / "02618.HK"

FUNDAMENTAL_CSV = BASE_DIR / "fundamental_quarterly.csv"
INGEST_LOG_CSV = BASE_DIR / "ingest_log.csv"

PRIMARY_KEY_FIELDS = ["symbol", "report_date", "period_type"]

DEFAULT_OPERATOR = "chatgpt"
DEFAULT_DATA_VERSION = "v1"
DEFAULT_STATUS_SUCCESS = "SUCCESS"
DEFAULT_STATUS_ERROR = "ERROR"
DEFAULT_ACTION_UPSERT = "upsert"

REQUIRED_MIN_FIELDS = [
    "symbol",
    "report_date",
    "announce_date",
    "period_type",
    "fiscal_year",
    "fiscal_period",
    "currency",
    "unit",
    "source_type",
    "source_title",
]

OPTIONAL_DEFAULTS = {
    "company_name_zh": "京东物流",
    "company_name_en": "JD Logistics, Inc.",
    "data_version": DEFAULT_DATA_VERSION,
    "quality_flag": "REVIEW",
    "quality_note": "",
    "is_manual_verified": "0",
    "verified_by": "",
    "verified_time": "",
    "source_url": "",
    "major_event_flag": "0",
    "guidance_change_flag": "0",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入京东物流基本面结构化记录到主表")
    parser.add_argument(
        "--input",
        required=True,
        help="待导入 JSON 文件路径，内容为记录列表",
    )
    parser.add_argument(
        "--operator",
        default=DEFAULT_OPERATOR,
        help="操作者标识，默认 chatgpt",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅校验和预演，不落库",
    )
    return parser.parse_args()


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def write_csv_rows(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            normalized = {h: normalize_value(row.get(h, "")) for h in headers}
            writer.writerow(normalized)


def normalize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def ensure_base_files_exist() -> None:
    missing = []
    if not FUNDAMENTAL_CSV.exists():
        missing.append(str(FUNDAMENTAL_CSV))
    if not INGEST_LOG_CSV.exists():
        missing.append(str(INGEST_LOG_CSV))
    if missing:
        raise FileNotFoundError(
            "以下基础文件不存在，请先初始化基本面底座：\n" + "\n".join(missing)
        )


def load_input_records(input_path: Path) -> list[dict[str, Any]]:
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("输入 JSON 顶层必须是列表 list")
    if not data:
        raise ValueError("输入 JSON 不能为空列表")

    normalized_records: list[dict[str, Any]] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {i} 条记录不是对象 dict")
        normalized_records.append(item)

    return normalized_records


def validate_record(record: dict[str, Any], allowed_headers: set[str], idx: int) -> None:
    for field in REQUIRED_MIN_FIELDS:
        if record.get(field) in (None, ""):
            raise ValueError(f"第 {idx} 条记录缺少必填字段：{field}")

    for field in PRIMARY_KEY_FIELDS:
        if record.get(field) in (None, ""):
            raise ValueError(f"第 {idx} 条记录缺少主键字段：{field}")

    unknown_fields = set(record.keys()) - allowed_headers
    if unknown_fields:
        raise ValueError(
            f"第 {idx} 条记录存在主表未定义字段：{sorted(unknown_fields)}"
        )

    period_type = str(record.get("period_type", "")).strip()
    if period_type not in {"quarter", "semiannual", "annual"}:
        raise ValueError(
            f"第 {idx} 条记录的 period_type 非法：{period_type}"
        )

    symbol = str(record.get("symbol", "")).strip()
    if symbol != "02618.HK":
        raise ValueError(
            f"第 {idx} 条记录的 symbol 非法：{symbol}，当前仅允许 02618.HK"
        )


def build_primary_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return tuple(str(record.get(k, "")).strip() for k in PRIMARY_KEY_FIELDS)  # type: ignore[return-value]


def apply_defaults(record: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(record)
    for k, v in OPTIONAL_DEFAULTS.items():
        if out.get(k) in (None, ""):
            out[k] = v

    if out.get("ingest_time") in (None, ""):
        out["ingest_time"] = utc_now_iso()

    if str(out.get("is_manual_verified", "")) in ("True", "true"):
        out["is_manual_verified"] = "1"
    elif str(out.get("is_manual_verified", "")) in ("False", "false"):
        out["is_manual_verified"] = "0"

    return out


def upsert_rows(
    existing_rows: list[dict[str, str]],
    incoming_records: list[dict[str, Any]],
    headers: list[str],
) -> tuple[list[dict[str, Any]], int, int]:
    row_map: dict[tuple[str, str, str], dict[str, Any]] = {
        build_primary_key(row): dict(row) for row in existing_rows
    }

    inserted = 0
    updated = 0

    for raw_record in incoming_records:
        record = apply_defaults(raw_record)
        key = build_primary_key(record)

        if key in row_map:
            existing = row_map[key]
            for h in headers:
                if h in record and record[h] not in (None, ""):
                    existing[h] = record[h]
            existing["ingest_time"] = utc_now_iso()
            row_map[key] = existing
            updated += 1
        else:
            new_row = {h: "" for h in headers}
            for h in headers:
                if h in record:
                    new_row[h] = record[h]
            row_map[key] = new_row
            inserted += 1

    merged_rows = list(row_map.values())
    merged_rows.sort(
        key=lambda r: (
            str(r.get("symbol", "")),
            str(r.get("report_date", "")),
            str(r.get("period_type", "")),
        )
    )
    return merged_rows, inserted, updated


def append_ingest_log(
    operator: str,
    source_file: str,
    source_type: str,
    source_url: str,
    report_date: str,
    period_type: str,
    rows_affected: int,
    status: str,
    message: str,
) -> None:
    headers, rows = read_csv_rows(INGEST_LOG_CSV)
    required_log_headers = {
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
    }
    if set(headers) != required_log_headers:
        raise ValueError("ingest_log.csv 表头与预期不一致，请先校验基础文件")

    rows.append(
        {
            "ingest_time": utc_now_iso(),
            "symbol": "02618.HK",
            "report_date": report_date,
            "period_type": period_type,
            "source_file": source_file,
            "source_type": source_type,
            "source_url": source_url,
            "action": DEFAULT_ACTION_UPSERT,
            "rows_affected": str(rows_affected),
            "status": status,
            "message": message,
            "operator": operator,
        }
    )
    write_csv_rows(INGEST_LOG_CSV, headers, rows)


def main() -> None:
    args = parse_args()
    ensure_base_files_exist()

    input_path = Path(args.input).resolve()
    fundamental_headers, existing_rows = read_csv_rows(FUNDAMENTAL_CSV)
    allowed_headers = set(fundamental_headers)

    incoming_records = load_input_records(input_path)

    for idx, record in enumerate(incoming_records, start=1):
        validate_record(record, allowed_headers, idx)

    merged_rows, inserted, updated = upsert_rows(
        existing_rows=existing_rows,
        incoming_records=incoming_records,
        headers=fundamental_headers,
    )

    total_affected = inserted + updated
    first_record = incoming_records[0]
    source_type = str(first_record.get("source_type", ""))
    source_url = str(first_record.get("source_url", ""))
    report_date = str(first_record.get("report_date", ""))
    period_type = str(first_record.get("period_type", ""))

    print("=" * 72)
    print("京东物流基本面导入脚手架（V1 Stub）")
    print("=" * 72)
    print(f"输入文件:      {input_path}")
    print(f"目标主表:      {FUNDAMENTAL_CSV}")
    print(f"目标日志表:    {INGEST_LOG_CSV}")
    print(f"输入记录数:    {len(incoming_records)}")
    print(f"新增行数:      {inserted}")
    print(f"更新行数:      {updated}")
    print(f"总影响行数:    {total_affected}")
    print(f"dry_run:       {args.dry_run}")
    print("")

    if args.dry_run:
        print("[DRY-RUN] 预演完成，未写入任何文件。")
        return

    write_csv_rows(FUNDAMENTAL_CSV, fundamental_headers, merged_rows)

    append_ingest_log(
        operator=args.operator,
        source_file=input_path.name,
        source_type=source_type,
        source_url=source_url,
        report_date=report_date,
        period_type=period_type,
        rows_affected=total_affected,
        status=DEFAULT_STATUS_SUCCESS,
        message=f"ingested {len(incoming_records)} record(s), inserted={inserted}, updated={updated}",
    )

    print("[OK] 主表已完成 upsert")
    print("[OK] ingest_log 已追加留痕")
    print("")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
