# JD-data Schema V1

目标：构建 02618.HK 及未来任意单票的可训练、可回放、可审计的数据仓。

## 目录规划
- data_raw/02618.HK/*.csv
- data_clean/02618.HK/*.parquet
- refresh_log/refresh_log.csv
- schema/schema_v1.md
- latest/jd-logistics-latest.json

## 字段契约（schema_v1）
- symbol, market, asset_type
- trade_date
- open, high, low, close, prev_close
- volume, amount
- pct_change, ret_1d, log_ret_1d
- quality_flag, ingest_time, data_version

## 刷新规则
- 每日追加历史，不覆盖历史
- latest 作为最近一日快照
- 失败不得覆盖旧数据
