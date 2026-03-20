## fundamental_quarterly -> model_features 字段映射表 V1

### 1. 目标定位

当前 `fundamental_quarterly.csv` 的角色，不再只是“可读的基本面汇总表”，而是要向下游拆成两层：

**A. 模型训练消费层（model_features）**
- 只保留可比较、可派生、可训练的字段
- 尽量减少强主观文本和口径漂移字段直接入模
- 允许保留缺失，但必须标注缺失机制

**B. 模型解释层（explanation layer）**
- 承接管理层摘要、事件说明、质量备注、指引等文本信息
- 用于预测结果解释、财报后状态标注、异常原因回溯
- 不直接裸喂数值模型

---

### 2. 分层原则

#### 2.1 直接保留
满足以下条件的字段直接进入 `model_features`：
- 财务意义明确
- 跨期可比较
- 定义相对稳定
- 数值型、离散型、日期型为主

#### 2.2 做派生
满足以下条件的字段优先转成派生特征：
- 单点值意义一般，但同比 / 环比 / 比率 / 结构占比更有价值
- 半年报 / 年报才能完整披露，需要转换为“可被模型统一理解”的口径
- 原始字段过于粗糙，但经组合后有更强解释力

#### 2.3 暂时弃用
满足以下情况先不进入首版模型：
- 口径混乱，短期内无法统一
- 缺失过多且非稳定披露
- 样本量阶段太小，容易制造噪音
- 与其它字段高度重复，且解释收益不高

#### 2.4 进入解释层
以下字段进入解释层而不是首版数值模型：
- 管理层语言描述
- 重大事件说明
- 质量注释
- 财报摘要性文字
- 指引、战略、业务进展、风险说明

---

### 3. 字段映射总表 V1

> 说明：  
> - “去向”分为：`direct` / `derived` / `drop_now` / `explain_only`  
> - “首版处理”表示当前阶段建议  
> - “备注”用于指出字段风险或后续动作

