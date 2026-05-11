"""Clinical Strand — Interactive Evaluation & Reporting App.

Run:  streamlit run app.py   (from the clinical_strand/ root)

Reads:
  data/processed/test.csv
  saved_models/model_*.joblib
  saved_metrics/training_metrics.csv   (optional)

Writes (on export):
  reference/evaluation_metrics.csv
  reference/Model_Safety_Report.html
  reference/omaib_submission.json
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── import your evaluate functions once implemented ───────────────────────────
from src.evaluate import (
    age_band,
    compute_metrics,
    compute_subgroup_metrics,
    compute_calibration,
    equity_gap,
    pr_curve_data,
    roc_curve_data,
    save_metrics_csv,
)
from src.report import (
    METRIC_REGISTRY,
    _META_KEYS,
    generate_full_submission,
    generate_html_report,
    generate_omaib_card,
)

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
DATA_DIR    = ROOT / "data" / "processed"
MODELS_DIR  = ROOT / "saved_models"
METRICS_DIR = ROOT / "saved_metrics"
REF_DIR     = ROOT / "reference"
REF_DIR.mkdir(exist_ok=True)

MODEL_LABELS = {
    "model_a": "Model A — Multimodal LightGBM",
    "model_b": "Model B — Your Implementation",
    "model_c": "Model C — Your Implementation",
}
VERDICT_COLOURS = {
    "APPROVE":      "#1a7a1a",
    "CONDITIONAL":  "#b35c00",
    "NOT APPROVED": "#a01010",
}
PLOT_COLOURS = ["#1f77b4", "#d62728", "#2ca02c"]


# ══════════════════════════════════════════════════════════════════════════════
# CLINICAL TRANSLATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _ward_simulation(m: dict, prevalence: float) -> dict | None:
    """Convert metrics to plain-English ward counts per 100 patients.

    Returns None if required keys (sensitivity, specificity, ppv, npv) are absent.
    """
    required = {"sensitivity", "specificity", "ppv", "npv"}
    if not required.issubset(m):
        return None

    n_sick  = round(prevalence * 100)
    n_well  = 100 - n_sick
    caught       = round(m["sensitivity"] * n_sick)
    missed       = n_sick - caught
    cleared      = round(m["specificity"] * n_well)
    false_alarms = n_well - cleared
    ppv_pct      = round(m["ppv"] * 100)
    npv_pct      = round(m["npv"] * 100)

    bs = m.get("brier_score")
    if bs is not None:
        if bs < 0.10:   calib = "excellent — risk scores are trustworthy"
        elif bs < 0.15: calib = "good — risk scores are broadly reliable"
        elif bs < 0.25: calib = "moderate — treat as ranks, not probabilities"
        else:           calib = "poor — do not use raw scores for thresholding"
    else:
        calib = "not computed"

    miss_pct = round((1 - m["sensitivity"]) * 100)
    return dict(
        n_sick=n_sick, n_well=n_well, caught=caught, missed=missed,
        cleared=cleared, false_alarms=false_alarms,
        ppv_pct=ppv_pct, npv_pct=npv_pct, miss_pct=miss_pct,
        calib=calib,
        q_miss=(
            f"In a ward of 100 patients (≈ {n_sick} will deteriorate):\n\n"
            f"- Model catches **{caught}** — misses **{missed}** ({miss_pct}% miss rate)\n"
            f"- Raises **{false_alarms} false alarms** among the {n_well} stable patients\n"
            f"- Correctly clears **{cleared}** stable patients"
        ),
        q_alert=(
            f"When the model raises an alert it is correct **{ppv_pct}% of the time** (PPV).\n"
            + (f"1 in every {round(100/ppv_pct)} alerts is a true deterioration."
               if ppv_pct > 0 else "")
        ),
        q_clear=(
            f"When the model gives the all-clear it is correct **{npv_pct}% of the time** (NPV).\n"
            + (f"This means {100-npv_pct}% of cleared patients will still deteriorate — "
               "consider clinical override protocols."
               if npv_pct < 95
               else "High NPV — a low-risk score is reliable for deprioritisation.")
        ),
        q_calib=f"Calibration (Brier score = {bs:.3f}): {calib}." if bs else "Brier score not computed.",
    )


def _fn_profile(err_df: pd.DataFrame) -> dict | None:
    fn = err_df[err_df["error_type"] == "FN — missed"]
    tp = err_df[err_df["error_type"] == "TP — caught"]
    if fn.empty or tp.empty:
        return None
    return dict(
        fn_age=fn["age"].mean(), tp_age=tp["age"].mean(),
        fn_sofa=fn["sofa_score"].mean(), tp_sofa=tp["sofa_score"].mean(),
        fn_no_notes=(1 - fn["has_notes"].mean()) * 100,
        tp_no_notes=(1 - tp["has_notes"].mean()) * 100,
        fn_n=len(fn), tp_n=len(tp),
    )


# ══════════════════════════════════════════════════════════════════════════════
# LOADERS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_test_data():
    p = DATA_DIR / "test.csv"
    return pd.read_csv(p) if p.exists() else None


@st.cache_resource
def load_models():
    return {
        k: joblib.load(MODELS_DIR / f"{k}.joblib")
        for k in MODEL_LABELS
        if (MODELS_DIR / f"{k}.joblib").exists()
    }


@st.cache_data
def load_training_metrics():
    p = METRICS_DIR / "training_metrics.csv"
    return pd.read_csv(p) if p.exists() else None


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG + SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="ICU AI Safety Evaluation", page_icon="🏥", layout="wide")

with st.sidebar:
    st.title("🏥 Clinical Strand")
    st.caption("ICU AI Safety Evaluation")
    st.divider()
    threshold = st.slider("Classification threshold", 0.10, 0.90, 0.50, 0.01,
                          help="Probability above which the model raises a high-risk alert.")
    st.divider()
    st.subheader("Status")
    test_df    = load_test_data()
    models     = load_models()
    tr_metrics = load_training_metrics()

    if test_df is not None:
        st.success(f"Test data: {len(test_df)} patients")
    else:
        st.error("No test.csv — run the notebook first")

    for key, label in MODEL_LABELS.items():
        short = label.split("—")[0].strip()
        if key in models:
            st.success(f"{short}: loaded")
        else:
            st.info(f"{short}: not yet saved")

    if not models:
        st.warning("Train and save at least one model in the notebook, then return here.")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Data Overview",
    "🎯 Model Performance",
    "👥 Subgroup Analysis",
    "🔬 Failure Analysis",
    "📋 Report Builder",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — DATA OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.header("Test dataset overview")
    if test_df is None:
        st.warning("Run the training notebook to produce `data/processed/test.csv`.")
        st.stop()

    prev = test_df["deteriorated"].mean()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Patients (test)", len(test_df))
    c2.metric("Deterioration rate", f"{prev:.1%}")
    c3.metric("Notes available",    f"{test_df['has_notes'].mean():.1%}")
    c4.metric("Mean age",           f"{test_df['age'].mean():.0f} yrs")

    st.info(
        f"**Baseline context:** {prev:.1%} of patients deteriorate. "
        f"A model that flags *every* patient achieves {prev:.1%} sensitivity "
        f"but also raises {1-prev:.1%} false alarms — a useless baseline. "
        f"Any useful model must be substantially better on both dimensions."
    )

    st.subheader("Feature completeness")
    miss = test_df.isnull().mean().rename("missing_rate").reset_index()
    miss.columns = ["feature", "missing_rate"]
    miss = miss[miss["missing_rate"] > 0].sort_values("missing_rate", ascending=False)
    if miss.empty:
        st.success("No missing values after preprocessing.")
    else:
        fig = go.Figure(go.Bar(
            x=miss["feature"], y=miss["missing_rate"],
            marker_color="#d62728",
            text=(miss["missing_rate"]*100).round(1).astype(str)+"%",
            textposition="outside",
        ))
        fig.update_layout(yaxis_title="Missing rate", height=250, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        test_df["age_band"] = age_band(test_df)
        ab = test_df.groupby("age_band")["deteriorated"].agg(["mean","count"]).rename(
            columns={"mean":"deterioration_rate","count":"n"})
        ab["deterioration_rate"] = ab["deterioration_rate"].round(3)
        st.write("**Deterioration rate by age band**")
        st.dataframe(ab, use_container_width=True)
    with col_b:
        nb = test_df.groupby("has_notes")["deteriorated"].agg(["mean","count"]).rename(
            columns={"mean":"deterioration_rate","count":"n"})
        nb.index = ["No clinical notes","Has clinical notes"]
        nb["deterioration_rate"] = nb["deterioration_rate"].round(3)
        st.write("**Deterioration rate by notes availability**")
        st.dataframe(nb, use_container_width=True)

    if tr_metrics is not None:
        st.subheader("Training / validation metrics (from notebook)")
        st.dataframe(tr_metrics, hide_index=True, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — MODEL PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.header("Model performance on test set")
    if not models:
        st.warning("No saved models found. Run the training notebook first.")
        st.stop()

    prev   = test_df["deteriorated"].mean()
    y_true = test_df["deteriorated"].values
    all_m  = {}

    for key, model in models.items():
        y_prob = model.predict_proba(test_df)[:, 1]
        try:
            all_m[key] = compute_metrics(y_true, y_prob, threshold,
                                         model_name=MODEL_LABELS[key])
        except NotImplementedError:
            st.error("Implement `compute_metrics()` in src/evaluate.py first.")
            st.stop()

    # ── Critical clinical questions ───────────────────────────────────────────
    st.subheader("Critical clinical questions")
    st.caption(
        "These are the questions a clinical governance team would ask before "
        "authorising deployment. Metrics alone do not answer them — your "
        "interpretation does."
    )

    for key, model in models.items():
        m  = all_m[key]
        sim = _ward_simulation(m, prev)
        with st.expander(
            f"**{MODEL_LABELS[key]}**"
            + (f"  —  AUROC {m.get('auroc','?')}" if "auroc" in m else ""),
            expanded=True,
        ):
            if sim:
                col_l, col_r = st.columns([3, 2])
                with col_l:
                    # Q1
                    st.markdown(
                        f"**Q1 — How many deteriorating patients will this model miss?** "
                        f"In a ward of 100 patients (≈ {sim['n_sick']} will deteriorate):"
                    )
                    st.text_area("Q1", key=f"q1_{key}", height=56,
                                 label_visibility="collapsed",
                                 placeholder="Your team's response goes here.")
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    mc1.metric("Caught per 100",        sim["caught"])
                    mc2.metric("Missed per 100",        sim["missed"],
                               delta=f"-{sim['missed']}", delta_color="inverse")
                    mc3.metric("False alarms per 100",  sim["false_alarms"],
                               delta=f"+{sim['false_alarms']}", delta_color="inverse")
                    mc4.metric("Correct clears per 100", sim["cleared"])
                    st.caption(
                        f"It raises {sim['false_alarms']} false alarms among the {sim['n_well']} "
                        f"stable patients. It correctly clears {sim['cleared']} patients."
                    )
                    st.markdown("---")

                    # Q2
                    st.markdown("**Q2 — When the model raises an alert, how often is it right?**")
                    st.text_area("Q2", key=f"q2_{key}", height=56,
                                 label_visibility="collapsed",
                                 placeholder="Your team's response goes here.")

                    # Q3
                    st.markdown("**Q3 — When the model gives the all-clear, is it safe?**")
                    st.text_area("Q3", key=f"q3_{key}", height=56,
                                 label_visibility="collapsed",
                                 placeholder="Your team's response goes here.")

                    # Q4
                    if "auroc" in m:
                        st.markdown("**Q4 — How well does the model separate sick from well patients?**")
                        st.text_area("Q4", key=f"q4_{key}", height=56,
                                     label_visibility="collapsed",
                                     placeholder="Your team's response goes here.")

                    # Q5
                    st.markdown("**Q5 — Can we use the model's risk scores to set care priorities?**")
                    st.text_area("Q5", key=f"q5_{key}", height=56,
                                 label_visibility="collapsed",
                                 placeholder="Your team's response goes here.")
                with col_r:
                    # Dynamic metrics table from METRIC_REGISTRY
                    display_metrics = [
                        {
                            "Metric": METRIC_REGISTRY[k].label if k in METRIC_REGISTRY else k.upper(),
                            "Value":  round(v, 4) if isinstance(v, float) else v,
                            "What it measures": (
                                METRIC_REGISTRY[k].general if k in METRIC_REGISTRY
                                else "Custom metric"
                            ),
                        }
                        for k, v in m.items()
                        if k not in _META_KEYS
                    ]
                    st.write("**Raw metrics**")
                    st.dataframe(
                        pd.DataFrame(display_metrics), hide_index=True,
                        use_container_width=True,
                        column_config={"What it measures": st.column_config.TextColumn(width="large")},
                    )
            else:
                st.warning(
                    "Ward simulation unavailable — ensure compute_metrics() returns "
                    "sensitivity, specificity, ppv, and npv."
                )
                st.json({k: v for k, v in m.items() if k not in _META_KEYS})

    st.divider()
    # ── ROC and Calibration side by side ─────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("ROC curves")
        fig = go.Figure()
        fig.add_shape(type="line", x0=0, x1=1, y0=0, y1=1,
                      line=dict(dash="dash", color="grey", width=1))
        for i, (key, model) in enumerate(models.items()):
            y_prob = model.predict_proba(test_df)[:, 1]
            try:
                fpr, tpr = roc_curve_data(y_true, y_prob)
                auc = all_m[key].get("auroc", "?")
                fig.add_trace(go.Scatter(
                    x=fpr, y=tpr, mode="lines",
                    name=f"{MODEL_LABELS[key].split('—')[0].strip()} (AUC={auc})",
                    line=dict(color=PLOT_COLOURS[i % 3], width=2),
                ))
            except NotImplementedError:
                st.warning("Implement roc_curve_data() to see ROC curves.")
        fig.update_layout(
            xaxis_title="False Positive Rate", yaxis_title="True Positive Rate",
            height=360, margin=dict(t=20),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("A good model hugs the top-left corner.")

    with col_b:
        st.subheader("Calibration")
        sel = st.selectbox("Model", list(models.keys()), format_func=lambda k: MODEL_LABELS[k])
        y_prob = models[sel].predict_proba(test_df)[:, 1]
        try:
            frac, mean_pred, counts = compute_calibration(y_true, y_prob)
            fig2 = go.Figure()
            fig2.add_shape(type="line", x0=0, x1=1, y0=0, y1=1,
                           line=dict(dash="dash", color="grey", width=1))
            fig2.add_trace(go.Scatter(
                x=mean_pred, y=frac, mode="lines+markers",
                marker=dict(size=9, color=counts, colorscale="Blues",
                            showscale=True, colorbar=dict(title="N")),
            ))
            fig2.update_layout(
                xaxis_title="Predicted probability",
                yaxis_title="Observed deterioration rate",
                height=360, margin=dict(t=20),
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("Points on the diagonal = well calibrated.")
        except NotImplementedError:
            st.warning("Implement compute_calibration() to see this plot.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — SUBGROUP ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.header("Subgroup analysis")
    st.caption(
        "A model safe *on average* may still fail specific patient groups. "
        "A model that performs worse for elderly patients, or for patients "
        "without clinical notes, represents a systemic equity risk."
    )
    if not models:
        st.stop()

    prev   = test_df["deteriorated"].mean()
    y_true = test_df["deteriorated"].values

    col_l, col_r = st.columns([2, 1])
    with col_l:
        sel_model = st.selectbox("Model", list(models.keys()),
                                 format_func=lambda k: MODEL_LABELS[k])
    with col_r:
        group_map = {
            "Age band":         "age_band",
            "Sex":              "sex",
            "Admission type":   "admission_type",
            "Notes available":  "has_notes",
        }
        sel_group_label = st.selectbox("Group by", list(group_map.keys()))
    sel_group = group_map[sel_group_label]
    sel_metric = st.selectbox("Metric", ["auroc", "sensitivity", "specificity", "ppv", "f1"])

    model   = models[sel_model]
    y_prob  = model.predict_proba(test_df)[:, 1]
    plot_df = test_df.copy()
    plot_df["age_band"]  = age_band(plot_df)
    plot_df["has_notes"] = plot_df["has_notes"].astype(str)

    try:
        sub_df = compute_subgroup_metrics(plot_df, y_prob, y_true, sel_group, threshold)
        if len(sub_df) > 1:
            ref = sub_df.loc[sub_df[sel_metric].idxmax(), "group_value"]
            sub_df = equity_gap(sub_df, reference_value=ref, metric=sel_metric)

        worst = sub_df.loc[sub_df[sel_metric].idxmin()]
        best  = sub_df.loc[sub_df[sel_metric].idxmax()]
        gap   = best[sel_metric] - worst[sel_metric]

        # Clinical framing of the gap
        n_sick = round(prev * 100)
        if sel_metric == "sensitivity" and gap > 0.02:
            delta_missed = round(gap * n_sick)
            st.error(
                f"**Equity gap:** The model misses **{delta_missed} more** "
                f"patients per 100 in group '{worst['group_value']}' "
                f"compared to '{best['group_value']}' "
                f"(sensitivity {worst[sel_metric]:.2f} vs {best[sel_metric]:.2f})."
            ) if gap > 0.05 else st.warning(
                f"Moderate gap: {delta_missed} extra missed per 100 in "
                f"'{worst['group_value']}'."
            )
        elif gap > 0.10:
            st.error(f"**Large equity gap ({gap:.3f})** — worst group: "
                     f"'{worst['group_value']}' {sel_metric}={worst[sel_metric]:.3f}")
        elif gap > 0.05:
            st.warning(f"Moderate gap ({gap:.3f}): '{worst['group_value']}' lags behind.")
        else:
            st.success("No meaningful equity gap detected on this metric.")

        bar_colours = [
            VERDICT_COLOURS["NOT APPROVED"] if abs(g) > 0.10
            else VERDICT_COLOURS["CONDITIONAL"] if abs(g) > 0.05
            else "#3a7abf"
            for g in sub_df.get(f"{sel_metric}_gap", [0]*len(sub_df))
        ]
        fig = go.Figure(go.Bar(
            x=sub_df["group_value"].astype(str), y=sub_df[sel_metric],
            marker_color=bar_colours,
            text=sub_df[sel_metric].round(3), textposition="outside",
        ))
        fig.update_layout(yaxis_range=[0, 1.1], height=300, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

        disp = sub_df[["group_value","n_group",sel_metric,
                        f"{sel_metric}_gap","sensitivity","specificity"]].rename(
            columns={"group_value": sel_group_label, "n_group": "N",
                     f"{sel_metric}_gap": "Gap vs best"})
        st.dataframe(disp, hide_index=True, use_container_width=True)

    except NotImplementedError:
        st.warning("Implement compute_subgroup_metrics() and equity_gap() in src/evaluate.py.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — FAILURE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.header("Failure analysis")
    st.caption(
        "Understanding WHO the model misses is as important as knowing HOW MANY. "
        "A systematic clinical profile in the false negatives is a safety risk — "
        "it means the model has a blind spot."
    )
    if not models:
        st.stop()

    y_true      = test_df["deteriorated"].values
    sel_fail    = st.selectbox("Model", list(models.keys()),
                               format_func=lambda k: MODEL_LABELS[k], key="fail_sel")
    model       = models[sel_fail]
    y_prob      = model.predict_proba(test_df)[:, 1]
    y_pred      = (y_prob >= threshold).astype(int)

    err_df = test_df.copy()
    err_df["age_band"]  = age_band(err_df)
    err_df["y_prob"]    = y_prob
    err_df["error_type"] = np.select(
        [(y_true==1)&(y_pred==1),(y_true==0)&(y_pred==0),
         (y_true==1)&(y_pred==0),(y_true==0)&(y_pred==1)],
        ["TP — caught","TN — correctly cleared","FN — missed","FP — false alarm"],
    )
    tp = int(((y_true==1)&(y_pred==1)).sum())
    tn = int(((y_true==0)&(y_pred==0)).sum())
    fn = int(((y_true==1)&(y_pred==0)).sum())
    fp = int(((y_true==0)&(y_pred==1)).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Caught (TP)",           tp)
    c2.metric("Correctly cleared (TN)", tn)
    c3.metric("Missed (FN)",           fn, delta=f"-{fn}", delta_color="inverse",
              help="Patients who deteriorate but are not flagged.")
    c4.metric("False alarms (FP)",     fp, delta=f"+{fp}", delta_color="inverse")

    st.divider()
    st.subheader("Who does this model miss?")

    fn_df = err_df[err_df["error_type"] == "FN — missed"]
    tp_df = err_df[err_df["error_type"] == "TP — caught"]
    fp_df = err_df[err_df["error_type"] == "FP — false alarm"]

    fp_df = err_df[err_df["error_type"] == "FP — false alarm"]
    tn_df = err_df[err_df["error_type"] == "TN — correctly cleared"]

    if not fn_df.empty and not tp_df.empty:
        prof = pd.DataFrame({
            "Feature":        ["Age (mean)","SOFA score (mean)",
                               "Lactate (mean)","No clinical notes (%)"],
            "Missed (FN)":    [f"{fn_df['age'].mean():.0f} yrs",
                               f"{fn_df['sofa_score'].mean():.1f}",
                               f"{fn_df['lactate'].mean():.2f}",
                               f"{(1-fn_df['has_notes'].mean())*100:.0f}%"],
            "Caught (TP)":    [f"{tp_df['age'].mean():.0f} yrs",
                               f"{tp_df['sofa_score'].mean():.1f}",
                               f"{tp_df['lactate'].mean():.2f}",
                               f"{(1-tp_df['has_notes'].mean())*100:.0f}%"],
        })
        st.dataframe(prof, hide_index=True, use_container_width=True)

        for cond, msg in [
            (fn_df["age"].mean() > tp_df["age"].mean() + 3,
             f"Missed patients are **older** ({fn_df['age'].mean():.0f} vs "
             f"{tp_df['age'].mean():.0f} yrs) — the model under-estimates "
             f"risk for elderly patients."),
            (fn_df["sofa_score"].mean() < tp_df["sofa_score"].mean() - 1,
             f"Missed patients have **lower SOFA scores** — they deteriorate "
             f"without the expected severity-score signals."),
            (fn_df["has_notes"].mean() < tp_df["has_notes"].mean() - 0.1,
             f"Missed patients are **more likely to lack clinical notes** — "
             f"the model loses signal when notes are absent."),
        ]:
            if cond:
                st.warning(msg)

    st.text_area(
        "Who does this model miss? — Team interpretation",
        key=f"fn_narr_{sel_fail}", height=80,
        placeholder=(
            "Describe any systematic pattern in missed patients. "
            "Are they older, less severely ill on admission, or lacking clinical notes? "
            "What clinical risk does this blind spot create?"
        ),
    )

    st.divider()
    st.subheader("What do false alarms look like?")
    if not fp_df.empty and not tn_df.empty:
        fp_prof = pd.DataFrame({
            "Feature":                ["Age (mean)", "SOFA score (mean)", "No notes (%)"],
            "False alarm (FP)":       [f"{fp_df['age'].mean():.0f} yrs",
                                       f"{fp_df['sofa_score'].mean():.1f}",
                                       f"{(1-fp_df['has_notes'].mean())*100:.0f}%"],
            "Correctly cleared (TN)": [f"{tn_df['age'].mean():.0f} yrs",
                                       f"{tn_df['sofa_score'].mean():.1f}",
                                       f"{(1-tn_df['has_notes'].mean())*100:.0f}%"],
        })
        st.dataframe(fp_prof, hide_index=True, use_container_width=True)
    elif fp_df.empty:
        st.info("No false alarms at this threshold — consider whether the threshold is too high.")
    st.text_area(
        "What do false alarms look like? — Team interpretation",
        key=f"fp_narr_{sel_fail}", height=80,
        placeholder=(
            "Describe the false-alarm patients. Do they share clinical characteristics "
            "(e.g., high SOFA but stable trajectory, post-operative noise)? "
            "What is the alert fatigue cost of this false alarm rate?"
        ),
    )

    st.divider()
    st.subheader("Feature importance")
    if hasattr(model, "feature_importance"):
        try:
            fi = model.feature_importance().head(12)
            fig = go.Figure(go.Bar(
                x=fi.values, y=fi.index, orientation="h", marker_color="#1f77b4",
            ))
            fig.update_layout(yaxis=dict(autorange="reversed"),
                              xaxis_title="Importance", height=320, margin=dict(t=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Clinical sense check: are the top features clinically plausible? "
                "A model relying on administrative fields (timestamps, IDs) "
                "has learned data artefacts, not patient physiology."
            )
        except NotImplementedError:
            st.info("Implement feature_importance() in your model to see this chart.")
    st.text_area(
        "What is the model using to make predictions? — Team interpretation",
        key=f"fi_narr_{sel_fail}", height=80,
        placeholder=(
            "Are the top features clinically plausible? "
            "e.g., 'lactate and sofa_score dominate — this aligns with clinical expectation. "
            "However, admission_type ranks unexpectedly high, which may indicate data leakage...'"
        ),
    )

    st.divider()
    st.subheader("Where do the models disagree?")
    st.caption(
        "Compare across all loaded models: which patients does one model flag "
        "that another misses? Model disagreement on deteriorating patients is the "
        "most safety-critical pattern."
    )
    if len(models) > 1:
        all_preds_tab4 = {}
        for mk, mdl in models.items():
            try:
                yp = mdl.predict_proba(test_df)[:, 1]
                all_preds_tab4[MODEL_LABELS[mk].split("—")[0].strip()] = (yp >= threshold).astype(int)
            except Exception:
                pass
        if len(all_preds_tab4) > 1:
            pred_mat = pd.DataFrame(all_preds_tab4)
            n_pos = pred_mat.sum(axis=1)
            disagree_mask = n_pos.between(1, len(all_preds_tab4) - 1)
            st.metric("Patients where models disagree", int(disagree_mask.sum()),
                      help="One or more models flag positive, one or more flag negative.")
            if disagree_mask.sum() > 0:
                sample = test_df[disagree_mask].assign(**all_preds_tab4).head(10)
                display_cols = ["age", "sofa_score", "has_notes"] + list(all_preds_tab4.keys())
                display_cols = [c for c in display_cols if c in sample.columns]
                st.dataframe(sample[display_cols], hide_index=True, use_container_width=True)
    else:
        st.info("Load more than one model to see disagreement analysis.")
    st.text_area(
        "Where do the models disagree? — Team interpretation",
        key=f"disagree_narr_{sel_fail}", height=80,
        placeholder=(
            "Describe the patients where models diverge. "
            "e.g., 'Model A flags elderly patients without notes that Model B misses — "
            "consistent with Model B losing signal when notes are absent. "
            "The disagreement is concentrated in patients with SOFA 4–6...'"
        ),
    )

    st.divider()
    st.subheader("Performance split: with notes vs without notes")
    prev = test_df["deteriorated"].mean()
    col_a, col_b = st.columns(2)
    for col, has, label in [(col_a, 1, "Has clinical notes"),
                            (col_b, 0, "No clinical notes")]:
        mask = test_df["has_notes"] == has
        if mask.sum() >= 5:
            try:
                m = compute_metrics(y_true[mask], y_prob[mask], threshold)
                sim = _ward_simulation(m, y_true[mask].mean())
                with col:
                    st.metric(label, f"n = {mask.sum()}")
                    if "auroc" in m:
                        st.metric("AUROC",       m["auroc"])
                    if "sensitivity" in m:
                        st.metric("Sensitivity", m["sensitivity"])
                    if sim:
                        st.metric("Missed per 100", sim["missed"],
                                  delta=f"-{sim['missed']}", delta_color="inverse")
            except NotImplementedError:
                pass

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — REPORT BUILDER
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.header("Report builder")
    st.caption(
        "Fill in verdicts and narratives. Metric fields are auto-populated. "
        "Every metric your compute_metrics() returns will appear in the exported report."
    )
    if not models:
        st.stop()

    prev   = test_df["deteriorated"].mean()
    y_true = test_df["deteriorated"].values

    st.subheader("Team information")
    team_name    = st.text_input("Team name",    placeholder="e.g., ICU Auditors")
    team_members = st.text_input("Team members", placeholder="Alice, Bob, Carol")
    st.divider()

    model_cards   = []
    subgroup_data = {}

    for key, model in models.items():
        label  = MODEL_LABELS[key]
        y_prob = model.predict_proba(test_df)[:, 1]
        try:
            m   = compute_metrics(y_true, y_prob, threshold, model_name=label)
        except NotImplementedError:
            st.warning("Implement compute_metrics() to enable the report builder.")
            break

        sim = _ward_simulation(m, prev)

        st.subheader(label)

        # Auto metrics summary
        metric_keys = [k for k in m if k not in _META_KEYS]
        cols = st.columns(min(len(metric_keys), 5))
        for col, k in zip(cols, metric_keys[:5]):
            info = METRIC_REGISTRY.get(k)
            col.metric(
                info.label if info else k.upper(),
                round(m[k], 3) if isinstance(m[k], float) else m[k],
                help=info.strand if info else None,
            )

        if sim:
            st.markdown(sim["q_miss"])

        # Clinical checklist
        with st.expander("Answer the clinical deployment questions"):
            if sim:
                st.radio(
                    f"Is a miss rate of {sim['missed']} per 100 acceptable?",
                    ["Yes — acceptable","No — too many missed","Uncertain"],
                    key=f"miss_{key}",
                )
                st.radio(
                    f"Is a false-alarm rate of {sim['false_alarms']} per 100 acceptable?",
                    ["Yes — manageable","No — alert fatigue risk","Uncertain"],
                    key=f"fa_{key}",
                )
                if "ppv" in m:
                    st.radio(
                        f"Is PPV {m['ppv']:.0%} sufficient to act on alerts without review?",
                        ["Yes","No — requires clinical review before escalation"],
                        key=f"ppv_{key}",
                    )
                if "npv" in m:
                    st.radio(
                        f"Is NPV {m['npv']:.0%} safe enough to deprioritise low-risk patients?",
                        ["Yes","No — clinicians should override regardless"],
                        key=f"npv_{key}",
                    )

        verdict = st.selectbox(
            "Deployment verdict",
            ["APPROVE","CONDITIONAL","NOT APPROVED"],
            key=f"verdict_{key}",
        )
        vc = VERDICT_COLOURS[verdict]
        st.markdown(
            f"<span style='background:{vc};color:white;padding:4px 14px;"
            f"border-radius:4px;font-weight:bold'>{verdict}</span>",
            unsafe_allow_html=True,
        )
        conditions = st.text_area(
            "Conditions / required safeguards",
            key=f"cond_{key}", height=80,
            placeholder="e.g., Mandatory clinical review for patients aged 75+.",
        )
        narrative = st.text_area(
            "Assessment narrative",
            key=f"narr_{key}", height=120,
            placeholder=(
                "Summarise in plain English: key failure modes, which patients "
                "are most at risk, and why you reached this verdict."
            ),
        )

        # Subgroup data for report
        plot_df = test_df.copy()
        plot_df["age_band"] = age_band(plot_df)
        try:
            sub = compute_subgroup_metrics(plot_df, y_prob, y_true, "age_band", threshold)
            if len(sub) > 0:
                ref = sub.loc[sub["auroc"].idxmax(), "group_value"]
                sub = equity_gap(sub, reference_value=ref, metric="auroc")
                subgroup_data[label] = sub.to_dict("records")
        except NotImplementedError:
            pass

        q_answers = {
            "miss_acceptable": st.session_state.get(f"miss_{key}", "—"),
            "fa_acceptable":   st.session_state.get(f"fa_{key}", "—"),
            "trust_alert":     st.session_state.get(f"ppv_{key}", "—"),
            "trust_clear":     st.session_state.get(f"npv_{key}", "—"),
        }
        q_narratives = {
            "q1": st.session_state.get(f"q1_{key}", ""),
            "q2": st.session_state.get(f"q2_{key}", ""),
            "q3": st.session_state.get(f"q3_{key}", ""),
            "q4": st.session_state.get(f"q4_{key}", ""),
            "q5": st.session_state.get(f"q5_{key}", ""),
        }
        failure_narratives = {
            "fn":       st.session_state.get(f"fn_narr_{key}", ""),
            "fp":       st.session_state.get(f"fp_narr_{key}", ""),
            "features": st.session_state.get(f"fi_narr_{key}", ""),
            "disagree": st.session_state.get(f"disagree_narr_{key}", ""),
        }
        model_cards.append({
            "model_name": label, "verdict": verdict,
            "conditions": conditions, "narrative": narrative,
            "metrics": m, "ward_sim": sim, "q_answers": q_answers,
            "q_narratives":       q_narratives,
            "failure_narratives": failure_narratives,
        })
        st.divider()

    overall_notes = st.text_area(
        "Overall assessment and recommendations",
        height=100,
        placeholder="Which model(s) can be deployed? What must change?",
    )

    st.divider()
    st.subheader("Export")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Save evaluation metrics CSV") and model_cards:
            save_metrics_csv([mc["metrics"] for mc in model_cards],
                             str(REF_DIR / "evaluation_metrics.csv"))
            st.success("Saved to reference/evaluation_metrics.csv")

    with col_b:
        if st.button("Generate HTML report") and model_cards:
            html = generate_html_report(
                team_name=team_name, overall_notes=overall_notes,
                model_cards=model_cards, subgroup_data=subgroup_data,
            )
            (REF_DIR / "Model_Safety_Report.html").write_text(html, encoding="utf-8")
            st.success("Saved to reference/Model_Safety_Report.html")
            st.download_button("Download HTML report", data=html,
                               file_name="Model_Safety_Report.html", mime="text/html")

    with col_c:
        if st.button("Export OMAIB JSON") and model_cards:
            cards = [
                generate_omaib_card(
                    model_name=mc["model_name"], metrics=mc["metrics"],
                    verdict=mc["verdict"], conditions=mc["conditions"],
                    narrative=mc["narrative"],
                    subgroup_gaps={
                        r["group_value"]: r.get("auroc_gap")
                        for r in subgroup_data.get(mc["model_name"], [])
                    },
                )
                for mc in model_cards
            ]
            sub = generate_full_submission(team_name, team_members, cards, overall_notes)
            js  = json.dumps(sub, indent=2)
            (REF_DIR / "omaib_submission.json").write_text(js, encoding="utf-8")
            st.success("Saved to reference/omaib_submission.json")
            st.download_button("Download OMAIB JSON", data=js,
                               file_name="omaib_submission.json",
                               mime="application/json")
