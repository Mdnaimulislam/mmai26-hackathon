"""Model A — Multimodal LightGBM fusion.

Uses all available modalities: demographics, vitals, labs, and clinical notes.
This is the strongest of the three models but still has identifiable failure modes.

Expected performance: AUROC 0.87-0.92.
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.base import BaseEstimator, ClassifierMixin

FEATURES = [
    # demographics / severity
    "age", "sex_enc", "admission_enc", "sofa_score",
    # vitals
    "hr_mean", "hr_std", "rr_mean", "rr_std",
    "spo2_mean", "spo2_min", "sbp_mean", "temp_mean",
    # labs
    "lactate", "creatinine", "wbc", "bilirubin",
    # notes
    "has_notes", "note_risk_imputed",
]


class ModelA(BaseEstimator, ClassifierMixin):
    """Multimodal LightGBM — all features."""

    def __init__(
        self,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        num_leaves: int = 31,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.num_leaves = num_leaves
        self.random_state = random_state
        self._clf = None
        self.feature_names_in_ = FEATURES

    # ── internal helpers ──────────────────────────────────────────────────────

    def _encode(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()
        df["sex_enc"]       = (df["sex"] == "M").astype(int)
        df["admission_enc"] = df["admission_type"].map(
            {"medical": 0, "surgical": 1, "trauma": 2}
        ).fillna(0)
        df["note_risk_imputed"] = df["note_risk_score"].fillna(0.5)
        return df[FEATURES]

    # ── public interface ──────────────────────────────────────────────────────

    def fit(self, X: pd.DataFrame, y) -> "ModelA":
        Xe = self._encode(X)
        self._clf = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            num_leaves=self.num_leaves,
            random_state=self.random_state,
            verbose=-1,
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
