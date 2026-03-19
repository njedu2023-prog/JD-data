# fundamental_source_mapping_v1

## 一、文档定位

本文件用于定义：

`data_fundamental/02618.HK/fundamental_quarterly.csv`

各字段在 V1 阶段的来源映射、入库方式与人工参与边界。

它不是字段字典的重复版，而是字段字典的**执行版补充**。  
核心作用是回答三个问题：

1. 哪些字段可直接结构化抓取
2. 哪些字段可半自动抽取后入库
3. 哪些字段必须人工核验或人工录入

后续你喂我 Excel、财报、公告、整理文档时，统一按本文件执行。

---

## 二、三类字段定义

### A 类：可直接结构化抓取
定义：
- 来源中通常已有明确字段名或明确表格位置
- 数值口径相对稳定
- 可直接进入主表
- 原则上优先自动化

典型来源：
- 港交所业绩公告正文表格
- 年报 / 中报 / 季报中的财务报表
- 已结构化 Excel
- 固定格式运营指标表

---

### B 类：可半自动抽取
定义：
- 来源中通常有对应信息，但不总是固定表格字段
- 需要人工做一次映射判断或摘要整理
- 可以进入主表，但要保留 `quality_note` 或 note 字段说明

典型来源：
- 管理层讨论与分析
- 财报正文中的经营描述
- 公告正文段落
- 业绩会摘要
- 你手工整理的 Excel / Word / Markdown

---

### C 类：需人工核验 / 人工录入
定义：
- 口径容易变
- 来源位置不稳定
- 含主观判断或跨段归纳
- 不能直接无脑自动入库

典型来源：
- 重大事件判断
- 管理层指引变化判断
- 质量备注
- 经营质量、利润质量、现金流质量等解释性字段
- 需要跨多处信息综合判断的字段

---

## 三、字段来源映射总表

---

# A. 主键与身份字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| symbol | A | 固定值 | 固定写入 | 京东物流固定为 `02618.HK` |
| company_name_zh | A | 固定值 | 固定写入 | 固定为 `京东物流` |
| company_name_en | A | 固定值 | 固定写入 | 固定为 `JD Logistics, Inc.` |
| report_date | A | 财报公告 | 直接提取 | 关键主键字段 |
| announce_date | A | 港交所公告 | 直接提取 | 关键主键字段 |
| period_type | A | 规则判断 | 规则写入 | `quarter / semiannual / annual` |
| fiscal_year | A | 财报公告 | 直接提取 | 可由 report_date 校验 |
| fiscal_period | A | 财报公告 / 规则判断 | 提取或规则写入 | 例如 `Q1 / H1 / Q3 / FY` |
| currency | A | 财报公告 | 直接提取 | 建议统一规范 |
| unit | A | 系统规则 | 规则写入 | 建议默认 `million_rmb` |

---

# B. 收入与增长字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| revenue | A | 财报正文 / 财务报表 | 直接提取 | 核心字段 |
| revenue_yoy | A | 财报正文 | 直接提取 | 若未给出可后算 |
| revenue_qoq | A | 主表历史期数 | 公式计算 | 依赖历史数据 |
| core_business_revenue | B | 财报分部披露 | 半自动映射 | 非每期必有 |
| supply_chain_revenue | A | 财报正文 | 直接提取 | 核心字段 |
| external_customer_revenue | A/B | 财报正文 / 管理层讨论 | 优先直接提取，缺失时人工映射 | 口径需核对 |
| other_revenue | B | 财报附注 | 半自动映射 | 非每期重点字段 |
| revenue_growth_quality_note | C | 管理层讨论 / 人工总结 | 人工填写 | 解释增长来源和质量 |

---

