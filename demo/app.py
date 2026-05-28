"""Run the housing demo baseline pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from src.data_pipeline import engineer_features, load_and_merge, split_by_property
from src.evaluate import compute_metrics, subgroup_auroc_gaps_reference, subgroup_auroc_scores
from src.evidence import (
    aggregate_dataset_audit,
    compute_equity_view,
    compute_leakage_view,
    compute_mnar_view,
    compute_sensor_quality_view,
)
from src.models.model_a import build_model_a
from src.models.model_b import build_model_b
from src.models.model_c import build_model_c


FEATURES = [
    "avgTemperature",
    "avgHumidity",
    "co2_imputed",
    "co2_missing",
    "smart_meter_kwh",
    "noise_db",
    "lag_temp",
    "day_of_week",
    "is_flat",
]


def generate_demo_outputs():
    root = Path(__file__).resolve().parent
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    metrics_dir = root / "saved_metrics"
    models_dir = root / "saved_models"

    processed_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    merged_df = load_and_merge(raw_dir)
    evidence_df = merged_df.copy()
    evidence_df["cold_risk"] = (evidence_df["avgTemperature"] < 19.0).astype(int)

    df = engineer_features(merged_df)
    train_df, test_df = split_by_property(df, test_size=0.25, seed=42)

    train_df.to_csv(processed_dir / "train_features.csv", index=False)
    test_df.to_csv(processed_dir / "test_features.csv", index=False)

    X_train = train_df[FEATURES]
    y_train = train_df["cold_risk"]
    X_test = test_df[FEATURES]
    y_test = test_df["cold_risk"]

    models = {
        "Model A Logistic Baseline": build_model_a(),
        "Model B RandomForest Baseline": build_model_b(),
        "Model C GradientBoosting Baseline": build_model_c(),
    }

    metric_rows_train = []
    metric_rows_test = []
    model_results = []
    equity_rows = []
    thresholds = [0.3, 0.5, 0.7]
    threshold_counts = {str(t): 0 for t in thresholds}

    for model_name, model in models.items():
        model.fit(X_train, y_train)
        y_prob_train = model.predict_proba(X_train)[:, 1]
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics_train = compute_metrics(y_train, y_prob_train, threshold=0.5)
        metrics_train["n_properties"] = int(train_df["reference"].nunique())
        metrics_test = compute_metrics(y_test, y_prob, threshold=0.5)
        metrics_test["n_properties"] = int(test_df["reference"].nunique())

        subgroup_scores = subgroup_auroc_scores(test_df, y_prob, subgroup_col="property_type")
        subgroup_gaps = subgroup_auroc_gaps_reference(subgroup_scores, reference_group="terraced")
        model_results.append({"name": model_name, "metrics": metrics_test, "subgroup_gaps": subgroup_gaps})

        metric_rows_train.append({"model": model_name, "split": "train", **metrics_train})
        metric_rows_test.append({"model": model_name, "split": "test", **metrics_test})

        for group, score in subgroup_scores.items():
            equity_rows.append(
                {
                    "model": model_name,
                    "group": group,
                    "auroc": 0.0 if pd.isna(score) else float(score),
                    "gap_vs_terraced": float(subgroup_gaps.get(group, 0.0)),
                }
            )

        for t in thresholds:
            threshold_counts[str(t)] += int((y_prob >= t).sum())

        model_file = model_name.lower().replace(" ", "_").replace("-", "_") + ".joblib"
        joblib.dump(model, models_dir / model_file)

    train_metrics_df = pd.DataFrame(metric_rows_train)
    test_metrics_df = pd.DataFrame(metric_rows_test)
    equity_df = pd.DataFrame(equity_rows)
    train_metrics_df.to_csv(metrics_dir / "training_metrics.csv", index=False)
    test_metrics_df.to_csv(metrics_dir / "evaluation_metrics.csv", index=False)
    equity_df.to_csv(metrics_dir / "subgroup_equity.csv", index=False)

    sensor_quality_view = compute_sensor_quality_view(evidence_df)
    mnar_view = compute_mnar_view(evidence_df)
    leakage_view = compute_leakage_view(train_df, test_df)
    equity_view = compute_equity_view(equity_rows)
    dataset_audit = aggregate_dataset_audit(
        sensor_quality_verdict=sensor_quality_view["verdict"],
        split_integrity_verdict=leakage_view["verdict"],
        equity_verdict=equity_view["verdict"],
    )
    evidence_dashboard = {
        "sensor_data_quality": sensor_quality_view,
        "mnar_analysis": mnar_view,
        "subgroup_equity": equity_view,
        "leakage_audit": leakage_view,
        "dataset_audit": {
            "data_quality": dataset_audit.data_quality,
            "split_integrity": dataset_audit.split_integrity,
            "equity": dataset_audit.equity,
            "overall_verdict": dataset_audit.overall,
        },
    }
    (metrics_dir / "evidence_dashboard.json").write_text(
        json.dumps(evidence_dashboard, indent=2), encoding="utf-8"
    )

    model_payload = {
        "model_results": model_results,
        "threshold_counts": threshold_counts,
    }
    (metrics_dir / "model_results.json").write_text(
        json.dumps(model_payload, indent=2), encoding="utf-8"
    )

    return {
        "merged_rows": len(df),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "metrics_dir": str(metrics_dir),
        "models_dir": str(models_dir),
        "evidence_dashboard_path": str(metrics_dir / "evidence_dashboard.json"),
    }


def run():
    result = generate_demo_outputs()
    print("Demo pipeline complete.")
    print(
        f"Merged rows: {result['merged_rows']} | train rows: {result['train_rows']} | "
        f"test rows: {result['test_rows']}"
    )
    print("Saved metrics, evidence dashboard outputs, and model artifacts.")


if __name__ == "__main__":
    run()
