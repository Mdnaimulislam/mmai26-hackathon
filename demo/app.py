"""Clinical Strand — Post-Surgical Step-Down Safety Brief.

Solution concept: generate a personalised monitoring protocol for each patient
being transferred from ICU to a surgical ward, based on AI-predicted 30-day
complication risk. Distinct from the three strand challenge ideas:
  - not a model readiness gate (patient-level, not deployment-level)
  - not a real-time bedside alarm (proactive handover tool, not reactive)
  - not a population drift monitor (individual risk, not cohort shift)

Run:  streamlit run app.py

Expects:
  data/processed/test.csv
  saved_models/model_*.joblib

Writes on export:
  reference/omaib_pathway.json
  reference/model_safety_report.json
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.evaluate import (
    clinical_translation,
    compute_calibration,
    compute_metrics,
    compute_subgroup_metrics,
    disagreement_set,
    equity_gap,
    pr_curve_data,
    profile_failure_modes,
    roc_curve_data,
    save_metrics_csv,
)
from src.report import generate_json_pathway, generate_json_safety_report

from models.model_a import FEATURES as FEAT_A
from models.model_c import TABULAR_FEATURES as FEAT_C_TAB

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
DATA_DIR    = ROOT / "data" / "processed"
MODELS_DIR  = ROOT / "saved_models"
METRICS_DIR = ROOT / "saved_metrics"
REF_DIR     = ROOT / "reference"
REF_DIR.mkdir(exist_ok=True)

MODEL_LABELS = {
    "model_a": "Model A — Multimodal LightGBM",
    "model_c": "Model C — PyKale Multimodal Fusion",
}
# model_c uses a custom predict_proba_full() — handled separately below
MODEL_FEATURES = {
    "model_a": FEAT_A,
    "model_c": FEAT_C_TAB,
}
VERDICT_COLOURS = {
    "APPROVE":      "#1a7a1a",
    "CONDITIONAL":  "#b35c00",
    "NOT APPROVED": "#a01010",
}
COLOURS = ["#1f77b4", "#d62728", "#2ca02c"]


# ── loaders ───────────────────────────────────────────────────────────────────

@st.cache_data
def load_test_data() -> pd.DataFrame | None:
    p = DATA_DIR / "test.csv"
    return pd.read_csv(p) if p.exists() else None


@st.cache_data
def load_modality_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load notes.csv and vitals_series.csv from data/raw/."""
    raw = ROOT / "data" / "raw"
    notes_path  = raw / "notes.csv"
    vitals_path = raw / "vitals_series.csv"
    notes  = pd.read_csv(notes_path)  if notes_path.exists()  else pd.DataFrame()
    vitals = pd.read_csv(vitals_path) if vitals_path.exists() else pd.DataFrame()
    return notes, vitals


@st.cache_resource
def load_models() -> dict:
    out = {}
    for key in MODEL_LABELS:
        p = MODELS_DIR / f"{key}.joblib"
        if p.exists():
            out[key] = joblib.load(p)
    return out


# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Post-Surgical Step-Down Brief",
    page_icon="🏥",
    layout="wide",
)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 Clinical Strand")
    st.caption("Post-surgical complication prediction — step-down monitoring")
    st.divider()

    test_df = load_test_data()
    models  = load_models()
    all_notes, all_vitals = load_modality_data()

    # Filter modality files to test-set patients
    if test_df is not None and len(all_notes):
        test_pids   = set(test_df["patient_id"])
        test_notes  = all_notes[all_notes["patient_id"].isin(test_pids)].reset_index(drop=True)
        test_vitals = all_vitals[all_vitals["patient_id"].isin(test_pids)].reset_index(drop=True)
    else:
        test_notes  = pd.DataFrame()
        test_vitals = pd.DataFrame()

    if test_df is not None:
        st.success(f"test.csv loaded: {len(test_df):,} patients")
    else:
        st.error("test.csv not found.")
        st.info("Run python setup.py first.")

    loaded  = [k for k in MODEL_LABELS if k in models]
    missing = [k for k in MODEL_LABELS if k not in models]
    if loaded:
        st.success(f"Models loaded: {', '.join(loaded)}")
    if missing:
        st.warning(f"Models missing: {', '.join(missing)}")

    st.divider()
    threshold = st.slider("Decision threshold", 0.10, 0.90, 0.35, 0.05)
    st.caption("Post-surgical context: lower threshold = higher sensitivity (fewer missed complications).")

# ── compute predictions ────────────────────────────────────────────────────────
all_probs: dict[str, np.ndarray] = {}
all_preds: dict[str, np.ndarray] = {}
all_metrics: dict[str, dict] = {}

if test_df is not None and models:
    y_true = test_df["major_complication_30d"].values
    for key, model in models.items():
        if key == "model_c" and hasattr(model, "predict_proba_full"):
            prob = model.predict_proba_full(test_df, test_notes, test_vitals)[:, 1]
        else:
            # Each model selects its own features internally
            prob = model.predict_proba(test_df)[:, 1]
        all_probs[key]   = prob
        all_preds[key]   = (prob >= threshold).astype(int)
        all_metrics[key] = compute_metrics(y_true, prob, threshold, model_name=key)

prevalence = float(test_df["major_complication_30d"].mean()) if test_df is not None else 0.27

