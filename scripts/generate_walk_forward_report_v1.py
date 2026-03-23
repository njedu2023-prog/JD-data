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
    eval_path = repo_root / "data_model" / "02618.HK" / "walk_forward_eval_v1.json"
    out_path = repo_root / "reports" / "walk_forward_report_v1.md"

    wf = load_json(eval_path)

    dataset = wf.get("dataset", {})
    params = wf.get("params", {})
    features = wf.get("features", {})

    reg = wf.get("regression", {})
    reg_summary = reg.get("summary", {})

    cls = wf.get("classification", {})
    cls_summary = cls.get("summary", {})

    folds = reg.get("folds", []) or cls.get("folds", []) or []

    report = f"""# Walk-forward Report v1

- report_version: walk_forward_report_v1
- built_at: {datetime.utcnow().isoformat()}Z

## Data & version

- dataset: {dataset.get('file', 'data_model/02618.HK/model_dataset.csv')}
- rows: {dataset.get('rows', '-')}
- asof_date: {dataset.get('asof_date_start', '-')}
- asof_date_end: {dataset.get('asof_date_end', '-')}
- feature_version: {dataset.get('build_version_unique', '-')}
- feature_cols: {features.get('count', '-')}

## Walk-forward params

- min_train: {params.get('min_train', '-')}
- test_size: {params.get('test_size', '-')}
- step: {params.get('step', '-')}
- folds: {len(folds)}

## Regression (y_ret_1d)

| model | MAE_mean | RMSE_mean | IC_mean |
|---|---:|---:|---:|
| random_walk | {fmt_metric(reg_summary.get('random_walk_mean', {}).get('mae'))} | {fmt_metric(reg_summary.get('random_walk_mean', {}).get('rmse'))} | {fmt_metric(reg_summary.get('random_walk_mean', {}).get('ic'))} |
| ridge | {fmt_metric(reg_summary.get('ridge_mean', {}).get('mae'))} | {fmt_metric(reg_summary.get('ridge_mean', {}).get('rmse'))} | {fmt_metric(reg_summary.get('ridge_mean', {}).get('ic'))} |

## Classification (y_up_1d)

| model | ACC_mean | F1_mean | ROC_AUC_mean | Brier_mean |
|---|---:|---:|---:|---:|
| majority | {fmt_metric(cls_summary.get('majority_mean', {}).get('accuracy'))} | {fmt_metric(cls_summary.get('majority_mean', {}).get('f1'))} | {fmt_metric(cls_summary.get('majority_mean', {}).get('roc_auc'))} | {fmt_metric(cls_summary.get('majority_mean', {}).get('brier'))} |
| logistic | {fmt_metric(cls_summary.get('logistic_mean', {}).get('accuracy'))} | {fmt_metric(cls_summary.get('logistic_mean', {}).get('f1'))} | {fmt_metric(cls_summary.get('logistic_mean', {}).get('roc_auc'))} | {fmt_metric(cls_summary.get('logistic_mean', {}).get('brier'))} |

"""

    out_path.write_text(report.strip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
