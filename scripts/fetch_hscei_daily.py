import math
import os
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

YF_TICKER = "^HSCE"
TS_CODE = "HSCEI"
SYMBOL = "HSCEI"
MARKET = "HK"
ASSET_TYPE = "index"
START_DATE = "2020-01-01"
DATA_VERSION_PREFIX = "D"

RAW_DIR = "data_raw/HSCEI"
CLEAN_DIR = "data_clean/HSCEI"
RAW_PATH = f"{RAW_DIR}/hscei_raw.csv"
CLEAN_PATH = f"{CLEAN_DIR}/hscei_clean.csv"
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
    return f"{DATA_VERSION_PREFIX}{datetime.now(timezone.utc).strftime('%Y%m%d')}.01"


def normalize_trade_date(series: pd.Series) -> pd.Series:
    s = pd.to_datetime(series, errors="coerce")
    return s.dt.strftime("%Y-%m-%d")


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
                "source": f"yfinance.{YF_TICKER}",
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


def fetch_raw_yfinance() -> pd.DataFrame:
    df = yf.download(
        YF_TICKER,
        start=START_DATE,
        auto_adjust=False,
        progress=False,
        interval="1d",
        actions=False,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.reset_index()

    # 兼容不同版本 yfinance 的列命名
    rename_map = {
        "Date": "trade_date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "vol",
    }
    df = df.rename(columns=rename_map)

    # MultiIndex 列兼容处理
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(x) for x in col if str(x) != ""]).strip("_")
            for col in df.columns
        ]

        multi_rename_map = {}
        for col in df.columns:
            lower = col.lower()
            if lower.startswith("date"):
                multi_rename_map[col] = "trade_date"
            elif lower.startswith("open"):
                multi_rename_map[col] = "open"
            elif lower.startswith("high"):
                multi_rename_map[col] = "high"
            elif lower.startswith("low"):
                multi_rename_map[col] = "low"
            elif lower.startswith("close"):
                multi_rename_map[col] = "close"
            elif lower.startswith("adj close"):
                multi_rename_map[col] = "adj_close"
            elif lower.startswith("volume"):
                multi_rename_map[col] = "vol"
        df = df.rename(columns=multi_rename_map)

    required_cols = ["trade_date", "open", "high", "low", "close"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"hscei yfinance raw missing required columns: {missing}")

    if "vol" not in df.columns:
        df["vol"] = pd.NA

    df["ts_code"] = TS_CODE
    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
    df["pre_close"] = pd.to_numeric(df["close"], errors="coerce").shift(1)
    df["change"] = pd.to_numeric(df["close"], errors="coerce") - pd.to_numeric(
        df["pre_close"], errors="coerce"
    )
    df["pct_chg"] = (
        pd.to_numeric(df["change"], errors="coerce")
        / pd.to_numeric(df["pre_close"], errors="coerce")
        * 100.0
    )
    df["swing"] = (
        (
            pd.to_numeric(df["high"], errors="coerce")
            - pd.to_numeric(df["low"], errors="coerce")
        )
        / pd.to_numeric(df["pre_close"], errors="coerce")
        * 100.0
    )
    df["amount"] = pd.NA

    df = df[
        [
            "ts_code",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "pre_close",
            "change",
            "pct_chg",
            "swing",
            "vol",
            "amount",
        ]
    ].copy()

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
                "swing",
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
    ]
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        raise ValueError(f"hscei raw missing required columns: {missing}")

    df = df_raw.copy()

    for col in ["change", "pct_chg", "swing", "vol", "amount"]:
        if col not in df.columns:
            df[col] = pd.NA

    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
    df = df.dropna(subset=["trade_date"]).copy()

    df = (
        df.sort_values("trade_date")
        .drop_duplicates(subset=["ts_code", "trade_date"], keep="last")
        .reset_index(drop=True)
    )

    # raw 层继续保留 YYYYMMDD 口径，尽量贴近现有指数 raw 风格
    df["trade_date"] = df["trade_date"].dt.strftime("%Y%m%d")

    return df


