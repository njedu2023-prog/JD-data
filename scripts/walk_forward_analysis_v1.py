import json
from pathlib import Path
from datetime import datetime

import numpy as np
from scipy import stats

IN_JSON = Path("data_model/02618.HK/walk_forward_eval_v1.json")
OUT_JSON = Path("data_model/02618.HK/walk_forward_analysis_v1.json")
OUT_MD = Path("reports/walk_forward_analysis_v1.md")


def safe_wilcoxon(a, b):
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
        res = stats.wilcoxon(a, b, alternative="less")
    except Exception:
        return None
    return float(res.pvalue)


def weighted_mean(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)

    mask = np.isfinite(values) & np.isfinite(weights)
    values = values[mask]
    weights = weights[mask]
    if len(values) == 0 or weights.sum() <= 0:
        return None

    return float(np.average(values, weights=weights))


def extract_weights(data, folds):
    weights = []
    for f in folds:
        meta = f.get("meta", {})
        w = meta.get("test_rows")
        if w is None:
            w = meta.get("test_size")
        if w is None:
            w = data.get("params", {}).get("test_size")
        weights.append(float(w) if w is not None else np.nan)
    return weights


def get_metric_list(folds, model, metric):
    vals = []
    for f in folds:
        m = f.get("metrics", {}).get(model, {})
        vals.append(m.get(metric))
    return vals


def build_section(folds, weights, model, baseline, metrics):
    section = {}
    for m in metrics:
        vals_model = get_metric_list(folds, model, m)
        vals_base = get_metric_list(folds, baseline, m)
        section[m] = {
            "weighted_mean": weighted_mean(vals_model, weights),
            "baseline_weighted_mean": weighted_mean(vals_base, weights),
            "p_worse_than_baseline": safe_wilcoxon(vals_model, vals_base),
        }
    return section


def main():
    data = json.loads(IN_JSON.read_text())

    reg = data.get("regression", {})
    cls = data.get("classification", {})

    reg_folds = reg.get("folds", [])
    cls_folds = cls.get("folds", [])
    weights = extract_weights(data, reg_folds)

    regression = build_section(reg_folds, weights, "ridge", "random_walk", ["mae", "rmse", "ic"])
    classification = build_section(cls_folds, weights, "logistic", "majority", ["accuracy", "f1", "roc_auc", "brier"])

    out = {
        "report_version": "walk_forward_analysis_v1",
        "built_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "meta": {
            "folds": len(reg_folds),
            "weights": weights,
        },
        "regression": regression,
        "classification": classification,
    }

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    md_lines = [
        "## walk-forward analysis v1",
        f"built_at: {out['built_at']}",
        "",
        "### regression (ridge vs random walk)",
    ]
    for k, v in regression.items():
        md_lines.append(f"- {k}: {v}")

    md_lines.append("")
    md_lines.append("### classification (logistic vs majority)")
    for k, v in classification.items():
        md_lines.append(f"- {k}: {v}")

    OUT_MD.write_text("\n".join(md_lines) + "\n")


if __name__ == "__main__":
    main()
