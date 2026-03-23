# model_features 字段分层设计 V1

## 1. 文档目的

本文件用于把 `fundamental_features.csv` 正式过渡为后续模型消费层 `model_features.csv` 的字段分层规则。

当前阶段目标不是直接训练模型，而是先解决以下问题：

1. 哪些字段可以直接进入模型  
2. 哪些字段需要标准化、缩放、滞后或改造后才能进入模型  
3. 哪些字段只适合进入解释层，不适合直接训练  
4. 哪些字段当前暂不纳入模型  
5. T+1、未来 1 个月、未来 6 个月三个预测周期分别应优先消费哪些字段

本文件是后续 `model_features.csv 表结构 V1`、`scripts/build_model_features.py`、标签设计与训练脚本的上游口径锚点。

---

## 2. 当前输入表范围

当前直接输入来源为：

- `data_fundamental/02618.HK/fundamental_features.csv`

当前判断：

- annual 主干字段已基本收口，可作为慢变量核心来源
- semiannual / quarter 记录已可作为补充层使用
- 但 semiannual / quarter 仍存在 `PARTIAL` / `RAW` 情况，因此不能无差别整表入模
- 当前应采用“字段分层 + 周期分层 + 口径分层”的消费方式，而不是整表平推

---

## 3. 总体分层原则

后续 `model_features` 的字段分为四层：

### A层：直接入模字段
定义：口径较稳定、含义明确、时间穿越风险低、跨期可比性较强，可直接进入模型。  
适用：annual 为主，必要时允许 semiannual 补充。

### B层：经处理后入模字段
定义：字段本身有价值，但需要做标准化、比例化、对数化、同比/环比化、滞后处理或缺失保护后再入模。  
适用：多数财务规模变量、经营结构变量、账龄变量、客户结构变量。

### C层：解释层字段
定义：业务解释价值高，但当前不适合作为首版模型直接输入。  
适用：文本标签、阶段标签、注释字段、source 字段、人工说明字段。

### D层：暂不入模字段
定义：当前缺失率高、口径仍不稳定、跨期连续性不足，或存在明显未来函数/噪声问题。  
适用：暂不稳定字段、填补痕迹过重字段、样本太少的字段。

---

## 4. 字段分层规则

## 4.1 A层：直接入模字段

以下字段可直接作为首版模型输入候选：

### 4.1.1 资本结构 / 资产负债慢变量
- `total_assets`
- `total_liabilities`
- `total_equity`
- `current_assets`
- `current_liabilities`
- `borrowings`
- `lease_liabilities`
- `net_cash`
- `working_capital`
- `debt_to_asset_ratio`
- `lease_burden_ratio`

### 4.1.2 现金流质量慢变量
- `operating_cash_flow`
- `investing_cash_flow`
- `financing_cash_flow`
- `free_cash_inflow`
- `free_cash_flow_margin`
- `capex_net`
- `capex_intensity`
- `operating_cash_flow_margin`
- `cash_conversion_quality_score`

### 4.1.3 收益质量 / 经营效率慢变量
- `revenue`
- `gross_profit`
- `gross_margin`
- `net_profit`
- `trade_receivables`
- `contract_assets`
- `inventories`
- `trade_payables`
- `receivables_ratio`
- `contract_assets_ratio`
- `inventory_ratio`
- `payables_ratio`

### 4.1.4 客户结构与收入结构慢变量
- `revenue_jd_group`
- `revenue_external`
- `revenue_integrated_supply_chain`
- `revenue_external_integrated_supply_chain`
- `revenue_other_customers`
- `external_revenue_ratio`
- `jd_group_revenue_ratio`
- `integrated_supply_chain_revenue_ratio`
- `external_isc_revenue_ratio`

### 4.1.5 运营规模慢变量
- `warehouse_count`
- `external_isc_customer_count`
- `external_isc_arpc`

说明：
A层字段要求优先取“最近可见”的已披露值，不允许未来函数穿越。

---

