"""Model factory + the unified triage router.

Three models, each chosen to *expose* a failure mode rather than to win:

* Model A — multimodal incl. CO2  (the MNAR trap)
* Model B — sensor-robust, no CO2 (the deployable fix for dropout stock)
* Model C — Model A trained/tested on a ROW-level split (the leakage exhibit)

All three are interpretable logistic-regression pipelines so the heating-failure
explainability layer (challenge 3) falls out of the coefficients for free.

``TriageRouter`` is the product: it ranks every property for upgrade and, for
properties whose CO2 sensor has failed, it refuses to trust the CO2 model and
falls back to Model B while flagging the property for sensor repair.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data_pipeline import (
    FEATURES_CO2_INTERP,
    FEATURES_CO2_MEAN,
    FEATURES_CO2_RAW,
    FEATURES_LAG,
    FEATURES_ROBUST,
)


def build_pipeline(seed: int = 42) -> Pipeline:
    """Median-impute -> standardise -> logistic regression. Interpretable + NaN-safe."""
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000, class_weight="balanced", random_state=seed
                ),
            ),
        ]
    )


def make_estimator(algo: str, seed: int = 42):
    """Estimator factory for the model roster.

    * ``logreg`` — interpretable linear model (median impute + scale)
    * ``rf``     — random forest, captures non-linear interactions (median impute)
    * ``hgb``    — gradient boosting with NATIVE missing-value handling (no imputer)
    """
    if algo == "logreg":
        return build_pipeline(seed)
    if algo == "rf":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(
                n_estimators=120, max_depth=14, min_samples_leaf=20, n_jobs=-1,
                class_weight="balanced", random_state=seed)),
        ])
    if algo == "hgb":
        # HistGradientBoosting routes NaNs down both splits -> no imputation needed.
        return HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.08, max_depth=6, random_state=seed)
    raise ValueError(f"unknown algo {algo!r}")


def train_model(train_df: pd.DataFrame, features: list[str], seed: int = 42) -> Pipeline:
    pipe = build_pipeline(seed)
    pipe.fit(train_df[features], train_df["cold_risk"])
    return pipe


# The roster the website's model-picker and the benchmark card iterate over.
# Each spec varies the ALGORITHM and/or the MISSING-DATA STRATEGY so the comparison
# is meaningful. `deployed` marks the model that powers the live ranking + predictor.
MODEL_SPECS = [
    {"id": "rf_robust", "label": "Random Forest — Sensor-robust (deployed)",
     "algo": "rf", "features": FEATURES_ROBUST, "missingness": "CO2 dropped",
     "interpretable": "medium", "verdict": "CONDITIONAL", "deployed": True},
    {"id": "logreg_robust", "label": "Logistic Regression — Sensor-robust (interpretable baseline)",
     "algo": "logreg", "features": FEATURES_ROBUST, "missingness": "CO2 dropped",
     "interpretable": "high", "verdict": "CONDITIONAL", "deployed": False},
    {"id": "hgb_co2_native", "label": "Gradient Boosting — CO2 (native NaN)",
     "algo": "hgb", "features": FEATURES_CO2_RAW, "missingness": "native (no imputation)",
     "interpretable": "medium", "verdict": "CONDITIONAL", "deployed": False},
    {"id": "logreg_co2_mean", "label": "Logistic — CO2 mean-imputed",
     "algo": "logreg", "features": FEATURES_CO2_MEAN, "missingness": "global-mean impute + flag",
     "interpretable": "high", "verdict": "NOT READY", "deployed": False},
    {"id": "logreg_co2_interp", "label": "Logistic — CO2 time-interpolated",
     "algo": "logreg", "features": FEATURES_CO2_INTERP, "missingness": "per-property interpolation + flag",
     "interpretable": "high", "verdict": "NOT READY", "deployed": False},
    {"id": "logreg_lag", "label": "Logistic — Nowcast + lag_temp (leakage)",
     "algo": "logreg", "features": FEATURES_LAG, "missingness": "n/a",
     "interpretable": "high", "verdict": "NOT READY", "deployed": False},
]


def explain(model: Pipeline, features: list[str], top_k: int = 6) -> list[dict]:
    """Plain-language driver list from logistic coefficients (signed direction)."""
    coefs = model.named_steps["clf"].coef_[0]
    order = np.argsort(np.abs(coefs))[::-1][:top_k]
    return [
        {
            "feature": features[i],
            "weight": round(float(coefs[i]), 4),
            "direction": "increases cold risk" if coefs[i] > 0 else "decreases cold risk",
        }
        for i in order
    ]


def explain_importances(model, features: list[str], top_k: int = 8) -> list[dict]:
    """Global feature importance for the deployed tree model (unsigned magnitude)."""
    clf = model.named_steps["clf"] if hasattr(model, "named_steps") else model
    imp = getattr(clf, "feature_importances_", None)
    if imp is None:
        return []
    order = np.argsort(imp)[::-1][:top_k]
    return [{"feature": features[i], "importance": round(float(imp[i]), 4)} for i in order]


class TriageRouter:
    """Per-property upgrade triage with honest reliability flags.

    For each property:
      * high CO2 dropout  -> score from Model B, reliability = LOW (sensor repair)
      * otherwise         -> score from Model A, reliability = HIGH
    """

    def __init__(self, model_a: Pipeline, model_b: Pipeline, features_a, features_b,
                 dropout_threshold: float = 0.5):
        self.model_a = model_a
        self.model_b = model_b
        self.features_a = features_a
        self.features_b = features_b
        self.dropout_threshold = dropout_threshold

    def score_properties(self, df: pd.DataFrame, winter_only: bool = True) -> pd.DataFrame:
        """Return one row per property: routed cold-risk score + reliability flag."""
        work = df.copy()
        pa = self.model_a.predict_proba(work[self.features_a])[:, 1]
        pb = self.model_b.predict_proba(work[self.features_b])[:, 1]
        work["p_a"] = pa
        work["p_b"] = pb
        work["use_b"] = work["co2_dropout_rate"] >= self.dropout_threshold
        work["p_routed"] = np.where(work["use_b"], work["p_b"], work["p_a"])

        if winter_only and "date" in work.columns:
            mask = work["date"].dt.month.isin([11, 12, 1, 2, 3])
            if mask.any():
                work = work[mask]

        g = work.groupby("reference")
        out = pd.DataFrame(
            {
                "property_type": g["property_type"].first(),
                "co2_dropout_rate": g["co2_dropout_rate"].first(),
                "score_model_a": g["p_a"].mean(),
                "score_model_b": g["p_b"].mean(),
                "score_routed": g["p_routed"].mean(),
                "observed_cold_rate": g["cold_risk"].mean(),
            }
        ).reset_index()
        out["reliability"] = np.where(
            out["co2_dropout_rate"] >= self.dropout_threshold, "LOW", "HIGH"
        )
        out["reason"] = np.where(
            out["reliability"] == "LOW",
            "CO2 sensor dropout >= "
            + str(int(self.dropout_threshold * 100))
            + "% — scored by sensor-robust Model B; flag for sensor repair",
            "Full multimodal signal available — scored by Model A",
        )
        return out.sort_values("score_routed", ascending=False).reset_index(drop=True)
