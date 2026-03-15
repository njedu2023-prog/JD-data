import os
from datetime import datetime, timezone

import pandas as pd
import tushare as ts


CALENDAR_DIR = "calendar"
CALENDAR_PATH = f"{CALENDAR_DIR}/hk_trade_calendar.csv"
REFRESH_LOG_PATH = "refresh_log/refresh_log.csv"

EXCHANGE = "XHKG"
MARKET = "HK"

# 先覆盖近几年到未来一年，够当前系统使用；
# 后面若需要再扩历史范围
START_DATE = "20200101"
END_DATE = "20271231"


def ensure_dirs() -> None:
    os.makedirs(CALENDAR_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REFRESH_LOG_PATH), exist_ok=True)


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def append_refresh_log(
    status: str,
    symbol: str,
    rows_raw: int,
    rows_clean: int,
    fail_rows: int,
    message: str,
) -> None:
    exists = os.path.exists(REFRESH_LOG_PATH)

    log_df = pd.DataFrame(
        [
            {
                "refresh_time": utc_now_iso(),
                "source": "tushare.hk_trade_calendar",
                "symbol": symbol,
                "rows_raw": rows_raw,
                "rows_clean": rows_clean,
                "rows_fail": fail_rows,
                "status": status,
                "message": message,
            }
        ]
    )

    log_df.to_csv(
        REFRESH_LOG_PATH,
        mode="a",
        header=not exists,
        index=False,
        encoding="utf-8",
    )


def normalize_calendar(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = ["exchange", "cal_date", "is_open"]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"trade calendar missing required columns: {missing}")

    out = df[required_cols].copy()

    out["calendar_date"] = (
        pd.to_datetime(out["cal_date"].astype(str).str.strip(), format="%Y%m%d", errors="coerce")
        .dt.strftime("%Y-%m-%d")
    )

    out["is_trade_day"] = pd.to_numeric(out["is_open"], errors="coerce").fillna(0).astype(int)
    out["market"] = MARKET
    out["exchange"] = out["exchange"].astype(str).str.strip()
    out["note"] = out["is_trade_day"].map(lambda x: "trade_day" if x == 1 else "non_trade_day")

    out = out[
        ["calendar_date", "is_trade_day", "market", "exchange", "note"]
    ].copy()

    out = out.drop_duplicates(subset=["calendar_date"], keep="last")
    out = out.sort_values("calendar_date").reset_index(drop=True)

    return out


def validate_calendar(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        raise ValueError("hk_trade_calendar is empty")

    required_cols = ["calendar_date", "is_trade_day", "market", "exchange", "note"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"hk_trade_calendar missing required columns: {missing}")

    null_counts = df[required_cols].isna().sum()
    bad_cols = null_counts[null_counts > 0]
    if len(bad_cols) > 0:
        raise ValueError(f"hk_trade_calendar has nulls: {bad_cols.to_dict()}")

    if df["calendar_date"].duplicated().any():
        dup_count = int(df["calendar_date"].duplicated().sum())
        raise ValueError(f"hk_trade_calendar has duplicated calendar_date rows: {dup_count}")

    if not df["calendar_date"].is_monotonic_increasing:
        raise ValueError("hk_trade_calendar calendar_date is not sorted ascending")

    unique_open = set(df["is_trade_day"].dropna().astype(int).unique().tolist())
    if not unique_open.issubset({0, 1}):
        raise ValueError(f"hk_trade_calendar has invalid is_trade_day values: {sorted(unique_open)}")

    if (df["market"] != MARKET).any():
        raise ValueError("hk_trade_calendar market contains invalid values")

    if (df["exchange"] != EXCHANGE).any():
        raise ValueError("hk_trade_calendar exchange contains invalid values")


def main() -> None:
    ensure_dirs()

    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if not token:
        raise SystemExit("TUSHARE_TOKEN not set")

    ts.set_token(token)
    pro = ts.pro_api()

    rows_raw = 0
    rows_clean = 0

    try:
        df_raw = pro.trade_cal(
            exchange=EXCHANGE,
            start_date=START_DATE,
            end_date=END_DATE,
            fields="exchange,cal_date,is_open",
        )

        if df_raw is None or df_raw.empty:
            append_refresh_log(
                status="empty",
                symbol="HK_CALENDAR",
                rows_raw=0,
                rows_clean=0,
                fail_rows=0,
                message="trade_cal returned empty dataframe",
            )
            raise SystemExit(0)

        rows_raw = len(df_raw)
        calendar_df = normalize_calendar(df_raw)
        rows_clean = len(calendar_df)

        validate_calendar(calendar_df)

        calendar_df.to_csv(CALENDAR_PATH, index=False, encoding="utf-8")

        append_refresh_log(
            status="success",
            symbol="HK_CALENDAR",
            rows_raw=rows_raw,
            rows_clean=rows_clean,
            fail_rows=0,
            message="hk trade calendar refresh completed",
        )

        print(f"[OK] rows_raw={rows_raw} rows_clean={rows_clean}")
        print(f"[OK] CALENDAR_PATH={CALENDAR_PATH}")

    except SystemExit:
        raise
    except Exception as e:
        append_refresh_log(
            status="error",
            symbol="HK_CALENDAR",
            rows_raw=rows_raw,
            rows_clean=rows_clean,
            fail_rows=0,
            message=str(e),
        )
        raise


if __name__ == "__main__":
    main()
