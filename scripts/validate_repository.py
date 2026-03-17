import os
from dataclasses import dataclass
from typing import List, Sequence, Set

import pandas as pd


# ============================================================
# Gate control
# 默认不把 1519.HK 纳入仓库级总闸门。
# 当且仅当你确认 1519.HK 已正式验收合格后，
# 再在 workflow 或 Actions env 中设置：
# INCLUDE_1519_IN_GATE=1
# ============================================================

INCLUDE_1519_IN_GATE = os.getenv("INCLUDE_1519_IN_GATE", "0").strip() == "1"


# ============================================================
# Config
# ============================================================

CLEAN_REQUIRED_COLS = [
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

CALENDAR_REQUIRED_COLS = [
    "calendar_date",
    "is_trade_day",
    "market",
    "exchange",
    "note",
]

REFRESH_LOG_REQUIRED_COLS = [
    "refresh_time",
    "source",
    "symbol",
    "rows_raw",
    "rows_clean",
    "rows_fail",
    "status",
    "message",
]


@dataclass(frozen=True)
class CleanSpec:
    path: str
    symbol: str
    asset_type: str


def _base_required_files() -> List[str]:
    files = [
        "data_raw/02618.HK/hk_daily_raw.csv",
        "data_clean/02618.HK/daily_clean.csv",
        "data_raw/9618.HK/hk_daily_raw.csv",
        "data_clean/9618.HK/daily_clean.csv",
        "data_raw/3690.HK/hk_daily_raw.csv",
        "data_clean/3690.HK/daily_clean.csv",
        "data_raw/9988.HK/hk_daily_raw.csv",
        "data_clean/9988.HK/daily_clean.csv",
        "data_raw/2057.HK/hk_daily_raw.csv",
        "data_clean/2057.HK/daily_clean.csv",
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
    if INCLUDE_1519_IN_GATE:
        files.extend(
            [
                "data_raw/1519.HK/hk_daily_raw.csv",
                "data_clean/1519.HK/daily_clean.csv",
            ]
        )
    return files


def _clean_specs() -> List[CleanSpec]:
    specs = [
        CleanSpec("data_clean/02618.HK/daily_clean.csv", "02618.HK", "equity"),
        CleanSpec("data_clean/9618.HK/daily_clean.csv", "9618.HK", "equity"),
        CleanSpec("data_clean/3690.HK/daily_clean.csv", "3690.HK", "equity"),
        CleanSpec("data_clean/9988.HK/daily_clean.csv", "9988.HK", "equity"),
        CleanSpec("data_clean/2057.HK/daily_clean.csv", "2057.HK", "equity"),
        CleanSpec("data_clean/HSI/hsi_clean.csv", "HSI", "index"),
        CleanSpec("data_clean/HKTECH/hktech_clean.csv", "HKTECH", "index"),
        CleanSpec("data_clean/HSCEI/hscei_clean.csv", "HSCEI", "index"),
    ]
    if INCLUDE_1519_IN_GATE:
        specs.append(CleanSpec("data_clean/1519.HK/daily_clean.csv", "1519.HK", "equity"))
    return specs


def _required_refresh_symbols() -> Set[str]:
    symbols = {
        "02618.HK",
        "9618.HK",
        "3690.HK",
        "9988.HK",
        "2057.HK",
        "HK_CALENDAR",
        "HSI",
        "HKTECH",
        "HSCEI",
    }
    if INCLUDE_1519_IN_GATE:
        symbols.add("1519.HK")
    return symbols


# ============================================================
# Generic assertions
# ============================================================

def assert_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"required file not found: {path}")


def _read_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise ValueError(f"failed to read csv: {path} | {exc}") from exc


def _assert_required_columns(df: pd.DataFrame, path: str, required_cols: Sequence[str]) -> None:
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing required columns: {missing}")


def _assert_not_empty(df: pd.DataFrame, path: str) -> None:
    if df is None or df.empty:
        raise ValueError(f"{path} is empty")


def _assert_non_null(df: pd.DataFrame, path: str, cols: Sequence[str]) -> None:
    null_counts = df[list(cols)].isna().sum()
    bad = null_counts[null_counts > 0]
    if len(bad) > 0:
        raise ValueError(f"{path} has nulls in required columns: {bad.to_dict()}")


def _assert_no_duplicate_dates(df: pd.DataFrame, path: str, date_col: str) -> None:
    dup_count = int(df[date_col].astype(str).duplicated().sum())
    if dup_count > 0:
        raise ValueError(f"{path} has duplicated {date_col}: {dup_count}")


def _assert_sorted(df: pd.DataFrame, path: str, date_col: str) -> None:
    s = df[date_col].astype(str)
    if not s.is_monotonic_increasing:
        raise ValueError(f"{path} {date_col} is not sorted ascending")


def _assert_constant_values(df: pd.DataFrame, path: str, col: str, allowed: Set[str]) -> None:
    values = set(df[col].dropna().astype(str).unique().tolist())
    if not values.issubset(allowed):
        raise ValueError(f"{path} column {col} has invalid values: {sorted(values)}")


def _assert_quality_pass_only(df: pd.DataFrame, path: str) -> None:
    values = set(df["quality_flag"].dropna().astype(str).unique().tolist())
    if values != {"PASS"}:
        raise ValueError(f"{path} quality_flag is not PASS-only: {sorted(values)}")


def _assert_parseable_dates(df: pd.DataFrame, path: str, date_col: str) -> None:
    parsed = pd.to_datetime(df[date_col], errors="coerce")
    bad = int(parsed.isna().sum())
    if bad > 0:
        raise ValueError(f"{path} {date_col} has unparseable values: {bad}")


def _assert_numeric_columns(df: pd.DataFrame, path: str, cols: Sequence[str]) -> None:
    bad_cols = {}
    for col in cols:
        s = pd.to_numeric(df[col], errors="coerce")
        bad = int(s.isna().sum())
        if bad > 0:
            bad_cols[col] = bad
    if bad_cols:
        raise ValueError(f"{path} has non-numeric values in numeric columns: {bad_cols}")


def _assert_non_negative(df: pd.DataFrame, path: str, cols: Sequence[str]) -> None:
    bad_cols = {}
    for col in cols:
        s = pd.to_numeric(df[col], errors="coerce")
        neg = int((s < 0).sum())
        if neg > 0:
            bad_cols[col] = neg
    if bad_cols:
        raise ValueError(f"{path} has negative values in non-negative columns: {bad_cols}")


def _assert_price_bounds(df: pd.DataFrame, path: str) -> None:
    open_ = pd.to_numeric(df["open"], errors="coerce")
    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")

    if (high < low).any():
        raise ValueError(f"{path} has rows where high < low")

    if (high < open_).any():
        raise ValueError(f"{path} has rows where high < open")

    if (high < close).any():
        raise ValueError(f"{path} has rows where high < close")

    if (low > open_).any():
        raise ValueError(f"{path} has rows where low > open")

    if (low > close).any():
        raise ValueError(f"{path} has rows where low > close")


def _assert_trade_date_latest_not_blank(df: pd.DataFrame, path: str, date_col: str) -> None:
    latest = str(df[date_col].iloc[-1]).strip()
    if latest == "" or latest.lower() == "nan":
        raise ValueError(f"{path} latest {date_col} is blank")


def _assert_values_in_set(df: pd.DataFrame, path: str, col: str, allowed: Set[str]) -> None:
    values = set(df[col].dropna().astype(str).str.upper().unique().tolist())
    allowed_upper = {x.upper() for x in allowed}
    if not values.issubset(allowed_upper):
        raise ValueError(f"{path} column {col} has invalid values: {sorted(values)}")


# ============================================================
# Checks
# ============================================================

def check_required_files() -> None:
    for path in _base_required_files():
        assert_file_exists(path)
    print("[OK] required files exist")


def check_clean(spec: CleanSpec) -> None:
    path = spec.path
    df = _read_csv(path)

    _assert_required_columns(df, path, CLEAN_REQUIRED_COLS)
    _assert_not_empty(df, path)
    _assert_non_null(df, path, CLEAN_REQUIRED_COLS)

    _assert_parseable_dates(df, path, "trade_date")
    _assert_no_duplicate_dates(df, path, "trade_date")
    _assert_sorted(df, path, "trade_date")
    _assert_trade_date_latest_not_blank(df, path, "trade_date")

    _assert_constant_values(df, path, "symbol", {spec.symbol})
    _assert_constant_values(df, path, "market", {"HK"})
    _assert_constant_values(df, path, "asset_type", {spec.asset_type})
    _assert_quality_pass_only(df, path)

    _assert_numeric_columns(
        df,
        path,
        [
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
        ],
    )

    _assert_non_negative(
        df,
        path,
        [
            "open",
            "high",
            "low",
            "close",
            "prev_close",
            "volume",
            "amount",
        ],
    )

    _assert_price_bounds(df, path)

    print(f"[OK] validated {path}")


def check_calendar() -> None:
    path = "calendar/hk_trade_calendar.csv"
    df = _read_csv(path)

    _assert_required_columns(df, path, CALENDAR_REQUIRED_COLS)
    _assert_not_empty(df, path)
    _assert_non_null(df, path, CALENDAR_REQUIRED_COLS)
    _assert_parseable_dates(df, path, "calendar_date")
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
    df = _read_csv(path)

    _assert_required_columns(df, path, REFRESH_LOG_REQUIRED_COLS)
    _assert_not_empty(df, path)
    _assert_non_null(df, path, REFRESH_LOG_REQUIRED_COLS)

    _assert_parseable_dates(df, path, "refresh_time")
    _assert_numeric_columns(df, path, ["rows_raw", "rows_clean", "rows_fail"])
    _assert_non_negative(df, path, ["rows_raw", "rows_clean", "rows_fail"])
    _assert_values_in_set(df, path, "status", {"SUCCESS", "FAIL", "PARTIAL_SUCCESS"})

    required_symbols = _required_refresh_symbols()
    existing_symbols = set(df["symbol"].astype(str).unique().tolist())
    missing_symbols = required_symbols - existing_symbols
    if missing_symbols:
        raise ValueError(f"{path} missing symbols in refresh log: {sorted(missing_symbols)}")

    for symbol in sorted(required_symbols):
        sub = df[df["symbol"].astype(str) == symbol].copy()
        if sub.empty:
            raise ValueError(f"{path} symbol has no rows: {symbol}")

        statuses = set(sub["status"].astype(str).str.upper().tolist())
        if "SUCCESS" not in statuses:
            raise ValueError(f"{path} symbol has no SUCCESS refresh record: {symbol}")

        success_rows = sub[sub["status"].astype(str).str.upper() == "SUCCESS"].copy()
        if success_rows.empty:
            raise ValueError(f"{path} symbol has empty SUCCESS refresh subset: {symbol}")

        if (pd.to_numeric(success_rows["rows_clean"], errors="coerce") <= 0).all():
            raise ValueError(f"{path} symbol SUCCESS rows_clean <= 0 only: {symbol}")

    print(f"[OK] validated {path}")


def check_gate_mode() -> None:
    if INCLUDE_1519_IN_GATE:
        print("[INFO] gate mode: 1519.HK included in repository gate")
    else:
        print("[INFO] gate mode: 1519.HK excluded from repository gate")


# ============================================================
# Main
# ============================================================

def main() -> None:
    check_gate_mode()
    check_required_files()

    for spec in _clean_specs():
        check_clean(spec)

    check_calendar()
    check_refresh_log()

    print("[OK] repository validation passed")


if __name__ == "__main__":
    main()
