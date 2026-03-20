# fundamental_statement_items.csv 表结构 V1 + item_code 清单

## 一、文档定位

本文档用于定义京东物流企业基本面数据底座中的**标准财报明细层**。

该层不替代：

- `fundamental_quarterly.csv`（摘要层）
- `fundamental_features.csv`（下游消费层）

而是作为二者之间的**标准化中间层 / 明细层**存在。

其主要职责是：

1. 承接 PDF / 年报 / 中报 / 季报 / 财务附注中的高价值标准化财务明细项  
2. 将不同年份、不同披露粒度的财务项目，统一映射到稳定的 `item_code`  
3. 为后续 `fundamental_features.csv` 的派生特征计算提供可靠输入  
4. 避免把大量标准财报细项直接塞进 `fundamental_quarterly.csv`，破坏摘要层定位

---

## 二、表文件路径

建议路径：

`data_fundamental/02618.HK/fundamental_statement_items.csv`

---

## 三、表粒度与主键

### 1. 表粒度

一行表示：

**某一只股票，在某一财报披露周期下，某一个标准化财务项目（item_code）的一个取值。**

即：

`1 row = 1 symbol + 1 report_date + 1 period_type + 1 statement_type + 1 item_code`

### 2. 主键

首版主键定义为：

- `symbol`
- `report_date`
- `period_type`
- `statement_type`
- `item_code`

如后续需要记录同一项目多个来源版本，再考虑加入：

- `source_doc`
- `source_page`

当前 V1 暂不加入主键。

---

## 四、字段表结构 V1

| 字段名 | 类型建议 | 必填 | 含义 |
|---|---|---:|---|
| symbol | string | 是 | 股票代码，例如 `02618.HK` |
| report_date | string | 是 | 报告期日期，建议格式 `YYYY-MM-DD` |
| period_type | string | 是 | 报告周期类型：`quarter` / `semiannual` / `annual` |
| statement_type | string | 是 | 财务项目所属层：如 `income_statement` / `balance_sheet` / `cash_flow` / `revenue_breakdown` / `working_capital_note` / `operating_metrics_note` |
| item_code | string | 是 | 标准化项目代码，供程序稳定识别 |
| item_name_cn | string | 是 | 中文项目名 |
| item_name_en | string | 否 | 英文项目名 |
| value | float | 否 | 项目数值 |
| unit | string | 是 | 单位，V1 统一建议为 `million_rmb` |
| currency | string | 是 | 币种，V1 固定为 `RMB` |
| source_doc | string | 否 | 来源文件名或来源标识 |
| source_page | string | 否 | 来源页码，可写单页或页码范围 |
| source_section | string | 否 | 来源章节，如“合并资产负债表”“管理层讨论与分析”等 |
| is_derived | int | 是 | 是否为派生值：`0` 原始抽取，`1` 派生计算 |
| quality_flag | string | 是 | 质量标记：`RAW` / `REVIEW` / `CONFIRMED` / `ESTIMATED` |
| note | string | 否 | 备注，说明口径、估算方式、页码歧义等 |
| updated_at | string | 是 | 更新时间戳，建议 ISO 格式 |

---

## 五、字段口径与存储规则

### 1. 金额单位统一规则

V1 统一要求：

- `currency = RMB`
- `unit = million_rmb`

即所有金额类字段统一转为**人民币百万元**

例如：

- 217,146.986 百万元 → 存 `217146.986`
- 18,765.124 百万元 → 存 `18765.124`

### 2. 百分比字段处理规则

本表原则上以“明细金额项”为主，少量比例类项目如果进入本表，统一按**百分数数值**存储。

例如：

- 9.1% → 存 `9.1`

不使用 `0.091` 这种小数形式，避免与其他表口径不一致。

### 3. 缺失规则

若原始文件未披露，不补造、不前填、不后填。直接留空，并在：

- `quality_flag`
- `note`

中注明原因。

### 4. 派生项规则

`is_derived = 1` 的项目允许存在，但仅限少数高价值、中间层明确需要的项目。  
首版建议以**原始抽取项为主**，避免在该层塞入过多衍生计算。

---

## 六、statement_type 枚举定义 V1

### 1. income_statement
利润表层项目

### 2. balance_sheet
资产负债表层项目

