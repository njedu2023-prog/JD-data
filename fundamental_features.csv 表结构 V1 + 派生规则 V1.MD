# fundamental_features.csv 表结构 V1 + 派生规则 V1

## 一、文档定位

本文档用于定义京东物流企业基本面数据底座中的**下游消费层**。

该层不等于：

- `fundamental_quarterly.csv`（摘要层）
- `fundamental_statement_items.csv`（标准财报明细层）

而是建立在上述两层之上的**模型消费层 / 规则消费层 / 分析消费层**。

其核心职责是：

1. 将摘要层与标准财报明细层合并为一张真正可消费的宽表  
2. 对原始字段进行口径统一、缺失约束、派生计算  
3. 输出可供模型、规则、排序、解释模块直接使用的企业基本面特征  
4. 保持主键稳定、字段意义稳定、跨期可比性稳定

---

## 二、表文件路径

建议路径：

`data_fundamental/02618.HK/fundamental_features.csv`

---

## 三、表粒度与主键

### 1. 表粒度

一行表示：

**某一只股票，在某一财报 / 经营披露周期下，经过摘要层 + 明细层合成后的企业基本面消费特征快照。**

即：

`1 row = 1 symbol + 1 report_date + 1 period_type`

### 2. 主键

首版主键定义为：

- `symbol`
- `report_date`
- `period_type`

---

## 四、上游输入来源

`fundamental_features.csv` 的上游输入固定为两张表：

### 1. 摘要层

`data_fundamental/02618.HK/fundamental_quarterly.csv`

作用：

- 提供管理层摘要口径
- 提供经营规模指标
- 提供部分核心财务摘要
- 提供文本解释入口

### 2. 标准财报明细层

`data_fundamental/02618.HK/fundamental_statement_items.csv`

作用：

- 提供标准报表明细项
- 提供收入拆分项
- 提供应收 / 应付账龄项
- 提供营运质量相关项目

---

## 五、表字段结构 V1

本表采用**宽表**结构，因为其定位就是“下游直接消费”。

字段分为六组：

1. 主键字段  
2. 直接保留字段  
3. 明细层补充字段  
4. 派生特征字段  
5. 标签 / 解释字段  
6. 元数据字段  

---

## 六、字段清单 V1

### A. 主键字段

| 字段名 | 类型建议 | 必填 | 含义 |
|---|---|---:|---|
| symbol | string | 是 | 股票代码，例如 `02618.HK` |
| report_date | string | 是 | 报告期日期，格式 `YYYY-MM-DD` |
| period_type | string | 是 | 周期类型：`quarter` / `semiannual` / `annual` |

---

### B. 直接保留字段（来自 fundamental_quarterly.csv）

| 字段名 | 类型建议 | 必填 | 含义 |
|---|---|---:|---|
| revenue | float | 否 | 收入 |
| gross_profit | float | 否 | 毛利 |
| gross_margin | float | 否 | 毛利率，百分数口径 |
| net_profit | float | 否 | 净利润 |
| non_ifrs_profit | float | 否 | 非 IFRS 净利润 |
| non_ifrs_ebitda | float | 否 | 非 IFRS EBITDA |
| total_assets | float | 否 | 总资产 |
| total_liabilities | float | 否 | 总负债 |
| total_equity | float | 否 | 总权益 |
| operating_cash_flow | float | 否 | 经营活动现金流量净额 |
| external_customer_revenue | float | 否 | 外部客户收入（摘要层原口径） |
| integrated_supply_chain_revenue | float | 否 | 一体化供应链客户收入 |
| warehouse_count | float | 否 | 仓库数量 |
| warehouse_gfa | float | 否 | 仓储总面积 |
| overseas_warehouse_area | float | 否 | 海外仓面积 |
| employee_count | float | 否 | 员工数量 |

说明：

- 该组字段保留摘要层已有价值
- 但在消费层不代表绝对权威
- 与明细层冲突时，应遵守后文的优先级规则

---

### C. 明细层补充字段（来自 fundamental_statement_items.csv）

