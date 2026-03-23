import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

DATASET_PATH = Path("data_model/02618.HK/model_dataset.csv")
OUTPUT_DIR = Path("data_model/02618.HK")
REPORT_FILE = OUTPUT_DIR / "baseline_eval_v1.json"


def main():
    df = pd.read_csv(DATASET_PATH)
    df = df.sort_values("asof_date")

    y = df["y_ret_1d"].astype(float).values
    y = y[~np.isnan(y)]

    report = {
        "report_version": "baseline_eval_v1",
        "built_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "regression": {
            "target": "y_ret_1d",
            "random_walk": {
                "MAE": float(np.mean(np.abs(y))),
                "RMSE": float(np.sqrt(np.mean(np.square(y)))),
                "IC": 0.0,
            },
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
