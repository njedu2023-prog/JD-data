import os
from typing import List

import pandas as pd


REQUIRED_FILES = [
    "data_raw/02618.HK/hk_daily_raw.csv",
    "data_clean/02618.HK/daily_clean.csv",
    "data_raw/9618.HK/hk_daily_raw.csv",
    "data_clean/9618.HK/daily_clean.csv",
    "data_raw/3690.HK/hk_daily_raw.csv",
    "data_clean/3690.HK/daily_clean.csv",
    "data_raw/9988.HK/hk_daily_raw.csv",
    "data_clean/9988.HK/daily_clean.csv",
    "calendar/hk_trade_calendar.csv",
    "data_raw/HSI/hsi_raw.csv",
    "data_clean/HSI/hsi_clean.csv",
    "data_raw/HKTECH/hktech_raw.csv",
    "data_clean/HKTECH/hktech_clean.csv",
    "data_raw/HSCEI/hscei_raw.csv",
    "data_clean/HSCEI/hscei_clean.csv",
    "refresh_log/refresh_log.csv",
    "jd-logistics-latest.json",
]


def assert_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"required file not found: {path}")


def check_required_files() -> None:
    for path in REQUIRED_FILES:
        assert_file_exists(path)
    print("[OK] required files exist")


def check_equity_clean(path: str, symbol: str) -> None:
    df = pd.read_csv(path)

    required_cols = [
        "symbol",
        "market",
        "asset_type",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "prev_close",
        "volume",
        "amount",
        "pct_change",
        "ret_1d",
        "log_ret_1d",
        "quality_flag",
        "ingest_time",
        "data_version",
    ]
    _assert_required_columns(df, path, required_cols)

    _assert_not_empty(df, path)
    _assert_non_null(df, path, required_cols)
    _assert_no_duplicate_dates(df, path, "trade_date")
    _assert_sorted(df, path, "trade_date")
    _assert_constant_values(df, path, "symbol", {symbol})
    _assert_constant_values(df, path, "market", {"HK"})
    _assert_constant_values(df, path, "asset_type", {"equity"})
    _assert_quality_pass_only(df, path)

    print(f"[OK] validated {path}")


def check_index_clean(path: str, symbol: str) -> None:
    df = pd.read_csv(path)

    required_cols = [
        "symbol",
        "market",
        "asset_type",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "prev_close",
        "volume",
        "amount",
        "pct_change",
        "ret_1d",
        "log_ret_1d",
        "quality_flag",
        "ingest_time",
        "data_version",
    ]
    _assert_required_columns(df, path, required_cols)

    _assert_not_empty(df, path)
    _assert_non_null(df, path, required_cols)
    _assert_no_duplicate_dates(df, path, "trade_date")
    _assert_sorted(df, path, "trade_date")
    _assert_constant_values(df, path, "symbol", {symbol})
    _assert_constant_values(df, path, "market", {"HK"})
    _assert_constant_values(df, path, "asset_type", {"index"})
    _assert_quality_pass_only(df, path)

    print(f"[OK] validated {path}")


def check_calendar() -> None:
    path = "calendar/hk_trade_calendar.csv"
    df = pd.read_csv(path)

    required_cols = ["calendar_date", "is_trade_day", "market", "exchange", "note"]
    _assert_required_columns(df, path, required_cols)

    _assert_not_empty(df, path)
    _assert_non_null(df, path, required_cols)
    _assert_no_duplicate_dates(df, path, "calendar_date")
    _assert_sorted(df, path, "calendar_date")
    _assert_constant_values(df, path, "market", {"HK"})
    _assert_constant_values(df, path, "exchange", {"XHKG"})

    values = set(
        pd.to_numeric(df["is_trade_day"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    if not values.issubset({0, 1}):
        raise ValueError(f"{path} has invalid is_trade_day values: {sorted(values)}")

    print(f"[OK] validated {path}")


def check_refresh_log() -> None:
    path = "refresh_log/refresh_log.csv"
    df = pd.read_csv(path)

    required_cols = [
        "refresh_time",
        "source",
        "symbol",
        "rows_raw",
        "rows_clean",
        "rows_fail",
        "status",
        "message",
    ]
    _assert_required_columns(df, path, required_cols)
    _assert_not_empty(df, path)
    _assert_non_null(df, path, required_cols)

    required_symbols = {
        "02618.HK",
        "9618.HK",
        "3690.HK",
        "9988.HK",
        "HK_CALENDAR",
        "HSI",
        "HKTECH",
        "HSCEI",
    }
    existing_symbols = set(df["symbol"].astype(str).unique().tolist())
    missing_symbols = required_symbols - existing_symbols
    if missing_symbols:
        raise ValueError(f"{path} missing symbols in refresh log: {sorted(missing_symbols)}")

    print(f"[OK] validated {path}")


def _assert_required_columns(df: pd.DataFrame, path: str, required_cols: List[str]) -> None:
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")


def _assert_not_empty(df: pd.DataFrame, path: str) -> None:
    if df is None or df.empty:
        raise ValueError(f"{path} is empty")


def _assert_non_null(df: pd.DataFrame, path: str, cols: List[str]) -> None:
    null_counts = df[cols].isna().sum()
    bad = null_counts[null_counts > 0]
    if len(bad) > 0:
        raise ValueError(f"{path} has nulls in required columns: {bad.to_dict()}")


def _assert_no_duplicate_dates(df: pd.DataFrame, path: str, date_col: str) -> None:
    dup_count = int(df[date_col].duplicated().sum())
    if dup_count > 0:
        raise ValueError(f"{path} has duplicated {date_col}: {dup_count}")


def _assert_sorted(df: pd.DataFrame, path: str, date_col: str) -> None:
    s = df[date_col].astype(str)
    if not s.is_monotonic_increasing:
        raise ValueError(f"{path} {date_col} is not sorted ascending")


def _assert_constant_values(df: pd.DataFrame, path: str, col: str, allowed: set) -> None:
    values = set(df[col].dropna().astype(str).unique().tolist())
    if not values.issubset(allowed):
        raise ValueError(f"{path} column {col} has invalid values: {sorted(values)}")


def _assert_quality_pass_only(df: pd.DataFrame, path: str) -> None:
    values = set(df["quality_flag"].dropna().astype(str).unique().tolist())
    if values != {"PASS"}:
        raise ValueError(f"{path} quality_flag is not PASS-only: {sorted(values)}")


def main() -> None:
    check_required_files()
    check_equity_clean("data_clean/02618.HK/daily_clean.csv", "02618.HK")
    check_equity_clean("data_clean/9618.HK/daily_clean.csv", "9618.HK")
    check_equity_clean("data_clean/3690.HK/daily_clean.csv", "3690.HK")
    check_equity_clean("data_clean/9988.HK/daily_clean.csv", "9988.HK")
    check_calendar()
    check_index_clean("data_clean/HSI/hsi_clean.csv", "HSI")
    check_index_clean("data_clean/HKTECH/hktech_clean.csv", "HKTECH")
    check_index_clean("data_clean/HSCEI/hscei_clean.csv", "HSCEI")
    check_refresh_log()
    print("[OK] repository validation passed")


if __name__ == "__main__":
    main()
