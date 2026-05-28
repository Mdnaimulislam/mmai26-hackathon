"""Evidence Dashboard helpers for housing strand demo."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class EvidenceVerdicts:
    data_quality: str
    split_integrity: str
    equity: str
    overall: str


def compute_sensor_quality_view(df: pd.DataFrame) -> dict:
    rates = (
        df[
            [
                "avgTemperature",
                "avgHumidity",
                "avgCo2",
                "smart_meter_kwh",
                "noise_db",
                "survey_score",
            ]
        ]
        .isna()
        .mean()
        .to_dict()
    )
    max_missing = max(rates.values()) if rates else 0.0
    verdict = "CONDITIONAL" if max_missing >= 0.1 else "READY"
    return {
        "verdict": verdict,
        "missingness_rates": {k: float(v) for k, v in rates.items()},
        "max_missing_rate": float(max_missing),
    }


def compute_mnar_view(df: pd.DataFrame) -> dict:
    co2_dropout_by_property = df.groupby("reference")["avgCo2"].apply(lambda s: s.isna().mean())
    top_dropout = co2_dropout_by_property.sort_values(ascending=False).head(5)

    property_type_dropout = (
        df.groupby("property_type")["avgCo2"]
        .apply(lambda s: s.isna().mean())
        .sort_values(ascending=False)
        .to_dict()
    )
    cold_vs_warm_survey_missing = (
        df.groupby("cold_risk")["survey_score"]
        .apply(lambda s: s.isna().mean())
        .to_dict()
    )

    patterns = [
        {
            "name": "co2_dropout_concentrated_properties",
            "mechanism": "CO2 missingness clusters by property, indicating non-random sensor failure.",
            "evidence": top_dropout.to_dict(),
        },
        {
            "name": "survey_nonresponse_by_risk_state",
            "mechanism": "Survey missingness differs between cold-risk and non-cold-risk days.",
            "evidence": {
                "cold_risk_0_missing_rate": float(cold_vs_warm_survey_missing.get(0, np.nan)),
                "cold_risk_1_missing_rate": float(cold_vs_warm_survey_missing.get(1, np.nan)),
            },
        },
    ]

    return {
        "verdict": "CONDITIONAL",
        "patterns": patterns,
        "co2_dropout_by_property_top5": {k: float(v) for k, v in top_dropout.items()},
        "co2_dropout_by_property_type": {k: float(v) for k, v in property_type_dropout.items()},
    }


def compute_leakage_view(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    overlap = sorted(set(train_df["reference"]) & set(test_df["reference"]))
    return {
        "verdict": "READY" if not overlap else "NOT READY",
        "split_method": "property_level",
        "overlap_count": len(overlap),
        "overlap_references": overlap,
    }


def compute_equity_view(model_equity_rows: list[dict]) -> dict:
    abs_gaps = [abs(row.get("gap_vs_terraced", 0.0)) for row in model_equity_rows]
    max_abs_gap = max(abs_gaps) if abs_gaps else 0.0
    verdict = "CONDITIONAL" if max_abs_gap > 0.05 else "READY"
    return {
        "verdict": verdict,
        "max_abs_gap_vs_terraced": float(max_abs_gap),
        "rows": model_equity_rows,
    }


def aggregate_dataset_audit(
    sensor_quality_verdict: str,
    split_integrity_verdict: str,
    equity_verdict: str,
) -> EvidenceVerdicts:
    components = [sensor_quality_verdict, split_integrity_verdict, equity_verdict]
    if "NOT READY" in components:
        overall = "NOT READY"
    elif "CONDITIONAL" in components:
        overall = "CONDITIONAL"
    else:
        overall = "READY"
    return EvidenceVerdicts(
        data_quality=sensor_quality_verdict,
        split_integrity=split_integrity_verdict,
        equity=equity_verdict,
        overall=overall,
    )
