import math
import os
from datetime import datetime, timezone

import pandas as pd
import tushare as ts


TS_CODE = "09618.HK"
SYMBOL = "9618.HK"
MARKET = "HK"
ASSET_TYPE = "equity"
START_DATE = "20200618"

RAW_DIR = "data_raw/9618.HK"
CLEAN_DIR = "data_clean/9618.HK"
RAW_PATH = f"{RAW_DIR}/hk_daily_raw.csv"
CLEAN_PATH = f"{CLEAN_DIR}/daily_clean.csv"
REFRESH_LOG_PATH = "refresh_log/refresh_log.csv"


def ensure_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLEAN_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REFRESH_LOG_PATH), exist_ok=True)


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def data_version() -> str:
    return f"D{datetime.now(timezone.utc).strftime('%Y%m%d')}.01"


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
                "source": "tushare.hk_daily",
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


def fetch_raw_from_tushare() -> pd.DataFrame:
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if not token:
        raise ValueError("missing TUSHARE_TOKEN")

    ts.set_token(token)
    pro = ts.pro_api()

    df = pro.hk_daily(ts_code=TS_CODE, start_date=START_DATE)
    if df is None or df.empty:
        return pd.DataFrame()

    return df


def prepare_raw_table(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return pd.DataFrame(
            columns=[
                "ts_code",
                "trade_date",
                "open",
                "high",
                "low",
                "close",
                "pre_close",
                "change",
                "pct_chg",
                "vol",
                "amount",
            ]
        )

    required_cols = [
        "ts_code",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "pre_close",
        "change",
        "pct_chg",
        "vol",
        "amount",
    ]
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        raise ValueError(f"hk_daily raw missing required columns: {missing}")

    df = df_raw.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["trade_date"]).copy()

    df = (
        df.sort_values("trade_date")
        .drop_duplicates(subset=["ts_code", "trade_date"], keep="last")
        .reset_index(drop=True)
    )

    df["trade_date"] = df["trade_date"].dt.strftime("%Y%m%d")
    return df