def build_clean_table(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    df = (
        df.sort_values("trade_date")
        .drop_duplicates(subset=["ts_code", "trade_date"], keep="last")
        .reset_index(drop=True)
    )

    clean = pd.DataFrame(index=df.index)
    clean["symbol"] = SYMBOL
    clean["market"] = MARKET
    clean["asset_type"] = ASSET_TYPE
    clean["trade_date"] = normalize_trade_date(df["trade_date"])
    clean["open"] = pd.to_numeric(df["open"], errors="coerce")
    clean["high"] = pd.to_numeric(df["high"], errors="coerce")
    clean["low"] = pd.to_numeric(df["low"], errors="coerce")
    clean["close"] = pd.to_numeric(df["close"], errors="coerce")
    clean["prev_close"] = pd.to_numeric(df["pre_close"], errors="coerce")

    # 指数口径下，Yahoo 常不给有效成交量/成交额；统一补零保持 schema 稳定
    clean["volume"] = pd.to_numeric(df["vol"], errors="coerce").fillna(0.0)
    clean["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

    clean["quality_flag"] = "PASS"

    # 历史首行没有 prev_close，不进入正式 clean 主表
    clean = clean[~clean["prev_close"].isna()].copy().reset_index(drop=True)

    clean["pct_change"] = clean["close"] / clean["prev_close"] - 1.0
    clean["ret_1d"] = clean["pct_change"]

    ratio = clean["close"] / clean["prev_close"]
    clean["log_ret_1d"] = ratio.map(
        lambda x: pd.NA if pd.isna(x) or x <= 0 else math.log(x)
    )

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
        raise ValueError("hscei_clean is empty")

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
        raise ValueError(f"hscei_clean missing required columns: {missing_cols}")

    null_counts = clean[required_not_null].isna().sum()
    bad_cols = null_counts[null_counts > 0]
    if len(bad_cols) > 0:
        raise ValueError(f"hscei_clean has nulls in required columns: {bad_cols.to_dict()}")

    fail_rows = int((clean["quality_flag"] == "FAIL").sum())
    if fail_rows > 0:
        raise ValueError(f"hscei_clean contains FAIL rows: {fail_rows}")

    if clean["trade_date"].duplicated().any():
        dup_count = int(clean["trade_date"].duplicated().sum())
        raise ValueError(f"hscei_clean has duplicated trade_date rows: {dup_count}")

    if not clean["trade_date"].is_monotonic_increasing:
        raise ValueError("hscei_clean trade_date is not sorted ascending")

    if (clean["symbol"] != SYMBOL).any():
        raise ValueError("hscei_clean symbol contains invalid values")

    if (clean["market"] != MARKET).any():
        raise ValueError("hscei_clean market contains invalid values")

    if (clean["asset_type"] != ASSET_TYPE).any():
        raise ValueError("hscei_clean asset_type contains invalid values")


def main() -> None:
    ensure_dirs()

    rows_raw = 0
    rows_clean = 0
    fail_rows = 0

    try:
        df_raw = fetch_raw_yfinance()

        if df_raw.empty:
            append_refresh_log(
                status="empty",
                symbol=SYMBOL,
                rows_raw=0,
                rows_clean=0,
                fail_rows=0,
                message="yfinance returned empty dataframe for HSCEI (^HSCE)",
            )
            raise ValueError("yfinance returned empty dataframe for HSCEI (^HSCE)")

        df_raw = prepare_raw_table(df_raw)
        rows_raw = len(df_raw)

        if rows_raw == 0:
            append_refresh_log(
                status="empty",
                symbol=SYMBOL,
                rows_raw=0,
                rows_clean=0,
                fail_rows=0,
                message="prepared raw table is empty for HSCEI",
            )
            raise ValueError("prepared raw table is empty for HSCEI")

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
            message="hscei full refresh completed via yfinance ^HSCE",
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
