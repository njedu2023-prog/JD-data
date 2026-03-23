import json
from datetime import datetime

import numpy as np
import pandas as pd


DATASET_PATH = "data_model/02618.HK/model_dataset.csv"


def _get_features(df: pd.DataFrame) -> list[str]:
    # Keep consistent with train_baseline_models_v3.
    drop_cols = {
        "date",
        "ticker",
        "index",
        "roll",
        "test_flag",
        "build_version",
        "returns",
        "benchmark",
        "HSI",
        "HSCEI",
        "HKTECH",
        "HSI_roll",
        "HSCEI_roll",
        "HKTECH_roll",
        "benchmark_roll",
    }
    features = [c for c in df.columns if not c.startswith("y_") and c not in drop_cols]
    return features


def _safe_corr(x: pd.Series, y: pd.Series) -> float | None:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return None
    return float(x[mask].corr(y[mask]))


def _yearly_corr_stability(df: pd.DataFrame, feat: str, target: str) -> dict:
    if "date" not in df.columns:
        return {"years": 0, "sign_changes": None, "year_corr": []}

    dfx = df[["date", feat, target]].copy()
    dfx["date"] = pd.to_datetime(dfx["date"], errors="coerce")
    dfx.dropna(subset=["date"], inplace=True)
    dfx["year"] = dfx["date"].dt.year

    per_year = []
    for y, g in dfx.groupby("year"):
        c = _safe_corr(g[feat], g[target])
        if c is not None:
            per_year.append((int(y), c))

    if not per_year:
        return {"years": 0, "sign_changes": None, "year_corr": []}

    per_year.sort(key=lambda t: t[0])
    corr_values = [c for _, c in per_year]
    signs = [np.sign(c) for c in corr_values]

    sign_changes = None
    if len(signs) >= 2:
        sign_changes = int(sum(int(a != b) for a, b in zip(signs, signs[1:])))

    return {
        "years": len(corr_values),
        "sign_changes": sign_changes,
        "year_corr": [{"year": y, "corr": float(c)} for y, c in per_year],
    }


def main():
    df = pd.read_csv(DATASET_PATH)
    features = _get_features(df)

    diagnostics = {}
    for feat in features:
        s = pd.to_numeric(df[feat], errors="coerce")
        miss_rate = float(s.isna().mean())
        nonfinite = float((~np.isfinite(s)).mean())

        diag = {
            "missing_rate": miss_rate,
            "nonfinite_rate": nonfinite,
            "mean": float(s.mean(skipna=True)) if miss_rate < 1 else None,
            "std": float(s.std(skipna=True)) if miss_rate < 1 else None,
            "min": float(s.min(skipna=True)) if miss_rate < 1 else None,
            "max": float(s.max(skipna=True)) if miss_rate < 1 else None,
            "corr_y_ret_1d": _safe_corr(s, df.get("y_ret_1d")),
            "corr_y_up_1d": _safe_corr(s, df.get("y_up_1d")),
        }

        diag["stability_ret"] = _yearly_corr_stability(df, feat, "y_ret_1d")
        diag["stability_up"] = _yearly_corr_stability(df, feat, "y_up_1d")

        diagnostics[feat] = diag

    def top_k(key, k=10, reverse=True, abs_value=False):
        items = []
        for feat, diag in diagnostics.items():
            v = diag.get(key)
            if v is None:
                continue
            val = abs(v) if abs_value else v
            items.append((feat, val, v))
        items.sort(key=lambda t: t[1], reverse=reverse)
        return items[:k]

    summary = {
        "report_version": "feature_diagnostics_v1",
        "built_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": {
            "rows": int(len(df)),
            "features": int(len(features)),
        },
        "top": {
            "missing_rate": top_k("missing_rate", reverse=True),
            "abs_corr_y_ret_1d": top_k("corr_y_ret_1d", reverse=True, abs_value=True),
            "abs_corr_y_up_1d": top_k("corr_y_up_1d", reverse=True, abs_value=True),
        },
    }

    output_json = {
        **summary,
        "diagnostics": diagnostics,
    }

    with open("data_model/02618.HK/feature_diagnostics_v1.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    # Lightweight markdown for quick review.
    lines = []
    lines.append("# Feature diagnostics v1")
    lines.append("")
    lines.append(f"生成时间：{summary['built_at']}")
    lines.append("")
    lines.append(f"数据：`{DATASET_PATH}` rows={summary['dataset']['rows']} features={summary['dataset']['features']}")
    lines.append("")
    lines.append("## Top missing rate")
    for feat, val, raw in summary["top"]["missing_rate"]:
        lines.append(f"- {feat}: missing_rate={raw:.6f}")

    lines.append("")
    lines.append("## Top abs corr with y_ret_1d")
    for feat, val, raw in summary["top"]["abs_corr_y_ret_1d"]:
        lines.append(f"- {feat}: corr={raw:.6f}")

    lines.append("")
    lines.append("## Top abs corr with y_up_1d")
    for feat, val, raw in summary["top"]["abs_corr_y_up_1d"]:
        lines.append(f"- {feat}: corr={raw:.6f}")
    lines.append("")

    with open("reports/feature_diagnostics_v1.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
