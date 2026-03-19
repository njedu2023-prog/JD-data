# fundamental_quarterly 字段字典 V1

## 一、文档定位

本字段字典用于解释：

`data_fundamental/02618.HK/fundamental_quarterly.csv`

中各字段的含义、类型、单位、来源与缺失处理方式。

它是 **《京东物流基本面主表 schema V1》** 的配套说明文档，作用不是替代主表，而是为后续：

- 数据落库
- 字段校验
- 半自动抽取
- 人工核验
- 模型消费

提供统一口径。

---

## 二、主表设计原则

### 1. 主表粒度
一行 = 一个财报 / 经营披露周期

### 2. 推荐周期类型
- `quarter`
- `semiannual`
- `annual`

### 3. 主键建议
`symbol + report_date + period_type`

### 4. 单位原则
除特别注明外，数值字段应尽量统一单位，避免同表混乱。

推荐：
- 金额类：`million_rmb`
- 比率类：小数或百分比需全表统一，不允许混用
- 面积类：平方米
- 客户 / 仓库数量类：整数

---

## 三、字段字典总表

字段说明格式：

- 字段名
- 中文注释
- 字段类型
- 推荐单位
- 是否关键字段
- 是否公式字段
- 推荐来源
- 缺失策略

---

# A. 主键与身份字段

### symbol
- 中文注释：股票代码
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：固定值
- 缺失策略：不允许为空
- 备注：京东物流固定为 `02618.HK`

### company_name_zh
- 中文注释：公司中文名
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：固定值
- 缺失策略：不允许为空
- 备注：固定为 `京东物流`

### company_name_en
- 中文注释：公司英文名
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：固定值
- 缺失策略：允许为空，但建议填写
- 备注：固定为 `JD Logistics, Inc.`

### report_date
- 中文注释：报告期截止日
- 字段类型：date
- 推荐单位：YYYY-MM-DD
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报公告
- 缺失策略：不允许为空

### announce_date
- 中文注释：公告发布日期
- 字段类型：date
- 推荐单位：YYYY-MM-DD
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：港交所公告
- 缺失策略：不允许为空

### period_type
- 中文注释：报告周期类型
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：规则字段
- 缺失策略：不允许为空
- 备注：限定为 `quarter / semiannual / annual`

### fiscal_year
- 中文注释：财年
- 字段类型：int
- 推荐单位：年
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报公告
- 缺失策略：不允许为空

### fiscal_period
- 中文注释：财务期标识
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：规则字段
- 缺失策略：不允许为空
- 备注：例如 `Q1 / H1 / Q3 / FY`

### currency
- 中文注释：币种
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报公告
- 缺失策略：不允许为空
- 备注：例如 `rmb`

### unit
- 中文注释：数值单位
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：规则字段
- 缺失策略：不允许为空
- 备注：建议统一为 `million_rmb`

---

# B. 收入与增长字段

### revenue
- 中文注释：营业收入
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：尽量不缺；若未披露，允许为空并在 `quality_note` 说明

### revenue_yoy
- 中文注释：营业收入同比增速
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：是
- 是否公式字段：否 / 可校验
- 推荐来源：财报正文
- 缺失策略：若正文未直接披露，可后算；若无法确认口径则为空并备注

### revenue_qoq
- 中文注释：营业收入环比增速
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：否
- 是否公式字段：是
- 推荐来源：由主表历史期数计算
- 缺失策略：缺上期数据时允许为空

### core_business_revenue
- 中文注释：核心业务收入
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：财报分部披露
- 缺失策略：未披露可为空

### supply_chain_revenue
- 中文注释：一体化供应链收入
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空并备注

### external_customer_revenue
- 中文注释：外部客户收入
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文 / 管理层讨论
- 缺失策略：未披露可为空并备注

### other_revenue
- 中文注释：其他收入
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：财报附注
- 缺失策略：未披露可为空

### revenue_growth_quality_note
- 中文注释：收入增长质量备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理 / 半自动抽取
- 缺失策略：允许为空
- 备注：用于说明增长来自价格、规模、外部客户、并购等因素

---

# C. 利润与盈利能力字段

### gross_profit
- 中文注释：毛利润
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否 / 可后算
- 推荐来源：财报正文
- 缺失策略：若未直接披露且口径清晰，可由收入和毛利率反推

