# 《JD-data 接入规范 V1》

## 一、文档定位

本文档用于统一约束 JD-data 仓库后续新增标的、指数、日历、代理层与市场基准数据时的接入方式、字段规则、文件路径、验收顺序与禁止事项。

本文档不是模型文档，不讨论预测，不讨论训练，不讨论收益，不讨论交易执行。

本文档只服务一个目标：

**把 JD-data 持续建设为可训练、可回放、可审计、字段完整、结构稳定、可整仓刷新、可整仓验收的正式源数据仓底座。**

---

## 二、当前仓库目标与边界

### 1. 当前主线目标

JD-data 当前主线不是做模型，而是先把底层源数据仓建设完整。

当前阶段重点包括：

- 数据能稳定抓取
- raw / clean 严格分层
- clean 主表字段统一
- refresh_log 留痕统一
- workflow 可自动刷新
- validate 可自动验收
- README 与真实目录同步
- 整仓可刷新、整仓可验收、整仓可维护

### 2. 当前阶段明确不做

当前阶段严禁跑偏到以下方向：

- 不切模型主线
- 不讨论预测精度
- 不讨论交易收益
- 不进入特征层
- 不进入训练层
- 不进入回测层
- 不在脏表上缝补
- 不把 raw 和 clean 混成一张表
- 不让文档与真实仓库状态脱节

---

## 三、接入对象分类

JD-data 当前允许接入的对象，按职责划分为以下几类。

### 1. 单票主标的

用于承载核心研究对象本身的正式历史数据。

例如：

- 京东物流 `02618.HK`

### 2. 代理层标的

用于描述核心标的所处的平台、竞争、生态、履约、消费或行业环境。

例如：

- 京东集团 `9618.HK`
- 美团 `3690.HK`
- 阿里巴巴 `9988.HK`

### 3. 市场基准

用于描述整体市场、风格、风险环境。

例如：

- 恒生指数 `HSI`
- 恒生科技指数 `HKTECH`
- 恒生中国企业指数 `HSCEI`

### 4. 交易日历

用于提供统一时间轴与交易日判定基准。

例如：

- 港股交易日历 `HK_CALENDAR`

---

## 四、接入新对象时的总原则

新增任何一个对象，必须遵守以下原则。

### 1. 先 raw，后 clean

上游原始口径先落 raw。

标准化后的正式主表落 clean。

不得省略 raw 层直接写 clean。

### 2. clean 是正式主表

clean 层不是原始缓存，不是半成品，不是随便堆字段的脏表。

clean 层必须是正式可消费、可验证、可追踪的主表。

### 3. 一个对象一条完整链路

每新增一个对象，必须完整补齐：

- 抓取脚本
- raw 文件
- clean 文件
- refresh_log 留痕
- 单线 workflow
- 仓库级 validate
- 整仓总线
- README 文档

只做其中一部分，视为未完成接入。

### 4. 先单线验收，再纳入总闸门

新增对象时，必须先走：

1. 新增抓取脚本
2. 新增单线 workflow
3. 单线手动跑通
4. 确认 raw / clean / refresh_log 真实落地
5. 再纳入 validate_repository.py
6. 再纳入 refresh_all_and_validate.yml
7. 最后同步 README

禁止反过来先改 validate，再去补数据文件。

### 5. 文档必须同步

每次正式接入完成后，README 必须同步更新。

不能出现：

- 仓库里已经有数据，README 还没写
- README 写了，实际文件还不存在
- workflow 已接入，但文档未体现

---

## 五、标准目录规范

新增对象时，必须遵守以下路径规范。

### 1. 股票 / 单票 / 代理层

raw 路径：

`data_raw/<SYMBOL>/hk_daily_raw.csv`

clean 路径：

`data_clean/<SYMBOL>/daily_clean.csv`

示例：

- `data_raw/02618.HK/hk_daily_raw.csv`
- `data_clean/02618.HK/daily_clean.csv`
- `data_raw/9618.HK/hk_daily_raw.csv`
- `data_clean/9618.HK/daily_clean.csv`
- `data_raw/3690.HK/hk_daily_raw.csv`
- `data_clean/3690.HK/daily_clean.csv`
- `data_raw/9988.HK/hk_daily_raw.csv`
- `data_clean/9988.HK/daily_clean.csv`

### 2. 指数

raw 路径：

`data_raw/<INDEX_SYMBOL>/<index_name>_raw.csv`

clean 路径：

