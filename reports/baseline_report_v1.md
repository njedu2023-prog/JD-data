# baseline_report_v1

生成时间: 2026-03-23T11:00:40Z
数据版本:
- model_features_v2.1
- data_model/02618.HK/model_dataset.csv

输入:
- data_model/02618.HK/baseline_model_v1.json
- data_model/02618.HK/baseline_eval_v1.json

## 回归任务 (y_ret_1d)
- train/test rows: 945 / 237
- benchmark_random_walk: MAE=0.017457, RMSE=0.027302, IC=0.000000
- ridge: MAE=0.018374, RMSE=0.027702, IC=0.015784

## 分类任务 (y_up_1d)
- train/test rows: 945 / 237
- benchmark_majority: accuracy=0.513102, f1=0.404292, roc_auc=0.500000, brier=0.249603
- logistic: accuracy=0.557296, f1=0.557296, roc_auc=0.589936, brier=0.243120

## baseline_eval_v1 校验
- built_at: 2026-03-23T10:33:18Z
- random_walk: MAE=0.017457, RMSE=0.027302, IC=0.000000