## 4.2 B层：经处理后入模字段

以下字段不能直接裸用，但处理后价值较高：

### 4.2.1 规模型字段：建议做对数化 / 比例化
- `cash_and_cash_equivalents`
- `restricted_cash`
- `term_deposits`
- `trade_receivables`
- `contract_assets`
- `inventories`
- `trade_payables`
- `borrowings`
- `lease_liabilities`
- `current_assets`
- `current_liabilities`

建议处理：
- 对大数值做 `log1p`
- 或除以 `revenue` / `total_assets` / `total_liabilities` 转成比例变量
- 保留原值与比例值二选一，避免强共线

### 4.2.2 账龄类字段：建议做占比化
- `receivables_within_3m`
- `receivables_3_to_6m`
- `receivables_6_to_12m`
- `receivables_over_12m`
- `receivables_loss_allowance`
- `payables_within_3m`
- `payables_3_to_6m`
- `payables_6_to_12m`
- `payables_over_12m`
- `supplier_finance_arrangements`

建议处理：
- 全部转成占总应收 / 总应付 / 总负债的比例
- 首版优先保留已经生成好的：
  - `receivables_over_6m_ratio`
  - `receivables_over_12m_ratio`
  - `payables_over_12m_ratio`
  - `receivables_loss_allowance_ratio`
  - `supplier_finance_ratio`

### 4.2.3 变化率字段：建议做同比化
- `external_isc_customer_count`
- `external_isc_arpc`

建议处理：
- 优先使用已生成：
  - `external_isc_customer_yoy`
  - `external_isc_arpc_yoy`
- 如原值与同比值同时保留，模型侧需防共线

### 4.2.4 半年报 / 季报补充字段
semiannual / quarter 中可见但不稳定的字段，必须满足以下条件才允许纳入：
1. 当前 `quality_flag` 不为明显低质量
2. 该字段在近年连续可见
3. 采用 as-of 口径，不穿越未来披露日期
4. 缺失值有明确填补或保留空值策略

---

## 4.3 C层：解释层字段

以下字段首版建议不直接入模，仅保留给解释系统、报告系统或审计系统：

- `working_capital_pressure_tag`
- `receivables_quality_tag`
- `supplier_finance_usage_tag`
- `cash_flow_quality_tag`
- `customer_structure_tag`
- `globalization_phase_tag`
- `network_expansion_tag`
- `feature_note`
- `mapped_item_count`
- `mapped_item_nonnull_count`
- `item_quality_score_sum`
- `item_quality_score_avg`
- `mapped_item_codes`
- `item_source_docs`
- `data_version`
- `quality_flag`
- `source_summary`
- `updated_at`

说明：
这些字段对“人类解释”很有用，但对首版模型训练容易引入噪音、泄漏或口径不稳定。

---

## 4.4 D层：暂不入模字段

以下字段当前暂不建议纳入首版模型：

- `non_ifrs_profit`
- `non_ifrs_ebitda`
- `warehouse_gfa`
- `overseas_warehouse_area`
- `employee_count`

暂不纳入原因如下：

### 4.4.1 连续性不足
部分字段跨期缺失明显，难以形成长期稳定样本。

### 4.4.2 披露口径不完全稳定
部分字段可能只在特定年报或特定阶段披露，不适合直接做统一训练输入。

### 4.4.3 首版边际价值不高
相比现金流、收入结构、资产负债压力、客户结构，这些字段首版带来的增量不一定最高。

说明：
这些字段不是永久废弃，而是暂列“二期候选层”。

---

## 5. 按预测周期分层

## 5.1 T+1 预测建议字段

T+1 不应过度依赖低频基本面。  
基本面在 T+1 中主要承担“状态锚定”和“结构过滤”作用。