def build_clean_table(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d", errors="coerce")
    df = (
        df.sort_values("trade_date")
        .drop_duplicates(subset=["ts_code", "trade_date"], keep="last")
        .reset_index(drop=True)
    )

    clean = pd.DataFrame(index=df.index)
    clean["symbol"] = SYMBOL
    clean["market"] = MARKET
    clean["asset_type"] = ASSET_TYPE
    clean["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")

    clean["open"] = pd.to_numeric(df["open"], errors="coerce")
    clean["high"] = pd.to_numeric(df["high"], errors="coerce")
    clean["low"] = pd.to_numeric(df["low"], errors="coerce")
    clean["close"] = pd.to_numeric(df["close"], errors="coerce")
    clean["prev_close"] = pd.to_numeric(df["pre_close"], errors="coerce")
    clean["volume"] = pd.to_numeric(df["vol"], errors="coerce")
    clean["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # 历史首行通常没有 prev_close，不进入正式 clean 主表
    clean = clean[~clean["prev_close"].isna()].copy().reset_index(drop=True)

    clean["pct_change"] = clean["close"] / clean["prev_close"] - 1.0
    clean["ret_1d"] = clean["pct_change"]

    ratio = clean["close"] / clean["prev_close"]
    clean["log_ret_1d"] = ratio.map(
        lambda x: pd.NA if pd.isna(x) or x <= 0 else math.log(x)
    )

    clean["quality_flag"] = "PASS"

    invalid_mask = (
        clean["symbol"].isna()
        | clean["market"].isna()
        | clean["asset_type"].isna()
        | clean["trade_date"].isna()
        | clean["open"].isna()
        | clean["high"].isna()
        | clean["low"].isna()
        | clean["close"].isna()
        | clean["prev_close"].isna()
        | clean["volume"].isna()
        | clean["amount"].isna()
        | (clean["high"] < clean["low"])
        | (clean["high"] < clean["open"])
        | (clean["high"] < clean["close"])
        | (clean["low"] > clean["open"])
        | (clean["low"] > clean["close"])
        | (clean["volume"] < 0)
        | (clean["amount"] < 0)
    )
    clean.loc[invalid_mask, "quality_flag"] = "FAIL"

    clean["ingest_time"] = utc_now_iso()
    clean["data_version"] = data_version()

    clean = clean[
        [
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
    ].copy()

    return clean


def validate_clean_table(clean: pd.DataFrame) -> None:
    if clean is None or clean.empty:
        raise ValueError("daily_clean is empty")

    required_not_null = [
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
        "quality_flag",
        "ingest_time",
        "data_version",
    ]
    missing_cols = [c for c in required_not_null if c not in clean.columns]
    if missing_cols:
        raise ValueError(f"daily_clean missing required columns: {missing_cols}")

    null_counts = clean[required_not_null].isna().sum()
    bad_cols = null_counts[null_counts > 0]
    if len(bad_cols) > 0:
        raise ValueError(f"daily_clean has nulls in required columns: {bad_cols.to_dict()}")

    fail_rows = int((clean["quality_flag"] == "FAIL").sum())
    if fail_rows > 0:
        raise ValueError(f"daily_clean contains FAIL rows: {fail_rows}")

    if clean["trade_date"].duplicated().any():
        dup_count = int(clean["trade_date"].duplicated().sum())
        raise ValueError(f"daily_clean has duplicated trade_date rows: {dup_count}")

    if not clean["trade_date"].is_monotonic_increasing:
        raise ValueError("daily_clean trade_date is not sorted ascending")

    if (clean["symbol"] != SYMBOL).any():
        raise ValueError("daily_clean symbol contains invalid values")

    if (clean["market"] != MARKET).any():
        raise ValueError("daily_clean market contains invalid values")

    if (clean["asset_type"] != ASSET_TYPE).any():
        raise ValueError("daily_clean asset_type contains invalid values")


def main() -> None:
    ensure_dirs()

    rows_raw = 0
    rows_clean = 0
    fail_rows = 0

    try:
        df_raw = fetch_raw_from_tushare()
        if df_raw.empty:
            append_refresh_log(
                status="empty",
                symbol=SYMBOL,
                rows_raw=0,
                rows_clean=0,
                fail_rows=0,
                message="tushare.hk_daily returned empty dataframe",
            )
            raise ValueError("tushare.hk_daily returned empty dataframe")

        df_raw = prepare_raw_table(df_raw)
        rows_raw = len(df_raw)
        if rows_raw == 0:
            append_refresh_log(
                status="empty",
                symbol=SYMBOL,
                rows_raw=0,
                rows_clean=0,
                fail_rows=0,
                message="prepared raw table is empty",
            )
            raise ValueError("prepared raw table is empty")

        df_raw.to_csv(RAW_PATH, index=False, encoding="utf-8")

        clean = build_clean_table(df_raw)
        rows_clean = len(clean)
        fail_rows = int((clean["quality_flag"] == "FAIL").sum())

        validate_clean_table(clean)
        clean.to_csv(CLEAN_PATH, index=False, encoding="utf-8")

        append_refresh_log(
            status="success",
            symbol=SYMBOL,
            rows_raw=rows_raw,
            rows_clean=rows_clean,
            fail_rows=fail_rows,
            message="full refresh from listing date completed",
        )

        print(f"[OK] raw_rows={rows_raw} clean_rows={rows_clean} fail_rows={fail_rows}")
        print(f"[OK] RAW_PATH={RAW_PATH}")
        print(f"[OK] CLEAN_PATH={CLEAN_PATH}")

    except Exception as e:
        append_refresh_log(
            status="error",
            symbol=SYMBOL,
            rows_raw=rows_raw,
            rows_clean=rows_clean,
            fail_rows=fail_rows,
            message=str(e),
        )
        raise


if __name__ == "__main__":
    main()
