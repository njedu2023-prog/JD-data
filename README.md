````md
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
````

---

## 已完成的数据表与职责

### 1. 京东物流单票主表

当前已落地：

* `data_raw/02618.HK/hk_daily_raw.csv`
* `data_clean/02618.HK/daily_clean.csv`
* `jd-logistics-latest.json`

职责说明：

* raw 层保留上游原始日线口径
* clean 层输出正式标准主表
* latest 由 clean 导出，不再直接依赖半成品口径

---

### 2. 京东集团代理层主表

当前已落地：

* `data_raw/9618.HK/hk_daily_raw.csv`
* `data_clean/9618.HK/daily_clean.csv`

职责说明：

* 提供京东生态主站代理层
* 为后续京东物流与京东集团联动、相对强弱、生态环境识别提供正式底层表
* 当前已完成单线 raw / clean 接入，并已纳入仓库级正式成员体系

---

### 3. 美团代理层主表

当前已落地：

* `data_raw/3690.HK/hk_daily_raw.csv`
* `data_clean/3690.HK/daily_clean.csv`

职责说明：

* 提供本地生活、即时零售、配送履约代理层
* 为后续京东物流与本地生活平台、即时配送环境、平台竞争格局联动分析提供正式底层表
* 当前已完成单线 raw / clean 接入，并已纳入仓库级正式成员体系

---

### 4. 港股交易日历表

当前已落地：

* `calendar/hk_trade_calendar.csv`

职责说明：

* 提供港股交易日 / 非交易日底层时间基准
* 为后续 T+1、缺失诊断、标签对齐提供统一时间轴

---

### 5. 恒生指数 HSI

当前已落地：

* `data_raw/HSI/hsi_raw.csv`
* `data_clean/HSI/hsi_clean.csv`

职责说明：

* 提供港股主市场基准
* 用于后续相对收益、联动、风险环境判断

---

### 6. 恒生科技指数 HKTECH

当前已落地：

* `data_raw/HKTECH/hktech_raw.csv`
* `data_clean/HKTECH/hktech_clean.csv`

职责说明：

* 提供港股科技成长风格基准
* 用于后续风格联动与成长环境判断

---

### 7. 恒生中国企业指数 HSCEI

当前已落地：

* `data_raw/HSCEI/hscei_raw.csv`
* `data_clean/HSCEI/hscei_clean.csv`

职责说明：

* 提供中资港股 / H 股风险基准
* 用于后续区分“港股整体大盘环境”与“中资港股环境”
* 当前通过 `yfinance ^HSCE` 接入仓库，作为正式市场基准成员

---

### 8. refresh_log 统一刷新日志表

当前已落地：

* `refresh_log/refresh_log.csv`

统一字段为：

* `refresh_time`
* `source`
* `symbol`
* `rows_raw`
* `rows_clean`
* `rows_fail`
* `status`
* `message`

职责说明：

* 记录每次刷新是否成功
* 记录各 symbol 的 raw / clean 行数
* 为整仓级运行追踪和问题定位提供留痕

---

## 当前仓库已经具备的结构能力

截至当前阶段，JD-data 已不再是“几条脚本能分别跑”的状态，而是已经具备以下能力：

### 1. 分层能力

* raw 层保存上游原始口径
* clean 层输出正式标准主表
* latest 从 clean 层导出
* raw 与 clean 长期分离

### 2. 多表能力

当前已不再只有一张单票表，而是已有：

* 京东物流单票主表
* 京东集团代理层主表
* 美团代理层主表
* 交易日历表
* 港股市场基准表
* 港股科技风格表
* 中资港股风险基准表
* 刷新日志表

### 3. 总线能力

当前已具备：

* 分线抓取 workflow
* 仓库级统一验收 workflow
* 一键整仓刷新 + 总验收 workflow

这意味着后续开发已经可以站在更正式的仓库级底座上继续推进，而不再停留在零散脚本级别。

---

## 当前已跑通的自动化能力

### 1. 仓库级统一验收

当前已新增并跑通：

* `.github/workflows/validate_repository.yml`
* `scripts/validate_repository.py`

当前统一检查范围包括：

* 关键文件是否存在
* clean 主表是否非空
* 身份字段是否正确
* 日期是否重复
* 日期是否升序
* `quality_flag` 是否全 PASS
* `refresh_log` 是否结构正确、关键 symbol 是否齐全

当前已覆盖的关键 symbol 包括：

* `02618.HK`
* `9618.HK`
* `3690.HK`
* `HK_CALENDAR`
* `HSI`
* `HKTECH`
* `HSCEI`

### 2. 一键整仓刷新 + 总验收总线

当前已新增并跑通：

* `.github/workflows/refresh_all_and_validate.yml`

当前总线已覆盖：

* 京东物流日线刷新
* 京东集团日线刷新
* 美团日线刷新
* 港股交易日历刷新
* 恒生指数刷新
* 恒生科技指数刷新
* 恒生中国企业指数刷新
* 最后统一执行仓库级验证

---

## 当前阶段正式结论

当前 JD-data 已从：

**“脚本可跑”**

升级到：

**“整仓可刷新、整仓可验收、整仓可维护”的正式底座阶段。**

并且当前已经从单票底座进一步升级到：

**“京东物流 + 京东集团代理层 + 美团代理层 + 港股市场基准”的正式底层联动底座阶段。**

---

## 当前阶段仍然没做的事

虽然底座已经明显成型，但当前还没有进入模型主线。

仍未进入的内容包括：

* 特征层
* 标签层
* 训练层
* 回测层
* 预测层

原因不是技术不能做，而是：

**当前策略仍然是先把未来真正需要的源数据底座尽量收齐，再进入下游。**

---

## 下一阶段最合理主线

下一阶段不回头修旧问题，继续补齐未来系统真正需要的底层表。

优先级建议如下：

### 第一优先级：继续补市场联动 / 基准 / 代理层

优先继续纳入：

* 阿里巴巴 `9988.HK`
* 更多未来特征层真正会消费的市场联动输入

### 第二优先级：继续强化仓库级治理

继续完善：

* workflow 输出与调试信息
* 仓库级校验范围
* schema / contract 文档
* refresh_log 进一步标准化

### 第三优先级：底座稳定后再进入下游

只有在底座继续稳定后，才进入：

* 特征层
* 标签层
* 训练层
* 回测层

---

## 当前阶段禁止跑偏项

下一轮开发中，继续避免以下错误：

* 不要切去模型层
* 不要讨论预测准不准
* 不要在脏表上追加修补
* 不要把 raw 和 clean 再混回一张表
* 不要让文档再和真实仓库状态脱节

---

## 当前阶段一句话总结

当前 JD-data 的真正主线不是“抓到一点数据”，而是：

**把京东物流、京东集团、美团及其相关市场基准数据，建设成一套可训练、可回放、可审计、字段完整、结构稳定、可整仓刷新、可整仓验收的正式源数据仓底座。**

```
```
