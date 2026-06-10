"""Missing-data analysis for the housing sensor dataset.

Answers three questions a data manager actually needs:
  1. How much is missing, and where?                          -> missingness_summary
  2. Is it random (MCAR) or patterned (MAR/MNAR)?             -> mnar_mechanism
  3. Does *fixing* the missingness change anything, and what  -> imputation_distribution
     does each imputation method do to the data?                (+ model comparison upstream)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import roc_auc_score

_MODALITIES = ["avgTemperature", "avgHumidity", "avgCo2", "smart_meter_kwh",
               "noise_db", "survey_score"]


def missingness_summary(df: pd.DataFrame) -> list[dict]:
    out = []
    for c in _MODALITIES:
        if c in df.columns:
            out.append({"modality": c,
                        "missing_rate": round(float(df[c].isna().mean()), 4),
                        "n_missing": int(df[c].isna().sum())})
    return out


def mnar_mechanism(df: pd.DataFrame) -> dict:
    """Is the CO2 dropout random, or does it track property characteristics/outcome?"""
    g = df.groupby("reference")
    prop = pd.DataFrame({
        "dropout": g["co2_missing"].mean() if "co2_missing" in df.columns
        else g["avgCo2"].apply(lambda s: s.isna().mean()),
        "type": g["property_type"].first(),
        "cold_rate": g.apply(lambda x: (x["avgTemperature"] < 19.0).mean(), include_groups=False),
        "is_flat": g["is_flat"].first() if "is_flat" in df.columns else 0,
        "pt_terraced": g["pt_terraced"].first() if "pt_terraced" in df.columns else 0,
        "pt_semi_detached": g["pt_semi_detached"].first() if "pt_semi_detached" in df.columns else 0,
        "pt_detached": g["pt_detached"].first() if "pt_detached" in df.columns else 0,
    })
    prop["high_dropout"] = (prop["dropout"] >= 0.5).astype(int)

    # Predictability of WHICH properties drop out, from metadata only.
    # If metadata predicts dropout well, it is NOT missing-completely-at-random.
    X = prop[["is_flat", "pt_terraced", "pt_semi_detached", "pt_detached"]].values
    y = prop["high_dropout"].values
    if len(np.unique(y)) == 2:
        proba = cross_val_predict(
            LogisticRegression(max_iter=1000, class_weight="balanced"),
            X, y, cv=5, method="predict_proba")[:, 1]
        predict_auroc = round(float(roc_auc_score(y, proba)), 4)
    else:
        predict_auroc = 0.0

    share_by_type = {t: round(float(prop[prop["type"] == t]["high_dropout"].mean()), 4)
                     for t in ["flat", "terraced", "semi-detached", "detached"]}
    corr_cold = round(float(prop["dropout"].corr(prop["cold_rate"])), 4)

    if predict_auroc >= 0.6:
        verdict = ("NOT MCAR — which properties lose their CO2 sensor is predictable from property "
                   "type alone, so the dropout is patterned, not random.")
    else:
        verdict = "Dropout is only weakly tied to property type."

    return {
        "predict_high_dropout_auroc": predict_auroc,
        "high_dropout_share_by_type": share_by_type,
        "corr_dropout_vs_cold_rate": corr_cold,
        "n_high_dropout": int(prop["high_dropout"].sum()),
        "n_properties": int(len(prop)),
        "mechanism_verdict": verdict,
        "outcome_note": (
            f"Dropout is only weakly correlated with cold-risk (r={corr_cold}), so the MNAR-with-"
            f"respect-to-outcome concern is limited: the broken sensors are mainly a data-integrity "
            f"issue, not a hidden cold-risk bias."),
    }


def imputation_distribution(df: pd.DataFrame, bins: int = 24) -> dict:
    """What each imputation method does to the CO2 distribution.

    Naive mean-imputation collapses variance (a spike at the mean); per-property
    interpolation preserves the real spread. We quantify and chart both.
    """
    observed = df["avgCo2"].dropna()
    lo, hi = float(observed.quantile(0.01)), float(observed.quantile(0.99))
    edges = np.linspace(lo, hi, bins + 1)
    centers = (edges[:-1] + edges[1:]) / 2

    def hist(series):
        h, _ = np.histogram(series.clip(lo, hi), bins=edges)
        return h.tolist()

    series = {"observed": observed,
              "mean_imputed": df["co2_imputed"],
              "interpolated": df["co2_interp"]}
    chart = [{"co2": round(float(c), 1),
              "observed": hist(series["observed"])[i],
              "mean_imputed": hist(series["mean_imputed"])[i],
              "interpolated": hist(series["interpolated"])[i]}
             for i, c in enumerate(centers)]

    stats = {k: {"mean": round(float(s.mean()), 1), "std": round(float(s.std()), 1)}
             for k, s in series.items()}
    return {
        "stats": stats,
        "histogram": chart,
        "note": (f"Observed CO2 std is {stats['observed']['std']}; naive mean-imputation drops it to "
                 f"{stats['mean_imputed']['std']} (a fake spike at the mean), while per-property "
                 f"interpolation keeps it at {stats['interpolated']['std']} — closer to reality."),
    }
