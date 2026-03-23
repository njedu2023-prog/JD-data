import json
from pathlib import Path
from datetime import datetime

import numpy as np
from scipy import stats

IN_JSON = Path("data_model/02618.HK/walk_forward_eval_v1.json")
OUT_JSON = Path("data_model/02618.HK/walk_forward_analysis_v1.json")
OUT_MD = Path("reports/walk_forward_analysis_v1.md")


def fold_weights(folds):
    if not folds:
        return np.array([], dtype=float)
    w = np.array([f.get("meta", {}).get("test_rows", 1) for f in folds], dtype=float)
    return w


def weighted_mean(vals, weights):
    v = np.asarray(vals, dtype=float)
    w = np.asarray(weights, dtype=float)
    mask = np.isfinite(v)
    if mask.sum() == 0:
        return None
    v = v[mask]
    w = w[mask]
    return float((w * v).sum() / w.sum())


def get_metric_vals(folds, model, metric):
    vals = []
    for f in folds:
        m = f.get("metrics", {}).get(model, {})
        vals.append(m.get(metric))
    return np.array(vals, dtype=float)


def safe_wilcoxon(a, b, alternative):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask]
    b = b[mask]
    if len(a) < 3:
        return None
    if np.allclose(a, b):
        return None
    try:
        res = stats.wilcoxon(a, b, alternative=alternative)
        return float(res.pvalue)
    except Exception:
        return None


def build_section(folds, weights, model, baseline, metrics):
    section = {}
    for m, alt in metrics:
        vals_model = get_metric_vals(folds, model, m)
        vals_base = get_metric_vals(folds, baseline, m)
        section[m] = {
            "weighted_mean": weighted_mean(vals_model, weights),
            "baseline_weighted_mean": weighted_mean(vals_base, weights),
            "p_worse_than_baseline": safe_wilcoxon(vals_model, vals_base, alternative=alt),
        }
    return section


def conclusion(p):
    if p is None:
        return "无法检验"
    if p < 0.05:
        return "显著更差"
    return "证据不足以证明更优"


def main():
    data = json.loads(IN_JSON.read_text())
    reg_folds = data.get("regression", {}).get("folds", [])
    cls_folds = data.get("classification", {}).get("folds", [])

    weights = fold_weights(reg_folds)

    out = {
        "analysis_version": "walk_forward_analysis_v1",
        "built_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "meta": {
            "folds": len(reg_folds),
            "weights": weights.tolist(),
        },
        "regression": {
            "weighted": build_section(
                reg_folds,
                weights,
                model="ridge",
                baseline="random_walk",
                metrics=[
                    ("mae", "greater"),  # MAE smaller is better; model worse => greater
                    ("rmse", "greater"),
                    ("ic", "less"),
                ],
            )
        },
        "classification": {
            "weighted": build_section(
                cls_folds,
                weights,
                model="logistic",
                baseline="majority",
                metrics=[
                    ("accuracy", "less"),
                    ("f1", "less"),
                    ("roc_auc", "less"),
                    ("brier", "greater"),  # Brier smaller is better
                ],
            )
        },
    }

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    md_lines = ["Walk-forward 分析 v1", "", f"* built_at: {out['built_at']}", f"* folds: {out['meta']['folds']}", "",]

    def add_table(title, metrics, section):
        md_lines.append(title)
        md_lines.append("")
        md_lines.append("|metric|model (weighted)|baseline (weighted)|p-value (model worse)|结论|")
        md_lines.append("|---|---:|---:|---:|---|")
        for m, _ in metrics:
            s = section[m]
            p = s["p_worse_than_baseline"]
            md_lines.append(
                f"|{m}|{s['weighted_mean']}|{s['baseline_weighted_mean']}|{p}|{conclusion(p)}|"
            )
        md_lines.append("")

    add_table("\u56de\u5f52 (Ridge vs Random walk)", [
        ("mae", "greater"),
        ("rmse", "greater"),
        ("ic", "less"),
    ], out["regression"]["weighted"])

    add_table("\u5206\u7c7b (Logistic vs Majority)", [
        ("accuracy", "less"),
        ("f1", "less"),
        ("roc_auc", "less"),
        ("brier", "greater"),
    ], out["classification"]["weighted"])

    OUT_MD.write_text("\n".join(md_lines))


if __name__ == "__main__":
    main()
