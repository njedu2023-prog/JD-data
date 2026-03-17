《京东物流基本面主表 schema V1》
一、文档定位

本 schema 用于为 京东物流（02618.HK） 建立后续中期与长期预测所需的基本面主表。
该表不是交易日频表，不替代现有 data_raw / data_clean 的价格层数据，而是作为：

1个月预测

6个月预测

事件后趋势判断

财报周期状态识别

经营质量变化跟踪

的正式底层表。

本表优先服务以下目标：

形成京东物流基本面“真值层”

为后续特征工程提供稳定字段源

保证可审计、可追溯、可持续维护

避免后续模型层直接读取杂乱公告文本

二、建议文件路径
data_fundamental/02618.HK/fundamental_quarterly.csv

如后续扩展，可增加：

data_fundamental/02618.HK/fundamental_semiannual.csv
data_fundamental/02618.HK/fundamental_annual.csv
data_fundamental/02618.HK/fundamental_event_notes.csv

但 V1 主表先只做一张：

fundamental_quarterly.csv
三、主表粒度定义
表粒度

一行 = 一个财报/经营披露周期

推荐周期粒度

优先兼容以下几类：

季度

半年度

年度

主键建议
symbol + report_date + period_type
四、字段总表（Schema V1）
A. 主键与身份字段

symbol：股票代码，固定为京东物流 02618.HK

company_name_zh：公司中文名，固定为京东物流

company_name_en：公司英文名，固定为 JD Logistics, Inc.

report_date：报告期截止日，例如 2024-12-31

announce_date：公告发布日期，例如 2025-03-06

period_type：报告周期类型，取值建议 quarter / semiannual / annual

fiscal_year：财年，例如 2024

fiscal_period：财务期标识，例如 Q1 / H1 / FY / Q3

currency：币种，默认 HKD 或 RMB，必须明示

unit：数值单位，例如 million_rmb / billion_rmb

B. 收入与增长字段

revenue：营业收入

revenue_yoy：营业收入同比增速

revenue_qoq：营业收入环比增速

core_business_revenue：核心业务收入

supply_chain_revenue：一体化供应链收入

external_customer_revenue：外部客户收入

other_revenue：其他收入

revenue_growth_quality_note：收入增长质量备注

C. 利润与盈利能力字段

gross_profit：毛利润

gross_margin：毛利率

operating_profit：营业利润

operating_margin：营业利润率

net_profit：净利润

net_profit_yoy：净利润同比增速

net_profit_qoq：净利润环比增速

net_margin：净利率

adj_net_profit：经调整净利润

adj_net_profit_yoy：经调整净利润同比增速

ebitda：息税折旧摊销前利润

ebitda_margin：EBITDA 利润率

adj_ebitda：经调整 EBITDA

adj_ebitda_margin：经调整 EBITDA 利润率

profit_quality_note：利润质量备注

D. 现金流与资本开支字段

operating_cash_flow：经营活动现金流

investing_cash_flow：投资活动现金流

financing_cash_flow：融资活动现金流

free_cash_flow：自由现金流

capex：资本开支

cash_and_equivalents：现金及现金等价物

restricted_cash：受限资金

cash_flow_quality_note：现金流质量备注

E. 资产负债结构字段

total_assets：总资产

total_liabilities：总负债

total_equity：股东权益

current_assets：流动资产

current_liabilities：流动负债

interest_bearing_debt：有息负债

net_cash：净现金

debt_to_asset_ratio：资产负债率

balance_sheet_quality_note：资产负债表质量备注

F. 运营效率字段

inventory：存货

inventory_turnover_days：存货周转天数

accounts_receivable：应收账款

accounts_receivable_turnover_days：应收周转天数

accounts_payable：应付账款

accounts_payable_turnover_days：应付周转天数

working_capital：营运资本

working_capital_change：营运资本变化

efficiency_note：运营效率备注

G. 业务结构与经营规模字段

integrated_supply_chain_clients：一体化供应链客户数量

warehouse_count：仓库数量

warehouse_area：仓储面积

