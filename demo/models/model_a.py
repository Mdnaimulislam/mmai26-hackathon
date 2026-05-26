"""Model A — Multimodal LightGBM (tabular champion).

Uses all available tabular features: pre-surgical context, intra-op events,
ICU severity, vitals aggregates, labs, and notes availability flag.
Strongest overall performance; most equitable across surgery types.

Known limitation: blood_loss_imputed uses mean imputation when blood loss
is not recorded (MNAR pattern in ~30 % of cardiac/vascular/emergency cases).
These patients' true blood loss is systematically higher than the imputed
mean, causing the model to under-estimate their 30-day complication risk.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import BaseEstimator, ClassifierMixin

TARGET = "major_complication_30d"

FEATURES = [
    # demographics
    "age", "sex_enc",
    # surgery context
    "surgery_enc", "urgency_enc", "asa_class", "op_duration_h",
    # intra-op
    "blood_loss_imputed", "blood_loss_missing", "transfused",
    # comorbidities
    "has_diabetes", "has_hypertension",
    # pre-op labs
    "preop_creatinine", "preop_wbc", "preop_lactate",
    # ICU severity
    "sofa_score",
    # ICU vitals aggregates
    "hr_mean", "hr_std", "rr_mean", "rr_std",
    "spo2_mean", "spo2_min", "sbp_mean", "temp_mean",
    # ICU labs
    "icu_lactate", "icu_creatinine", "icu_wbc", "icu_bilirubin",
    # notes (pre-extracted NLP score, MNAR)
    "has_notes", "note_risk_imputed",
    # ICU stay
    "icu_hours",
]


class ModelA(BaseEstimator, ClassifierMixin):
    """Multimodal LightGBM — all tabular features."""

    def __init__(
        self,
        n_estimators: int = 90,
        learning_rate: float = 0.08,
        max_depth: int = 3,
        num_leaves: int = 16,
        min_child_samples: int = 50,
        subsample: float = 0.78,
        colsample_bytree: float = 0.62,
        reg_alpha: float = 0.30,
        reg_lambda: float = 0.50,
        random_state: int = 42,
    ):
        self.n_estimators      = n_estimators
        self.learning_rate     = learning_rate
        self.max_depth         = max_depth
        self.num_leaves        = num_leaves
        self.min_child_samples = min_child_samples
        self.subsample         = subsample
        self.colsample_bytree  = colsample_bytree
        self.reg_alpha         = reg_alpha
        self.reg_lambda        = reg_lambda
        self.random_state      = random_state
        self._clf              = None

    def _encode(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        if "sex" in df.columns and "sex_enc" not in df.columns:
            df["sex_enc"] = (df["sex"] == "F").astype(int)
        if "note_risk_score" in df.columns:
            df["note_risk_imputed"] = df["note_risk_score"].fillna(0.5)
        elif "note_risk_imputed" not in df.columns:
            df["note_risk_imputed"] = 0.5
        return df[FEATURES]

    def fit(self, X: pd.DataFrame, y) -> "ModelA":
        Xe = self._encode(X)
        self._clf = LGBMClassifier(
            n_estimators      = self.n_estimators,
            learning_rate     = self.learning_rate,
            max_depth         = self.max_depth,
            num_leaves        = self.num_leaves,
            min_child_samples = self.min_child_samples,
            subsample         = self.subsample,
            colsample_bytree  = self.colsample_bytree,
            reg_alpha         = self.reg_alpha,
            reg_lambda        = self.reg_lambda,
            random_state      = self.random_state,
            verbose           = -1,
        )
        self._clf.fit(Xe, y)
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self._clf.predict_proba(self._encode(X))

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= threshold).astype(int)

    def feature_importance(self) -> pd.Series:
        if self._clf is None:
            raise RuntimeError("Call fit() first.")
        return pd.Series(
            self._clf.feature_importances_, index=FEATURES
        ).sort_values(ascending=False)