### gross_margin
- 中文注释：毛利率
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：是
- 是否公式字段：是
- 推荐来源：财报正文 / 公式计算
- 缺失策略：可由 `gross_profit / revenue` 补算

### operating_profit
- 中文注释：营业利润
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空并备注

### operating_margin
- 中文注释：营业利润率
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：否
- 是否公式字段：是
- 推荐来源：公式计算
- 缺失策略：基础字段缺失时为空

### net_profit
- 中文注释：净利润
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：尽量不缺

### net_profit_yoy
- 中文注释：净利润同比增速
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：是
- 是否公式字段：否 / 可校验
- 推荐来源：财报正文 / 历史期数对比
- 缺失策略：无可比期时允许为空

### net_profit_qoq
- 中文注释：净利润环比增速
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：否
- 是否公式字段：是
- 推荐来源：历史期数计算
- 缺失策略：缺上期数据时为空

### net_margin
- 中文注释：净利率
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：是
- 是否公式字段：是
- 推荐来源：公式计算
- 缺失策略：基础字段缺失时为空

### adj_net_profit
- 中文注释：经调整净利润
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文 / 非IFRS口径
- 缺失策略：未披露时为空并备注口径缺失

### adj_net_profit_yoy
- 中文注释：经调整净利润同比增速
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：否
- 是否公式字段：否 / 可校验
- 推荐来源：财报正文 / 历史期数计算
- 缺失策略：缺上期数据时为空

### ebitda
- 中文注释：息税折旧摊销前利润
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空

### ebitda_margin
- 中文注释：EBITDA 利润率
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：否
- 是否公式字段：是
- 推荐来源：公式计算
- 缺失策略：基础字段缺失时为空

### adj_ebitda
- 中文注释：经调整 EBITDA
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空

### adj_ebitda_margin
- 中文注释：经调整 EBITDA 利润率
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：是
- 是否公式字段：是
- 推荐来源：公式计算 / 财报正文
- 缺失策略：基础字段缺失时为空

### profit_quality_note
- 中文注释：利润质量备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

---

# D. 现金流与资本开支字段

### operating_cash_flow
- 中文注释：经营活动现金流
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：现金流量表
- 缺失策略：未披露可为空

### investing_cash_flow
- 中文注释：投资活动现金流
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：现金流量表
- 缺失策略：允许为空

### financing_cash_flow
- 中文注释：融资活动现金流
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：现金流量表
- 缺失策略：允许为空

### free_cash_flow
- 中文注释：自由现金流
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：是
- 推荐来源：公式计算
- 缺失策略：基础字段缺失时为空

### capex
- 中文注释：资本开支
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报附注 / 现金流量表
- 缺失策略：未披露可为空并备注

### cash_and_equivalents
- 中文注释：现金及现金等价物
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：尽量不缺

### restricted_cash
- 中文注释：受限资金
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：财报附注
- 缺失策略：未披露可为空

### cash_flow_quality_note
- 中文注释：现金流质量备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

---

# E. 资产负债结构字段

### total_assets
- 中文注释：总资产
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：尽量不缺

### total_liabilities
- 中文注释：总负债
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：尽量不缺

### total_equity
- 中文注释：股东权益
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：尽量不缺

### current_assets
- 中文注释：流动资产
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：允许为空

### current_liabilities
- 中文注释：流动负债
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：允许为空

### interest_bearing_debt
- 中文注释：有息负债
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：否 / 可整理
- 推荐来源：财报附注 / 负债科目整理
- 缺失策略：若无法明确口径则为空并备注

### net_cash
- 中文注释：净现金
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：是
- 是否公式字段：是
- 推荐来源：公式计算
- 缺失策略：基础字段缺失时为空

### debt_to_asset_ratio
- 中文注释：资产负债率
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：是
- 是否公式字段：是
- 推荐来源：公式计算
- 缺失策略：基础字段缺失时为空

### balance_sheet_quality_note
- 中文注释：资产负债表质量备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

---

# F. 运营效率字段

### inventory
- 中文注释：存货
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：允许为空

### inventory_turnover_days
- 中文注释：存货周转天数
- 字段类型：float
- 推荐单位：天
- 是否关键字段：否
- 是否公式字段：否 / 可后算
- 推荐来源：财报正文 / 运营指标
- 缺失策略：未披露可为空

### accounts_receivable
- 中文注释：应收账款
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：允许为空