cloud_warehouse_count：云仓数量

county_coverage_ratio：区县覆盖率

delivery_network_note：配送网络备注

fulfillment_scale_note：履约规模备注

H. 市场与估值辅助字段

这一组不是财报原字段，但建议在主表中保留，便于后续合并使用。

market_cap：公告日附近总市值

ps_ttm：市销率 TTM

pe_ttm：市盈率 TTM

pb：市净率

ev_to_ebitda：企业价值倍数

valuation_note：估值备注

I. 事件与管理层备注字段

major_event_flag：重大事件标记

major_event_type：重大事件类型，例如 acquisition / restructuring / policy / guidance

major_event_note：重大事件说明

management_guidance：管理层指引摘要

guidance_change_flag：指引变化标记

guidance_note：指引说明

J. 数据治理字段

source_type：来源类型，例如 hkex_announcement / annual_report / interim_report

source_url：源文件或源公告链接

source_title：源公告标题

ingest_time：入库时间

data_version：数据版本

quality_flag：质量标记，建议 PASS / REVIEW / ERROR

quality_note：质量说明

is_manual_verified：是否已人工核验

verified_by：核验人

verified_time：核验时间

五、字段口径要求
1. 收入、利润类

必须统一口径，不允许一部分用“报告期口径”，另一部分用“TTM 口径”混在一起。
V1 建议：

主表数值字段默认使用 报告期口径

TTM 类字段单独命名，如 ps_ttm、pe_ttm

2. 币种与单位

必须显式写入：

currency

unit

禁止仅靠 README 或人工记忆判断。

3. 同比、环比字段

建议统一用小数，不用百分号字符串。

例如：

0.241 表示同比增长 24.1%

-0.053 表示下降 5.3%

4. 备注字段

备注字段允许文本，但禁止把关键数值只写在备注里。
关键数值必须结构化落表。

六、缺失值策略
1. 能从原公告明确取到的字段

必须填值，不允许空着。

2. 公告未披露的字段

填空值，但必须：

quality_flag 不降为 ERROR

在 quality_note 或对应 note 字段中说明“未披露”

3. 推导字段

例如：

gross_margin

net_margin

debt_to_asset_ratio

free_cash_flow

可以由原始字段推导，但必须满足：

推导逻辑固定

公式写入 schema 文档

不同批次不能改变口径

七、推荐公式口径

gross_margin：毛利率 = 毛利润 / 营业收入

operating_margin：营业利润率 = 营业利润 / 营业收入

net_margin：净利率 = 净利润 / 营业收入

ebitda_margin：EBITDA 利润率 = EBITDA / 营业收入

debt_to_asset_ratio：资产负债率 = 总负债 / 总资产

net_cash：净现金 = 现金及现金等价物 - 有息负债

free_cash_flow：自由现金流 = 经营活动现金流 - 资本开支

八、字段分层建议

后续为了防止主表过宽，可以分逻辑层维护，但 V1 仍建议先保留一张主表。

可分成的逻辑层

身份层

收入层

利润层

现金流层

资产负债层

运营效率层

业务规模层

估值辅助层

治理层

但在工程上，V1 先不拆表，避免复杂度过早上升。

九、最小可用字段集（MVP）

如果你要先快速落一版，不必一次填满全部字段。
V1 最小可用字段集建议如下：

symbol：股票代码，固定为京东物流 02618.HK

report_date：报告期截止日

announce_date：公告发布日期

period_type：报告周期类型

fiscal_year：财年

fiscal_period：财务期标识

currency：币种

unit：单位

revenue：营业收入

revenue_yoy：营业收入同比增速

net_profit：净利润

net_profit_yoy：净利润同比增速

adj_net_profit：经调整净利润

gross_margin：毛利率

net_margin：净利率

adj_ebitda：经调整 EBITDA

adj_ebitda_margin：经调整 EBITDA 利润率

operating_cash_flow：经营活动现金流

cash_and_equivalents：现金及现金等价物

capex：资本开支

supply_chain_revenue：一体化供应链收入

external_customer_revenue：外部客户收入

