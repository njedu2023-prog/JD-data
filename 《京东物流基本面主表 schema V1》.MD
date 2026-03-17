# 《京东物流基本面主表 schema V1》

## 一、文档定位

本 schema 用于为 **京东物流（02618.HK）** 建立后续中期与长期预测所需的**基本面主表**。  
该表不是交易日频表，不替代现有价格层 `data_raw` / `data_clean`，而是作为：

- 未来 1 个月预测
- 未来 6 个月预测
- 事件后趋势判断
- 财报周期状态识别
- 经营质量变化跟踪

的正式底层表。

---

## 二、建议文件路径

```text
data_fundamental/02618.HK/fundamental_quarterly.csv
```

---

## 三、主表粒度定义

**一行 = 一个财报/经营披露周期**

推荐兼容周期：

- quarter
- semiannual
- annual

主键建议：

```text
symbol + report_date + period_type
```

---

## 四、字段总表（Schema V1）

> 写法：英文字段后，根上中文注释。

### A. 主键与身份字段

- `symbol` 股票代码，固定为京东物流 02618.HK
- `company_name_zh` 公司中文名，固定为京东物流
- `company_name_en` 公司英文名，固定为 JD Logistics, Inc.
- `report_date` 报告期截止日
- `announce_date` 公告发布日期
- `period_type` 报告周期类型（quarter / semiannual / annual）
- `fiscal_year` 财年
- `fiscal_period` 财务期标识（Q1 / H1 / FY / Q3）
- `currency` 币种
- `unit` 数值单位（例 million_rmb / billion_rmb）

### B. 收入与增长字段

- `revenue` 营业收入
- `revenue_yoy` 营业收入同比增速
- `revenue_qoq` 营业收入环比增速
- `core_business_revenue` 核心业务收入
- `supply_chain_revenue` 一体化供应链收入
- `external_customer_revenue` 外部客户收入
- `other_revenue` 其他收入
- `revenue_growth_quality_note` 收入增长质量备注

### C. 利润与盈利能力字段

- `gross_profit` 毛利润
- `gross_margin` 毛利率
- `operating_profit` 营业利润
- `operating_margin` 营业利润率
- `net_profit` 净利润
- `net_profit_yoy` 净利润同比增速
- `net_profit_qoq` 净利润环比增速
- `net_margin` 净利率
- `adj_net_profit` 经调整净利润
- `adj_net_profit_yoy` 经调整净利润同比增速
- `ebitda` 息税折旧摊销前利润
- `ebitda_margin` EBITDA 利润率
- `adj_ebitda` 经调整 EBITDA
- `adj_ebitda_margin` 经调整 EBITDA 利润率
- `profit_quality_note` 利润质量备注

### D. 现金流与资本开支字段

- `operating_cash_flow` 经营活动现金流
- `investing_cash_flow` 投资活动现金流
- `financing_cash_flow` 融资活动现金流
- `free_cash_flow` 自由现金流
- `capex` 资本开支
- `cash_and_equivalents` 现金及现金等价物
- `restricted_cash` 受限资金
- `cash_flow_quality_note` 现金流质量备注

### E. 资产负债结构字段

- `total_assets` 总资产
- `total_liabilities` 总负债
- `total_equity` 股东权益
- `current_assets` 流动资产
- `current_liabilities` 流动负债
- `interest_bearing_debt` 有息负债
- `net_cash` 净现金
- `debt_to_asset_ratio` 资产负债率
- `balance_sheet_quality_note` 资产负债表质量备注

### F. 运营效率字段

- `inventory` 存货
- `inventory_turnover_days` 存货周转天数
- `accounts_receivable` 应收账款
- `accounts_receivable_turnover_days` 应收周转天数
- `accounts_payable` 应付账款
- `accounts_payable_turnover_days` 应付周转天数
- `working_capital` 营运资本
- `working_capital_change` 营运资本变化
- `efficiency_note` 运营效率备注

### G. 业务结构与经营规模字段

- `integrated_supply_chain_clients` 一体化供应链客户数量
- `warehouse_count` 仓库数量
- `warehouse_area` 仓储面积
- `cloud_warehouse_count` 云仓数量
- `county_coverage_ratio` 区县覆盖率
- `delivery_network_note` 配送网络备注
- `fulfillment_scale_note` 履约规模备注

### H. 市场与估值辅助字段

- `market_cap` 总市值（公告日附近）
- `ps_ttm` 市销率TTM
- `pe_ttm` 市盈率TTM
- `pb` 市净率
- `ev_to_ebitda` EV/EBITDA
- `valuation_note` 估值备注

### I. 事件与管理层备注字段

- `major_event_flag` 重大事件标记
- `major_event_type` 重大事件类型
- `major_event_note` 重大事件说明
- `management_guidance` 管理层指引摘要
- `guidance_change_flag` 指引变化标记
- `guidance_note` 指引说明

### J. 数据治理字段

- `source_type` 来源类型（hkex_announcement / annual_report / interim_report）
- `source_url` 源文件链接
- `source_title` 源公告标题
- `ingest_time` 入库时间
- `data_version` 数据版本
- `quality_flag` 质量标记（PASS / REVIEW / ERROR）
- `quality_note` 质量说明
- `is_manual_verified` 是否人工核验
- `verified_by` 核验人
- `verified_time` 核验时间

---

## 五、缺失值策略（V1）

- 关键字段必须结构化，不能只写在 note 里。
- 未披露字段允许空，但必须在 `quality_note` 说明“未披露”。
- 质量标记必须可追溯：源头 + 入库时间 + 人工核验信息。

---

## 六、推荐公式口径（V1）

- `gross_margin` = gross_profit / revenue
- `operating_margin` = operating_profit / revenue
- `net_margin` = net_profit / revenue
- `ebitda_margin` = ebitda / revenue
- `debt_to_asset_ratio` = total_liabilities / total_assets
- `net_cash` = cash_and_equivalents - interest_bearing_debt
- `free_cash_flow` = operating_cash_flow - capex

---
