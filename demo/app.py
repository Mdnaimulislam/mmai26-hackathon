"""Run the clinical strand baseline pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.evaluate import compute_metrics, compute_subgroup_metrics, equity_gap
from models.model_a import ModelA

THRESHOLD = 0.35


def generate_demo_outputs():
    root = Path(__file__).resolve().parent
    data_dir = root / "data" / "processed"
    raw_dir = root / "data" / "raw"
    metrics_dir = root / "saved_metrics"
    models_dir = root / "saved_models"

    metrics_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(data_dir / "train.csv")
    test_df = pd.read_csv(data_dir / "test.csv")

    notes = pd.read_csv(raw_dir / "notes.csv") if (raw_dir / "notes.csv").exists() else pd.DataFrame()
    vitals = pd.read_csv(raw_dir / "vitals_series.csv") if (raw_dir / "vitals_series.csv").exists() else pd.DataFrame()

    train_pids = set(train_df["patient_id"])
    test_pids = set(test_df["patient_id"])
    train_notes = notes[notes["patient_id"].isin(train_pids)].reset_index(drop=True) if len(notes) else pd.DataFrame()
    test_notes = notes[notes["patient_id"].isin(test_pids)].reset_index(drop=True) if len(notes) else pd.DataFrame()
    train_vitals = vitals[vitals["patient_id"].isin(train_pids)].reset_index(drop=True) if len(vitals) else pd.DataFrame()
    test_vitals = vitals[vitals["patient_id"].isin(test_pids)].reset_index(drop=True) if len(vitals) else pd.DataFrame()

    model = ModelA()
    y_train = train_df["major_complication_30d"].values
    model.fit(train_df, y_train, notes_df=train_notes, vitals_df=train_vitals)
    joblib.dump(model, models_dir / "model_a.joblib")

    y_test = test_df["major_complication_30d"].values
    y_prob = model.predict_proba_full(test_df, test_notes, test_vitals)[:, 1]

    metrics = compute_metrics(y_test, y_prob, threshold=THRESHOLD, model_name="model_a")

    sub = compute_subgroup_metrics(test_df, y_prob, group_col="surgery_type", threshold=THRESHOLD)
    gapped = equity_gap(sub, reference_group="abdominal", metric="auroc")
    subgroup_gaps = {
        str(row["group_value"]): float(row.get("auroc_gap", 0.0))
        for _, row in gapped.iterrows()
    }

    clean_metrics = {k: v for k, v in metrics.items() if k not in ("model", "tp", "fp", "tn", "fn")}
    metrics_df = pd.DataFrame([{"model": "model_a", "split": "test", **clean_metrics}])
    metrics_df.to_csv(metrics_dir / "evaluation_metrics.csv", index=False)

    equity_rows = [
        {"model": "model_a", "group": g, "auroc_gap_vs_abdominal": v}
        for g, v in subgroup_gaps.items()
    ]
    pd.DataFrame(equity_rows).to_csv(metrics_dir / "subgroup_equity.csv", index=False)

    evidence_dashboard = {
        "metrics": clean_metrics,
        "subgroup_gaps": subgroup_gaps,
    }
    (metrics_dir / "evidence_dashboard.json").write_text(
        json.dumps(evidence_dashboard, indent=2), encoding="utf-8"
    )

    model_results = [
        {"name": "model_a", "metrics": {k: v for k, v in metrics.items() if k != "model"}, "subgroup_gaps": subgroup_gaps}
    ]
    (metrics_dir / "model_results.json").write_text(
        json.dumps({"model_results": model_results}, indent=2), encoding="utf-8"
    )

    return {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "metrics_dir": str(metrics_dir),
        "evidence_dashboard_path": str(metrics_dir / "evidence_dashboard.json"),
    }


def run():
    result = generate_demo_outputs()
    print("Demo pipeline complete.")
    print(f"Train rows: {result['train_rows']} | Test rows: {result['test_rows']}")
    print("Saved metrics and model artifacts.")


if __name__ == "__main__":
    run()
