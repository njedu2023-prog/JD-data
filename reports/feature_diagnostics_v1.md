## feature diagnostics v1
built_at: 2026-03-23T17:22:00Z

dataset rows: 1184
feature count: 99

### top missing
- external_isc_customer_yoy: missing_rate=0.33361486486486486
- external_isc_arpc_yoy: missing_rate=0.33361486486486486
- receivables_loss_allowance_ratio: missing_rate=0.33192567567567566
- contract_assets: missing_rate=0.3302364864864865
- contract_assets_ratio: missing_rate=0.3302364864864865
- borrowings: missing_rate=0.125
- lease_liabilities: missing_rate=0.125
- free_cash_inflow: missing_rate=0.125
- capex_net: missing_rate=0.125
- net_cash: missing_rate=0.125

### top |corr| with y_ret_1d
- stock_close: corr=-0.06858914713578658
- ret_3690_1d: corr=0.062373975497903855
- stock_vol_5d: corr=0.049693477827286094
- stock_ret_1d: corr=0.04931670840118319
- ret_9988_5d: corr=-0.0488780952085889
- net_cash: corr=-0.048303246099315106
- ret_9618_1d: corr=0.04762992908069005
- revenue: corr=0.04604713795965355
- ret_2057_5d: corr=-0.04598131376165918
- current_liabilities: corr=0.04468186015988698

### top |corr| with y_up_1d
- stock_close: corr=-0.07211778789294568
- gross_margin: corr=0.04505458526181313
- operating_cash_flow: corr=0.043956473385782714
- missing_ratio: corr=-0.04381812775531364
- current_assets: corr=0.04370542742711887
- operating_cash_flow_margin: corr=0.04329887793484442
- hscei_ret_5d: corr=-0.04315517001094189
- trade_year: corr=0.04301291738299624
- stock_vol_5d: corr=0.04290969767534286
- hsi_ret_5d: corr=-0.04257658785603606