### 3. cash_flow
现金流量表层项目

### 4. revenue_breakdown
收入拆分口径项目

### 5. working_capital_note
营运资本、应收应付账龄、供应链金融等附注项目

### 6. operating_metrics_note
经营指标附注项目，如客户数、仓网、员工等

---

## 七、item_code 设计原则

### 原则 1：英文蛇形命名
统一使用小写英文 + 下划线，例如：

- `trade_receivables`
- `free_cash_inflow`

### 原则 2：同一 item_code 口径固定
一旦定义，不允许跨年份随意改变含义。

### 原则 3：摘要层已有字段，不等于明细层不能再有
若某项既出现在摘要层，也属于标准报表核心项目，可在本表保留，后续由消费层决定优先级。

### 原则 4：优先保留可派生价值高的字段
优先收录能直接支持：

- 偿债能力
- 现金质量
- 营运效率
- 收入结构
- 财务质量

的项目。

---

## 八、item_code 清单 V1

以下为首版建议纳入的 `item_code` 清单。

---

### A. 利润表层（income_statement）

| item_code | 中文名 |
|---|---|
| revenue | 收入 |
| cost_of_revenue | 营业成本 |
| gross_profit | 毛利 |
| operating_profit | 经营利润 |
| profit_before_tax | 税前利润 |
| net_profit | 净利润 |
| net_profit_attributable_to_owners | 归母净利润 |
| non_ifrs_profit | 非 IFRS 净利润 |
| non_ifrs_ebitda | 非 IFRS EBITDA |

---

### B. 资产负债表层（balance_sheet）

| item_code | 中文名 |
|---|---|
| current_assets | 流动资产 |
| non_current_assets | 非流动资产 |
| total_assets | 总资产 |
| current_liabilities | 流动负债 |
| non_current_liabilities | 非流动负债 |
| total_liabilities | 总负债 |
| total_equity | 总权益 |
| cash_and_cash_equivalents | 现金及现金等价物 |
| restricted_cash | 受限现金 |
| term_deposits | 定期存款 |
| trade_receivables | 应收账款 |
| contract_assets | 合同资产 |
| prepayments_other_receivables_other_assets | 预付款项、其他应收款及其他资产 |
| inventories | 存货 |
| property_and_equipment | 物业及设备 |
| right_of_use_assets | 使用权资产 |
| investment_properties | 投资性房地产 |
| goodwill | 商誉 |
| other_intangible_assets | 其他无形资产 |
| interests_in_associates | 联营企业权益 |
| interests_in_joint_ventures | 合营企业权益 |
| financial_assets_at_fvtpl | 以公允价值计量且其变动计入当期损益的金融资产 |
| equity_instruments_at_fvoci | 以公允价值计量且其变动计入其他综合收益的权益工具 |
| deferred_tax_assets | 递延所得税资产 |
| trade_payables | 应付账款 |
| contract_liabilities | 合同负债 |
| accrued_expenses_and_other_payables | 应计费用及其他应付款项 |
| advances_from_customers | 客户预付款项 |
| borrowings | 有息借款 |
| lease_liabilities | 租赁负债 |
| deferred_tax_liabilities | 递延所得税负债 |
| income_tax_payables | 应交所得税 |

---

### C. 现金流层（cash_flow）

| item_code | 中文名 |
|---|---|
| operating_cash_flow | 经营活动现金流量净额 |
| investing_cash_flow | 投资活动现金流量净额 |
| financing_cash_flow | 融资活动现金流量净额 |
| net_change_in_cash_and_cash_equivalents | 现金及现金等价物净变动 |
| free_cash_inflow | 自由现金流入 |
| capex_net | 净资本开支 |
| depreciation_and_amortization | 折旧与摊销 |
| payments_relating_to_leases | 租赁相关支付 |

---

### D. 收入拆分层（revenue_breakdown）

| item_code | 中文名 |
|---|---|
| revenue_jd_group | 来自京东集团收入 |
| revenue_external | 来自外部客户收入 |
| revenue_integrated_supply_chain | 一体化供应链客户收入 |
| revenue_other_customers | 其他客户收入 |
| revenue_external_integrated_supply_chain | 外部一体化供应链客户收入 |
| revenue_over_time | 按时段确认收入 |
| revenue_point_in_time | 按时点确认收入 |
| external_isc_customer_count | 外部一体化供应链客户数 |
| external_isc_arpc | 外部一体化供应链客户 ARPC |

