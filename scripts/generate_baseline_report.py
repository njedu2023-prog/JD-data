import json
from datetime import datetime
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def fmt_metric(value, digits: int = 6):
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def main():
    repo_root = Path(__file__).resolve().parents[1]

    baseline_model_path = repo_root / "data_model" / "02618.HK" / "baseline_model_v1.json"
    baseline_eval_path = repo_root / "data_model" / "02618.HK" / "baseline_eval_v1.json"

    out_path = repo_root / "reports" / "baseline_report_v1.md"

    baseline_model = load_json(baseline_model_path)
    baseline_eval = load_json(baseline_eval_path)

    reg = baseline_model.get("regression", {})
    cls = baseline_model.get("classification", {})

    reg_meta = reg.get("meta", {})
    reg_metrics = reg.get("metrics", {})
    reg_benchmark = reg.get("benchmark_random_walk", {})

    cls_meta = cls.get("meta", {})
    cls_metrics = cls.get("metrics", {})
    cls_benchmark = cls.get("benchmark_majority", {})

    eval_reg = baseline_eval.get("regression", {}).get("random_walk", {})
    eval_cls = baseline_eval.get("classification", {})

    report = f"""# Baseline Report v1

- report_version: baseline_report_v1
- built_at: {datetime.utcnow().isoformat()}Z

## Data & version

- dataset: {baseline_model.get('dataset', {}).get('file', 'data_model/02618.HK/model_dataset.csv')}
- rows/train_rows/test_rows: {reg_meta.get('rows', '-')}/{reg_meta.get('train_rows', '-')}/{reg_meta.get('test_rows', '-')}
- feature_cols: {reg_meta.get('feature_cols', '-')}
- feature_version: {reg_meta.get('build_version_unique', '-')}

## Regression (target: {reg_meta.get('target', 'y_ret_1d')})

| model | MAE | RMSE | IC |
|---|---:|---:|---:|
| random_walk | {fmt_metric(reg_benchmark.get('mae'))} | {fmt_metric(reg_benchmark.get('rmse'))} | {fmt_metric(reg_benchmark.get('ic'))} |
| ridge | {fmt_metric(reg_metrics.get('mae'))} | {fmt_metric(reg_metrics.get('rmse'))} | {fmt_metric(reg_metrics.get('ic'))} |

## Classification (target: {cls_meta.get('target', 'y_up_1d')})

| model | ACC | F1 | ROC_AUC | Brier |
|---|---:|---:|---:|---:|
| majority | {fmt_metric(cls_benchmark.get('accuracy'))} | {fmt_metric(cls_benchmark.get('f1'))} | {fmt_metric(cls_benchmark.get('roc_auc'))} | {fmt_metric(cls_benchmark.get('brier'))} |
| logistic | {fmt_metric(cls_metrics.get('accuracy'))} | {fmt_metric(cls_metrics.get('f1'))} | {fmt_metric(cls_metrics.get('roc_auc'))} | {fmt_metric(cls_metrics.get('brier'))} |

- majority_class_train: {cls_meta.get('majority_class_train', '-')}
- majority_prob_train: {fmt_metric(cls_meta.get('majority_prob_train'))}

## Eval sanity (baseline_eval_v1.json)

- regression random_walk MAE: {fmt_metric(eval_reg.get('MAE'))}
- regression random_walk RMSE: {fmt_metric(eval_reg.get('RMSE'))}
- regression random_walk IC: {fmt_metric(eval_reg.get('IC'))}
- classification entries: {len(eval_cls)}

"""

    out_path.write_text(report.strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