### accounts_receivable_turnover_days
- 中文注释：应收周转天数
- 字段类型：float
- 推荐单位：天
- 是否关键字段：否
- 是否公式字段：否 / 可后算
- 推荐来源：财报正文 / 运营指标
- 缺失策略：未披露可为空

### accounts_payable
- 中文注释：应付账款
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：资产负债表
- 缺失策略：允许为空

### accounts_payable_turnover_days
- 中文注释：应付周转天数
- 字段类型：float
- 推荐单位：天
- 是否关键字段：否
- 是否公式字段：否 / 可后算
- 推荐来源：财报正文 / 运营指标
- 缺失策略：未披露可为空

### working_capital
- 中文注释：营运资本
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：是 / 半公式
- 推荐来源：公式计算
- 缺失策略：基础字段缺失时为空

### working_capital_change
- 中文注释：营运资本变化
- 字段类型：float
- 推荐单位：million_rmb
- 是否关键字段：否
- 是否公式字段：是
- 推荐来源：历史期数计算
- 缺失策略：首期或缺上期数据时为空

### efficiency_note
- 中文注释：运营效率备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

---

# G. 业务结构与经营规模字段

### integrated_supply_chain_clients
- 中文注释：一体化供应链客户数量
- 字段类型：float / int
- 推荐单位：个
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空

### warehouse_count
- 中文注释：仓库数量
- 字段类型：int
- 推荐单位：个
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空

### warehouse_area
- 中文注释：仓储面积
- 字段类型：float
- 推荐单位：平方米
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空

### cloud_warehouse_count
- 中文注释：云仓数量
- 字段类型：int
- 推荐单位：个
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：财报正文
- 缺失策略：未披露可为空

### county_coverage_ratio
- 中文注释：区县覆盖率
- 字段类型：float
- 推荐单位：ratio 或 pct
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：财报正文 / 运营披露
- 缺失策略：未披露可为空

### delivery_network_note
- 中文注释：配送网络备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

### fulfillment_scale_note
- 中文注释：履约规模备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

---

# H. 市场与估值辅助字段

### market_cap
- 中文注释：总市值（公告日附近）
- 字段类型：float
- 推荐单位：million_hkd 或 billion_hkd
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：行情侧推算
- 缺失策略：允许为空
- 备注：必须在字段治理中统一币种口径

### ps_ttm
- 中文注释：市销率TTM
- 字段类型：float
- 推荐单位：倍
- 是否关键字段：否
- 是否公式字段：否 / 可推算
- 推荐来源：行情估值侧
- 缺失策略：允许为空

### pe_ttm
- 中文注释：市盈率TTM
- 字段类型：float
- 推荐单位：倍
- 是否关键字段：否
- 是否公式字段：否 / 可推算
- 推荐来源：行情估值侧
- 缺失策略：亏损时允许为空

### pb
- 中文注释：市净率
- 字段类型：float
- 推荐单位：倍
- 是否关键字段：否
- 是否公式字段：否 / 可推算
- 推荐来源：行情估值侧
- 缺失策略：允许为空

### ev_to_ebitda
- 中文注释：EV/EBITDA
- 字段类型：float
- 推荐单位：倍
- 是否关键字段：否
- 是否公式字段：否 / 可推算
- 推荐来源：行情估值侧
- 缺失策略：基础字段不足时为空

### valuation_note
- 中文注释：估值备注
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

---

# I. 事件与管理层备注字段

### major_event_flag
- 中文注释：重大事件标记
- 字段类型：int / bool
- 推荐单位：0/1
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理 / 事件抽取
- 缺失策略：默认 0

### major_event_type
- 中文注释：重大事件类型
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：无事件时为空
- 备注：例如并购、组织调整、业务扩张、监管变化等

### major_event_note
- 中文注释：重大事件说明
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理 / 半自动抽取
- 缺失策略：允许为空

### management_guidance
- 中文注释：管理层指引摘要
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：业绩会 / 财报文字披露 / 管理层讨论
- 缺失策略：未披露可为空

### guidance_change_flag
- 中文注释：指引变化标记
- 字段类型：int / bool
- 推荐单位：0/1
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工判断 / 规则抽取
- 缺失策略：默认 0

### guidance_note
- 中文注释：指引说明
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工整理
- 缺失策略：允许为空

---

# J. 数据治理字段