### T+1 优先使用
- `gross_margin`
- `net_profit`
- `operating_cash_flow_margin`
- `free_cash_flow_margin`
- `cash_conversion_quality_score`
- `debt_to_asset_ratio`
- `lease_burden_ratio`
- `receivables_ratio`
- `supplier_finance_ratio`
- `external_revenue_ratio`
- `jd_group_revenue_ratio`
- `integrated_supply_chain_revenue_ratio`
- `external_isc_revenue_ratio`
- `external_isc_customer_yoy`
- `external_isc_arpc_yoy`

### T+1 中基本面定位
- 不做短线方向主驱动
- 主要做风险过滤、结构识别、状态加权

---

## 5.2 未来 1 个月预测建议字段

1 个月周期可以适度提高基本面权重。

### 1个月优先使用
- A层全部核心慢变量
- B层中经比例化、同比化后的客户结构字段
- 账龄质量字段
- 现金流质量字段
- 收入结构字段

### 1个月中基本面定位
- 与市场环境、行业代理层、价格趋势共同决定中短周期表现
- 重点关注经营质量改善、客户结构改善、现金流改善

---

## 5.3 未来 6 个月预测建议字段

6 个月周期应明显提高基本面权重，特别是 annual 与 semiannual 的经营结构信息。

### 6个月优先使用
- `revenue`
- `gross_profit`
- `gross_margin`
- `net_profit`
- `total_assets`
- `total_liabilities`
- `total_equity`
- `operating_cash_flow`
- `free_cash_inflow`
- `net_cash`
- `working_capital`
- `debt_to_asset_ratio`
- `receivables_ratio`
- `supplier_finance_ratio`
- `external_revenue_ratio`
- `jd_group_revenue_ratio`
- `integrated_supply_chain_revenue_ratio`
- `external_isc_revenue_ratio`
- `external_isc_customer_yoy`
- `external_isc_arpc_yoy`
- `warehouse_count`

### 6个月中基本面定位
- 作为核心驱动层之一
- 重点刻画企业经营趋势、资金质量、客户结构和成长质量

---

## 6. 首版 as-of 消费原则

后续 `model_features.csv` 必须遵守以下规则：

### 6.1 不允许未来函数
任意交易日 `asof_date` 只能消费在该日期之前已经披露的财报数据。

### 6.2 annual 优先
如果可见 annual，则优先使用最近 annual。  
若最近 annual 尚未披露，可退而使用最近 semiannual。  
quarter 仅作为补充，不得强行替代 annual 主干。

### 6.3 缺失宁可空，不乱填
对于关键附注层字段：
- 首版允许缺失
- 禁止无依据人工脑补
- 允许有限规则派生，但必须留痕

### 6.4 解释字段与训练字段分开
所有标签类、说明类、来源类字段，不能混入首版训练主表。

---

## 7. 首版字段入模建议总表

### 7.1 直接入模
- 资产负债结构
- 现金流质量
- 收入结构
- 客户结构
- 经营效率
- 慢变量规模

### 7.2 经处理后入模
- 账龄类
- 大数额绝对值变量
- 部分半年报 / 季报补充项
- 同比 / 比例 / 对数型变量

### 7.3 仅解释层
- 各类 tag
- feature_note
- source / quality / 映射统计
- 版本与来源说明

### 7.4 暂不入模
- 非 IFRS 类未连续字段
- 披露不稳定运营字段
- 当前缺失明显字段

---

## 8. 当前阶段结论

截至当前 V1 阶段：

1. `fundamental_features.csv` 的 annual 主干已可作为正式慢变量来源  
2. 首版模型应采用“annual 为主、semiannual 为辅、quarter 慎用”的消费策略  
3. 当前最合理路径不是直接写训练脚本，而是先定义 `model_features.csv` 正式表结构  
4. 本文件是后续 `model_features.csv 表结构 V1` 的上游口径依据

---

## 9. 下一步动作

本文件完成后，下一步立即进入：

**《model_features.csv 表结构 V1.MD》**

该文件将明确：

- 主键
- 时间锚点
- as-of 规则
- 正式字段清单
- 字段类型
- 字段单位
- 缺失策略
- 训练层与解释层分列方案
