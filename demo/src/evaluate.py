"""Evaluation helpers for housing demo models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)


def compute_metrics(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    ppv = tp / (tp + fp) if (tp + fp) else 0.0
    npv = tn / (tn + fn) if (tn + fn) else 0.0

    return {
        "auroc": float(roc_auc_score(y_true, y_prob)),
        "auprc": float(average_precision_score(y_true, y_prob)),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "ppv": float(ppv),
        "npv": float(npv),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "threshold": float(threshold),
    }


def subgroup_auroc_scores(df: pd.DataFrame, y_prob: np.ndarray, subgroup_col="property_type"):
    work = df[[subgroup_col, "cold_risk"]].copy()
    work["y_prob"] = y_prob

    subgroup_scores = {}
    for group, grp_df in work.groupby(subgroup_col):
        if grp_df["cold_risk"].nunique() < 2:
            subgroup_scores[group] = np.nan
            continue
        subgroup_scores[group] = roc_auc_score(grp_df["cold_risk"], grp_df["y_prob"])

    return subgroup_scores


def subgroup_auroc_gaps_reference(
    subgroup_scores: dict[str, float],
    reference_group: str = "terraced",
):
    ref_score = subgroup_scores.get(reference_group, np.nan)
    gaps = {}
    for group in ["flat", "terraced", "semi-detached", "detached"]:
        score = subgroup_scores.get(group, np.nan)
        if np.isnan(score) or np.isnan(ref_score):
            gaps[group] = 0.0
        else:
            gaps[group] = float(score - ref_score)
    return gaps
