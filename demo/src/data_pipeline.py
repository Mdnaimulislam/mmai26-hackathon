"""Data loading and feature engineering for demo flow."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


KEY_COLS = ["reference", "year", "month", "day"]


def load_and_merge(raw_dir: Path) -> pd.DataFrame:
    properties = pd.read_csv(raw_dir / "properties.csv")
    env = pd.read_csv(raw_dir / "indoor_environment_daily.csv")
    energy = pd.read_csv(raw_dir / "energy_noise_daily.csv")
    survey = pd.read_csv(raw_dir / "resident_feedback_daily.csv")

    merged = env.merge(energy, on=KEY_COLS, how="left").merge(survey, on=KEY_COLS, how="left")
    merged = merged.merge(properties, on="reference", how="left")

    merged["date"] = pd.to_datetime(merged[["year", "month", "day"]], errors="coerce")
    merged = merged.sort_values(["reference", "date"]).reset_index(drop=True)
    return merged


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["cold_risk"] = (out["avgTemperature"] < 19.0).astype(int)
    out["lag_temp"] = out.groupby("reference")["avgTemperature"].shift(1)
    out["co2_missing"] = out["avgCo2"].isna().astype(int)
    out["co2_imputed"] = out["avgCo2"].fillna(out["avgCo2"].mean())
    out["day_of_week"] = out["date"].dt.dayofweek
    out["survey_missing"] = out["survey_score"].isna().astype(int)

    numeric_fill = {
        "avgTemperature": out["avgTemperature"].median(),
        "avgHumidity": out["avgHumidity"].median(),
        "smart_meter_kwh": out["smart_meter_kwh"].median(),
        "noise_db": out["noise_db"].median(),
        "lag_temp": out["lag_temp"].median(),
        "survey_score": out["survey_score"].median(skipna=True),
    }
    out = out.fillna(numeric_fill)
    return out


def split_by_property(df: pd.DataFrame, test_size: float = 0.25, seed: int = 42):
    refs = df["reference"].drop_duplicates()
    train_refs, test_refs = train_test_split(refs, test_size=test_size, random_state=seed)

    train_df = df[df["reference"].isin(train_refs)].copy()
    test_df = df[df["reference"].isin(test_refs)].copy()

    overlap = set(train_df["reference"]) & set(test_df["reference"])
    if overlap:
        raise ValueError(f"Leakage detected in property split: {sorted(overlap)}")

    return train_df, test_df
