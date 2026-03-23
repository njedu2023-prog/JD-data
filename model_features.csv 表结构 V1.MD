# model_features.csv 表结构 V1

## 1. 文档目的

本文件用于定义 `model_features.csv` 的首版正式表结构。

`model_features.csv` 的职责不是保存原始财报，也不是保存解释性注释，而是：

- 作为后续模型训练、验证、推理的正式消费表
- 作为 `fundamental_features.csv`、市场日线表、指数表、代理层表向模型层过渡的统一中间层
- 作为未来标签表、训练样本表、预测样本表的上游标准输入表

因此，本表必须满足以下要求：

1. 字段含义稳定  
2. 不允许未来函数  
3. 可按 `asof_date` 追溯  
4. 可支持 T+1、未来 1 个月、未来 6 个月 三类预测周期  
5. 训练字段与解释字段严格分离

---

## 2. 表定位

## 2.1 输入来源

首版 `model_features.csv` 计划消费以下上游表：

### 基本面层
- `data_fundamental/02618.HK/fundamental_features.csv`

### 个股行情层
- `data_clean/02618.HK/daily_clean.csv`

### 市场基准层
- `data_clean/HSI/hsi_clean.csv`
- `data_clean/HKTECH/hktech_clean.csv`
- `data_clean/HSCEI/hscei_clean.csv`

### 代理层
- `data_clean/9618.HK/daily_clean.csv`
- `data_clean/3690.HK/daily_clean.csv`
- `data_clean/9988.HK/daily_clean.csv`
- `data_clean/2057.HK/daily_clean.csv`
- `data_clean/1519.HK/daily_clean.csv`

### 时间基准层
- `calendar/hk_trade_calendar.csv`

---

## 2.2 输出定位

`model_features.csv` 是：

- 模型输入表  
- 标签表的左表  
- 推理样本表的母表  
- 非解释型正式训练底表

它不是：

- 原始数据表
- 财报附注明细表
- 文本解释表
- 报告输出表

---

## 3. 主键与时间锚点设计

## 3.1 主键

首版联合主键定义为：

- `symbol`
- `asof_date`

说明：

- `symbol`：证券代码，首版固定为 `02618.HK`
- `asof_date`：样本可见时点，对应一个港股交易日

这意味着：

**每一个交易日，最多生成一行模型样本。**

---

## 3.2 asof_date 定义

`asof_date` 定义为：

**该行样本在该交易日开盘前或收盘后可见的、允许进入模型的全部信息所对齐的交易日日期。**

首版建议统一使用港股交易日历中的交易日。

说明：

- 若是做 T+1 收盘后预测，则 `asof_date` 对应预测时点当天
- 若是做下一交易日盘前预测，则也以最近一个已完成数据对齐的交易日作为 `asof_date`

---

## 3.3 不允许未来函数

对任意一行 `(symbol, asof_date)`：

- 只能使用 `asof_date` 当日及以前已经公开可见的数据
- 不能提前引用未来披露的年报 / 中报 / 季报
- 不能提前引用未来行情或未来标签

这是本表最高优先级约束。

---

## 4. 首版表结构分层

首版 `model_features.csv` 按以下五层组织：

1. 身份层  
2. 时间锚点层  
3. 基本面慢变量层  
4. 市场与代理层特征层  
5. 元数据与质量控制层  

解释字段与标签字段不进入本表主体。

---

## 5. 字段清单 V1

## 5.1 身份层字段

### `symbol`
- 含义：证券代码
- 类型：string
- 示例：`02618.HK`
- 规则：必填

### `asof_date`
- 含义：样本时点对应交易日
- 类型：date
- 示例：`2025-12-31`
- 规则：必填

### `trade_year`
- 含义：`asof_date` 所在年份
- 类型：int
- 规则：由 `asof_date` 派生

### `trade_month`
- 含义：`asof_date` 所在月份
- 类型：int
- 规则：由 `asof_date` 派生

### `trade_dayofweek`
- 含义：星期几
- 类型：int
- 规则：由 `asof_date` 派生

---

## 5.2 财报锚点层字段

### `fundamental_anchor_date`
- 含义：该样本实际消费的最近一份基本面记录的 `report_date`
- 类型：date
- 规则：必填