| 字段名 | 类型建议 | 必填 | 含义 |
|---|---|---:|---|
| cash_and_cash_equivalents | float | 否 | 现金及现金等价物 |
| restricted_cash | float | 否 | 受限现金 |
| term_deposits | float | 否 | 定期存款 |
| trade_receivables | float | 否 | 应收账款 |
| contract_assets | float | 否 | 合同资产 |
| inventories | float | 否 | 存货 |
| trade_payables | float | 否 | 应付账款 |
| borrowings | float | 否 | 有息借款 |
| lease_liabilities | float | 否 | 租赁负债 |
| current_assets | float | 否 | 流动资产 |
| current_liabilities | float | 否 | 流动负债 |
| investing_cash_flow | float | 否 | 投资活动现金流量净额 |
| financing_cash_flow | float | 否 | 融资活动现金流量净额 |
| free_cash_inflow | float | 否 | 自由现金流入 |
| capex_net | float | 否 | 净资本开支 |
| revenue_jd_group | float | 否 | 来自京东集团收入 |
| revenue_external | float | 否 | 来自外部客户收入（标准拆分口径） |
| revenue_integrated_supply_chain | float | 否 | 一体化供应链客户收入（标准拆分口径） |
| revenue_external_integrated_supply_chain | float | 否 | 外部一体化供应链客户收入 |
| revenue_other_customers | float | 否 | 其他客户收入 |
| external_isc_customer_count | float | 否 | 外部一体化供应链客户数 |
| external_isc_arpc | float | 否 | 外部一体化供应链客户 ARPC |
| receivables_within_3m | float | 否 | 3个月内应收账款 |
| receivables_3_to_6m | float | 否 | 3至6个月应收账款 |
| receivables_6_to_12m | float | 否 | 6至12个月应收账款 |
| receivables_over_12m | float | 否 | 12个月以上应收账款 |
| receivables_loss_allowance | float | 否 | 应收账款减值准备 |
| payables_within_3m | float | 否 | 3个月内应付账款 |
| payables_3_to_6m | float | 否 | 3至6个月应付账款 |
| payables_6_to_12m | float | 否 | 6至12个月应付账款 |
| payables_over_12m | float | 否 | 12个月以上应付账款 |
| supplier_finance_arrangements | float | 否 | 供应商融资安排规模 |

---

### D. 派生特征字段（本表核心）

| 字段名 | 类型建议 | 必填 | 含义 |
|---|---|---:|---|
| net_cash | float | 否 | 净现金 |
| working_capital | float | 否 | 营运资本 |
| debt_to_asset_ratio | float | 否 | 资产负债率，百分数口径 |
| lease_burden_ratio | float | 否 | 租赁负担比率，百分数口径 |
| receivables_ratio | float | 否 | 应收占收入比，百分数口径 |
| contract_assets_ratio | float | 否 | 合同资产占收入比，百分数口径 |
| inventory_ratio | float | 否 | 存货占收入比，百分数口径 |
| payables_ratio | float | 否 | 应付占成本或收入比，V1 先按收入口径 |
| supplier_finance_ratio | float | 否 | 供应商融资依赖比率，百分数口径 |
| receivables_over_6m_ratio | float | 否 | 6个月以上应收占比，百分数口径 |
| receivables_over_12m_ratio | float | 否 | 12个月以上应收占比，百分数口径 |
| payables_over_12m_ratio | float | 否 | 12个月以上应付占比，百分数口径 |
| receivables_loss_allowance_ratio | float | 否 | 应收减值准备占应收比，百分数口径 |
| free_cash_flow_margin | float | 否 | 自由现金流率，百分数口径 |
| capex_intensity | float | 否 | 资本开支强度，百分数口径 |
| operating_cash_flow_margin | float | 否 | 经营现金流率，百分数口径 |
| cash_conversion_quality_score | float | 否 | 现金转化质量分值 |
| external_revenue_ratio | float | 否 | 外部客户收入占比，百分数口径 |
| jd_group_revenue_ratio | float | 否 | 京东集团收入占比，百分数口径 |
| integrated_supply_chain_revenue_ratio | float | 否 | 一体化供应链收入占比，百分数口径 |
| external_isc_revenue_ratio | float | 否 | 外部一体化供应链收入占比，百分数口径 |
| external_isc_customer_yoy | float | 否 | 外部一体化供应链客户数同比，百分数口径 |
| external_isc_arpc_yoy | float | 否 | 外部一体化供应链 ARPC 同比，百分数口径 |

