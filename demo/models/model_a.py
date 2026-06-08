"""Model A — Logistic Regression baseline for cold-risk prediction.

A simple sklearn LogisticRegression pipeline with standard scaling.
Teams may replace or extend this with more complex models.
"""

from __future__ import annotations

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model_a() -> Pipeline:
    """Return an untrained logistic regression pipeline."""
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