# ── tabs ──────────────────────────────────────────────────────────────────────
tab_brief, tab_perf, tab_equity, tab_fail, tab_deploy, tab_report = st.tabs([
    "📋 Step-Down Brief",
    "📊 Model Performance",
    "⚖️ Equity & MNAR",
    "🔍 Failure Modes",
    "🏥 Deployment Assessment",
    "📝 Report Builder",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — STEP-DOWN BRIEF (THE SOLUTION)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_brief:
    st.header("Post-Surgical Step-Down Monitoring Brief")
    st.caption(
        "Select a patient from the test set. The tool generates a personalised ward "
        "monitoring protocol based on AI-predicted 30-day complication risk. "
        "This brief is intended for handover — it is not a real-time alarm."
    )

    if test_df is None or not all_probs:
        st.warning("Run `python setup.py` first to generate data and models.")
        st.stop()

    col_sel, col_info = st.columns([1, 2])

    with col_sel:
        patient_ids = test_df["patient_id"].tolist()
        selected_id = st.selectbox("Select patient", patient_ids)
        idx = test_df[test_df["patient_id"] == selected_id].index[0]
        row = test_df.loc[idx]

        st.markdown("**Patient summary**")
        st.markdown(f"- Age: **{int(row['age'])}** | Sex: **{row['sex']}**")
        st.markdown(f"- Surgery: **{row['surgery_type'].capitalize()}** | ASA class: **{int(row['asa_class'])}**")
        st.markdown(f"- Op duration: **{row['op_duration_h']:.1f} h** | ICU hours: **{int(row['icu_hours'])}**")
        st.markdown(f"- Blood loss recorded: **{'No' if row['blood_loss_missing'] else 'Yes'}**")
        if not row["blood_loss_missing"]:
            st.markdown(f"  Blood loss: **{int(row['blood_loss_ml'])} mL** | Transfused: **{'Yes' if row['transfused'] else 'No'}**")
        st.markdown(f"- Diabetes: **{'Yes' if row['has_diabetes'] else 'No'}** | Hypertension: **{'Yes' if row['has_hypertension'] else 'No'}**")

    with col_info:
        st.markdown("**ICU vitals (24 h mean)**")
        vc1, vc2, vc3, vc4, vc5 = st.columns(5)
        vc1.metric("HR (bpm)",   f"{row['hr_mean']:.0f}")
        vc2.metric("SBP (mmHg)", f"{row['sbp_mean']:.0f}")
        vc3.metric("SpO₂ (%)",   f"{row['spo2_mean']:.1f}")
        vc4.metric("Temp (°C)",  f"{row['temp_mean']:.1f}")
        vc5.metric("Lactate",    f"{row['icu_lactate']:.2f}")

        st.markdown("**Pre-op labs**")
        lc1, lc2, lc3 = st.columns(3)
        lc1.metric("Creatinine (mg/dL)", f"{row['preop_creatinine']:.2f}")
        lc2.metric("WBC (×10⁹/L)",       f"{row['preop_wbc']:.1f}")
        lc3.metric("Lactate pre-op",      f"{row['preop_lactate']:.2f}")

    st.divider()

    # ── AI risk assessment ─────────────────────────────────────────────────────
    st.subheader("AI Risk Assessment")

    risk_probs = {}
    for key, model in models.items():
        if key == "model_c" and hasattr(model, "predict_proba_full"):
            pt_notes  = test_notes[test_notes["patient_id"] == selected_id] if len(test_notes) else pd.DataFrame()
            pt_vitals = test_vitals[test_vitals["patient_id"] == selected_id] if len(test_vitals) else pd.DataFrame()
            prob = model.predict_proba_full(test_df.loc[[idx]], pt_notes, pt_vitals)[0, 1]
        else:
            prob = model.predict_proba(test_df.loc[[idx]])[0, 1]
        risk_probs[key] = prob

    rc1, rc2 = st.columns(2)
    for col, (key, label) in zip([rc1, rc2], MODEL_LABELS.items()):
        if key not in risk_probs:
            continue
        p = risk_probs[key]
        if p >= threshold + 0.15:
            level, colour = "HIGH RISK", "#a01010"
        elif p >= threshold - 0.05:
            level, colour = "MODERATE", "#b35c00"
        else:
            level, colour = "LOW RISK", "#1a7a1a"

        bar_filled = int(round(p * 20))
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        col.markdown(
            f"**{label.split('—')[0].strip()}**\n\n"
            f"`{bar}` **{p:.2f}**\n\n"
            f"<span style='background:{colour};color:white;padding:3px 10px;"
            f"border-radius:4px;font-size:0.9em'>{level}</span>",
            unsafe_allow_html=True,
        )

    n_high = sum(1 for p in risk_probs.values() if p >= threshold + 0.15)
    n_mod  = sum(1 for p in risk_probs.values() if threshold - 0.05 <= p < threshold + 0.15)
    if n_high >= 1:
        consensus_label, consensus_col = "HIGH RISK", "#a01010"
    elif n_mod >= 1:
        consensus_label, consensus_col = "MODERATE RISK", "#b35c00"
    else:
        consensus_label, consensus_col = "LOW RISK", "#1a7a1a"

    st.markdown(
        f"**Consensus risk ({n_high}/2 models flag HIGH):** "
        f"<span style='background:{consensus_col};color:white;padding:4px 14px;"
        f"border-radius:4px;font-weight:bold'>{consensus_label}</span>",
        unsafe_allow_html=True,
    )

    # MNAR caveats
    if row["blood_loss_missing"]:
        st.warning(
            "⚠️  Blood loss not recorded for this patient (MNAR). "
            "Model A uses mean imputation — risk may be underestimated. "
            "Model C's multimodal fusion is also affected."
        )
    if not row["has_notes"]:
        st.warning(
            "⚠️  No clinical note available for this patient. "
            "Model C's text branch receives a zero vector — prediction degrades "
            "to tabular-only performance. Consider Model A for this patient."
        )

    st.divider()

    # ── Monitoring protocol ────────────────────────────────────────────────────
    st.subheader("Recommended Monitoring Protocol")

    mean_risk = np.mean(list(risk_probs.values()))

    if consensus_label == "HIGH RISK":
        obs_freq   = "Every **1 hour** for first 12 hours, then every 2 hours"
        hr_thresh  = 108
        sbp_thresh = 88
        spo2_thresh = 92
        lac_thresh  = 2.5
        temp_thresh = 38.4
    elif consensus_label == "MODERATE RISK":
        obs_freq   = "Every **2 hours** for first 12 hours, then every 4 hours"
        hr_thresh  = 112
        sbp_thresh = 90
        spo2_thresh = 93
        lac_thresh  = 3.0
        temp_thresh = 38.6
    else:
        obs_freq   = "Every **4 hours** (standard ward protocol)"
        hr_thresh  = 115
        sbp_thresh = 92
        spo2_thresh = 93
        lac_thresh  = 3.5
        temp_thresh = 38.8

    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown(f"**Observations:** {obs_freq}")
        st.markdown("**Escalation triggers — contact surgical registrar if:**")
        st.markdown(
            f"- HR > **{hr_thresh}** bpm (sustained >20 min)\n"
            f"- SBP < **{sbp_thresh}** mmHg\n"
            f"- SpO₂ < **{spo2_thresh}%**\n"
            f"- Lactate > **{lac_thresh}** mmol/L\n"
            f"- Temperature > **{temp_thresh}** °C\n"
            f"- Urine output < 0.5 mL/kg/h for 2 consecutive hours\n"
            f"- Patient reports severe pain (>8/10) or confusion"
        )

    with pc2:
        st.markdown("**Top risk factors driving this assessment:**")
        # Rank factors by how far they deviate from the safe range
        factors = []
        if row["asa_class"] >= 3:
            factors.append(f"ASA class {int(row['asa_class'])} — severe systemic disease")
        if row["surgery_type"] in ["cardiac", "vascular"]:
            comp_rate = {"cardiac": "~40%", "vascular": "~32%"}[row["surgery_type"]]
            factors.append(f"{row['surgery_type'].capitalize()} surgery — 30-day complication rate {comp_rate}")
        if not row["blood_loss_missing"] and row["blood_loss_ml"] > 600:
            factors.append(f"High intraoperative blood loss ({int(row['blood_loss_ml'])} mL)")
        elif row["blood_loss_missing"]:
            factors.append("Blood loss not recorded — MNAR uncertainty applies")
        if row["transfused"]:
            factors.append("Received intraoperative transfusion")
        if row["icu_lactate"] > 2.0:
            factors.append(f"Elevated ICU lactate ({row['icu_lactate']:.2f} mmol/L)")
        if row["preop_creatinine"] > 1.4:
            factors.append(f"Elevated pre-op creatinine ({row['preop_creatinine']:.2f} mg/dL)")
        if row["has_diabetes"]:
            factors.append("Diabetes mellitus")

        if not factors:
            factors = ["No individual high-risk features identified — routine monitoring applies"]

        for i, f in enumerate(factors[:5], 1):
            st.markdown(f"**{i}.** {f}")

    st.divider()

    # ── Handover summary ───────────────────────────────────────────────────────
    st.subheader("Handover Summary (plain language)")

    summary = (
        f"Patient **{selected_id}** is a **{int(row['age'])}-year-old {row['sex']}** "
        f"who underwent **{row['surgery_type']} surgery** (ASA class {int(row['asa_class'])}, "
        f"duration {row['op_duration_h']:.1f} hours). "
        f"They spent **{int(row['icu_hours'])} hours** in the ICU before step-down.\n\n"
        f"AI risk stratification assigns **{consensus_label}** of 30-day major complication "
        f"(mean probability {mean_risk:.2f} across {len(risk_probs)} models).\n\n"
        f"Recommended monitoring: **{obs_freq.replace('**', '')}**. "
        f"Priority escalation triggers have been set for HR >{hr_thresh}, "
        f"SBP <{sbp_thresh} mmHg, SpO₂ <{spo2_thresh}%, or lactate >{lac_thresh} mmol/L.\n\n"
    )

    if row["blood_loss_missing"]:
        summary += (
            "**Note:** Intraoperative blood loss was not recorded for this patient. "
            "Model C's prediction carries additional uncertainty. "
            "Clinical judgement should weight Model A more heavily.\n\n"
        )

    summary += (
        "*This brief is generated by an AI risk stratification tool and is advisory only. "
        "Clinical judgement must always override algorithmic recommendations.*"
    )

    st.markdown(summary)

    actual = int(row["major_complication_30d"])
    if actual == 1:
        st.error(f"**Test-set ground truth:** This patient DID experience a major complication (label = 1).")
    else:
        st.success(f"**Test-set ground truth:** This patient did NOT experience a major complication (label = 0).")

    st.caption("Ground truth is shown here for evaluation purposes only. In deployment, the outcome is not known at the time of step-down.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MODEL PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_perf:
    st.header("Model performance — test set")

    if not all_metrics:
        st.warning("No models or test data loaded.")
        st.stop()

    y_true = test_df["major_complication_30d"].values

    for key, label in MODEL_LABELS.items():
        if key not in all_metrics:
            st.info(f"{label} not loaded.")
            continue

        m = all_metrics[key]
        trans = clinical_translation(m, prevalence)

        st.subheader(label)
        c1, c2, c3 = st.columns(3)
        c1.metric("AUROC",       m["auroc"])
        c2.metric("AUPRC",       m["auprc"])
        c3.metric("Brier score", m["brier_score"])

        c4, c5, c6, c7 = st.columns(4)
        c4.metric("Sensitivity", m["sensitivity"])
        c5.metric("Specificity", m["specificity"])
        c6.metric("PPV",         m["ppv"])
        c7.metric("NPV",         m["npv"])

        col_roc, col_pr, col_cal = st.columns(3)

        with col_roc:
            roc = roc_curve_data(y_true, all_probs[key])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=roc["fpr"], y=roc["tpr"], mode="lines",
                name=f"ROC (AUC={m['auroc']})",
                line=dict(color=COLOURS[list(MODEL_LABELS).index(key)]),
            ))
            fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                          line=dict(dash="dash", color="grey"))
            fig.update_layout(title="ROC curve", xaxis_title="FPR", yaxis_title="TPR",
                              height=250, margin=dict(t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_pr:
            pr = pr_curve_data(y_true, all_probs[key])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=pr["recall"], y=pr["precision"], mode="lines",
                name=f"PR (AP={m['auprc']})",
                line=dict(color=COLOURS[list(MODEL_LABELS).index(key)]),
            ))
            fig.add_shape(type="line", x0=0, y0=prevalence, x1=1, y1=prevalence,
                          line=dict(dash="dash", color="grey"))
            fig.update_layout(title="PR curve", xaxis_title="Recall", yaxis_title="Precision",
                              height=250, margin=dict(t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_cal:
            cal = compute_calibration(y_true, all_probs[key])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=cal["mean_predicted"], y=cal["fraction_positive"],
                mode="markers+lines", name="Calibration",
                marker=dict(size=8, color=COLOURS[list(MODEL_LABELS).index(key)]),
            ))
            fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1,
                          line=dict(dash="dash", color="grey"))
            fig.update_layout(title="Calibration", xaxis_title="Mean predicted prob",
                              yaxis_title="Fraction positive",
                              height=250, margin=dict(t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with st.expander(f"Ward simulation — {label}"):
            st.markdown(trans["q1"])
            st.markdown(trans["q2"])
            st.markdown(trans["q3"])
            st.markdown(trans["q4"])

        st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — EQUITY & MNAR
# ═══════════════════════════════════════════════════════════════════════════════
with tab_equity:
    st.header("Equity & MNAR analysis")
    st.caption(
        "Evaluate whether each model performs equitably across surgery types. "
        "Model A uses blood_loss_imputed (MNAR for ~36% of cardiac/vascular cases). "
        "Model C depends on note_text (MNAR for ~31% of patients) and blood_loss_imputed — "
        "performance degrades for notes-absent patients."
    )

    if test_df is None or not all_probs:
        st.warning("No test data or model predictions available.")
        st.stop()

    y_true = test_df["major_complication_30d"].values

    # ── Surgery-type subgroup metrics ─────────────────────────────────────────
    st.subheader("Metrics by surgery type")
    stype_rows = []
    for key, label in MODEL_LABELS.items():
        if key not in all_probs:
            continue
        sub = compute_subgroup_metrics(
            test_df, all_probs[key],
            group_col="surgery_type", threshold=threshold,
        )
        sub["model"] = label
        stype_rows.append(sub)

    if stype_rows:
        stype_df = pd.concat(stype_rows, ignore_index=True)
        st.dataframe(
            stype_df[["model", "group_value", "auroc", "sensitivity", "ppv", "n_group"]].rename(
                columns={"group_value": "Surgery type", "model": "Model",
                         "auroc": "AUROC", "sensitivity": "Sensitivity",
                         "ppv": "PPV", "n_group": "N patients"}
            ),
            hide_index=True, use_container_width=True,
        )

    # ── AUROC gap bar chart ───────────────────────────────────────────────────
    st.subheader("AUROC equity gap by surgery type (reference = abdominal)")
    gap_rows = []
    for key, label in MODEL_LABELS.items():
        if key not in all_probs:
            continue
        sub = compute_subgroup_metrics(
            test_df, all_probs[key],
            group_col="surgery_type", threshold=threshold,
        )
        gapped = equity_gap(sub, reference_group="abdominal", metric="auroc")
        for _, row in gapped.iterrows():
            gap_rows.append({
                "Model": label,
                "Surgery type": row["group_value"],
                "AUROC gap vs abdominal": row.get("auroc_gap", 0.0),
            })

    if gap_rows:
        gap_df = pd.DataFrame(gap_rows)
        fig = go.Figure()
        for i, (key, label) in enumerate(MODEL_LABELS.items()):
            sg = gap_df[gap_df["Model"] == label]
            fig.add_trace(go.Bar(
                name=label, x=sg["Surgery type"],
                y=sg["AUROC gap vs abdominal"],
                marker_color=COLOURS[i],
                text=sg["AUROC gap vs abdominal"].round(3),
                textposition="outside",
            ))
        fig.add_shape(type="line", x0=-0.5, y0=0, x1=3.5, y1=0,
                      line=dict(color="black", dash="dash"))
        fig.update_layout(
            barmode="group", xaxis_title="Surgery type",
            yaxis_title="AUROC gap vs abdominal",
            height=320, margin=dict(t=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Model C expected to show negative gaps for cardiac/vascular surgery (notes MNAR). "
            "Zero = performs equally to abdominal reference group."
        )

    st.divider()

    # ── ASA class subgroup ────────────────────────────────────────────────────
    st.subheader("Metrics by ASA class")
    asa_rows = []
    for key, label in MODEL_LABELS.items():
        if key not in all_probs:
            continue
        sub = compute_subgroup_metrics(
            test_df, all_probs[key],
            group_col="asa_class", threshold=threshold,
        )
        sub["model"] = label
        asa_rows.append(sub)

    if asa_rows:
        asa_df = pd.concat(asa_rows, ignore_index=True)
        st.dataframe(
            asa_df[["model", "group_value", "auroc", "sensitivity", "n_group"]].rename(
                columns={"group_value": "ASA class", "model": "Model",
                         "auroc": "AUROC", "sensitivity": "Sensitivity", "n_group": "N"}
            ),
            hide_index=True, use_container_width=True,
        )

    st.divider()

    # ── Model C MNAR ─────────────────────────────────────────────────────────
    st.subheader("Model C — blood_loss_missing MNAR subgroup")
    if "model_c" in all_probs and "blood_loss_missing" in test_df.columns:
        miss_sub = compute_subgroup_metrics(
            test_df, all_probs["model_c"],
            group_col="blood_loss_missing", threshold=threshold,
        )
        st.dataframe(
            miss_sub[["group_value", "auroc", "auprc", "sensitivity", "n_group"]].rename(
                columns={"group_value": "blood_loss_missing",
                         "auroc": "AUROC", "auprc": "AUPRC",
                         "sensitivity": "Sensitivity", "n_group": "N"}
            ),
            hide_index=True, use_container_width=True,
        )
        sub0 = miss_sub[miss_sub["group_value"] == "0"]
        sub1 = miss_sub[miss_sub["group_value"] == "1"]
        if not sub0.empty and not sub1.empty:
            gap = round(float(sub1["auroc"].iloc[0]) - float(sub0["auroc"].iloc[0]), 4)
            st.warning(
                f"**MNAR AUROC gap:** blood loss observed = {float(sub0['auroc'].iloc[0]):.4f} "
                f"vs blood loss missing = {float(sub1['auroc'].iloc[0]):.4f} "
                f"(gap = {gap:+.4f}). "
                "Note: subgroup AUROCs are noisy with small n — see calibration analysis below."
            )

        # Calibration comparison (more robust than AUROC with small n)
        st.markdown("**Model C — predicted risk vs actual rate by MNAR status**")
        mnar_mask = (test_df["blood_loss_missing"] == 1).values
        obs_mask  = (test_df["blood_loss_missing"] == 0).values
        cal_rows  = []
        for mask, grp in [(obs_mask, "Blood loss recorded"), (mnar_mask, "Blood loss MISSING (MNAR)")]:
            if mask.sum() > 3:
                pred   = float(all_probs["model_c"][mask].mean())
                actual = float(y_true[mask].mean())
                cal_rows.append({
                    "Group":                             f"{grp}  (n={mask.sum()})",
                    "Model C mean predicted probability": f"{pred:.1%}",
                    "Actual complication rate":           f"{actual:.1%}",
                    "Bias (actual − predicted)":         f"{actual - pred:+.1%}",
                })
        if cal_rows:
            st.dataframe(pd.DataFrame(cal_rows), hide_index=True, use_container_width=True)
            if len(cal_rows) == 2:
                pred_obs  = float(all_probs["model_c"][obs_mask].mean())
                act_obs   = float(y_true[obs_mask].mean())
                pred_mnar = float(all_probs["model_c"][mnar_mask].mean())
                act_mnar  = float(y_true[mnar_mask].mean())
                bias_obs  = act_obs  - pred_obs
                bias_mnar = act_mnar - pred_mnar
                if abs(bias_mnar) > abs(bias_obs) + 0.04:
                    st.warning(
                        f"Model C underestimates risk for MNAR patients by **{abs(bias_mnar):.1%}** "
                        f"(vs {abs(bias_obs):.1%} for observed patients). "
                        "Blood loss is mean-imputed for MNAR cases (~650 mL vs true average ~950+ mL), "
                        "causing systematically low risk predictions for the highest-risk subgroup."
                    )

    st.divider()

    # ── Equity narrative text areas ───────────────────────────────────────────
    st.subheader("Equity analysis — team responses")
    st.markdown("**Which surgery type shows the largest AUROC gap across models, and why?**")
    st.text_area("eq1", key="eq1_clin", height=80, label_visibility="collapsed",
                 placeholder="e.g., 'Cardiac surgery shows the largest gap — blood loss is MNAR for ~58% of cardiac patients, causing mean-imputed risk to be systematically underestimated ...'")

    st.markdown("**Is the MNAR blood loss gap in Model A an equity concern?**")
    st.text_area("eq2", key="eq2_clin", height=80, label_visibility="collapsed",
                 placeholder="e.g., 'Blood loss is missing for the highest-risk cardiac/vascular patients. Model A uses mean imputation — it is least reliable exactly where reliable predictions matter most ...'")

    st.markdown("**How does note absence affect Model C, and for which patients?**")
    st.text_area("eq3", key="eq3_clin", height=80, label_visibility="collapsed",
                 placeholder="e.g., 'Model C degrades to tabular-only performance when notes are absent. Notes are absent for ~61% of cardiac patients — the highest-risk subgroup ...'")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — FAILURE MODES
# ═══════════════════════════════════════════════════════════════════════════════
with tab_fail:
    st.header("Failure mode analysis")
    st.caption(
        "Profile missed complications (false negatives) and unnecessary escalations "
        "(false positives). False negatives are the high-consequence failure in this context."
    )

    if test_df is None or not all_probs:
        st.warning("No test data or model predictions available.")
        st.stop()

    y_true = test_df["major_complication_30d"].values

    for key, label in MODEL_LABELS.items():
        if key not in all_probs:
            continue

        st.subheader(label)
        failure = profile_failure_modes(test_df, y_true, all_probs[key], threshold)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("False negative rate", f"{failure['fn_rate']:.1%}",
                  help="Fraction of patients with complications that were missed")
        c2.metric("False positive rate", f"{failure['fp_rate']:.1%}",
                  help="Fraction of low-risk patients unnecessarily escalated")
        c3.metric("FN: blood loss missing", f"{failure['fn_blood_miss']:.1%}",
                  help="Of missed complications — fraction where blood loss was not recorded")
        c4.metric("FP: ASA 1–2 rate", f"{failure['fp_asa1_rate']:.1%}",
                  help="Of false positives — fraction who are ASA 1 or 2 (low surgical risk)")

        col_fn, col_fp = st.columns(2)
        show_cols = [c for c in ["surgery_type", "asa_class", "icu_lactate",
                                  "blood_loss_missing", "major_complication_30d"]
                     if c in test_df.columns]

        with col_fn:
            st.markdown("**Missed complications (false negatives) — top 10**")
            fn_df = failure["fn_df"]
            if not fn_df.empty:
                st.dataframe(fn_df[[c for c in show_cols if c in fn_df.columns]].head(10),
                             hide_index=True, use_container_width=True)
            else:
                st.info("No false negatives at this threshold.")

        with col_fp:
            st.markdown("**Unnecessary escalations (false positives) — top 10**")
            fp_df = failure["fp_df"]
            if not fp_df.empty:
                st.dataframe(fp_df[[c for c in show_cols if c in fp_df.columns]].head(10),
                             hide_index=True, use_container_width=True)
            else:
                st.info("No false positives at this threshold.")

        # Feature importance for Model A
        if key == "model_a" and key in models:
            try:
                raw_model = models[key]
                fi = pd.Series(
                    raw_model.feature_importances_,
                    index=MODEL_FEATURES["model_a"],
                ).sort_values(ascending=False)
                st.markdown("**Feature importance — Model A (LightGBM gain)**")
                fig = go.Figure(go.Bar(
                    x=fi.values[:15], y=fi.index[:15],
                    orientation="h", marker_color="#1f77b4",
                ))
                fig.update_layout(
                    xaxis_title="Importance",
                    yaxis=dict(autorange="reversed"),
                    height=340, margin=dict(t=10),
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.info("Feature importance unavailable for this model.")

        st.markdown(f"**FN narrative — {label}**")
        st.text_area("fn", key=f"fn_narr_{key}", height=80, label_visibility="collapsed",
                     placeholder="Which patients does this model most often miss? Is blood loss missingness a factor?")

        st.markdown(f"**FP narrative — {label}**")
        st.text_area("fp", key=f"fp_narr_{key}", height=80, label_visibility="collapsed",
                     placeholder="Are false positives concentrated in low-ASA patients or specific surgery types?")

        if key == "model_a":
            st.markdown("**Feature importance narrative — Model A**")
            st.text_area("fi", key=f"fi_narr_{key}", height=80, label_visibility="collapsed",
                         placeholder="What do the top features tell you about how Model A makes its predictions?")

        st.divider()

    # ── Model disagreement ─────────────────────────────────────────────────────
    st.subheader("Model disagreement (A vs C)")
    if len(all_probs) >= 2:
        keys = list(all_probs.keys())
        pairs = [(keys[i], keys[j]) for i in range(len(keys)) for j in range(i + 1, len(keys))]
        for ka, kb in pairs:
            dis = disagreement_set(all_probs[ka], all_probs[kb], threshold)
            st.metric(
                f"{MODEL_LABELS[ka]} vs {MODEL_LABELS[kb]}",
                f"{dis.mean():.1%} of test patients",
                help="Rows where the two models predict different classes at the current threshold.",
            )
        st.markdown("**Disagreement narrative**")
        st.text_area("dis", key="disagree_narr", height=80, label_visibility="collapsed",
                     placeholder="On which patient types do Model A and Model C disagree? Are notes-absent or cardiac patients over-represented in disagreements?")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — DEPLOYMENT ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_deploy:
    st.header("Clinical deployment assessment")
    st.caption(
        "Answer the five deployment questions for each model. "
        "These answers feed directly into the model_safety_report.json (item C)."
    )

    if not all_metrics:
        st.warning("No model metrics available.")
        st.stop()

    y_true = test_df["major_complication_30d"].values

    for key, label in MODEL_LABELS.items():
        if key not in all_metrics:
            continue

        m = all_metrics[key]
        trans = clinical_translation(m, prevalence)
        st.subheader(label)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AUROC",       m["auroc"])
        c2.metric("Sensitivity", m["sensitivity"])
        c3.metric("PPV",         m["ppv"])
        c4.metric("NPV",         m["npv"])

        # Ward simulation counts
        with st.expander(f"Ward simulation — {label}"):
            n_comp   = trans["n_comp"]
            n_nocomp = trans["n_nocomp"]
            caught   = trans["caught"]
            missed   = trans["missed"]
            false_a  = trans["false_alerts"]
            cleared  = trans["cleared"]
            sim_df = pd.DataFrame({
                "Group":     ["Patients with complication", "Patients without complication"],
                "Flagged":   [caught, false_a],
                "Not flagged": [missed, cleared],
            })
            st.caption(f"Per 100 step-down patients (est. {n_comp} with complication risk)")
            st.dataframe(sim_df, hide_index=True, use_container_width=True)
            st.markdown(trans["q1"])

        st.markdown(f"**Q1 — How many patients with complications will this model miss?**")
        st.text_area(
            "dq1", key=f"dq1_{key}", height=80, label_visibility="collapsed",
            placeholder=f"e.g., 'At threshold {threshold}: {trans['missed']} of ~{trans['n_comp']} patients with complications will be missed ({trans['missed']/trans['n_comp']:.1%} miss rate) ...'",
        )

        st.markdown(f"**Q2 — When the model alerts, how often is there an actual complication?**")
        st.text_area(
            "dq2", key=f"dq2_{key}", height=80, label_visibility="collapsed",
            placeholder=f"e.g., 'PPV = {m['ppv']} — roughly {round(m['ppv']*100)}% of alerts correspond to actual complications ...'",
        )

        st.markdown(f"**Q3 — When the model gives the all-clear, is it safe to use standard monitoring?**")
        st.text_area(
            "dq3", key=f"dq3_{key}", height=80, label_visibility="collapsed",
            placeholder=f"e.g., 'NPV = {m['npv']} — {round((1-m['npv'])*100)}% of all-clear patients may still have complications ...'",
        )

        st.markdown(f"**Q4 — How well does this model separate high- from low-risk patients?**")
        st.text_area(
            "dq4", key=f"dq4_{key}", height=80, label_visibility="collapsed",
            placeholder=f"e.g., 'AUROC = {m['auroc']} — the model ranks a complication patient above a non-complication patient {round(m['auroc']*100)}% of the time ...'",
        )

        st.markdown(f"**Q5 — Are there specific patient groups where this model is less reliable?**")
        st.text_area(
            "dq5", key=f"dq5_{key}", height=80, label_visibility="collapsed",
            placeholder="e.g., 'Model A under-performs for cardiac/vascular patients with missing blood loss (MNAR) — mean imputation suppresses risk signal for the highest-acuity cases ...'",
        )

        st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — REPORT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
with tab_report:
    st.header("Report builder")
    st.caption(
        "Work through each model, select a verdict, enter conditions and narrative. "
        "Then export omaib_pathway.json (item B) and model_safety_report.json (item C)."
    )

    st.subheader("Team information")
    team_name    = st.text_input("Team name",    placeholder="e.g., Surgical AI Auditors")
    team_members = st.text_input("Team members", placeholder="Alice, Bob, Carol")

    st.divider()

    for key, label in MODEL_LABELS.items():
        st.subheader(label)

        if key in all_metrics:
            m = all_metrics[key]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("AUROC",       m["auroc"])
            c2.metric("AUPRC",       m["auprc"])
            c3.metric("Sensitivity", m["sensitivity"])
            c4.metric("PPV",         m["ppv"])

        with st.expander(f"Governance checklist — {label}"):
            st.radio("Is the overall AUROC adequate for the monitoring context?",
                     ["Yes — AUROC is sufficient",
                      "No — AUROC too low for this use case",
                      "Conditional — acceptable with documented limitations"],
                     key=f"gc_auroc_{key}")
            st.radio("Are equity gaps across surgery types acceptable?",
                     ["Yes — gaps within acceptable range",
                      "No — gaps require investigation before deployment",
                      "Uncertain — domain expert review required"],
                     key=f"gc_eq_{key}")
            st.radio("Is the MNAR blood loss issue adequately handled?",
                     ["Yes — blood_loss_missing indicator compensates adequately",
                      "No — model is not reliable for blood-loss-missing patients",
                      "Conditional — use with documented caveats for missing records"],
                     key=f"gc_mnar_{key}")

        st.selectbox(f"Verdict — {label}", ["APPROVE", "CONDITIONAL", "NOT APPROVED"],
                     key=f"verdict_{key}")
        vc = VERDICT_COLOURS.get(st.session_state.get(f"verdict_{key}", "CONDITIONAL"), "#555")
        st.markdown(
            f"<span style='background:{vc};color:white;padding:5px 16px;"
            f"border-radius:4px;font-weight:bold;font-size:1.05em'>"
            f"{st.session_state.get(f'verdict_{key}', 'CONDITIONAL')}</span>",
            unsafe_allow_html=True,
        )

        st.text_area(f"Conditions — {label}", key=f"cond_{key}", height=80,
                     placeholder="e.g., 'Must not be used as the sole risk tool for vascular surgery patients.'")
        st.text_area(f"Assessment narrative — {label}", key=f"narr_{key}", height=120,
                     placeholder="Summarise this model's strengths, failure modes, and the conditions for safe use.")
        st.divider()

    # ── Option-specific (E) ────────────────────────────────────────────────────
    st.subheader("E. Option-specific deliverable")
    st.caption(
        "This demo uses the step-down brief concept. "
        "The option_specific section captures the brief's risk stratification logic."
    )
    opt_type = st.selectbox("Option type", ["scoring_rubric", "alert_burden_analysis",
                                             "threshold_sensitivity_report"])
    opt_title = st.text_input("Option title", value="Post-Surgical Step-Down Risk Stratification")
    opt_content = st.text_area("Option content (JSON or plain text)", height=120,
                               placeholder='{"low_threshold": 0.25, "high_threshold": 0.50, "rationale": "..."}')

    st.divider()

    # ── Overall notes ──────────────────────────────────────────────────────────
    st.subheader("Overall assessment")
    overall_notes = st.text_area("Overall notes", height=120, key="overall_notes_clin",
                                  placeholder="Which model(s) are approved? What conditions apply?")

    # ── Export ─────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Export")

    if st.button("Generate omaib_pathway.json + model_safety_report.json"):
        verdicts   = {k: st.session_state.get(f"verdict_{k}", "CONDITIONAL") for k in MODEL_LABELS}
        conditions = {k: st.session_state.get(f"cond_{k}",    "")            for k in MODEL_LABELS}
        narratives = {k: st.session_state.get(f"narr_{k}",    "")            for k in MODEL_LABELS}

        # Subgroup gaps from equity tab (simplified — abdominal reference)
        subgroup_gaps: dict[str, dict] = {}
        for key in MODEL_LABELS:
            if key in all_probs:
                sub = compute_subgroup_metrics(
                    test_df, all_probs[key],
                    group_col="surgery_type", threshold=threshold,
                )
                gapped = equity_gap(sub, reference_group="abdominal", metric="auroc")
                gaps_dict = {}
                for _, row in gapped.iterrows():
                    gaps_dict[row["group_value"]] = row.get("auroc_gap", 0.0)
                subgroup_gaps[key] = gaps_dict

        deployment_qs = {}
        for k in MODEL_LABELS:
            deployment_qs[k] = {
                f"q{i}": st.session_state.get(f"dq{i}_{k}", "Not provided")
                for i in range(1, 6)
            }

        try:
            opt_content_parsed = json.loads(opt_content) if opt_content.strip().startswith("{") else opt_content
        except Exception:
            opt_content_parsed = opt_content

        option_specific = {
            "type":    opt_type,
            "title":   opt_title,
            "content": opt_content_parsed,
        }

        if all_metrics:
            save_metrics_csv(list(all_metrics.values()),
                             METRICS_DIR / "evaluation_metrics.csv")

        pathway = generate_json_pathway(
            metrics_by_model=all_metrics,
            verdicts=verdicts, conditions=conditions, narratives=narratives,
            subgroup_gaps=subgroup_gaps,
            team_name=team_name, team_members=team_members,
            overall_notes=overall_notes,
        )
        pathway_str = json.dumps(pathway, indent=2)
        (REF_DIR / "omaib_pathway.json").write_text(pathway_str, encoding="utf-8")

        report = generate_json_safety_report(
            metrics_by_model=all_metrics,
            verdicts=verdicts, conditions=conditions, narratives=narratives,
            subgroup_gaps=subgroup_gaps, deployment_qs=deployment_qs,
            option_specific=option_specific,
            team_name=team_name, team_members=team_members,
            overall_notes=overall_notes,
        )
        report_str = json.dumps(report, indent=2)
        (REF_DIR / "model_safety_report.json").write_text(report_str, encoding="utf-8")

        st.success("Exported reference/omaib_pathway.json and reference/model_safety_report.json")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Download omaib_pathway.json",
                               data=pathway_str,
                               file_name="omaib_pathway.json",
                               mime="application/json")
        with col2:
            st.download_button("Download model_safety_report.json",
                               data=report_str,
                               file_name="model_safety_report.json",
                               mime="application/json")
