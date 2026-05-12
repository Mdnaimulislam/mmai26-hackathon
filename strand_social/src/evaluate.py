"""Evaluation utilities for the Housing Strand — data quality & forecast error.

This strand audits dataset readiness and a fixed baseline forecast (no trainable
models). Implementations are provided for convenience; you may extend them in
your notebooks or add new functions for the judges' questions you want to
answer numerically.

The optional Streamlit app imports `summarise_forecast_errors` only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def mae_rmse_mbe(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float]:
    """Mean absolute error, RMSE, and mean bias error (mean residual = y_true - y_pred)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    err = y_true[mask] - y_pred[mask]
    if err.size == 0:
        return {"mae": float("nan"), "rmse": float("nan"), "mbe": float("nan")}
    return {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mbe": float(np.mean(err)),
    }


def missing_rate(series: pd.Series) -> float:
    """Fraction of rows that are NA or blank string (after strip)."""
    if series.dtype == object:
        s = series.astype(str).str.strip()
        bad = s.eq("") | s.eq("nan") | series.isna()
    else:
        bad = series.isna()
    return float(bad.mean())


def summarise_forecast_errors(
    df: pd.DataFrame,
    actual_col: str = "smart_meter_kwh",
    pred_col: str = "forecast_model",
    group_col: str = "property_type",
) -> pd.DataFrame:
    """Overall and per-group MAE / RMSE / MBE for the baseline forecast column."""
    need = {actual_col, pred_col, group_col}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing columns: {sorted(missing)}")

    overall = mae_rmse_mbe(df[actual_col].values, df[pred_col].values)
    rows = [{"group": "__overall__", **overall}]
    for g, sub in df.groupby(group_col):
        m = mae_rmse_mbe(sub[actual_col].values, sub[pred_col].values)
        rows.append({"group": str(g), **m})
    return pd.DataFrame(rows)


def load_benchmark_card(path: str | Path) -> dict:
    """Load `reference/benchmark_card.json` (or team copy) as a dict."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_audit_metrics_csv(rows: list[dict], path: str | Path) -> None:
    """Write a flat table of audit metrics (same *role* as evaluation_metrics.csv elsewhere)."""
    path = Path(path)
    pd.DataFrame(rows).to_csv(path, index=False)
