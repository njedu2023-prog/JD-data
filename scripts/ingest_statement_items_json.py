# -*- coding: utf-8 -*-
"""
将 staging JSON 装入 fundamental_statement_items.csv

功能：
1. 读取 data_fundamental/02618.HK/temp_statement_items_2025_fy.json
2. upsert 到 data_fundamental/02618.HK/fundamental_statement_items.csv
3. 主键：
   symbol + report_date + period_type + statement_type + item_code
4. 输出：
   inserted_count / updated_count / total_count

用法：
python scripts/ingest_statement_items_json.py

可选：
python scripts/ingest_statement_items_json.py \
  --json data_fundamental/02618.HK/temp_statement_items_2025_fy.json \
  --csv  data_fundamental/02618.HK/fundamental_statement_items.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

CSV_COLUMNS = [
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

PRIMARY_KEY_FIELDS = [
    "symbol",
    "report_date",
    "period_type",
    "statement_type",
    "item_code",
]

REQUIRED_JSON_FIELDS = CSV_COLUMNS


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_json = repo_root / "data_fundamental" / "02618.HK" / "temp_statement_items_2025_fy.json"
    default_csv = repo_root / "data_fundamental" / "02618.HK" / "fundamental_statement_items.csv"

    parser = argparse.ArgumentParser(description="Ingest statement items JSON into CSV with upsert.")
    parser.add_argument("--json", dest="json_path", default=str(default_json), help="Path to staging JSON file.")
    parser.add_argument("--csv", dest="csv_path", default=str(default_csv), help="Path to target CSV file.")
    return parser.parse_args()


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json_records(json_path: Path) -> List[Dict[str, Any]]:
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    try:
        text = json_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = json_path.read_text(encoding="utf-8-sig")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {json_path}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"JSON root must be a list, got: {type(data).__name__}")

    normalized_records: List[Dict[str, Any]] = []
    for idx, record in enumerate(data, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"Record #{idx} must be an object, got: {type(record).__name__}")

        missing = [field for field in REQUIRED_JSON_FIELDS if field not in record]
        if missing:
            raise ValueError(f"Record #{idx} missing fields: {missing}")

        normalized = {col: normalize_value(record.get(col)) for col in CSV_COLUMNS}
        validate_primary_key(normalized, idx)
        normalized_records.append(normalized)

    return normalized_records


def normalize_value(value: Any) -> Any:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return value


def validate_primary_key(record: Dict[str, Any], idx: int) -> None:
    missing_pk = [field for field in PRIMARY_KEY_FIELDS if str(record.get(field, "")).strip() == ""]
    if missing_pk:
        raise ValueError(f"Record #{idx} has empty primary key fields: {missing_pk}")


def read_existing_csv(csv_path: Path) -> List[Dict[str, Any]]:
    if not csv_path.exists():
        return []

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return []

            existing_columns = reader.fieldnames
            missing_columns = [col for col in CSV_COLUMNS if col not in existing_columns]
            if missing_columns:
                raise ValueError(
                    f"Existing CSV missing required columns: {missing_columns}. "
                    f"Expected columns: {CSV_COLUMNS}"
                )

            rows: List[Dict[str, Any]] = []
            for row in reader:
                normalized = {col: row.get(col, "") for col in CSV_COLUMNS}
                rows.append(normalized)
            return rows
    except UnicodeDecodeError:
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return []

            existing_columns = reader.fieldnames
            missing_columns = [col for col in CSV_COLUMNS if col not in existing_columns]
            if missing_columns:
                raise ValueError(
                    f"Existing CSV missing required columns: {missing_columns}. "
                    f"Expected columns: {CSV_COLUMNS}"
                )

            rows = []
            for row in reader:
                normalized = {col: row.get(col, "") for col in CSV_COLUMNS}
                rows.append(normalized)
            return rows


def pk_tuple(record: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    return tuple(str(record[field]) for field in PRIMARY_KEY_FIELDS)  # type: ignore[return-value]


def records_equal(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    for col in CSV_COLUMNS:
        if str(a.get(col, "")) != str(b.get(col, "")):
            return False
    return True


def upsert_records(
    existing_rows: List[Dict[str, Any]],
    new_rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int, int]:
    existing_map: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {
        pk_tuple(row): row for row in existing_rows
    }

    inserted_count = 0
    updated_count = 0

    for row in new_rows:
        key = pk_tuple(row)
        old_row = existing_map.get(key)

        if old_row is None:
            existing_map[key] = row
            inserted_count += 1
        else:
            if not records_equal(old_row, row):
                existing_map[key] = row
                updated_count += 1

    merged_rows = list(existing_map.values())
    merged_rows.sort(
        key=lambda r: (
            str(r["symbol"]),
            str(r["report_date"]),
            str(r["period_type"]),
            str(r["statement_type"]),
            str(r["item_code"]),
        )
    )
    return merged_rows, inserted_count, updated_count


def write_csv(csv_path: Path, rows: List[Dict[str, Any]]) -> None:
    ensure_parent_dir(csv_path)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            ordered_row = {col: row.get(col, "") for col in CSV_COLUMNS}
            writer.writerow(ordered_row)


def main() -> int:
    args = parse_args()
    json_path = Path(args.json_path).resolve()
    csv_path = Path(args.csv_path).resolve()

    try:
        new_rows = load_json_records(json_path)
        existing_rows = read_existing_csv(csv_path)
        merged_rows, inserted_count, updated_count = upsert_records(existing_rows, new_rows)
        write_csv(csv_path, merged_rows)

        print(f"JSON source   : {json_path}")
        print(f"CSV target    : {csv_path}")
        print(f"Inserted rows : {inserted_count}")
        print(f"Updated rows  : {updated_count}")
        print(f"Total rows    : {len(merged_rows)}")
        return 0

    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
