"""Model C — Notes-Dependent Deterioration Predictor  (implement this)

═══════════════════════════════════════════════════════════════════════════════
DESIGN BRIEF
═══════════════════════════════════════════════════════════════════════════════

This model predicts ICU patient deterioration using clinical notes as a
primary signal, combined with basic laboratory and vital-sign features.

Clinical notes encode a clinician's narrative assessment of the patient —
observations, concerns, suspected diagnoses, and clinical reasoning.
The `note_risk_score` column in this dataset represents a structured
summary of that narrative on a 0-1 scale (0 = reassuring, 1 = concerning).

The model's power comes from this richer signal. Its vulnerability is that
approximately 30% of patients have no notes — and the model must decide
what to do in that situation.

───────────────────────────────────────────────────────────────────────────────
CLINICAL CONTEXT — read before choosing your missing-notes strategy
───────────────────────────────────────────────────────────────────────────────

Features available in the dataset:

  note_risk_score     Structured note summary (0-1). NaN when has_notes == 0.
  has_notes           1 if notes exist for this patient, 0 if absent.

  sofa_score          Severity of illness score (0-20, higher = more severe)
  lactate             Blood lactate — marker of circulatory failure
  creatinine          Kidney function marker
  hr_mean             Heart rate mean
  spo2_mean           Oxygen saturation mean

Notes are MISSING NOT AT RANDOM (MNAR):
  • Surgical patients are less likely to have notes (~46% missing)
  • Patients without notes have a LOWER deterioration rate in the data
    (14% vs 44% for patients with notes)

This means any imputation strategy will introduce a systematic bias.
The choice you make here determines whether the model is safe to deploy
for the 30% of patients without notes.

───────────────────────────────────────────────────────────────────────────────
YOUR DECISION — how to handle missing notes
───────────────────────────────────────────────────────────────────────────────

Option A: Silent imputation (the dangerous option — implement it knowingly)
  → Replace NaN with the population mean note_risk_score.
  → The model continues producing confident predictions for patients without notes.
  → This is the most common real-world approach and the most commonly criticised.
  → If you choose this: your assessment narrative MUST quantify and flag the
    degradation in performance for the notes-absent group.

Option B: Uncertainty-aware imputation
  → Replace NaN with a neutral 0.5 and add a flag feature (has_notes).
  → The model learns to discount the note signal when notes are absent.
  → Evaluate whether the has_notes flag materially reduces the performance gap.

Option C: Explicit abstention / two-model approach
  → Route patients with notes to a notes-aware model.
  → Route patients without notes to a notes-free fallback (similar to Model B).
  → More complex but clinically honest. Report separately on each route.

Your choice and its consequences ARE the hackathon output for this model.
A submission that implements Option A, measures the damage, and recommends
CONDITIONAL deployment with mandatory notes-absent flagging is more valuable
than Option C poorly implemented.

───────────────────────────────────────────────────────────────────────────────
INTERFACE — do not change these method signatures
───────────────────────────────────────────────────────────────────────────────
"""

# ── TODO: import your chosen model ───────────────────────────────────────────
# from sklearn.linear_model import LogisticRegression
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import StandardScaler
# import lightgbm as lgb

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin

# ── Features this model may use ───────────────────────────────────────────────
BASE_FEATURES = ["sofa_score", "lactate", "creatinine", "hr_mean", "spo2_mean"]
NOTE_FEATURES = ["note_risk_score", "has_notes"]
# You may use any combination of BASE_FEATURES + NOTE_FEATURES.
# You may NOT use features from model_b.VITALS unless you explicitly justify
# combining modalities — and document the overlap in your narrative.


class ModelC(BaseEstimator, ClassifierMixin):
    """Notes-dependent deterioration predictor.

    Replace this docstring with a one-line description of your implementation
    and the missing-notes strategy you chose from the design brief above.
    """

    def __init__(self):
        # TODO: define your model hyperparameters here
        pass

    # ── fit ───────────────────────────────────────────────────────────────────

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "ModelC":
        """Train the model.

        Parameters
        ----------
        X : pd.DataFrame  — full feature DataFrame
        y : np.ndarray    — binary labels (1 = deteriorated within 24h)

        Notes
        -----
        • note_risk_score is NaN for ~30% of patients — handle this here.
        • If you compute a mean for imputation on the training set, store it
          as self._note_mean so predict_proba can use the same value (not the
          test-set mean — that would leak information).
        • Set self.classes_ = np.array([0, 1]) before returning.
        """
        # TODO: implement
        raise NotImplementedError("Implement ModelC.fit()")

    # ── predict_proba ─────────────────────────────────────────────────────────

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Return probability estimates for each class.

        Parameters
        ----------
        X : pd.DataFrame

        Returns
        -------
        np.ndarray of shape (n_samples, 2)
          Column 0 : P(no deterioration)
          Column 1 : P(deterioration)

        Notes
        -----
        For patients with has_notes == 0, your output here is the key
        deployability question. Consider:
          • Do the predicted probabilities spread across the full 0-1 range
            (suggesting the model is discriminating), or cluster near 0.5
            (suggesting it has defaulted to uncertainty)?
          • The evaluation app will show performance split by has_notes,
            so the evidence will be visible regardless of what you choose.
        """
        # TODO: implement
        raise NotImplementedError("Implement ModelC.predict_proba()")

    # ── predict ───────────────────────────────────────────────────────────────

    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Classify at a given threshold."""
        return (self.predict_proba(X)[:, 1] >= threshold).astype(int)

    # ── feature_importance ────────────────────────────────────────────────────

    def feature_importance(self) -> pd.Series:
        """Return feature importances sorted descending.

        Strongly recommended — the Explainer track will specifically want to
        see how heavily note_risk_score is weighted relative to clinical labs,
        and whether has_notes appears as an important feature.
        """
        raise NotImplementedError(
            "Implement feature_importance() to enable the Explainer track."
        )
