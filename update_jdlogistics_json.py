import os
import json
import datetime
from zoneinfo import ZoneInfo

import tushare as ts


TS_CODE = "02618.HK"
OUT_FILE = "jd-logistics-latest.json"
TZ = ZoneInfo("Asia/Shanghai")


def today_cn() -> datetime.date:
    """返回北京时间的日期（避免 GitHub Actions 默认 UTC 导致日期偏差）"""
    return datetime.datetime.now(TZ).date()


def fetch_data():
    # 从 GitHub Secrets 注入的环境变量读取 token
    token = os.getenv("HK_API_TOKEN")
    if not token:
        raise RuntimeError("Missing HK_API_TOKEN in environment")

    ts.set_token(token)
    pro = ts.pro_api()

    # 用北京时间计算日期区间
    end_date = today_cn().strftime("%Y%m%d")
    start_date = (today_cn() - datetime.timedelta(days=14)).strftime("%Y%m%d")

    df = pro.hk_daily(ts_code=TS_CODE, start_date=start_date, end_date=end_date)
    if df is None or df.empty:
        return None

    # 确保按交易日升序，取最后一行
    df = df.sort_values("trade_date", ascending=True)
    latest = df.iloc[-1]

    # 价格字段
    open_p = float(latest["open"])
    high_p = float(latest["high"])
    low_p = float(latest["low"])
    close_p = float(latest["close"])

    # 成交量/成交额字段：tushare 有时是 vol/amount，也可能缺失
    vol = latest.get("vol", 0) if hasattr(latest, "get") else latest["vol"]
    amount = latest.get("amount", None) if hasattr(latest, "get") else latest.get("amount")

    # vol 可能是字符串/浮点，统一转 int
    try:
        volume_i = int(float(vol)) if vol is not None else 0
    except Exception:
        volume_i = 0

    # amount 可能缺失，则用 close * volume 粗算一个（仅兜底）
    if amount is None:
        amount_f = round(close_p * volume_i, 2)
    else:
        try:
            amount_f = float(amount)
        except Exception:
            amount_f = round(close_p * volume_i, 2)

    # trade_date: YYYYMMDD -> YYYY-MM-DD
    trade_date = str(latest["trade_date"])
    date_fmt = f"{trade_date[0:4]}-{trade_date[4:6]}-{trade_date[6:8]}"

    data = {
        "symbol": TS_CODE,
        "date": date_fmt,
        "open": round(open_p, 2),
        "high": round(high_p, 2),
        "low": round(low_p, 2),
        "close": round(close_p, 2),
        "volume": volume_i,
        "amount": round(amount_f, 2),
    }
    return data


def main():
    try:
        data = fetch_data()
        if not data:
            print("No data from Tushare.")
            return

        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("Updated:", data)

    except Exception as e:
        print("ERROR:", repr(e))
        raise


if __name__ == "__main__":
    main()
