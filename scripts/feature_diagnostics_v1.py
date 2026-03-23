import json
from datetime import datetime from pathlib import Path

import numpy as np
import pandas as pd

DATASET_PATH = "data_model/02618.HK/model_dataset.csv"


def get_features(df: pd.DataFrame) -> list[str]:
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
        "symbol",
        "asof_date",
        "fundamental_anchor_date",
        "fundamental_anchor_period_type",
        "fundamental_quality_flag",
        "fundamental_data_version",
        "row_quality_flag",
    }

    def is_meta(col: str) -> bool:
        if col in drop_cols:
            return True
        if col.startswith("y_"):
            return True
        if col.startswith("built_at"):
            return True
        if col.endswith("_flag"):
            return True
        if col.endswith("_version"):
            return True
        return False

    # remove columns that are entirely missing
    candidates = [c for c in df.columns if not is_meta(c)]
    features = [c for c in candidates if df[c].notna().sum() > 0]
    return features


def safe_corr(x: pd.Series, y: pd.Series) -> float | None:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return None
    return float(x[mask].corr(y[mask]))


def main():
    df = pd.read_csv(DATASET_PATH)

    features = get_features(df)
    df_feat = df[features].copy()

    y_ret = df.get("y_ret_1d")
    y_up = df.get("y_up_1d")

    rows = len(df)

    records = []
    for c in features:
        s = df_feat[c]
        missing_rate = float(s.isna().mean())
        nonfinite_rate = float((~np.isfinite(pd.to_numeric(s, errors="coerce"))).mean())
        arr = pd.to_numeric(s, errors="coerce")
        records.append(
            {
                "feature": c,
                "missing_rate": missing_rate,
                "nonfinite_rate": nonfinite_rate,
                "mean": float(arr.mean(skipna=True)) if arr.notna().any() else None,
                "std": float(arr.std(skipna=True)) if arr.notna().any() else None,
                "corr_y_ret_1d": safe_corr(arr, y_ret),
                "corr_y_up_1d": safe_corr(arr, y_up),
            }
        )

    top_missing = sorted(records, key=lambda r: r["missing_rate"], reverse=True)[:10]
    top_corr_ret = sorted(records, key=lambda r: abs(r["corr_y_ret_1d"] or 0), reverse=True)[:10]
    top_corr_up = sorted(records, key=lambda r: abs(r["corr_y_up_1d"] or 0), reverse=True)[:10]

    out = {
        "report_version": "feature_diagnostics_v1",
        "built_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "dataset": {"rows": rows, "features": len(features)},
        "top": {
            "missing_rate": [(r["feature"], r["missing_rate"]) for r in top_missing],
            "corr_y_ret_1d": [(r["feature"], r["corr_y_ret_1d"]) for r in top_corr_ret],
            "corr_y_up_1d": [(r["feature"], r["corr_y_up_1d"]) for r in top_corr_up],
        },
    }

    Path("data_model/02618.HK/feature_diagnostics_v1.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    md_lines = [
        "## feature diagnostics v1",
        f"built_at: {out['built_at']}",
        "",
        f"dataset rows: {rows}",
        f"feature count: {len(features)}",
        "",
        "### top missing",
    ]
    for f, v in out["top"]["missing_rate"]:
        md_lines.append(f"- {f}: missing_rate={v}")

    md_lines.append("")
    md_lines.append("### top |corr| with y_ret_1d")
    for f, v in out["top"]["corr_y_ret_1d"]:
        md_lines.append(f"- {f}: corr={v}")

    md_lines.append("")
    md_lines.append("### top |corr| with y_up_1d")
    for f, v in out["top"]["corr_y_up_1d"]:
        md_lines.append(f"- {f}: corr={v}")

    Path("reports/feature_diagnostics_v1.md").write_text("\n".join(md_lines) + "\n")


if __name__ == "__main__":
    main()
