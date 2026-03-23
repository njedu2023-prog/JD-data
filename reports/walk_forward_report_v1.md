# Walk-forward Report v1

- report_version: walk_forward_report_v1
- built_at: 2026-03-23T11:37:43.740579Z

## Data & version

- dataset: data_model/02618.HK/model_dataset.csv
- rows: 1182
- asof_date: 2021-05-28
- asof_date_end: 2026-03-19
- feature_version: ['model_features_v2.1']
- feature_cols: 100

## Walk-forward params

- min_train: 500
- test_size: 60
- step: 60
- folds: 11

## Regression (y_ret_1d)

| model | MAE_mean | RMSE_mean | IC_mean |
|---|---:|---:|---:|
| random_walk | 0.020080 | 0.027508 | 0.000000 |
| ridge | 0.025366 | 0.034290 | 0.010963 |

## Classification (y_up_1d)

| model | ACC_mean | F1_mean | ROC_AUC_mean | Brier_mean |
|---|---:|---:|---:|---:|
| majority | 0.521212 | 0.000000 | 0.500000 | 0.250369 |
| logistic | 0.521212 | 0.333800 | 0.527158 | 0.295074 |
