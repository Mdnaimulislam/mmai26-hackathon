"""Evaluation utilities for the Clinical Strand (post-surgical complication).

All functions accept plain numpy arrays or pandas Series / DataFrames and return
plain Python dicts or DataFrames — no Streamlit or plotting imports here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
)


# ── Core metrics ──────────────────────────────────────────────────────────────

def compute_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
    model_name: str = "",
) -> dict:
    """Return a flat dict of classification metrics at a given threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    f1  = 2 * ppv * sensitivity / (ppv + sensitivity) if (ppv + sensitivity) > 0 else 0.0

    try:
        auroc = round(roc_auc_score(y_true, y_prob), 4)
    except Exception:
        auroc = float("nan")
    try:
        auprc = round(average_precision_score(y_true, y_prob), 4)
    except Exception:
        auprc = float("nan")

    return {
        "model":        model_name,
        "threshold":    threshold,
        "auroc":        auroc,
        "auprc":        auprc,
        "brier_score":  round(brier_score_loss(y_true, y_prob), 4),
        "sensitivity":  round(sensitivity, 4),
        "specificity":  round(specificity, 4),
        "ppv":          round(ppv, 4),
        "npv":          round(npv, 4),
        "f1":           round(f1, 4),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "n_positive":   int(y_true.sum()),
        "n_total":      int(len(y_true)),
    }


# ── ROC / PR curve data ───────────────────────────────────────────────────────

