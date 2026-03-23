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


def fmt_metric(value, digits=6):
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

    baseline_model = load_json(baseline_model_path)
    baseline_eval = load_json(baseline_eval_path)

    report_lines = []
    report_lines.append("# baseline_report_v1")
    report_lines.append("")
    report_lines.append("生成时间: " + datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
    report_lines.append("输入:")
    report_lines.append(f"- baseline_model_v1.json: {baseline_model_path}")
    report_lines.append(f"- baseline_eval_v1.json: {baseline_eval_path} (可选)")
    report_lines.append("")

    report_lines.append("## 回归任务 (y_ret_1d)")
    reg = baseline_model.get("regression", {})
    report_lines.append("- RandomWalk MAE: " + fmt_metric(reg.get("random_walk_mae")))
    report_lines.append("- RandomWalk RMSE: " + fmt_metric(reg.get("random_walk_rmse")))
    report_lines.append("- Ridge MAE: " + fmt_metric(reg.get("ridge_mae")))
    report_lines.append("- Ridge RMSE: " + fmt_metric(reg.get("ridge_rmse")))
    report_lines.append("- IC: " + fmt_metric(reg.get("ic")))
    report_lines.append("")

    report_lines.append("## 分类任务 (y_up_1d)")
    cls = baseline_model.get("classification", {})
    report_lines.append("- Majority Acc: " + fmt_metric(cls.get("majority_acc")))
    report_lines.append("- Logistic Acc: " + fmt_metric(cls.get("logistic_acc")))
    report_lines.append("- Logistic F1: " + fmt_metric(cls.get("logistic_f1")))
    report_lines.append("- Logistic AUC: " + fmt_metric(cls.get("logistic_auc")))
    report_lines.append("- Logistic Brier: " + fmt_metric(cls.get("logistic_brier")))
    report_lines.append("")

    if baseline_eval:
        report_lines.append("## 补充: v2 baseline_eval (random_walk)")
        report_lines.append("这部分仅作为历史记录。")
        report_lines.append("- MAE: " + fmt_metric(baseline_eval.get("mae")))
        report_lines.append("- RMSE: " + fmt_metric(baseline_eval.get("rmse")))
        report_lines.append("")

    report_text = "\n".join(report_lines)

    output_path = repo_root / "reports" / "baseline_report_v1.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    print("[OK] write", output_path)


if __name__ == "__main__":
    main()
