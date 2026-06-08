"""Evaluation helpers for housing demo models."""

from __future__ import annotations

from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
)


def compute_metrics(
    y_true,
    y_prob,
    threshold: float = 0.5,
    model_name: str = "",
) -> dict:
    """Return a flat dict of classification metrics at a given threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    try:
        auroc = round(float(roc_auc_score(y_true, y_prob)), 4)
    except Exception:
        auroc = float("nan")
    try:
        auprc = round(float(average_precision_score(y_true, y_prob)), 4)
    except Exception:
        auprc = float("nan")

    return {
        "model": model_name,
        "threshold": threshold,
        "auroc": auroc,
        "auprc": auprc,
        "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4),
        "sensitivity": round(sensitivity, 4),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "n_positive": int(y_true.sum()),
        "n_total": int(len(y_true)),
    }