warehouse_count：仓库数量

warehouse_area：仓储面积

source_url：源链接

source_title：源公告标题

ingest_time：入库时间

data_version：数据版本

quality_flag：质量标记

quality_note：质量说明

十、CSV 列顺序建议
symbol, 股票代码
company_name_zh, 公司中文名
company_name_en, 公司英文名
report_date, 报告期截止日
announce_date, 公告发布日期
period_type, 报告周期类型
fiscal_year, 财年
fiscal_period, 财务期标识
currency, 币种
unit, 数值单位
revenue, 营业收入
revenue_yoy, 营业收入同比增速
revenue_qoq, 营业收入环比增速
core_business_revenue, 核心业务收入
supply_chain_revenue, 一体化供应链收入
external_customer_revenue, 外部客户收入
other_revenue, 其他收入
gross_profit, 毛利润
gross_margin, 毛利率
operating_profit, 营业利润
operating_margin, 营业利润率
net_profit, 净利润
net_profit_yoy, 净利润同比增速
net_profit_qoq, 净利润环比增速
net_margin, 净利率
adj_net_profit, 经调整净利润
adj_net_profit_yoy, 经调整净利润同比增速
ebitda, 息税折旧摊销前利润
ebitda_margin, EBITDA 利润率
adj_ebitda, 经调整 EBITDA
adj_ebitda_margin, 经调整 EBITDA 利润率
operating_cash_flow, 经营活动现金流
investing_cash_flow, 投资活动现金流
financing_cash_flow, 融资活动现金流
free_cash_flow, 自由现金流
capex, 资本开支
cash_and_equivalents, 现金及现金等价物
restricted_cash, 受限资金
total_assets, 总资产
total_liabilities, 总负债
total_equity, 股东权益
current_assets, 流动资产
current_liabilities, 流动负债
interest_bearing_debt, 有息负债
net_cash, 净现金
debt_to_asset_ratio, 资产负债率
inventory, 存货
inventory_turnover_days, 存货周转天数
accounts_receivable, 应收账款
accounts_receivable_turnover_days, 应收周转天数
accounts_payable, 应付账款
accounts_payable_turnover_days, 应付周转天数
working_capital, 营运资本
working_capital_change, 营运资本变化
integrated_supply_chain_clients, 一体化供应链客户数量
warehouse_count, 仓库数量
warehouse_area, 仓储面积
cloud_warehouse_count, 云仓数量
county_coverage_ratio, 区县覆盖率
market_cap, 总市值
ps_ttm, 市销率TTM
pe_ttm, 市盈率TTM
pb, 市净率
ev_to_ebitda, EV/EBITDA
major_event_flag, 重大事件标记
major_event_type, 重大事件类型
major_event_note, 重大事件说明
management_guidance, 管理层指引摘要
guidance_change_flag, 指引变化标记
guidance_note, 指引说明
revenue_growth_quality_note, 收入增长质量备注
profit_quality_note, 利润质量备注
cash_flow_quality_note, 现金流质量备注
balance_sheet_quality_note, 资产负债表质量备注
efficiency_note, 运营效率备注
delivery_network_note, 配送网络备注
fulfillment_scale_note, 履约规模备注
valuation_note, 估值备注
source_type, 来源类型
source_url, 源文件链接
source_title, 源公告标题
ingest_time, 入库时间
data_version, 数据版本
quality_flag, 质量标记
quality_note, 质量说明
is_manual_verified, 是否人工核验
verified_by, 核验人
verified_time, 核验时间
十一、阶段性执行建议
第一阶段

先只整理京东物流近几年最关键财报周期，落成 fundamental_quarterly.csv。

第二阶段

补齐缺失字段，统一口径。

第三阶段

再考虑是否扩展到：

9618.HK 基本面主表

2057.HK / 1519.HK 同业基本面表

基本面衍生特征层

十二、一句话结论

V1 的核心不是追求字段越多越好，而是先把京东物流基本面做成一张口径统一、来源可查、可持续维护、可直接服务 1个月与 6个月预测的正式主表。