---

### E. 标签 / 解释字段

| 字段名 | 类型建议 | 必填 | 含义 |
|---|---|---:|---|
| working_capital_pressure_tag | string | 否 | 营运资本压力标签 |
| receivables_quality_tag | string | 否 | 应收质量标签 |
| supplier_finance_usage_tag | string | 否 | 供应商融资使用强度标签 |
| cash_flow_quality_tag | string | 否 | 现金流质量标签 |
| customer_structure_tag | string | 否 | 客户结构标签 |
| globalization_phase_tag | string | 否 | 全球化阶段标签 |
| network_expansion_tag | string | 否 | 仓网扩张标签 |
| feature_note | string | 否 | 说明字段，记录重要解释或口径提醒 |

---

### F. 元数据字段

| 字段名 | 类型建议 | 必填 | 含义 |
|---|---|---:|---|
| data_version | string | 是 | 版本号，建议 V1 |
| quality_flag | string | 是 | 行级质量标记：`RAW` / `REVIEW` / `CONFIRMED` / `PARTIAL` |
| source_summary | string | 否 | 来源摘要，如 quarterly+statement_items |
| updated_at | string | 是 | 更新时间戳，建议 ISO 格式 |

---

## 七、字段口径统一规则 V1

### 规则 1：金额统一规则

所有金额类字段统一为：

- `currency = RMB`
- `unit = million_rmb`

即全部统一为**人民币百万元**

---

### 规则 2：百分比统一规则

本表所有比例字段统一按**百分数数值**存储。

例如：

- 9.1% → 存 `9.1`
- 35.6% → 存 `35.6`

不使用 `0.091` 或 `0.356`

---

### 规则 3：摘要层与明细层冲突时的优先级

若摘要层字段与明细层字段出现同名或同义冲突，V1 规则为：

- **用于派生计算：优先使用明细层**
- **用于解释展示：保留摘要层**
- 如口径无法判定，保留摘要值，但整行 `quality_flag = REVIEW`

---

### 规则 4：Q1 / Q3 缺失规则

若 Q1 / Q3 未披露完整资产负债表或现金流量表：

- 不前填
- 不后填
- 不人工伪造

直接留空，并在：

- `quality_flag`
- `feature_note`

中注明“披露口径缺失”

---

### 规则 5：文本字段不直接进入数值特征

摘要层文本项如：

- `major_event_note`
- `management_guidance`
- `quality_note`

不直接进入数值字段，但允许在后续映射为标签字段。

---

### 规则 6：external_customer_revenue 优先级规则

`external_customer_revenue` 在摘要层存在口径混用风险。

因此 V1 规定：

- 若 `revenue_external` 存在，则优先使用 `revenue_external`
- `external_customer_revenue` 仅保留作参考与解释
- 若二者冲突明显，则整行 `quality_flag = REVIEW`

---

## 八、合成规则 V1

### 1. 合成逻辑

`fundamental_features.csv` 的生成逻辑为：

`fundamental_quarterly.csv`
+
`fundamental_statement_items.csv`（按 item_code 透视）
=
`fundamental_features.csv`

### 2. 连接主键

连接键固定为：

- `symbol`
- `report_date`
- `period_type`

### 3. statement_items 宽表化规则

在构建时，将 `fundamental_statement_items.csv` 按主键透视为临时宽表：

- `item_code` → 列名
- `value` → 数值

然后与摘要层左连接。

---

## 九、派生规则 V1

以下为首版核心派生规则。

---

### 1. 净现金