# C. 利润与盈利能力字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| gross_profit | A | 财报正文 | 直接提取 | 未披露时可反推 |
| gross_margin | A | 财报正文 / 公式计算 | 优先提取，缺失时计算 | |
| operating_profit | A/B | 财报正文 / 报表 | 直接提取或映射 | 港股有时口径不完全统一 |
| operating_margin | A | 公式计算 | 系统计算 | |
| net_profit | A | 财报正文 | 直接提取 | 核心字段 |
| net_profit_yoy | A | 财报正文 | 直接提取 | |
| net_profit_qoq | A | 主表历史期数 | 公式计算 | |
| net_margin | A | 公式计算 | 系统计算 | |
| adj_net_profit | A | 财报正文 | 直接提取 | 非IFRS 常见字段 |
| adj_net_profit_yoy | A/B | 财报正文 / 历史期数 | 提取或计算 | |
| ebitda | B | 财报正文 | 半自动提取 | 非每期必有 |
| ebitda_margin | A | 公式计算 | 系统计算 | |
| adj_ebitda | A | 财报正文 | 直接提取 | 京东物流常见关键字段 |
| adj_ebitda_margin | A | 财报正文 / 公式计算 | 提取或计算 | |
| profit_quality_note | C | 人工总结 | 人工填写 | 解释利润改善或恶化原因 |

---

# D. 现金流与资本开支字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| operating_cash_flow | A | 现金流量表 | 直接提取 | 核心字段 |
| investing_cash_flow | A | 现金流量表 | 直接提取 | |
| financing_cash_flow | A | 现金流量表 | 直接提取 | |
| free_cash_flow | A | `operating_cash_flow - capex` | 系统计算 | |
| capex | B | 财报附注 / 现金流量表 | 半自动提取 | 常需看附注或口径解释 |
| cash_and_equivalents | A | 资产负债表 | 直接提取 | 核心字段 |
| restricted_cash | B | 财报附注 | 半自动提取 | 非每期重点披露 |
| cash_flow_quality_note | C | 人工总结 | 人工填写 | 解释经营现金流与利润背离等情况 |

---

# E. 资产负债结构字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| total_assets | A | 资产负债表 | 直接提取 | 核心字段 |
| total_liabilities | A | 资产负债表 | 直接提取 | 核心字段 |
| total_equity | A | 资产负债表 | 直接提取 | 核心字段 |
| current_assets | A | 资产负债表 | 直接提取 | |
| current_liabilities | A | 资产负债表 | 直接提取 | |
| interest_bearing_debt | B/C | 财报附注 / 负债科目整理 | 半自动整理后人工核验 | 容易口径不统一 |
| net_cash | A | 公式计算 | 系统计算 | |
| debt_to_asset_ratio | A | 公式计算 | 系统计算 | |
| balance_sheet_quality_note | C | 人工总结 | 人工填写 | 解释杠杆、负债结构、资金安全性 |

---

# F. 运营效率字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| inventory | A/B | 资产负债表 | 直接提取或映射 | 视披露形式而定 |
| inventory_turnover_days | B | 财报正文 / 运营指标 | 半自动提取 | |
| accounts_receivable | A | 资产负债表 | 直接提取 | |
| accounts_receivable_turnover_days | B | 财报正文 / 运营指标 | 半自动提取 | |
| accounts_payable | A | 资产负债表 | 直接提取 | |
| accounts_payable_turnover_days | B | 财报正文 / 运营指标 | 半自动提取 | |
| working_capital | A | 公式计算 | 系统计算 | |
| working_capital_change | A | 历史期数计算 | 系统计算 | |
| efficiency_note | C | 人工总结 | 人工填写 | 解释效率变化与经营影响 |

---

# G. 业务结构与经营规模字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| integrated_supply_chain_clients | A | 财报正文 | 直接提取 | 核心经营字段 |
| warehouse_count | A | 财报正文 | 直接提取 | 核心经营字段 |
| warehouse_area | A | 财报正文 | 直接提取 | 核心经营字段 |
| cloud_warehouse_count | A/B | 财报正文 | 直接提取或映射 | |
| county_coverage_ratio | B | 财报正文 / 运营披露 | 半自动提取 | 有时文字披露而非标准表格 |
| delivery_network_note | C | 人工总结 | 人工填写 | 描述配送网络变化 |
| fulfillment_scale_note | C | 人工总结 | 人工填写 | 描述履约规模与结构变化 |

---

