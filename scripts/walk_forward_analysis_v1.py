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
    # drop nans
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


def main():
    data = json.loads(IN_JSON.read_text())
    folds = data.get("folds", [])

    weights = []
    for f in folds:
        meta = f.get("meta", {})
        w = meta.get("test_size")
        if w is None:
            w = meta.get("test_rows")
        if w is None:
            w = f.get("test_size")
        if w is None:
            w = 1
        weights.append(w)

    reg_metric_names = ["mae", "rmse", "ic"]
    reg_model = {m: [] for m in reg_metric_names}
    reg_base = {m: [] for m in reg_metric_names}

    cls_metric_names = ["accuracy", "f1", "roc_auc", "brier"]
    cls_model = {m: [] for m in cls_metric_names}
    cls_base = {m: [] for m in cls_metric_names}

    for f in folds:
        reg = f.get("regression", {})
        ridge = reg.get("ridge", {})
        rw = reg.get("random_walk", {})
        reg_model["mae"].append(ridge.get("MAE") or ridge.get("mae"))
        reg_model["rmse"].append(ridge.get("RMSE") or ridge.get("rmse"))
        reg_model["ic"].append(ridge.get("IC") or ridge.get("ic"))

        reg_base["mae"].append(rw.get("MAE") or rw.get("mae"))
        reg_base["rmse"].append(rw.get("RMSE") or rw.get("rmse"))
        reg_base["ic"].append(rw.get("IC") or rw.get("ic"))

        cls = f.get("classification", {})
        lg = cls.get("logistic", {})
        maj = cls.get("majority", {})
        for m in cls_metric_names:
            cls_model[m].append(lg.get(m))
            cls_base[m].append(maj.get(m))

    analysis = {
        "analysis_version": "walk_forward_analysis_v1",
        "built_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "meta": {
            "folds": len(folds),
            "weights": weights,
        },
        "regression": {
            "weighted": {
                m: {
                    "ridge": weighted_mean(reg_model[m], weights),
                    "random_walk": weighted_mean(reg_base[m], weights),
                }
                for m in reg_metric_names
            },
            "pvalues": {m: safe_wilcoxon(reg_model[m], reg_base[m]) for m in reg_metric_names},
        },
        "classification": {
            "weighted": {
                m: {
                    "logistic": weighted_mean(cls_model[m], weights),
                    "majority": weighted_mean(cls_base[m], weights),
                }
                for m in cls_metric_names
            },
            "pvalues": {m: safe_wilcoxon(cls_model[m], cls_base[m]) for m in cls_metric_names},
        },
    }

    def fmt(x):
        return "None" if x is None else f"{x:.6f}"

    md_lines = []
    md_lines.append("# Walk-forward 分析 v1")
    md_lines.append("")
    md_lines.append(f"- built_at: {analysis['built_at']}")
    md_lines.append(f"- folds: {len(folds)}")
    md_lines.append("")

    md_lines.append("## 回归（Ridge vs Random walk）")
    md_lines.append("")
    md_lines.append("|metric|ridge (weighted)|random_walk (weighted)|p-value (ridge<base)|结论|")
    md_lines.append("|---|---:|---:|---:|---|")
    for m in reg_metric_names:
        pv = analysis["regression"]["pvalues"][m]
        if pv is None:
            concl = "无法检验"
        elif pv < 0.05:
            concl = "显著弱于基线"
            #: noqa
        else:
            concl = "未显著弱于基线"
        md_lines.append(
            f"|{m}|{fmt(analysis['regression']['weighted'][m]['ridge'])}|"
            f"{fmt(analysis['regression']['weighted'][m]['random_walk'])}|{fmt(pv)}|{concl}|"
        )

    md_lines.append("")
    md_lines.append("## 分类（Logistic vs Majority）")
    md_lines.append("")
    md_lines.append("|metric|logistic (weighted)|majority (weighted)|p-value (logistic<base)|结论|")
    md_lines.append("|---|---:|---:|---:|---|")
    for m in cls_metric_names:
        pv = analysis["classification"]["pvalues"][m]
        if pv is None:
            concl = "无法检验"
        elif pv < 0.05:
            concl = "显著弱于基线"
        else:
            concl = "未显著弱于基线"
        md_lines.append(
            f"|{m}|{fmt(analysis['classification']['weighted'][m]['logistic'])}|"
            f"{fmt(analysis['classification']['weighted'][m]['majority'])}|{fmt(pv)}|{concl}|"
        )

    OUT_JSON.write_text(json.dumps(analysis, ensure_ascii=False, indent=2))
    OUT_MD.write_text("\n".join(md_lines))


if __name__ == "__main__":
    main()