---

### E. 营运资本与附注层（working_capital_note）

| item_code | 中文名 |
|---|---|
| receivables_within_3m | 3个月内应收账款 |
| receivables_3_to_6m | 3至6个月应收账款 |
| receivables_6_to_12m | 6至12个月应收账款 |
| receivables_over_12m | 12个月以上应收账款 |
| receivables_loss_allowance | 应收账款减值准备 |
| payables_within_3m | 3个月内应付账款 |
| payables_3_to_6m | 3至6个月应付账款 |
| payables_6_to_12m | 6至12个月应付账款 |
| payables_over_12m | 12个月以上应付账款 |
| supplier_finance_arrangements | 供应商融资安排规模 |

---

### F. 经营指标附注层（operating_metrics_note）

| item_code | 中文名 |
|---|---|
| warehouse_count | 仓库数量 |
| warehouse_gfa | 仓储总面积 |
| overseas_warehouse_count | 海外仓数量 |
| overseas_warehouse_area | 海外仓面积 |
| sorting_center_count | 分拣中心数量 |
| delivery_station_count | 配送站及网点数量 |
| bulky_item_warehouse_count | 大件仓数量 |
| cold_chain_warehouse_count | 冷链仓数量 |
| pharma_warehouse_count | 医药仓数量 |
| employee_count | 员工数量 |
| inhouse_delivery_personnel_count | 自有配送及操作人员数量 |
| overseas_country_coverage_count | 海外覆盖国家和地区数量 |

---

## 九、首版必须优先落地的核心 item_code

虽然上面是完整 V1 清单，但首版落地时，不需要一次性全抽。  
建议优先抽取下列高价值项目，先形成能支撑下游消费层的最小闭环。

### 第一优先级（必须先落）

#### 资产负债表核心
- `cash_and_cash_equivalents`
- `restricted_cash`
- `term_deposits`
- `trade_receivables`
- `inventories`
- `trade_payables`
- `borrowings`
- `lease_liabilities`
- `current_assets`
- `current_liabilities`
- `total_assets`
- `total_liabilities`
- `total_equity`

#### 现金流核心
- `operating_cash_flow`
- `investing_cash_flow`
- `financing_cash_flow`
- `free_cash_inflow`
- `capex_net`

#### 收入拆分核心
- `revenue_jd_group`
- `revenue_external`
- `revenue_integrated_supply_chain`
- `revenue_external_integrated_supply_chain`
- `external_isc_customer_count`
- `external_isc_arpc`

#### 质量附注核心
- `receivables_over_12m`
- `payables_over_12m`
- `supplier_finance_arrangements`

---

## 十、与其他表的关系

### 1. 与 `fundamental_quarterly.csv` 的关系

`fundamental_quarterly.csv` 继续承担：

- 摘要层
- 管理层口径
- 文本解释入口

`fundamental_statement_items.csv` 负责：

- 标准报表细项
- 明细附注项
- 口径更稳的财务结构项

二者不是替代关系，而是并行分层关系。

### 2. 与 `fundamental_features.csv` 的关系

`fundamental_features.csv` 由以下两表合成：

- `fundamental_quarterly.csv`
- `fundamental_statement_items.csv`

其中：

- 摘要层字段直接保留或标签化
- 明细层字段用于派生特征计算

---

## 十一、V1 暂不纳入范围

为避免首版过度膨胀，以下内容暂不纳入 `fundamental_statement_items.csv`：

1. 大段管理层文本原文  
2. 公司治理说明  
3. 股本变动细表  
4. 募资用途详表  
5. 审计意见原文  
6. 纯叙述性战略展望段落

这些内容如后续需要，可进入：

- `extracted_text/*.md`
- `management_commentary.csv`
- `event_notes.csv`

而不是塞入本表。

---

## 十二、一句话结论

`fundamental_statement_items.csv` 的定位是：**承接标准财报明细和高价值附注项的长表层**；它不取代 `fundamental_quarterly.csv`，而是与之并行，共同为 `fundamental_features.csv` 提供稳定、可计算、可扩展的企业基本面输入底座。