`data_clean/<INDEX_SYMBOL>/<index_name>_clean.csv`

示例：

- `data_raw/HSI/hsi_raw.csv`
- `data_clean/HSI/hsi_clean.csv`
- `data_raw/HKTECH/hktech_raw.csv`
- `data_clean/HKTECH/hktech_clean.csv`
- `data_raw/HSCEI/hscei_raw.csv`
- `data_clean/HSCEI/hscei_clean.csv`

### 3. 交易日历

路径：

`calendar/hk_trade_calendar.csv`

### 4. 刷新日志

路径：

`refresh_log/refresh_log.csv`

### 5. 脚本目录

路径：

`scripts/`

### 6. workflow 目录

路径：

`.github/workflows/`

---

## 六、clean 主表字段契约

### 1. 股票 / 单票 / 代理层 clean 主表标准字段

以下字段为正式标准字段：

- `symbol`
- `market`
- `asset_type`
- `trade_date`
- `open`
- `high`
- `low`
- `close`
- `prev_close`
- `volume`
- `amount`
- `pct_change`
- `ret_1d`
- `log_ret_1d`
- `quality_flag`
- `ingest_time`
- `data_version`

### 2. 字段含义

#### `symbol`
仓库统一识别符号。

示例：

- `02618.HK`
- `9618.HK`
- `3690.HK`
- `9988.HK`

#### `market`
市场标识。

港股统一为：

- `HK`

#### `asset_type`
资产类型。

股票统一为：

- `equity`

指数统一为：

- `index`

#### `trade_date`
正式交易日期，clean 层统一使用日期字符串，格式为：

- `YYYY-MM-DD`

#### `open / high / low / close`
当日 OHLC 价格字段。

#### `prev_close`
前收盘价。

若首行历史数据无 `prev_close`，允许在 raw 存在，但不得进入正式 clean 主表。

#### `volume`
成交量。

#### `amount`
成交额。

#### `pct_change`
简单收益率，定义为：

`close / prev_close - 1`

#### `ret_1d`
当前与 `pct_change` 保持同口径。

#### `log_ret_1d`
对数收益率。

#### `quality_flag`
质量闸门结果。

当前正式合法值只允许：

- `PASS`

出现 `FAIL` 的行不得进入正式可通过验收的 clean 主表。

#### `ingest_time`
本次写入时间，使用 UTC ISO 格式。

#### `data_version`
本次写入版本号，当前采用日版本形式。

---

## 七、raw 表规范

### 1. raw 的职责

raw 层用于保留上游原始抓取口径，不承担最终消费责任。

raw 的目标是：

- 便于追溯
- 便于排查
- 便于重建 clean
- 保留上游字段形态

### 2. raw 禁止事项

- 禁止把 raw 当最终主表消费
- 禁止在 raw 中做过度业务加工
- 禁止把 clean 字段回写成 raw
- 禁止删掉对后续追溯有价值的上游原始字段

---

## 八、refresh_log 契约

refresh_log 路径固定为：

`refresh_log/refresh_log.csv`

### 1. 标准字段

- `refresh_time`
- `source`
- `symbol`
- `rows_raw`
- `rows_clean`
- `rows_fail`
- `status`
- `message`

### 2. 字段说明

#### `refresh_time`
本次刷新时间，统一采用 UTC ISO 字符串。

#### `source`
本次数据来源。

示例：

- `tushare.hk_daily`
- `tushare.index_global`
- `tushare.hk_trade_calendar`
- `yfinance.^HSCE`

#### `symbol`
本次刷新的对象标识。

示例：

- `02618.HK`
- `9618.HK`
- `3690.HK`
- `9988.HK`
- `HK_CALENDAR`
- `HSI`
- `HKTECH`
- `HSCEI`

#### `rows_raw`
本次 raw 输出行数。

#### `rows_clean`
本次 clean 输出行数。

#### `rows_fail`
本次质量失败行数。

#### `status`
当前允许的典型值包括：

- `success`
- `empty`
- `error`

#### `message`
本次刷新结果说明。

### 3. refresh_log 原则

- 每次刷新必须落日志
- 成功失败都要留痕
- 不允许静默失败
- 不允许混用旧版列名与新版列名
- refresh_log 必须长期维持统一 schema

---

## 九、单线接入标准步骤

新增一个对象时，必须严格按以下顺序执行。

### 第一步：新增抓取脚本

在 `scripts/` 下新增抓取脚本。

命名应与对象职责对应，保持清晰可读。