`net_cash = cash_and_cash_equivalents + restricted_cash + term_deposits - borrowings`

说明：

- 若 `term_deposits` 缺失，则按 0 处理
- 若 `borrowings` 缺失，不强算，留空更稳

---

### 2. 营运资本

`working_capital = current_assets - current_liabilities`

---

### 3. 资产负债率

`debt_to_asset_ratio = total_liabilities / total_assets * 100`

前提：

- `total_assets > 0`

---

### 4. 租赁负担比率

`lease_burden_ratio = lease_liabilities / total_liabilities * 100`

前提：

- `total_liabilities > 0`

---

### 5. 应收占收入比

`receivables_ratio = trade_receivables / revenue * 100`

前提：

- `revenue > 0`

---

### 6. 合同资产占收入比

`contract_assets_ratio = contract_assets / revenue * 100`

前提：

- `revenue > 0`

---

### 7. 存货占收入比

`inventory_ratio = inventories / revenue * 100`

前提：

- `revenue > 0`

---

### 8. 应付占收入比

V1 为简化口径，先定义：

`payables_ratio = trade_payables / revenue * 100`

说明：

- 后续若 `cost_of_revenue` 稳定落库，可升级为按成本口径

---

### 9. 供应商融资依赖比率

`supplier_finance_ratio = supplier_finance_arrangements / trade_payables * 100`

前提：

- `trade_payables > 0`

---

### 10. 6个月以上应收占比

`receivables_over_6m_ratio = (receivables_6_to_12m + receivables_over_12m) / trade_receivables * 100`

前提：

- `trade_receivables > 0`

---

### 11. 12个月以上应收占比

`receivables_over_12m_ratio = receivables_over_12m / trade_receivables * 100`

前提：

- `trade_receivables > 0`

---

### 12. 12个月以上应付占比

`payables_over_12m_ratio = payables_over_12m / trade_payables * 100`

前提：

- `trade_payables > 0`

---

### 13. 应收减值准备占比

`receivables_loss_allowance_ratio = receivables_loss_allowance / trade_receivables * 100`

前提：

- `trade_receivables > 0`

---

### 14. 自由现金流率

`free_cash_flow_margin = free_cash_inflow / revenue * 100`

前提：

- `revenue > 0`

---

### 15. 资本开支强度

`capex_intensity = capex_net / revenue * 100`

前提：

- `revenue > 0`

---

### 16. 经营现金流率

`operating_cash_flow_margin = operating_cash_flow / revenue * 100`

前提：

- `revenue > 0`

---

### 17. 现金转化质量分值

V1 先定义为一个简化分值：

`cash_conversion_quality_score = operating_cash_flow_margin - receivables_ratio`

说明：

- 该分值不是财务会计指标
- 只是消费层便于排序和筛选的工程指标
- 后续可升级

---

### 18. 外部客户收入占比

若 `revenue_external` 存在：

`external_revenue_ratio = revenue_external / revenue * 100`

否则回退：

`external_revenue_ratio = external_customer_revenue / revenue * 100`

---

### 19. 京东集团收入占比

`jd_group_revenue_ratio = revenue_jd_group / revenue * 100`

前提：

- `revenue > 0`

---

### 20. 一体化供应链收入占比

优先使用明细层：

`integrated_supply_chain_revenue_ratio = revenue_integrated_supply_chain / revenue * 100`

若缺失，则可回退摘要层：

`integrated_supply_chain_revenue_ratio = integrated_supply_chain_revenue / revenue * 100`

---

### 21. 外部一体化供应链收入占比

`external_isc_revenue_ratio = revenue_external_integrated_supply_chain / revenue * 100`

前提：

- `revenue > 0`

---

### 22. 外部一体化供应链客户数同比

`external_isc_customer_yoy = (current_external_isc_customer_count - prev_year_same_period_external_isc_customer_count) / prev_year_same_period_external_isc_customer_count * 100`

前提：

- 存在上年同期
- 上年同期值 > 0

---

### 23. 外部一体化供应链 ARPC 同比