# H. 市场与估值辅助字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| market_cap | B | 行情数据 | 半自动写入 | 需明确公告日附近取值规则 |
| ps_ttm | B | 行情估值侧 | 半自动写入 | 可后续再自动化 |
| pe_ttm | B | 行情估值侧 | 半自动写入 | 亏损期可能为空 |
| pb | B | 行情估值侧 | 半自动写入 | |
| ev_to_ebitda | B/C | 行情 + 财报字段 | 半自动计算后核验 | 口径易漂移 |
| valuation_note | C | 人工总结 | 人工填写 | 用于解释估值高低背景 |

---

# I. 事件与管理层备注字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| major_event_flag | C | 公告 / 人工判断 | 人工写入 | 是否存在重大事件 |
| major_event_type | C | 公告 / 人工判断 | 人工写入 | 并购、组织调整、业务扩张等 |
| major_event_note | C | 公告正文 / 人工总结 | 人工填写 | |
| management_guidance | B/C | 管理层讨论 / 业绩会 / 公告 | 半自动抽取后人工润色 | 核心解释字段 |
| guidance_change_flag | C | 当前期与上期对比 | 人工判断 / 规则辅助 | 是否发生指引变化 |
| guidance_note | C | 人工总结 | 人工填写 | 指引变化说明 |

---

# J. 数据治理字段

| 字段名 | 分类 | 推荐来源 | 入库方式 | 备注 |
|---|---|---|---|---|
| source_type | A | 源文件属性 | 规则写入 | 必填 |
| source_url | A/B | 源链接 | 直接写入 | 没有链接可空，但后续建议补齐 |
| source_title | A/B | 源公告标题 / 文件标题 | 直接提取或写入 | |
| ingest_time | A | 系统时间 | 系统写入 | 必填 |
| data_version | A | 系统规则 | 规则写入 | 例如 `v1` |
| quality_flag | A/B | 校验流程 | 系统写入 | `PASS / REVIEW / ERROR` |
| quality_note | B/C | 校验流程 / 人工补充 | 写入说明 | 缺失字段必须说明原因 |
| is_manual_verified | A | 人工流程 | 规则写入 | 0/1 |
| verified_by | C | 人工填写 | 人工写入 | |
| verified_time | C | 人工填写 / 系统时间 | 人工或系统写入 | |

---

## 四、V1 执行原则

### 1. 能直接结构化的，优先结构化
优先入主表，不要偷懒写进 note。

### 2. 不能稳定结构化的，允许先进 note
但必须写清楚原因，不能模糊处理。

### 3. 涉及主观判断的，必须人工核验
尤其是：
- 重大事件
- 指引变化
- 质量类备注
- 利润质量 / 现金流质量 / 经营质量解释

### 4. 公式字段尽量系统算
不要每次人工手填：
- gross_margin
- operating_margin
- net_margin
- free_cash_flow
- net_cash
- debt_to_asset_ratio
- revenue_qoq
- net_profit_qoq
- working_capital
- working_capital_change

---

## 五、后续喂数执行流程

后续你给我 Excel、财报、公告、Markdown 文档时，统一按下面流程：

### 第一步：识别源文件类型
分为：
- 港交所公告
- 年报 / 中报 / 季报
- Excel 手工表
- Markdown / Word 整理稿
- 其它辅助文件

### 第二步：按本映射表拆字段
拆成：
- A 类直接入库
- B 类半自动入库
- C 类待人工核验

### 第三步：更新主表
按：
- `symbol`
- `report_date`
- `period_type`

对齐后执行：
- insert
- update
- upsert

### 第四步：写入 ingest_log.csv
记录：
- 本次使用了什么文件
- 更新了哪些周期
- 影响了几行
- 状态是否成功
- 是否需要复核

---

## 六、V1 当前结论

在 V1 阶段：

- **A 类字段** 是优先自动化对象
- **B 类字段** 是过渡阶段重点
- **C 类字段** 必须允许人工参与

也就是说，这一版不是追求“全自动”，而是追求：

**结构稳定、口径清晰、可持续追加、后续可升级自动化。**

---

## 七、下一步开发任务

本文件完成后，下一步最合理的不是继续写说明文档，而是进入：

### `scripts/ingest_fundamental_stub.py`

先做一个**最小可用导入脚本骨架**，让后面你喂文件时，不是纯手工改 CSV，而是进入“半自动导入”模式。
