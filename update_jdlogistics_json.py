import os
import json
import datetime
import tushare as ts


def fetch_data():
    # 从 GitHub Secrets 注入的环境变量读取 token
    token = os.getenv("HK_API_TOKEN")
    if not token:
        raise RuntimeError("Missing HK_API_TOKEN in environment")

    ts.set_token(token)
    pro = ts.pro_api()

    ts_code = "02618.HK"

    end_date = datetime.date.today().strftime("%Y%m%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%Y%m%d")

    df = pro.hk_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

    if df is None or df.empty:
        return None

    df = df.sort_values("trade_date")
    latest = df.iloc[-1]

    open_p = float(latest["open"])
    high_p = float(latest["high"])
    low_p = float(latest["low"])
    close_p = float(latest["close"])

    vol = latest.get("vol", 0)
    amount = latest.get("amount", None)

    volume_i = int(float(vol))

    if amount is None:
        amount_f = round(close_p * volume_i, 2)
    else:
        amount_f = float(amount)

    trade_date = str(latest["trade_date"])
    date_fmt = f"{trade_date[0:4]}-{trade_date[4:6]}-{trade_date[6:8]}"

    data = {
        "symbol": ts_code,
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

        with open("jd-logistics-latest.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("Updated:", data)

    except Exception as e:
        print("ERROR:", repr(e))
        raise


if __name__ == "__main__":
    main()