def roc_curve_data(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    return {"fpr": fpr, "tpr": tpr}


def pr_curve_data(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    prec, rec, _ = precision_recall_curve(y_true, y_prob)
    return {"precision": prec, "recall": rec}


# ── Calibration ───────────────────────────────────────────────────────────────

def compute_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> dict:
    bins = np.linspace(0, 1, n_bins + 1)
    frac_pos, mean_pred = [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() < 3:
            continue
        frac_pos.append(float(y_true[mask].mean()))
        mean_pred.append(float(y_prob[mask].mean()))
    return {
        "fraction_positive": np.array(frac_pos),
        "mean_predicted":    np.array(mean_pred),
    }


# ── Subgroup analysis ─────────────────────────────────────────────────────────

def compute_subgroup_metrics(
    df: pd.DataFrame,
    y_prob: np.ndarray,
    group_col: str,
    label_col: str = "major_complication_30d",
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Return per-group classification metrics for a single grouping variable."""
    y_true = df[label_col].values
    results = []
    for group_val in sorted(df[group_col].unique()):
        mask = (df[group_col] == group_val).values
        if mask.sum() < 8:
            continue
        m = compute_metrics(y_true[mask], y_prob[mask], threshold)
        m["group_col"]   = group_col
        m["group_value"] = str(group_val)
        m["n_group"]     = int(mask.sum())
        results.append(m)
    return pd.DataFrame(results)


def equity_gap(
    subgroup_df: pd.DataFrame,
    reference_group: str,
    metric: str = "auroc",
) -> pd.DataFrame:
    ref = subgroup_df.loc[
        subgroup_df["group_value"] == reference_group, metric
    ].values
    if len(ref) == 0:
        return subgroup_df
    df = subgroup_df.copy()
    df[f"{metric}_gap"] = (df[metric] - ref[0]).round(4)
    return df


# ── Failure mode profiling ────────────────────────────────────────────────────

def profile_failure_modes(
    df: pd.DataFrame,
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """Profile false negatives (missed complications) and false positives."""
    y_pred = (y_prob >= threshold).astype(int)
    df_ = df.copy()
    df_["_y_true"] = y_true
    df_["_y_prob"] = y_prob
    df_["_y_pred"] = y_pred

    fn_mask = (df_["_y_true"] == 1) & (df_["_y_pred"] == 0)
    fp_mask = (df_["_y_true"] == 0) & (df_["_y_pred"] == 1)

    fn_df = df_[fn_mask].copy()
    fp_df = df_[fp_mask].copy()

    n_pos = int(y_true.sum())
    n_neg = int((1 - y_true).sum())

    fn_rate = round(fn_mask.sum() / n_pos, 4) if n_pos > 0 else 0.0
    fp_rate = round(fp_mask.sum() / n_neg, 4) if n_neg > 0 else 0.0

    fn_blood_miss = 0.0
    fp_asa1_rate  = 0.0
    if "blood_loss_missing" in fn_df.columns and len(fn_df) > 0:
        fn_blood_miss = round(float(fn_df["blood_loss_missing"].mean()), 4)
    if "asa_class" in fp_df.columns and len(fp_df) > 0:
        fp_asa1_rate = round(float((fp_df["asa_class"] <= 2).mean()), 4)

    return {
        "fn_df":           fn_df.drop(columns=["_y_true", "_y_prob", "_y_pred"], errors="ignore"),
        "fp_df":           fp_df.drop(columns=["_y_true", "_y_prob", "_y_pred"], errors="ignore"),
        "fn_rate":         fn_rate,
        "fp_rate":         fp_rate,
        "fn_blood_miss":   fn_blood_miss,
        "fp_asa1_rate":    fp_asa1_rate,
    }


# ── Inter-model disagreement ──────────────────────────────────────────────────

def disagreement_set(
    y_prob_a: np.ndarray,
    y_prob_b: np.ndarray,
    threshold: float = 0.5,
) -> np.ndarray:
    pred_a = (y_prob_a >= threshold).astype(int)
    pred_b = (y_prob_b >= threshold).astype(int)
    return pred_a != pred_b


# ── Ward simulation translation ───────────────────────────────────────────────

def clinical_translation(m: dict, prevalence: float) -> dict:
    """Convert metrics to plain-English ward simulation (per 100 step-down patients)."""
    n_comp  = round(prevalence * 100)
    n_nocomp = 100 - n_comp

    caught       = round(m["sensitivity"] * n_comp)
    missed       = n_comp - caught
    cleared      = round(m["specificity"] * n_nocomp)
    false_alerts = n_nocomp - cleared

    ppv_pct = round(m["ppv"] * 100)
    npv_pct = round(m["npv"] * 100)
    miss_pct = round((1 - m["sensitivity"]) * 100)

    bs = m["brier_score"]
    if bs < 0.10:
        calib = "excellent — risk scores can inform monitoring intensity directly"
    elif bs < 0.15:
        calib = "good — risk scores are broadly reliable for triage"
    elif bs < 0.22:
        calib = "moderate — use as ranks, not absolute probabilities"
    else:
        calib = "poor — do not set monitoring thresholds from raw scores"

    return {
        "n_comp":      n_comp,
        "n_nocomp":    n_nocomp,
        "caught":      caught,
        "missed":      missed,
        "cleared":     cleared,
        "false_alerts": false_alerts,
        "q1": (
            f"**Per 100 patients stepped down** (est. {n_comp} with major complication risk):\n\n"
            f"- Model flags **{caught}** correctly — and **misses {missed}** ({miss_pct}% miss rate).\n"
            f"- Raises **{false_alerts} unnecessary escalation alerts** among {n_nocomp} low-risk patients."
        ),
        "q2": (
            f"**When the model alerts**, it is correct **{ppv_pct}%** of the time (PPV).\n"
            + (f"Roughly 1 in {round(100/ppv_pct)} alerts corresponds to a true complication."
               if ppv_pct > 0 else "PPV undefined at this threshold.")
        ),
        "q3": (
            f"**When the model gives the all-clear**, it is correct **{npv_pct}%** of the time (NPV).\n"
            + ("High NPV — standard monitoring is safe for low-risk patients."
               if npv_pct >= 92
               else f"{100-npv_pct}% of 'low risk' patients may still experience complications — "
                    "consider a safety net observation protocol.")
        ),
        "q4": f"**Calibration (Brier {m['brier_score']}):** {calib}.",
    }


# ── Metrics I/O ───────────────────────────────────────────────────────────────

def save_metrics_csv(metrics: list | dict | pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(metrics, pd.DataFrame):
        metrics.to_csv(path, index=False)
    elif isinstance(metrics, list):
        pd.DataFrame(metrics).to_csv(path, index=False)
    else:
        pd.DataFrame([metrics]).to_csv(path, index=False)
