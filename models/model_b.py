"""Model B — Vitals-Only Deterioration Predictor  (implement this)

═══════════════════════════════════════════════════════════════════════════════
DESIGN BRIEF
═══════════════════════════════════════════════════════════════════════════════

This model predicts ICU patient deterioration using ONLY vital-sign data.
No laboratory results. No clinical notes. No demographic information
(though you may use 'age' if your design explicitly accounts for it —
see clinical context below).

A vitals-only model represents the kind of system deployable even in
resource-limited settings where lab results are delayed, notes are unavailable,
or a lightweight automated triage is needed. It is a realistic deployment
scenario with well-documented clinical strengths and limitations.

───────────────────────────────────────────────────────────────────────────────
CLINICAL CONTEXT — read before choosing your architecture
───────────────────────────────────────────────────────────────────────────────

Vital signs available in the dataset:

  hr_mean, hr_std      Heart rate 24-hour mean and variability
  rr_mean, rr_std      Respiratory rate mean and variability
  spo2_mean, spo2_min  Oxygen saturation mean and worst recorded value
  sbp_mean             Systolic blood pressure mean
  temp_mean            Body temperature mean

Clinical evidence shows that elderly patients (aged 75+) can deteriorate
WITHOUT showing the alarming vital-sign changes seen in younger adults:
  • Baseline heart rate and respiratory rate are naturally lower
  • Reduced physiological reserve means smaller changes precede collapse
  • SpO2 often stays deceptively normal until late-stage deterioration

A model trained on a general population without accounting for age will
systematically under-estimate risk for elderly patients.

───────────────────────────────────────────────────────────────────────────────
YOUR DECISION — architectural trade-offs to choose from
───────────────────────────────────────────────────────────────────────────────

Option A: Ignore the age limitation
  → Build the simplest viable model. Document the elderly patient gap as
    a known failure mode in your assessment narrative. Recommend NOT APPROVED
    for elderly-majority wards.

Option B: Add 'age' as an input feature
  → Extend VITALS to include age. The model may learn the age interaction
    but cannot reliably learn from a training set that underrepresents 75+
    patients. Document whether this actually closed the gap.

Option C: Separate models by age band
  → Train distinct models for under-65, 65-74, and 75+ patients. More
    complex but potentially more equitable. Report on whether performance
    differences remain.

There is no single correct choice. The choice you make and the evidence
you produce to justify it IS the hackathon output.

───────────────────────────────────────────────────────────────────────────────
INTERFACE — do not change these method signatures
───────────────────────────────────────────────────────────────────────────────
"""

# ── TODO: import your chosen model ───────────────────────────────────────────
# from sklearn.linear_model import LogisticRegression
# from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
# import lightgbm as lgb
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import StandardScaler

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin

# ── Features this model is permitted to use ──────────────────────────────────
VITALS = [
    "hr_mean", "hr_std",
    "rr_mean", "rr_std",
    "spo2_mean", "spo2_min",
    "sbp_mean",
    "temp_mean",
]
# Optionally extend with ["age"] if you chose Option B above.


class ModelB(BaseEstimator, ClassifierMixin):
    """Vitals-only deterioration predictor.

    Replace this docstring with a one-line description of your implementation
    and the architectural choice you made from the design brief above.
    """

    def __init__(self):
        # TODO: define your model hyperparameters here
        # e.g. self.C = 1.0  for logistic regression
        #      self.n_estimators = 100  for tree-based models
        pass

    # ── fit ───────────────────────────────────────────────────────────────────

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "ModelB":
        """Train the model.

        Parameters
        ----------
        X : pd.DataFrame  — full feature DataFrame (you select VITALS columns here)
        y : np.ndarray    — binary labels (1 = deteriorated within 24h)

        Notes
        -----
        You must set  self.classes_ = np.array([0, 1])  before returning self.
        This is required by scikit-learn's BaseEstimator interface.

        Example skeleton:
            X_vitals = X[VITALS]          # select only vital-sign features
            # ... preprocessing ...
            self._model.fit(X_vitals, y)
            self.classes_ = np.array([0, 1])
            return self
        """
        # TODO: implement
        raise NotImplementedError("Implement ModelB.fit()")

    # ── predict_proba ─────────────────────────────────────────────────────────

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return probability estimates for each class.

        Parameters
        ----------
        X : pd.DataFrame  — feature DataFrame (same structure as fit)

        Returns
        -------
        np.ndarray of shape (n_samples, 2)
          Column 0 : P(no deterioration)
          Column 1 : P(deterioration)   ← the risk score used everywhere downstream

        Notes
        -----
        Column 1 probabilities must lie in [0, 1] and columns must sum to 1.
        If you add any age-based correction (Option B), apply it here.
        """
        # TODO: implement
        raise NotImplementedError("Implement ModelB.predict_proba()")

    # ── predict ───────────────────────────────────────────────────────────────

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Classify at a given threshold (default 0.5 — adjustable in the app)."""
        return (self.predict_proba(X)[:, 1] >= threshold).astype(int)

    # ── feature_importance ────────────────────────────────────────────────────

    def feature_importance(self) -> pd.Series:
        """Return a Series of |feature| → importance, sorted descending.

        Used by the Explainer track in the evaluation app.
        Optional but strongly recommended — without it the feature importance
        tab in the app will be empty for this model.

        For logistic regression: use |coef_|
        For tree-based models:   use feature_importances_
        """
        raise NotImplementedError(
            "Implement feature_importance() to enable the Explainer track."
        )