### `fundamental_anchor_period_type`
- 含义：锚定财报类型
- 类型：string
- 可选值：
  - `annual`
  - `semiannual`
  - `quarter`

### `fundamental_lag_days`
- 含义：`asof_date - fundamental_anchor_date` 的天数差
- 类型：int
- 规则：非负

### `fundamental_quality_flag`
- 含义：本行样本所消费基本面记录的质量标记
- 类型：string
- 来源：映射自 `fundamental_features.csv` 的 `quality_flag`

### `fundamental_data_version`
- 含义：基本面记录版本号
- 类型：string
- 来源：映射自 `data_version`

说明：
这一层用于审计样本到底吃的是哪一期财报，防止后续训练/推理口径失控。

---

## 5.3 基本面慢变量层字段

以下字段首版纳入正式消费表。

### 收益与利润结构
- `revenue`
- `gross_profit`
- `gross_margin`
- `net_profit`

### 资产负债结构
- `total_assets`
- `total_liabilities`
- `total_equity`
- `current_assets`
- `current_liabilities`
- `borrowings`
- `lease_liabilities`

### 现金流结构
- `operating_cash_flow`
- `investing_cash_flow`
- `financing_cash_flow`
- `free_cash_inflow`
- `capex_net`

### 营运资本与偿债结构
- `net_cash`
- `working_capital`
- `debt_to_asset_ratio`
- `lease_burden_ratio`

### 营运效率与质量
- `trade_receivables`
- `contract_assets`
- `inventories`
- `trade_payables`
- `receivables_ratio`
- `contract_assets_ratio`
- `inventory_ratio`
- `payables_ratio`

### 账龄与质量
- `supplier_finance_arrangements`
- `supplier_finance_ratio`
- `receivables_over_6m_ratio`
- `receivables_over_12m_ratio`
- `payables_over_12m_ratio`
- `receivables_loss_allowance_ratio`

### 现金流质量
- `free_cash_flow_margin`
- `capex_intensity`
- `operating_cash_flow_margin`
- `cash_conversion_quality_score`

### 客户与收入结构
- `revenue_jd_group`
- `revenue_external`
- `revenue_integrated_supply_chain`
- `revenue_external_integrated_supply_chain`
- `revenue_other_customers`
- `external_revenue_ratio`
- `jd_group_revenue_ratio`
- `integrated_supply_chain_revenue_ratio`
- `external_isc_revenue_ratio`

### 客户运营规模
- `warehouse_count`
- `external_isc_customer_count`
- `external_isc_arpc`
- `external_isc_customer_yoy`
- `external_isc_arpc_yoy`

---

## 5.4 市场与个股层字段

以下字段来自 `daily_clean.csv` 与市场基准表，首版先定义接口，不在本文件中展开全部日线 schema，但需要预留消费口径。

### 个股自身收益与波动
- `stock_close`
- `stock_ret_1d`
- `stock_ret_5d`
- `stock_ret_20d`
- `stock_vol_5d`
- `stock_vol_20d`

### 市场基准收益
- `hsi_ret_1d`
- `hsi_ret_5d`
- `hsi_ret_20d`
- `hktech_ret_1d`
- `hktech_ret_5d`
- `hktech_ret_20d`
- `hscei_ret_1d`
- `hscei_ret_5d`
- `hscei_ret_20d`

### 相对强弱
- `alpha_hsi_5d`
- `alpha_hktech_5d`
- `alpha_hscei_5d`
- `alpha_hsi_20d`
- `alpha_hktech_20d`
- `alpha_hscei_20d`

说明：
以上字段具体由后续 `build_model_features.py` 按 clean 表派生。

---

## 5.5 代理层联动字段

首版预留以下代理层特征：

### 京东集团代理层
- `ret_9618_1d`
- `ret_9618_5d`
- `ret_9618_20d`

### 美团代理层
- `ret_3690_1d`
- `ret_3690_5d`
- `ret_3690_20d`

### 阿里代理层
- `ret_9988_1d`
- `ret_9988_5d`
- `ret_9988_20d`

### 中通代理层
- `ret_2057_1d`
- `ret_2057_5d`
- `ret_2057_20d`

### 极兔代理层
- `ret_1519_1d`
- `ret_1519_5d`
- `ret_1519_20d`

