"""Metric computation for cold-risk classifiers.

``compute_metrics`` returns every field the OMAIB manifest and benchmark card
require, plus n_total / n_positive for display. It is defensive about
degenerate cases (a subgroup with only one class) so subgroup loops never crash.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
)


def _safe_div(a: float, b: float) -> float:
    return float(a) / float(b) if b else 0.0


def compute_metrics(y_true, y_prob, threshold: float = 0.5, model_name: str | None = None) -> dict:
    """Compute the full metric block at a given decision threshold.

    Parameters
    ----------
    y_true : array-like of {0,1}
    y_prob : array-like of predicted probabilities for the positive class
    threshold : decision threshold for the hard-label metrics
    model_name : optional label echoed back into the dict
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    n_total = int(len(y_true))
    n_positive = int(y_true.sum())
    both_classes = len(np.unique(y_true)) == 2

    auroc = float(roc_auc_score(y_true, y_prob)) if both_classes else 0.0
    auprc = float(average_precision_score(y_true, y_prob)) if both_classes else 0.0
    brier = float(brier_score_loss(y_true, y_prob)) if n_total else 0.0

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    sensitivity = _safe_div(tp, tp + fn)   # recall / TPR
    specificity = _safe_div(tn, tn + fp)   # TNR
    ppv = _safe_div(tp, tp + fp)           # precision
    npv = _safe_div(tn, tn + fn)
    f1 = _safe_div(2 * ppv * sensitivity, ppv + sensitivity)

    out = {
        "auroc": round(auroc, 4),
        "auprc": round(auprc, 4),
        "brier_score": round(brier, 4),
        "sensitivity": round(sensitivity, 4),
        "specificity": round(specificity, 4),
        "ppv": round(ppv, 4),
        "npv": round(npv, 4),
        "f1": round(f1, 4),
        "threshold": round(float(threshold), 4),
        "n_total": n_total,
        "n_positive": n_positive,
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }
    if model_name is not None:
        out["model_name"] = model_name
    return out


def subgroup_auroc(y_true, y_prob) -> float:
    """AUROC for a subgroup, 0.0 if the subgroup is single-class."""
    y_true = np.asarray(y_true).astype(int)
    if len(np.unique(y_true)) < 2:
        return 0.0
    return round(float(roc_auc_score(y_true, np.asarray(y_prob, dtype=float))), 4)
