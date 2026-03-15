# JD-data

JD-data 是一个面向港股单票、市场基准与代理层的源数据仓库。

当前主线不是模型，不是预测，不是交易执行，而是：

**先把源数据仓建设成可训练、可回放、可审计、字段完整、结构稳定、可持续扩展的正式底座。**

当前首个核心标的是：

- 京东物流 `02618.HK`

当前已纳入的市场基准与底层辅助数据包括：

- 港股交易日历
- 恒生指数 `HSI`
- 恒生科技指数 `HKTECH`
- 恒生中国企业指数 `HSCEI`
- 京东集团代理层 `9618.HK`
- 美团代理层 `3690.HK`

---

## 当前主线目标

当前阶段唯一重点：

**先把源数据仓彻底收口，并把整仓刷新与整仓验收总线打通。**

这意味着当前优先解决的是：

- 数据是否拿到手
- raw / clean 是否分层
- clean 主表是否字段完整
- 交易日历是否落地
- 市场基准是否落地
- 代理层是否落地
- refresh_log 是否统一收口
- 自动刷新与自动验收是否稳定
- 文档与真实目录是否一致

当前阶段明确不做：

- 不切模型主线
- 不讨论预测精度
- 不讨论交易收益
- 不进入下游训练层
- 不在脏表上继续缝补
- 不把 raw 与 clean 混成一张表

---

## 当前仓库结构

```text
JD-data/
├── .github/
│   └── workflows/
│       ├── fetch_hk_daily.yml
│       ├── fetch_jd_group_daily.yml
│       ├── fetch_meituan_daily.yml
│       ├── fetch_hk_calendar.yml
│       ├── fetch_hsi_daily.yml
│       ├── fetch_hktech_daily.yml
│       ├── fetch_hscei_daily.yml
│       ├── validate_repository.yml
│       ├── refresh_all_and_validate.yml
│       └── update-jdlogistics-json.yml
├── calendar/
│   └── hk_trade_calendar.csv
├── data_raw/
│   ├── 02618.HK/
│   │   └── hk_daily_raw.csv
│   ├── 9618.HK/
│   │   └── hk_daily_raw.csv
│   ├── 3690.HK/
│   │   └── hk_daily_raw.csv
│   ├── HSI/
│   │   └── hsi_raw.csv
│   ├── HKTECH/
│   │   └── hktech_raw.csv
│   └── HSCEI/
│       └── hscei_raw.csv
├── data_clean/
│   ├── 02618.HK/
│   │   └── daily_clean.csv
│   ├── 9618.HK/
│   │   └── daily_clean.csv
│   ├── 3690.HK/
│   │   └── daily_clean.csv
│   ├── HSI/
│   │   └── hsi_clean.csv
│   ├── HKTECH/
│   │   └── hktech_clean.csv
│   └── HSCEI/
│       └── hscei_clean.csv
├── refresh_log/
│   └── refresh_log.csv
├── scripts/
│   ├── fetch_hk_daily.py
│   ├── fetch_jd_group_daily.py
│   ├── fetch_meituan_daily.py
│   ├── fetch_hk_calendar.py
│   ├── fetch_hsi_daily.py
│   ├── fetch_hktech_daily.py
│   ├── fetch_hscei_daily.py
│   └── validate_repository.py
├── jd-logistics-latest.json
└── README.md
