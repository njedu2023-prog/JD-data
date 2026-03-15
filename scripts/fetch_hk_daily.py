import os
import json
from datetime import datetime, timezone

import pandas as pd
import tushare as ts


TS_CODE = "02618.HK"
MARKET = "HK"
ASSET_TYPE = "equity"

START_DATE = "20210517"  # 京东物流上市后起始日，当前阶段统一全量拉取
DATA_VERSION_PREFIX = "D"

RAW_DIR = "data_raw/02618.HK"
CLEAN_DIR = "data_clean/02618.HK"

RAW_PATH = f"{RAW_DIR}/hk_daily_raw.csv"
CLEAN_PATH = f"{CLEAN_DIR}/daily_clean.csv"
LATEST_PATH = "jd-logistics-latest.json"
REFRESH_LOG_PATH = "refresh_log/refresh_log.csv"


def ensure_parent_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLEAN_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(REFRESH_LOG_PATH), exist_ok=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def data_version() -> str:
    return f"{DATA_VERSION_PREFIX}{datetime.now(timezone.utc).strftime('%Y%m%d')}.01"


def normalize_trade_date(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    # 统一输出 YYYY-MM-DD
    s = pd.to_datetime(s, format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d")
    return s


def build_clean_table(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    # 排序 + 去重
    df = df.sort_values("trade_date").drop_duplicates(subset=["ts_code", "trade_date"], keep="last").reset_index(drop=True)

    # 标准字段
    clean = pd.DataFrame()
    clean["symbol"] = TS_CODE
    clean["market"] = MARKET
    clean["asset_type"] = ASSET_TYPE
    clean["trade_date"] = normalize_trade_date(df["trade_date"])

    clean["open"] = pd.to_numeric(df["open"], errors="coerce")
    clean["high"] = pd.to_numeric(df["high"], errors="coerce")
    clean["low"] = pd.to_numeric(df["low"], errors="coerce")
    clean["close"] = pd.to_numeric(df["close"], errors="coerce")
    clean["prev_close"] = pd.to_numeric(df["pre_close"], errors="coerce")
    clean["volume"] = pd.to_numeric(df["vol"], errors="coerce")
    clean["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # 衍生字段
    clean["pct_change"] = clean["close"] / clean["prev_close"] - 1.0
    clean["ret_1d"] = clean["pct_change"]
    clean["log_ret_1d"] = (clean["close"] / clean["prev_close"]).map(
        lambda x: pd.NA if pd.isna(x) or x <= 0 else float(pd.Series([x]).map(lambda v: __import__("math").log(v))[0])
    )

    # 质量标记
    clean["quality_flag"] = "PASS"
    invalid_mask = (
        clean["open"].isna()
        | clean["high"].isna()
        | clean["low"].isna()
        | clean["close"].isna()
        | clean["prev_close"].isna()
        | (clean["high"] < clean["low"])
        | (clean["volume"] < 0)
        | (clean["amount"] < 0)
    )
    clean.loc[invalid_mask, "quality_flag"] = "FAIL"

    now_iso = utc_now_iso()
    dv = data_version()
    clean["ingest_time"] = now_iso
    clean["data_version"] = dv

    return clean


def write_latest_json(clean: pd.DataFrame) -> None:
    latest_row = clean.sort_values("trade_date").iloc[-1]

    latest_json = {
        "symbol": latest_row["symbol"],
        "date": latest_row["trade_date"],
        "open": None if pd.isna(latest_row["open"]) else float(latest_row["open"]),
        "high": None if pd.isna(latest_row["high"]) else float(latest_row["high"]),
        "low": None if pd.isna(latest_row["low"]) else float(latest_row["low"]),
        "close": None if pd.isna(latest_row["close"]) else float(latest_row["close"]),
        "volume": None if pd.isna(latest_row["volume"]) else float(latest_row["volume"]),
        "amount": None if pd.isna(latest_row["amount"]) else float(latest_row["amount"]),
        "quality_flag": latest_row["quality_flag"],
        "data_version": latest_row["data_version"],
    }

    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        json.dump(latest_json, f, ensure_ascii=False, indent=2)


def append_refresh_log(status: str, rows_raw: int, rows_clean: int, fail_rows: int, message: str) -> None:
    exists = os.path.exists(REFRESH_LOG_PATH)
    log_df = pd.DataFrame(
        [
            {
                "refresh_time": utc_now_iso(),
                "source": "tushare.hk_daily",
                "symbol": TS_CODE,
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


def main() -> None:
    ensure_parent_dirs()

    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if not token:
        raise SystemExit("TUSHARE_TOKEN not set")

    ts.set_token(token)
    pro = ts.pro_api()

    # 当前阶段：每天全量拉取上市以来历史，确保能纠偏、补齐、统一
    df_raw = pro.hk_daily(
        ts_code=TS_CODE,
        start_date=START_DATE,
        fields="ts_code,trade_date,open,high,low,close,pre_close,vol,amount",
    )

    if df_raw is None or len(df_raw) == 0:
        append_refresh_log(
            status="empty",
            rows_raw=0,
            rows_clean=0,
            fail_rows=0,
            message="hk_daily returned empty dataframe",
        )
        raise SystemExit(0)

    # 原始层：保留 Tushare 原始字段
    df_raw = df_raw.sort_values("trade_date").drop_duplicates(subset=["ts_code", "trade_date"], keep="last").reset_index(drop=True)
    df_raw.to_csv(RAW_PATH, index=False, encoding="utf-8")

    # 清洗层：输出正式训练主表
    clean = build_clean_table(df_raw)
    clean.to_csv(CLEAN_PATH, index=False, encoding="utf-8")

    # latest
    write_latest_json(clean)

    fail_rows = int((clean["quality_flag"] == "FAIL").sum())
    append_refresh_log(
        status="success",
        rows_raw=len(df_raw),
        rows_clean=len(clean),
        fail_rows=fail_rows,
        message="full refresh from listing date completed",
    )

    print(f"[OK] raw_rows={len(df_raw)} clean_rows={len(clean)} fail_rows={fail_rows}")
    print(f"[OK] RAW_PATH={RAW_PATH}")
    print(f"[OK] CLEAN_PATH={CLEAN_PATH}")
    print(f"[OK] LATEST_PATH={LATEST_PATH}")


if __name__ == "__main__":
    main()