| fundamental_quarterly 字段 | 中文含义 | 去向 | 首版处理 | 备注 |
|---|---|---:|---|---|
| symbol | 股票代码 | direct | 保留 | 主键维度字段 |
| report_date | 报告日期 | direct | 保留 | 时间锚点 |
| period_type | 周期类型 | direct | 保留 | quarter / semiannual / annual |
| fiscal_year | 财年 | direct | 保留 | 方便跨年建模 |
| fiscal_period | 财报期别 | direct | 保留 | 如 Q1 / H1 / Q3 / FY |
| revenue | 收入 | direct | 保留 | 核心主干字段 |
| gross_profit | 毛利 | direct | 保留 | 核心盈利字段 |
| gross_margin | 毛利率 | direct | 保留 | 比绝对值更稳 |
| net_profit | 净利润 | direct | 保留 | 核心盈利字段 |
| adjusted_net_profit | 调整后净利润 | direct | 保留 | 对经营趋势更有参考价值 |
| net_margin | 净利率 | derived | 由净利润/收入派生 | 若原表已有则双保留校验 |
| operating_cash_flow | 经营现金流 | direct | 保留 | 但注意 Q1/Q3 结构性缺失 |
| total_assets | 总资产 | direct | 保留 | 重点用于 H1/FY |
| total_liabilities | 总负债 | direct | 保留 | 重点用于 H1/FY |
| total_equity | 总权益 | direct | 保留 | 重点用于 H1/FY |
| current_assets | 流动资产 | direct | 保留 | 后续做流动性派生 |
| current_liabilities | 流动负债 | direct | 保留 | 后续做流动性派生 |
| accounts_receivable | 应收账款 | direct | 保留 | 后续做周转派生 |
| accounts_payable | 应付账款 | direct | 保留 | 后续做周转派生 |
| inventory | 存货 | direct | 保留 | 物流行业解释力一般，但保留 |
| cash_and_equivalents | 现金及等价物 | direct | 保留 | 可做安全垫特征 |
| restricted_cash | 受限现金 | direct | 保留 | 后续与现金类合并处理 |
| interest_bearing_debt | 有息负债 | direct | 保留 | 用于偿债压力 |
| investing_cash_flow | 投资现金流 | direct | 保留 | 首版可保留，后续做 capex 归并 |
| financing_cash_flow | 融资现金流 | direct | 保留 | 首版可保留 |
| external_customer_revenue | 外部客户相关收入 | drop_now | 暂不裸入模 | 口径歧义，需先统一 |
| integrated_supply_chain_revenue | 一体化供应链收入 | direct | 保留 | 业务核心字段 |
| external_integrated_supply_chain_revenue | 外部一体化供应链客户收入 | direct | 保留 | 若口径明确，优先高于 external_customer_revenue |
| customer_count | 客户数 | direct | 保留 | 离散经营规模指标 |
| warehouse_count | 仓库数量 | direct | 保留 | 基础运营规模指标 |
| storage_area | 仓储面积 | direct | 保留 | 若已有，建议保留 |
| network_coverage | 网络覆盖 | explain_only | 解释层 | 文本/半结构化表达居多 |
| capex | 资本开支 | derived | 后续统一派生 | 建议由标准报表口径派生 |
| free_cash_flow | 自由现金流 | derived | 派生 | OCF - capex |
| net_cash | 净现金 | derived | 派生 | 现金及等价物 - 有息负债 |
| working_capital | 营运资本 | derived | 派生 | 流动资产 - 流动负债 |
| debt_to_asset_ratio | 资产负债率 | derived | 派生 | 总负债 / 总资产 |
| current_ratio | 流动比率 | derived | 派生 | 流动资产 / 流动负债 |
| ar_turnover_days | 应收周转天数 | derived | 派生 | 应收账款 / 收入 * 天数 |
| ap_turnover_days | 应付周转天数 | derived | 派生 | 应付账款 / 成本 * 天数，若成本缺失则暂缓 |
| inventory_turnover_days | 存货周转天数 | derived | 派生 | 存货 / 成本 * 天数，若成本缺失则暂缓 |
| yoy_revenue_growth | 收入同比 | derived | 派生 | 极重要 |
| yoy_gross_profit_growth | 毛利同比 | derived | 派生 | 建议纳入 |
| yoy_net_profit_growth | 净利润同比 | derived | 派生 | 建议纳入 |
| yoy_adjusted_net_profit_growth | 调整后净利润同比 | derived | 派生 | 建议纳入 |
| yoy_ocf_growth | 经营现金流同比 | derived | 派生 | 仅在可比期存在时生成 |
| gross_margin_change | 毛利率变化 | derived | 派生 | 与上年同期比较 |
| net_margin_change | 净利率变化 | derived | 派生 | 与上年同期比较 |
| revenue_share_isc | 一体化供应链收入占比 | derived | 派生 | 一体化供应链收入 / 总收入 |
| revenue_share_external_isc | 外部一体化供应链收入占比 | derived | 派生 | 外部一体化供应链收入 / 总收入 |
| revenue_growth_quality_note | 收入增长质量说明 | explain_only | 解释层 | 文本，不直接入模 |
| profit_quality_note | 利润质量说明 | explain_only | 解释层 | 文本 |
| cash_flow_quality_note | 现金流质量说明 | explain_only | 解释层 | 文本 |
| major_event_note | 重大事件说明 | explain_only | 解释层 | 文本 |
| management_guidance | 管理层指引 | explain_only | 解释层 | 文本 |
| quality_note | 质量备注 | explain_only | 解释层 | 文本 |
| quality_flag | 质量标签 | direct | 保留 | 但只作为可信度辅助特征，不作目标变量 |
| source_type | 来源类型 | direct | 保留 | 区分标准报表/摘要/人工整理 |
| source_file | 来源文件 | drop_now | 首版不入模 | 留在数据治理层 |
| ingest_time | 入库时间 | drop_now | 首版不入模 | 仅工程留痕 |
| updated_at | 更新时间 | drop_now | 首版不入模 | 仅工程留痕 |

---

### 4. 首版 model_features 建议保留字段池

#### 4.1 基础识别字段
- symbol
- report_date
- period_type
- fiscal_year
- fiscal_period
- quality_flag
- source_type

#### 4.2 原始数值主干字段
- revenue
- gross_profit
- gross_margin
- net_profit
- adjusted_net_profit
- operating_cash_flow
- total_assets
- total_liabilities
- total_equity
- current_assets
- current_liabilities
- accounts_receivable
- accounts_payable
- inventory
- cash_and_equivalents
- restricted_cash
- interest_bearing_debt
- investing_cash_flow
- financing_cash_flow
- integrated_supply_chain_revenue
- external_integrated_supply_chain_revenue
- customer_count
- warehouse_count
- storage_area

