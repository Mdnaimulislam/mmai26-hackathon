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
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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


def train_model(train_df: pd.DataFrame, features: list[str], seed: int = 42) -> Pipeline:
    pipe = build_pipeline(seed)
    pipe.fit(train_df[features], train_df["cold_risk"])
    return pipe


def explain(model: Pipeline, features: list[str], top_k: int = 6) -> list[dict]:
    """Plain-language driver list from logistic coefficients (challenge-3 layer)."""
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