`external_isc_arpc_yoy = (current_external_isc_arpc - prev_year_same_period_external_isc_arpc) / prev_year_same_period_external_isc_arpc * 100`

前提：

- 存在上年同期
- 上年同期值 > 0

---

## 十、标签规则 V1

### 1. 营运资本压力标签

规则建议：

- `working_capital < 0` → `HIGH_PRESSURE`
- `working_capital >= 0` 且 `receivables_ratio > 20` → `WATCH`
- 其他 → `NORMAL`

---

### 2. 应收质量标签

规则建议：

- `receivables_over_12m_ratio >= 10` → `WEAK`
- `receivables_over_12m_ratio >= 5 且 < 10` → `WATCH`
- `< 5` → `GOOD`

---

### 3. 供应商融资使用强度标签

规则建议：

- `supplier_finance_ratio >= 20` → `HIGH`
- `supplier_finance_ratio >= 10 且 < 20` → `MEDIUM`
- `< 10` → `LOW`

---

### 4. 现金流质量标签

规则建议：

- `free_cash_flow_margin < 0` 且 `non_ifrs_profit > 0` → `PROFIT_CASH_DIVERGENCE`
- `operating_cash_flow_margin > 0` 且 `free_cash_flow_margin > 0` → `GOOD`
- 其他 → `REVIEW`

---

### 5. 客户结构标签

规则建议：

- `external_revenue_ratio >= 60` → `EXTERNAL_DOMINANT`
- `jd_group_revenue_ratio >= 40` → `JD_GROUP_DEPENDENT`
- 其他 → `BALANCED`

---

### 6. 全球化阶段标签

规则建议（首版可弱规则）：

- `overseas_warehouse_area` 明显持续增长 → `GLOBALIZING`
- 无数据或变化不显著 → `DOMESTIC_CORE`

---

### 7. 仓网扩张标签

规则建议：

- `warehouse_count` 同比明显增长 → `EXPANDING`
- 基本稳定 → `STABLE`
- 无法判断 → `REVIEW`

---

## 十一、质量标记规则 V1

### 行级 `quality_flag` 建议规则

- `CONFIRMED`：核心字段完整、口径清晰、可计算
- `PARTIAL`：能计算部分特征，但缺若干关键字段
- `REVIEW`：存在明显口径歧义或摘要 / 明细冲突
- `RAW`：仅完成首版拼接，尚未人工校验

---

## 十二、首版必须优先落地的核心字段

为了尽快形成下游可消费表，V1 首批必须至少保证以下字段能产出：

### 1. 直接保留字段
- `revenue`
- `gross_profit`
- `net_profit`
- `non_ifrs_profit`
- `operating_cash_flow`

### 2. 明细补充字段
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
- `free_cash_inflow`
- `capex_net`
- `revenue_external`
- `revenue_jd_group`
- `revenue_external_integrated_supply_chain`
- `external_isc_customer_count`
- `supplier_finance_arrangements`

### 3. 核心派生字段
- `net_cash`
- `working_capital`
- `debt_to_asset_ratio`
- `receivables_ratio`
- `free_cash_flow_margin`
- `external_revenue_ratio`

---

## 十三、验收标准 V1

`fundamental_features.csv` 首版完成后，应至少满足以下条件：

1. 主键无重复  
2. 表已真实生成，不是空表  
3. 至少一批报告期已完成摘要层 + 明细层合成  
4. 核心派生字段已非空：  
   - `net_cash`
   - `working_capital`
   - `debt_to_asset_ratio`
   - `receivables_ratio`
   - `free_cash_flow_margin`
5. Q1 / Q3 缺失未被伪造填充  
6. `quality_flag` 能真实反映数据质量  
7. `fundamental_quarterly.csv` 的摘要层定位未被破坏  

---

## 十四、一句话结论

`fundamental_features.csv` 的定位是：**在摘要层与标准财报明细层之上，生成一张真正可被模型、规则和分析模块直接消费的企业基本面宽表**；其本质不是简单拼接，而是经过口径统一、派生计算和标签化处理后的消费层产物。