例如：

- `fetch_alibaba_daily.py`

### 第二步：定义 raw / clean 路径

脚本中明确：

- raw 输出路径
- clean 输出路径
- refresh_log 路径
- symbol / market / asset_type
- 起始日期
- 数据源

### 第三步：脚本内完成 clean 校验

脚本中必须对正式 clean 主表做基本质量验证，包括：

- 非空
- 必需字段非空
- 日期去重
- 日期升序
- `symbol` 正确
- `market` 正确
- `asset_type` 正确
- `quality_flag` 不得出现 `FAIL`

### 第四步：新增单线 workflow

在 `.github/workflows/` 下新增对应 workflow。

例如：

- `fetch_alibaba_daily.yml`

### 第五步：手动跑通单线 workflow

这一步必须真实执行，不可跳过。

必须确认三类产物真实出现：

- raw 文件
- clean 文件
- refresh_log 新增对应 symbol 记录

### 第六步：验收单线产物

至少验收以下内容：

- raw 是否非空
- clean 是否非空
- `symbol / market / asset_type` 是否正确
- `trade_date` 是否升序
- `quality_flag` 是否全 PASS
- refresh_log 是否 success

### 第七步：纳入仓库级 validate

确认单线真实通过后，再修改：

- `scripts/validate_repository.py`

将新对象加入：

- `REQUIRED_FILES`
- `check_refresh_log()` 必备 symbol
- `main()` 中的正式校验链路

### 第八步：纳入整仓总线

修改：

- `.github/workflows/refresh_all_and_validate.yml`

新增：

- 运行该对象抓取脚本
- `git add` 该对象 raw / clean
- 保证最后统一执行 `validate_repository.py`

### 第九步：同步 README

README 必须补齐：

- 新对象职责说明
- 仓库结构路径
- 自动化能力说明
- 正式结论中的对象范围

---

## 十、仓库级验收标准

仓库级正式验收至少包括以下内容。

### 1. 文件存在性

关键 raw / clean / calendar / refresh_log / latest 文件必须存在。

### 2. clean 主表质量

必须通过：

- 非空
- 必需字段非空
- 日期不重复
- 日期升序
- 身份字段正确
- `quality_flag` 全 PASS

### 3. refresh_log 结构正确

必须通过：

- 字段完整
- 非空
- 关键 symbol 齐全
- status / rows / message 正常

### 4. workflow 跑通

必须至少确认：

- 单线 workflow 跑通
- 整仓总线 workflow 跑通
- validate workflow 跑通

### 5. README 同步

README 必须与真实仓库状态一致。

---

## 十一、当前仓库级接入清单

截至 V1，当前已正式纳入仓库级体系的对象包括：

### 单票主标的
- `02618.HK`

### 代理层
- `9618.HK`
- `3690.HK`
- `9988.HK`

### 交易日历
- `HK_CALENDAR`

### 市场基准
- `HSI`
- `HKTECH`
- `HSCEI`

---

## 十二、禁止事项

后续任何人新增对象时，禁止出现以下做法。

### 1. 先改 validate，再补数据
这是高风险错误。

正确顺序必须是：

先单线真实落地，再纳入 validate。

### 2. 只写脚本，不写 workflow
这不算正式接入。

### 3. 只写 workflow，不做 refresh_log 留痕
这不算正式接入。

### 4. 只生成 raw，不生成 clean
这不算正式接入。

### 5. clean 字段随意变化
clean 主表字段必须受契约约束，不得随意漂移。

### 6. README 不同步
代码与文档脱节，视为未正式收口。

### 7. 在已有脏表上局部缝补
若结构不对，应重建，不应继续在脏结构上加补丁。

### 8. 把 raw 和 clean 混回一张表
这条必须长期锁死。

---

## 十三、下一阶段执行建议

在当前 V1 规范建立后，下一阶段建议按以下顺序推进：

### 第一优先级
继续补未来特征层真正会消费的环境型代理层或市场基准。

### 第二优先级
继续强化 schema / contract 文档，把当前隐含规则显式化。

### 第三优先级
仅在底座持续稳定后，再进入：

- 特征层
- 标签层
- 训练层
- 回测层
- 预测层

---

## 十四、当前一句话结论

JD-data 的新增对象接入，不是“多抓一张表”，而是：

**把一个新对象完整纳入 raw / clean / refresh_log / workflow / validate / 总线 / README 的正式仓库级体系。**

只有完成这一整条链，才算正式接入成功。
