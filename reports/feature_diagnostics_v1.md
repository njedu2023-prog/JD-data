## feature diagnostics v1
built_at: 2026-03-23T15:43:38Z

dataset rows: 1183
feature count: 103

### top missing
- ret_1519_20d: missing_rate=0.5190194420963652
- ret_1519_5d: missing_rate=0.5063398140321217
- alpha_vs_1519_5d: missing_rate=0.5063398140321217
- ret_1519_1d: missing_rate=0.5029585798816568
- external_isc_customer_yoy: missing_rate=0.3338968723584108
- external_isc_arpc_yoy: missing_rate=0.3338968723584108
- receivables_loss_allowance_ratio: missing_rate=0.3322062552831784
- contract_assets: missing_rate=0.3305156382079459
- contract_assets_ratio: missing_rate=0.3305156382079459
- borrowings: missing_rate=0.12510566356720204

### top |corr| with y_ret_1d
- ret_1519_20d: corr=-0.0772687941774146
- stock_close: corr=-0.0687986128081322
- ret_3690_1d: corr=0.06196033369562811
- ret_9988_5d: corr=-0.04973204035205239
- stock_vol_5d: corr=0.04959900069094069
- net_cash: corr=-0.049453042979156286
- stock_ret_1d: corr=0.04898466748207832
- revenue: corr=0.0476493271510538
- ret_9618_1d: corr=0.04762992908069005
- current_liabilities: corr=0.04607848165758298

### top |corr| with y_up_1d
- stock_close: corr=-0.07235279605384594
- gross_margin: corr=0.04579982941324928
- missing_ratio: corr=-0.045489540707389683
- operating_cash_flow: corr=0.04469853100194069
- trade_year: corr=0.044565028578014414
- hscei_ret_5d: corr=-0.044318751137367364
- current_assets: corr=0.04402437095320067
- operating_cash_flow_margin: corr=0.043417280719565826
- gross_profit: corr=0.04319710756033432
- stock_vol_5d: corr=0.04307920074575286
