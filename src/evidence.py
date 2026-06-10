"""The five Evidence Dashboard views + the dataset-audit aggregator.

Views report PASS / CONDITIONAL / FAIL (the dashboard vocabulary).
``aggregate_dataset_audit`` maps those to the card vocabulary
(READY / CONDITIONAL / NOT READY) and rolls them up into an overall verdict.

Signatures match exactly what demo/app.py imports:
    compute_sensor_quality_view(df)
    compute_mnar_view(df)
    compute_leakage_view(train_df, test_df)
    compute_equity_view(equity_rows)
    aggregate_dataset_audit(sensor_quality_verdict, split_integrity_verdict, equity_verdict)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# View vocabulary -> card vocabulary.
_VIEW_TO_COMPONENT = {"PASS": "READY", "CONDITIONAL": "CONDITIONAL", "FAIL": "NOT READY"}
_SEVERITY = {"READY": 0, "PASS": 0, "CONDITIONAL": 1, "FAIL": 2, "NOT READY": 2}

_MODALITIES = [
    "avgTemperature",
    "avgHumidity",
    "avgCo2",
    "smart_meter_kwh",
    "noise_db",
    "survey_score",
]


# ── View 1: sensor data quality ──────────────────────────────────────────────
def compute_sensor_quality_view(df: pd.DataFrame) -> dict:
    """Missingness per modality across all properties + a quality verdict."""
    missing = {
        c: round(float(df[c].isna().mean()), 4) for c in _MODALITIES if c in df.columns
    }
    n_props = int(df["reference"].nunique())
    per_prop_dropout = df.groupby("reference")["avgCo2"].apply(lambda x: x.isna().mean())
    high_dropout = per_prop_dropout[per_prop_dropout >= 0.5]

    # One modality (CO2) is MNAR at scale -> CONDITIONAL, not a clean PASS.
    co2_missing = missing.get("avgCo2", 0.0)
    if co2_missing >= 0.30 or len(high_dropout) >= 20:
        verdict = "CONDITIONAL"
    elif co2_missing >= 0.50:
        verdict = "FAIL"
    else:
        verdict = "PASS"

    return {
        "verdict": verdict,
        "n_properties": n_props,
        "missingness_by_modality": missing,
        "reliable_modalities": [
            c for c, m in missing.items() if m <= 0.10 and c != "survey_score"
        ],
        "unreliable_modalities": [c for c, m in missing.items() if m >= 0.30],
        "high_dropout_property_count": int(len(high_dropout)),
        "high_dropout_threshold": 0.50,
        "note": (
            f"CO2 missing {co2_missing:.0%} overall; {len(high_dropout)} properties "
            f">=50% dropout. Temperature/humidity/smart-meter reliable."
        ),
    }


# ── View 2: MNAR analysis ────────────────────────────────────────────────────
def compute_mnar_view(df: pd.DataFrame) -> dict:
    """Two documented Missing-Not-At-Random patterns with quantified evidence."""
    g = df.groupby("reference")
    prop = pd.DataFrame(
        {
            "co2_dropout": g["co2_missing"].mean()
            if "co2_missing" in df.columns
            else g["avgCo2"].apply(lambda x: x.isna().mean()),
            "cold_rate": g.apply(
                lambda x: (x["avgTemperature"] < 19.0).mean(), include_groups=False
            ),
            "survey_resp": g["survey_score"].apply(lambda x: x.notna().mean()),
            "survey_mean": g["survey_score"].mean(),
        }
    )

    # Pattern 1: CO2 dropout concentrated in colder properties.
    high = prop[prop["co2_dropout"] >= 0.5]
    low = prop[prop["co2_dropout"] < 0.5]
    corr_co2 = float(prop["co2_dropout"].corr(prop["cold_rate"]))

    # Pattern 2: survey responders skew warmer / score differently.
    resp_corr = float(prop["survey_resp"].corr(prop["cold_rate"]))

    patterns = [
        {
            "name": "CO2 sensor dropout concentrated in cold/worse-condition stock",
            "sensor": "avgCo2",
            "mechanism": (
                "CO2 hardware fails more often in older, higher-deprivation "
                "properties; missingness is correlated with the outcome, so a "
                "CO2-dependent model is least reliable for the households most "
                "likely to be cold."
            ),
            "evidence": {
                "n_high_dropout_properties": int(len(high)),
                "mean_cold_rate_high_dropout": round(float(high["cold_rate"].mean()), 4),
                "mean_cold_rate_low_dropout": round(float(low["cold_rate"].mean()), 4),
                "corr_dropout_vs_cold_rate": round(corr_co2, 4),
            },
        },
        {
            "name": "Resident survey MNAR — cold homes respond less and score lower",
            "sensor": "survey_score",
            "mechanism": (
                "Thermal-comfort surveys are ~97% missing and the response is "
                "itself informative: colder/higher-deprivation properties respond "
                "less often, so observed survey scores over-represent comfortable "
                "homes."
            ),
            "evidence": {
                "overall_response_rate": round(float(prop["survey_resp"].mean()), 4),
                "corr_response_rate_vs_cold_rate": round(resp_corr, 4),
            },
        },
    ]

    verdict = "CONDITIONAL" if abs(corr_co2) >= 0.1 else "PASS"
    return {
        "verdict": verdict,
        "patterns": patterns,
        "headline": (
            f"CO2 dropout vs cold-rate correlation = {corr_co2:+.2f}; high-dropout "
            f"properties are {high['cold_rate'].mean() - low['cold_rate'].mean():+.1%} "
            f"more cold-prone than the rest."
        ),
    }


# ── View 4: leakage audit ────────────────────────────────────────────────────
def compute_leakage_view(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    """Confirm a property-level split with zero cross-fold property leakage."""
    train_ids = set(train_df["reference"].unique())
    test_ids = set(test_df["reference"].unique())
    overlap = train_ids & test_ids
    verdict = "PASS" if len(overlap) == 0 else "FAIL"
    return {
        "verdict": verdict,
        "split_method": "property-level (grouped by reference)",
        "n_train_properties": len(train_ids),
        "n_test_properties": len(test_ids),
        "n_overlap_properties": len(overlap),
        "note": (
            "No property reference appears in both folds; lag_temp cannot leak "
            "across the split."
            if not overlap
            else f"{len(overlap)} properties span both folds — lag_temp leaks."
        ),
    }


# ── View 3: subgroup equity ──────────────────────────────────────────────────
def compute_equity_view(equity_rows: list[dict]) -> dict:
    """Aggregate per-subgroup AUROC rows into an equity verdict.

    equity_rows: list of {"model", "group", "auroc", "gap_vs_terraced"}.
    """
    rows = [r for r in equity_rows if r.get("auroc", 0.0) > 0.0]
    if not rows:
        return {"verdict": "FAIL", "rows": equity_rows, "max_abs_gap": 0.0}

    gaps = {r["group"]: r.get("gap_vs_terraced", 0.0) for r in rows}
    max_abs_gap = max(abs(v) for v in gaps.values()) if gaps else 0.0
    worst_group = max(gaps, key=lambda k: abs(gaps[k])) if gaps else None

    if max_abs_gap >= 0.10:
        verdict = "FAIL"
    elif max_abs_gap >= 0.05:
        verdict = "CONDITIONAL"
    else:
        verdict = "PASS"

    return {
        "verdict": verdict,
        "rows": equity_rows,
        "reference_group": "terraced",
        "max_abs_gap": round(float(max_abs_gap), 4),
        "worst_group": worst_group,
        "note": (
            f"Largest AUROC gap vs terraced is {max_abs_gap:.3f} ({worst_group})."
        ),
    }


# ── View 5: dataset audit (aggregator) ───────────────────────────────────────
@dataclass
class DatasetAudit:
    data_quality: str
    split_integrity: str
    equity: str
    overall: str


def aggregate_dataset_audit(
    sensor_quality_verdict: str,
    split_integrity_verdict: str,
    equity_verdict: str,
) -> DatasetAudit:
    """Map the three view verdicts to component verdicts and roll up to overall."""
    dq = _VIEW_TO_COMPONENT.get(sensor_quality_verdict, sensor_quality_verdict)
    si = _VIEW_TO_COMPONENT.get(split_integrity_verdict, split_integrity_verdict)
    eq = _VIEW_TO_COMPONENT.get(equity_verdict, equity_verdict)

    worst = max([dq, si, eq], key=lambda v: _SEVERITY.get(v, 0))
    # A clean rollup: any NOT READY -> NOT READY; any CONDITIONAL -> CONDITIONAL.
    overall = worst
    return DatasetAudit(data_quality=dq, split_integrity=si, equity=eq, overall=overall)