### source_type
- 中文注释：来源类型
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：入库时写入
- 缺失策略：不允许为空
- 备注：例如 `hkex_announcement / annual_report / interim_report`

### source_url
- 中文注释：源文件链接
- 字段类型：string
- 推荐单位：URL
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：入库时写入
- 缺失策略：不允许为空

### source_title
- 中文注释：源公告标题
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：源公告
- 缺失策略：不允许为空

### ingest_time
- 中文注释：入库时间
- 字段类型：datetime
- 推荐单位：ISO 8601
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：系统写入
- 缺失策略：不允许为空

### data_version
- 中文注释：数据版本
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：系统写入
- 缺失策略：不允许为空

### quality_flag
- 中文注释：质量标记
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：校验流程
- 缺失策略：不允许为空
- 备注：限定值 `PASS / REVIEW / ERROR`

### quality_note
- 中文注释：质量说明
- 字段类型：string
- 推荐单位：无
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：校验流程 / 人工补充
- 缺失策略：允许为空，但缺字段时必须说明原因

### is_manual_verified
- 中文注释：是否人工核验
- 字段类型：int / bool
- 推荐单位：0/1
- 是否关键字段：是
- 是否公式字段：否
- 推荐来源：人工核验流程
- 缺失策略：默认 0

### verified_by
- 中文注释：核验人
- 字段类型：string
- 推荐单位：无
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工填写
- 缺失策略：未人工核验时为空

### verified_time
- 中文注释：核验时间
- 字段类型：datetime
- 推荐单位：ISO 8601
- 是否关键字段：否
- 是否公式字段：否
- 推荐来源：人工填写 / 系统写入
- 缺失策略：未人工核验时为空

---

## 四、V1 关键字段建议

以下字段建议作为 V1 重点保障字段，优先保证可落库、可追溯、可复核：

### 核心身份与周期
- symbol
- report_date
- announce_date
- period_type
- fiscal_year
- fiscal_period
- currency
- unit

### 核心经营结果
- revenue
- revenue_yoy
- supply_chain_revenue
- external_customer_revenue
- gross_profit
- gross_margin
- net_profit
- net_profit_yoy
- adj_net_profit
- adj_ebitda
- adj_ebitda_margin

### 核心财务质量
- operating_cash_flow
- free_cash_flow
- capex
- cash_and_equivalents
- total_assets
- total_liabilities
- total_equity
- interest_bearing_debt
- net_cash
- debt_to_asset_ratio

### 核心经营规模
- integrated_supply_chain_clients
- warehouse_count
- warehouse_area
- cloud_warehouse_count

### 核心事件与治理
- management_guidance
- major_event_flag
- major_event_type
- source_type
- source_url
- source_title
- ingest_time
- data_version
- quality_flag
- quality_note
- is_manual_verified

---

## 五、V1 缺失值处理规则

### 1. 不允许为空
以下字段原则上不允许为空：
- symbol
- report_date
- announce_date
- period_type
- fiscal_year
- fiscal_period
- currency
- unit
- source_type
- source_url
- source_title
- ingest_time
- data_version
- quality_flag

### 2. 关键财务字段尽量不为空
以下字段应作为优先保证对象：
- revenue
- net_profit
- total_assets
- total_liabilities
- total_equity
- cash_and_equivalents

### 3. 未披露可为空，但必须可追溯
若字段确实未披露：
- 允许为空
- 必须在 `quality_note` 说明“未披露”
- 必要时在相关 note 字段补充背景

### 4. 公式字段允许后算
例如：
- gross_margin
- operating_margin
- net_margin
- free_cash_flow
- net_cash
- debt_to_asset_ratio

若源公告未直接给出，但基础字段完整，可由系统计算补齐。

---

## 六、V1 工程结论

`fundamental_quarterly.csv` 在 V1 阶段应被视为：

**京东物流财报周期级别的基本面主表。**

它的职责不是追求一次性完美，而是先建立：

1. 稳定字段框架  
2. 清晰口径定义  
3. 来源可追溯  
4. 缺失可解释  
5. 后续可自动化扩展  

---

## 七、下一步直接开发任务

本字典完成后，下一步应直接进入：

### 《fundamental_quarterly 字段来源映射表 V1》

按字段进一步划分为三类：

1. 可直接结构化抓取
2. 可半自动抽取
3. 需人工核验 / 人工录入

这是后续把 schema 真正推进到 ingestion 设计的关键一步。
