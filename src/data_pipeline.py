"""Data loading, feature engineering, and *honest* splits.

This module is deliberately conservative about leakage:

* The label ``cold_risk`` is derived from same-day ``avgTemperature``.
  Therefore same-day ``avgTemperature`` is NEVER used as a feature — doing so
  is target leakage (the model would just relearn the threshold). We predict
  from ``lag_temp`` (yesterday's temperature) and the other modalities instead.
* Splits are made at the PROPERTY level. Each property contributes 731 daily
  rows; a row-level split would leak ``lag_temp`` across train/test for the same
  property. ``make_row_split`` exists only to *demonstrate* that failure mode.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Two columns are excluded from EVERY deployable feature set, on evidence:
#   * avgTemperature — it defines the label (cold_risk = temp < 19): target leakage.
#   * lag_temp       — yesterday's indoor temperature is ~yesterday's label. Adding it
#                      inflates AUROC 0.84 -> 0.93 (+0.09). It is a leakage feature, not
#                      a useful predictor for an upgrade decision. Kept ONLY for Model C.
#
# Model A — SENSOR-ROBUST (deployed): environment + metadata, no CO2, no lag.
FEATURES_ROBUST = [
    "avgHumidity",
    "smart_meter_kwh",
    "noise_db",
    "day_of_week",
    "month",
    "is_flat",
    "pt_terraced",
    "pt_semi_detached",
    "pt_detached",
]

# Model B — MULTIMODAL incl. CO2: Model A plus the MNAR CO2 channel. Evidence shows
# CO2 adds ~0 lift (+0.0015 AUROC) while introducing a 38%-missing dependency.
FEATURES_CO2 = FEATURES_ROBUST + ["co2_imputed", "co2_missing"]

# Model C — NOWCAST incl. lag_temp: the target-leakage exhibit. Do not deploy.
FEATURES_LAG = FEATURES_ROBUST + ["lag_temp"]

# Every engineered feature any model can use (for the modelling frame).
ALL_FEATURES = sorted(set(FEATURES_ROBUST + FEATURES_CO2 + FEATURES_LAG))

# The default feature set the demo app loads = the deployable model (Model A).
FEATURES = FEATURES_ROBUST

# Back-compat aliases (older imports).
FEATURES_A = FEATURES_ROBUST
FEATURES_B = FEATURES_CO2

COLD_RISK_THRESHOLD_C = 19.0  # WHO minimum indoor temperature for social housing
HIGH_DROPOUT_THRESHOLD = 0.5  # per-property CO2 missingness flagged as unreliable


def _find_raw_csv(raw_dir: str | Path | None) -> Path:
    """Locate housing_properties_daily.csv robustly.

    Accepts a directory (looks for the file inside) or None, and walks up from
    this file to find ``data/raw/housing_properties_daily.csv`` so the pipeline
    works whether called from the repo root or from ``demo/``.
    """
    name = "housing_properties_daily.csv"
    candidates: list[Path] = []
    if raw_dir is not None:
        raw_dir = Path(raw_dir)
        candidates += [raw_dir / name, raw_dir]
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidates.append(parent / "data" / "raw" / name)
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(
        f"Could not locate {name}. Looked in: "
        + ", ".join(str(c) for c in candidates)
    )


def load_and_merge(raw_dir: str | Path | None = None) -> pd.DataFrame:
    """Load the daily CSV and return a feature-engineered dataframe.

    The raw file is already one merged daily table, so "merge" here means
    "attach engineered features" (date, lag_temp, CO2 missingness, one-hots).
    """
    csv_path = _find_raw_csv(raw_dir)
    df = pd.read_csv(csv_path, low_memory=False, dtype={"reference": str})
    return engineer_features(df)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add label and engineered features without mutating the caller's frame."""
    df = df.copy()

    # Calendar date from the three split columns -> ordering + day_of_week.
    df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
    df = df.sort_values(["reference", "date"]).reset_index(drop=True)
    df["day_of_week"] = df["date"].dt.dayofweek

    # Target: below the WHO 19C minimum that day.
    df["cold_risk"] = (df["avgTemperature"] < COLD_RISK_THRESHOLD_C).astype(int)

    # Previous-day indoor temperature, per property (NaN on each property's day 1).
    df["lag_temp"] = df.groupby("reference")["avgTemperature"].shift(1)

    # CO2 channel: missingness flag + simple mean-imputation baseline.
    df["co2_missing"] = df["avgCo2"].isna().astype(int)
    df["co2_imputed"] = df["avgCo2"].fillna(df["avgCo2"].mean())

    # Property-type one-hots (flat is the reference level, captured by is_flat).
    pt = df["property_type"].astype(str)
    df["pt_terraced"] = (pt == "terraced").astype(int)
    df["pt_semi_detached"] = (pt == "semi-detached").astype(int)
    df["pt_detached"] = (pt == "detached").astype(int)
    if "is_flat" not in df.columns:
        df["is_flat"] = (pt == "flat").astype(int)

    # Per-property CO2 dropout rate + high-dropout flag (the MNAR cohort).
    dropout = df.groupby("reference")["co2_missing"].transform("mean")
    df["co2_dropout_rate"] = dropout
    df["high_dropout"] = (dropout >= HIGH_DROPOUT_THRESHOLD).astype(int)

    return df


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return the modelling frame: features + label + metadata for grouping."""
    keep = list(ALL_FEATURES)
    meta = [
        "reference",
        "property_type",
        "cold_risk",
        "co2_dropout_rate",
        "high_dropout",
        "date",
    ]
    cols = [c for c in keep + meta if c in df.columns]
    return df[cols].copy()


def make_property_split(
    df: pd.DataFrame,
    test_size: float = 0.25,
    seed: int = 42,
    stratify_by: str = "property_type",
):
    """PROPERTY-level stratified split — the only honest split for this data.

    Returns (train_df, test_df, train_ids, test_ids). No property reference
    appears in both folds.
    """
    props = (
        df[["reference", stratify_by]]
        .drop_duplicates("reference")
        .reset_index(drop=True)
    )
    train_ids, test_ids = train_test_split(
        props["reference"],
        test_size=test_size,
        random_state=seed,
        stratify=props[stratify_by],
    )
    train_ids, test_ids = set(train_ids), set(test_ids)
    train_df = df[df["reference"].isin(train_ids)].reset_index(drop=True)
    test_df = df[df["reference"].isin(test_ids)].reset_index(drop=True)
    return train_df, test_df, sorted(train_ids), sorted(test_ids)


def make_row_split(df: pd.DataFrame, test_size: float = 0.25, seed: int = 42):
    """ROW-level random split — DELIBERATELY WRONG, for the leakage exhibit.

    The same property's consecutive days land in both folds, so ``lag_temp``
    leaks yesterday's truth into the test set. Used only to quantify how much
    a naive split inflates apparent performance.
    """
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=seed)
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def property_dropout_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-property summary: CO2 dropout rate, cold-risk rate, type."""
    g = df.groupby("reference")
    out = pd.DataFrame(
        {
            "property_type": g["property_type"].first(),
            "co2_dropout_rate": g["co2_missing"].mean(),
            "cold_risk_rate": g["cold_risk"].mean(),
            "mean_survey_score": g["survey_score"].mean(),
            "survey_response_rate": g["survey_score"].apply(lambda x: x.notna().mean()),
            "n_days": g.size(),
        }
    ).reset_index()
    out["high_dropout"] = (out["co2_dropout_rate"] >= HIGH_DROPOUT_THRESHOLD).astype(int)
    return out