#### 4.3 首版重点派生特征
- yoy_revenue_growth
- yoy_gross_profit_growth
- yoy_net_profit_growth
- yoy_adjusted_net_profit_growth
- yoy_ocf_growth
- net_margin
- gross_margin_change
- net_margin_change
- working_capital
- net_cash
- free_cash_flow
- debt_to_asset_ratio
- current_ratio
- revenue_share_isc
- revenue_share_external_isc
- ar_turnover_days

---

### 5. 首版暂时弃用字段

以下字段建议 **暂时不进入首版训练层**：

#### 5.1 口径存在歧义
- external_customer_revenue

原因：
- 不同年份可能不是同一统计口径
- 有时像“外部客户总收入”
- 有时更像“外部一体化供应链客户收入”
- 若直接入模，会制造跨期假变化

#### 5.2 工程留痕字段
- source_file
- ingest_time
- updated_at

原因：
- 对预测业务没有直接价值
- 主要用于审计、排错、追踪

#### 5.3 难以稳定量化的文本/半文本
- network_coverage
- revenue_growth_quality_note
- profit_quality_note
- cash_flow_quality_note
- major_event_note
- management_guidance
- quality_note

原因：
- 首版先进入解释层
- 后续可再做标签化或 embedding 化

---

### 6. 文本字段解释层设计建议

解释层不与数值表混在一起，建议后续单独做：

`fundamental_explanations`

建议字段：
- symbol
- report_date
- period_type
- major_event_note
- management_guidance
- revenue_growth_quality_note
- profit_quality_note
- cash_flow_quality_note
- quality_note
- event_tag
- sentiment_tag
- risk_tag
- operation_tag

其中：
- `event_tag`：如 并购 / 业务扩张 / 客户增长 / 成本扰动 / 政策影响
- `sentiment_tag`：正向 / 中性 / 负向
- `risk_tag`：口径不稳 / 一次性损益 / 现金流承压 / 负债上升
- `operation_tag`：仓网扩张 / 客户增长 / 时效改善 / 外部单量提升

---

### 7. 当前最需要优先统一口径的字段

#### 第一优先
- external_customer_revenue

#### 第二优先
- integrated_supply_chain_revenue
- external_integrated_supply_chain_revenue

#### 第三优先
- capex
- free_cash_flow
- net_cash

原因：
前两类决定业务结构解释是否失真，后三类决定现金流和资本开支因子是否能稳定训练。

---

### 8. 对 external_customer_revenue 的首版处理结论

在口径未完全统一前：

**处理原则：**
1. 不直接进入首版模型训练表
2. 在原始底表中保留
3. 在字段字典里单独标注“口径待统一”
4. 若某些年份能确认其等价于“外部一体化供应链客户收入”，也不要直接混并覆盖原值
5. 后续新增：
   - `external_customer_revenue_raw`
   - `external_customer_revenue_standardized`
   - `external_customer_revenue_caliber_flag`

这样做的好处是：
- 不破坏原始数据
- 不制造伪连续时间序列
- 给后续口径修订留出空间

---

### 9. 首版落地结论

当前 `fundamental_quarterly.csv` 不应直接裸喂成熟模型，而应拆成：

- **原始基本面源表**
- **可训练特征表（model_features / fundamental_features）**
- **文本解释层表（fundamental_explanations）**

首版映射原则已经明确：

- **直接保留**：标准财务数值、核心经营规模、基础元字段
- **做派生**：同比、利润率、结构占比、偿债与流动性、现金流质量
- **暂时弃用**：口径歧义字段、工程留痕字段
- **进入解释层**：管理层文本、重大事件、质量说明

---

### 10. 下一步直接续做

如果本映射表 V1 认可，下一步直接进入三件事：

#### A. 定义首版 `fundamental_features` 表结构
把上面的 direct + derived 字段正式落成一张可训练上游表。

#### B. 制定口径统一规则 V1
优先处理：
- external_customer_revenue
- external_integrated_supply_chain_revenue
- integrated_supply_chain_revenue

#### C. 规划标准财报底表与 ingestion 前处理层
形成：
- 标准财报底表
- Excel / PDF / Word -> staging JSON
- staging JSON -> fundamental_quarterly / fundamental_features

---