### 与代理层相对强弱
- `alpha_vs_9618_5d`
- `alpha_vs_3690_5d`
- `alpha_vs_9988_5d`
- `alpha_vs_2057_5d`
- `alpha_vs_1519_5d`

说明：
代理层特征用于表达：
- 京东物流与京东生态的联动
- 与平台竞争环境的联动
- 与同业物流环境的联动

---

## 5.6 元数据与质量控制字段

### `row_quality_flag`
- 含义：该行模型样本整体质量标签
- 类型：string
- 可选值建议：
  - `PASS`
  - `PARTIAL`
  - `REVIEW`

### `missing_ratio`
- 含义：本行模型字段缺失比例
- 类型：float

### `feature_count_total`
- 含义：理论应有特征数
- 类型：int

### `feature_count_nonnull`
- 含义：实际非空特征数
- 类型：int

### `build_version`
- 含义：构建脚本版本
- 类型：string

### `built_at`
- 含义：该行生成时间
- 类型：datetime

说明：
这层字段可以保留在 `model_features.csv` 中，因为它们属于数据质量审计，不属于解释文本层。

---

## 6. 明确不进入本表的字段

以下字段不进入 `model_features.csv` 主体：

### 6.1 解释标签类
- `working_capital_pressure_tag`
- `receivables_quality_tag`
- `supplier_finance_usage_tag`
- `cash_flow_quality_tag`
- `customer_structure_tag`
- `globalization_phase_tag`
- `network_expansion_tag`

### 6.2 文本说明类
- `feature_note`
- `source_summary`

### 6.3 明细追踪类
- `mapped_item_codes`
- `item_source_docs`

### 6.4 原始解释质量类
- `mapped_item_count`
- `mapped_item_nonnull_count`
- `item_quality_score_sum`
- `item_quality_score_avg`

说明：
这些字段应进入：
- 审计表
- 解释表
- 报告表
而不是首版正式训练主表。

---

## 7. 缺失值策略

## 7.1 基本原则
- 不乱填
- 不脑补
- 不为凑满表而牺牲真实性

## 7.2 首版建议
### 对关键慢变量
- 缺失则保留空值
- 允许模型侧后续再决定是否插补

### 对比例变量
- 若分母缺失或为 0，则保留空值
- 不强行置 0

### 对同比变量
- 若上一年同期不存在，则保留空值

### 对代理层与市场层
- 若该日停牌或无行情，按 clean 表规则处理
- 不允许直接引用未来交易日补齐

---

## 8. 首版样本生成规则

对每一个港股交易日：

1. 读取该交易日 `asof_date`
2. 找到该日以前最近一份已披露基本面记录
3. 拉取对应慢变量字段
4. 拉取当日及回看窗口的个股、指数、代理层行情特征
5. 生成一行 `(symbol, asof_date)` 样本
6. 计算缺失率与质量标记
7. 写入 `model_features.csv`

---

## 9. 首版周期适配建议

## 9.1 T+1
首版可使用：
- 市场层 / 个股层高频特征
- 基本面层慢变量作为状态过滤器

## 9.2 未来 1 个月
首版可使用：
- 高频行情特征
- 基本面结构特征
- 代理层联动特征

## 9.3 未来 6 个月
首版应提高：
- annual / semiannual 慢变量权重
- 客户结构与现金流质量权重
- 资产负债质量权重

说明：
本表不区分任务单独建三张表，先统一建一张母表。  
后续各预测周期从同一张母表中选取不同特征子集。

---

## 10. 首版正式结论

`model_features.csv` 首版应满足：

1. 一行对应一个 `symbol + asof_date`
2. 只消费当时可见信息
3. annual 为主，semiannual 为辅，quarter 慎用
4. 基本面、市场、代理层统一收口到同一训练底表
5. 解释字段不混入正式模型输入表

---

## 11. 下一步动作

本文件完成后，下一步进入：

**`scripts/build_model_features.py` 首版设计**

脚本职责为：

1. 读取 `fundamental_features.csv`
2. 读取个股 / 指数 / 代理层 clean 表
3. 按 `asof_date` 做 as-of 对齐
4. 生成正式 `model_features.csv`
5. 输出质量检查结果与构建日志
