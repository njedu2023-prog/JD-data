import os, json
from datetime import datetime
import pandas as pd
import tushare as ts

TS_CODE="02618.HK"
HISTORY="data_raw/02618.HK/history.csv"
LATEST="jd-logistics-latest.json"
LOG="refresh_log/refresh_log.csv"
START="20210517"

ts.set_token(os.environ["TUSHARE_TOKEN"])
pro=ts.pro_api()

if os.path.exists(HISTORY):
    df_old=pd.read_csv(HISTORY,dtype={"trade_date":str})
    start=df_old["trade_date"].max()
else:
    df_old=pd.DataFrame()
    start=START

df=pro.hk_daily(ts_code=TS_CODE,start_date=start,
                fields="ts_code,trade_date,open,high,low,close,pre_close,vol,amount")
if df is None or len(df)==0:
    raise SystemExit(0)

df=df.sort_values("trade_date").drop_duplicates(["ts_code","trade_date"],keep="last")
df_all=df
if len(df_old):
    df_all=pd.concat([df_old,df_all],ignore_index=True)
df_all=df_all.drop_duplicates(["ts_code","trade_date"],keep="last")
df_all=df_all.sort_values("trade_date")
added=len(df_all)-len(df_old)
df_all.to_csv(HISTORY,index=False)

row=df_all.iloc[-1]
latest={"symbol":TS_CODE,
        "date":f"{row.trade_date[:4]}-{row.trade_date[4:6]}-{row.trade_date[6:]}",
        "open":float(row.open),"high":float(row.high),"low":float(row.low),
        "close":float(row.close),"volume":int(row.vol),"amount":float(row.amount)}
json.dump(latest,open(LATEST,"w"),ensure_ascii=False)

ts_iso=datetime.utcnow().isoformat(timespec="seconds")+"Z"
log_line=f"{ts_iso},hk_daily,{TS_CODE},{added},0,success,"
with open(LOG,"a") as f:
    f.write(log_line+"\n")
print("added",added)
