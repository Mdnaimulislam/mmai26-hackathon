"""SCA-dream-soultion — Cold-Home Triage (website).

Interactive tool for a council housing team deciding which social-housing
properties get a boiler upgrade this winter. Three jobs in one tool:
  1. rank homes for a boiler upgrade,
  2. fuse + audit the multimodal sensor data behind the ranking,
  3. prove the ranking is fair — and surface the data faults.

Run:  streamlit run app.py

Charts use Plotly (renders reliably inside Streamlit tabs). Reads the precomputed
bundle from `python build_submission.py`; self-healing if the bundle is missing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "reports" / "app_bundle.json"
MODEL = ROOT / "saved_models" / "model_a_logistic_baseline.joblib"

PT_ORDER = ["flat", "terraced", "semi-detached", "detached"]
SEASON_MONTH = {"Winter (January)": 1, "Spring (April)": 4, "Summer (July)": 7, "Autumn (October)": 10}
REL_COLORS = {"HIGH": "#1a7f37", "LOW": "#b42318"}
VERDICT_COLOR = {"READY": "#1a7f37", "PASS": "#1a7f37", "CONDITIONAL": "#9a6700",
                 "NOT READY": "#b42318", "FAIL": "#b42318"}
FEAT_LABEL = {
    "month": "Season (time of year)", "smart_meter_kwh": "Energy use", "avgHumidity": "Humidity",
    "noise_db": "Noise", "is_flat": "Is a flat", "day_of_week": "Day of week",
    "pt_terraced": "Type: terraced", "pt_semi_detached": "Type: semi-detached",
    "pt_detached": "Type: detached", "co2_imputed": "CO₂ (imputed)", "co2_missing": "CO₂ missing flag",
    "lag_temp": "Yesterday's temperature",
}

st.set_page_config(page_title="Cold-Home Triage", page_icon="🏠", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.4rem;}
.badge {display:inline-block;padding:3px 12px;border-radius:14px;color:#fff;font-weight:700;
        font-size:0.85rem;letter-spacing:.3px;}
.small {color:#6b7280;font-size:0.85rem;}
h1,h2,h3 {letter-spacing:-.01em;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="First run: building models & evidence from the dataset…")
def bootstrap() -> str:
    if BUNDLE.exists() and MODEL.exists():
        return "ok"
    try:
        from build_submission import main as build_main
        build_main()
        return "ok"
    except Exception as exc:
        return f"build failed: {exc}"


@st.cache_data
def load_bundle():
    return json.loads(BUNDLE.read_text(encoding="utf-8")) if BUNDLE.exists() else None


@st.cache_resource
def load_model():
    import joblib
    try:
        return joblib.load(MODEL)
    except Exception:
        try:
            from build_submission import main as build_main
            build_main()
            return joblib.load(MODEL)
        except Exception:
            return None


@st.cache_data(show_spinner=False)
def load_features():
    from src.data_pipeline import build_feature_frame, load_and_merge, make_property_split
    feat = build_feature_frame(load_and_merge(ROOT / "data" / "raw"))
    tr, te, _, _ = make_property_split(feat, seed=42)
    return tr, te


@st.cache_data(show_spinner=False)
def fit_eval(cols_tuple):
    from sklearn.metrics import roc_auc_score
    from src.models import build_pipeline
    cols = list(cols_tuple)
    tr, te = load_features()
    mdl = build_pipeline(42).fit(tr[cols], tr["cold_risk"])
    p = mdl.predict_proba(te[cols])[:, 1]
    overall = round(float(roc_auc_score(te["cold_risk"], p)), 4)
    per = {}
    for t in PT_ORDER:
        msk = (te["property_type"] == t).values
        yt = te["cold_risk"].values[msk]
        per[t] = round(float(roc_auc_score(yt, p[msk])), 4) if len(set(yt)) > 1 else None
    return overall, per


def badge(v: str) -> str:
    return f'<span class="badge" style="background:{VERDICT_COLOR.get(v, "#475467")}">{v}</span>'


def show(fig, height=300):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=30, b=8),
                      plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


_status = bootstrap()
B = load_bundle()
if B is None:
    st.error(f"Could not load app data ({_status}). Run `python build_submission.py` locally, or ensure "
             f"data/raw/housing_properties_daily.csv is present.")
    st.stop()

rank_df = pd.DataFrame(B["ranking"])
DEP = next((m for m in B["models"] if m.get("deployed")), B["models"][0])

# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏠 Cold-Home Triage")
    st.caption("MultimodalAI'26 · Housing Strand")
    st.markdown(f"**Team:** {B['team']['name']}")
    st.divider()
    st.caption(f"{B['dataset']['n_properties']} properties · {B['dataset']['n_rows']:,} property-days · "
               f"{len(B['models'])} models benchmarked")

# ── header ───────────────────────────────────────────────────────────────────
st.title("Cold-Home Triage")
st.markdown("**Three jobs in one tool:** rank homes for a boiler upgrade · fuse & audit the "
            "**multimodal** sensor data behind the ranking · prove the ranking is fair — honest about "
            "what the data can't support.")
k = st.columns(4)
k[0].metric("Properties", B["dataset"]["n_properties"])
k[1].metric("Cold-risk rate", f"{B['dataset']['cold_rate']*100:.1f}%")
k[2].metric("Deployed model AUROC", f"{DEP['metrics']['auroc']:.2f}")
k[3].metric("Models benchmarked", len(B["models"]))

tabs = st.tabs(["🏠 Priorities", "🔀 Multimodal Fusion", "🧩 Sensor Data & Missingness",
                "⚖️ Equity & Fairness", "📊 Benchmark & Evidence"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Priorities
# ════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Top 20 homes that need a boiler upgrade")
    st.caption(f"Out of all {B['dataset']['n_properties']} properties. Every property is scored by 5-fold "
               "cross-validation — each one is rated by a model that did **not** train on it, so all 250 "
               "get an honest, held-out score (no property is left untested).")
    top = rank_df.head(20)
    fig = px.bar(top, x="cold_risk_score", y="reference", orientation="h",
                 color="data_reliability", range_x=[0, 1], color_discrete_map=REL_COLORS,
                 category_orders={"reference": list(top["reference"])[::-1]},
                 labels={"cold_risk_score": "Cold-risk score (0–1)", "reference": "",
                         "data_reliability": "Sensor data"},
                 hover_data=["rank", "property_type", "observed_cold_rate", "co2_dropout_rate",
                             "recommended_action"])
    show(fig, 480)
    st.download_button("⬇ Download full ranked list of all 250 (CSV)", rank_df.to_csv(index=False),
                       "upgrade_ranking.csv", "text/csv")

    st.divider()
    lc, rc = st.columns(2)
    with lc:
        st.markdown("#### 📑 Look up a property")
        st.caption("Cold-risk score, sensor-data reliability, and the recommended action for any home.")
        ref = st.selectbox("Choose a property", rank_df["reference"].tolist())
        row = rank_df[rank_df["reference"] == ref].iloc[0]
        st.markdown(f"**Rank #{int(row['rank'])} of {len(rank_df)}** · {row['property_type']}")
        m = st.columns(3)
        m[0].metric("Cold-risk score", f"{row['cold_risk_score']:.2f}")
        m[1].metric("Observed cold days", f"{row['observed_cold_rate']*100:.0f}%")
        m[2].metric("CO₂ sensor dropout", f"{row['co2_dropout_rate']*100:.0f}%")
        st.markdown(f"- **Can we trust the sensor data here?** "
                    f"{'🟢 Yes — sensors reliable' if row['data_reliability']=='HIGH' else '🔴 No — CO₂ sensor failing'}")
        st.markdown(f"- **Recommended action:** {row['recommended_action']}")
        if row["sensor_repair_needed"]:
            st.warning("This home's CO₂ sensor has failed — send a repair so future audits are complete.")
    with rc:
        st.markdown("#### ⚡ Real-time cold-risk estimate")
        st.caption("Enter a home's conditions and the model scores its cold-risk live (interpretable baseline).")
        model = load_model()
        if model is None:
            st.warning("Baseline model not found — run build_submission.py.")
        else:
            pt = st.selectbox("Property type", PT_ORDER, key="wf_pt")
            season = st.selectbox("Time of year", list(SEASON_MONTH.keys()), key="wf_s")
            hum = st.slider("Indoor humidity (%)", 30.0, 90.0, 60.0, key="wf_h")
            kwh = st.slider("Energy use (kWh/day)", 0.0, 60.0, 18.0, key="wf_k")
            fr = pd.DataFrame([{"avgHumidity": hum, "smart_meter_kwh": kwh, "noise_db": 40.0,
                                "day_of_week": 2, "month": SEASON_MONTH[season],
                                "is_flat": int(pt == "flat"), "pt_terraced": int(pt == "terraced"),
                                "pt_semi_detached": int(pt == "semi-detached"),
                                "pt_detached": int(pt == "detached")}])
            prob = float(model.predict_proba(fr)[:, 1][0])
            st.metric("Predicted cold-risk probability", f"{prob*100:.0f}%")
            st.progress(min(max(prob, 0.0), 1.0))

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Multimodal Fusion
# ════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("Multimodal Fusion")
    st.markdown("Cold-risk is predicted by **fusing several sensor + metadata streams**. Fusion beats any "
                "single stream — the chart shows how much each one actually contributes.")
    mm = B["multimodal"]
    best = max(mm["single"], key=lambda s: s["auroc"])
    cA, cB = st.columns([2, 1])
    with cA:
        ldf = pd.DataFrame(mm["leave_one_out"]).sort_values("marginal")
        ldf["strong"] = ldf["marginal"] >= 0.02
        fig = px.bar(ldf, x="marginal", y="modality", orientation="h", color="strong",
                     color_discrete_map={True: "#16a34a", False: "#94a3b8"},
                     labels={"marginal": "AUROC lost if removed (real contribution)", "modality": ""},
                     hover_data=["auroc_without"])
        fig.update_layout(showlegend=False)
        show(fig, 300)
    with cB:
        st.metric("Fused multimodal AUROC", mm["combined_auroc"])
        st.metric(f"Best single ({best['modality']})", best["auroc"])
        co2_marg = [l['marginal'] for l in mm['leave_one_out'] if l['modality'] == 'CO₂'][0]
        st.caption(f"Energy & humidity carry the signal; **CO₂ adds only {co2_marg:+}** — the same conclusion "
                   f"the Missingness tab reaches another way.")

    st.divider()
    st.markdown("#### 🛠 Build your own fusion (live)")
    st.caption("Pick which modalities to feed the model — it re-fits on the held-out split instantly.")
    cols_map = dict(mm["columns"])
    chosen = st.multiselect("Modalities", list(cols_map.keys()), default=list(cols_map.keys()))
    use_lag = st.checkbox("➕ Add 'yesterday's indoor temperature' (⚠️ target leakage — for demonstration)", False)
    sel_cols = [c for mod in chosen for c in cols_map[mod]] + (["lag_temp"] if use_lag else [])
    if not sel_cols:
        st.warning("Select at least one modality.")
    else:
        with st.spinner("Re-fitting model…"):
            auroc, per = fit_eval(tuple(sel_cols))
        a, b2 = st.columns([1, 2])
        with a:
            st.metric("AUROC (your fusion)", f"{auroc:.3f}", delta=round(auroc - mm["combined_auroc"], 3))
            if use_lag:
                st.error("Leakage on: the jump is ~yesterday's value of the target, not real skill.")
        with b2:
            pdf = pd.DataFrame([{"property_type": t, "auroc": per[t]} for t in PT_ORDER if per[t] is not None])
            fig = px.bar(pdf, x="property_type", y="auroc", range_y=[0.5, 1.0],
                         category_orders={"property_type": PT_ORDER},
                         color="auroc", color_continuous_scale=["#b42318", "#9a6700", "#2563eb"],
                         labels={"auroc": "AUROC", "property_type": ""})
            fig.update_layout(coloraxis_showscale=False)
            show(fig, 240)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Sensor Data & Missingness
# ════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Sensor data quality & the missing-data problem")
    miss = pd.DataFrame([{"modality": k2, "missing": v}
                         for k2, v in B["sensor_health"]["missingness_by_modality"].items()
                         if k2 != "survey_score"]).sort_values("missing")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Missingness by sensor**")
        miss["high"] = miss["missing"] > 0.3
        fig = px.bar(miss, x="missing", y="modality", orientation="h", color="high",
                     color_discrete_map={True: "#b42318", False: "#1a7f37"},
                     category_orders={"modality": list(miss["modality"])},
                     labels={"missing": "% missing", "modality": ""})
        fig.update_layout(showlegend=False, xaxis_tickformat=".0%")
        show(fig, 240)
        st.caption("Temperature, humidity, smart-meter, noise are reliable. **CO₂ is 38% missing** and "
                   "Not At Random — concentrated in specific homes.")
    with c2:
        st.markdown("**Which homes lose their CO₂ sensor?**")
        thr = st.slider("Flag homes with CO₂ dropout ≥", 0.1, 0.95, 0.5, step=0.05)
        drop = pd.DataFrame(B["sensor_health"]["dropout_distribution"])
        st.metric("Homes flagged for sensor repair", int((drop["co2_dropout_rate"] >= thr).sum()))
        fig = px.histogram(drop, x="co2_dropout_rate", nbins=20, color_discrete_sequence=["#7c3aed"],
                           labels={"co2_dropout_rate": "CO₂ dropout rate per home"})
        fig.add_vline(x=thr, line_dash="dash", line_color="#111")
        show(fig, 230)

    st.divider()
    st.markdown("#### Missing-data algorithms compared — can a smarter one recover the CO₂ signal?")
    imp_cmp = pd.DataFrame(B["missingness"]["imputation_comparison"])
    c3, c4 = st.columns(2)
    with c3:
        fig = px.bar(imp_cmp.sort_values("auroc"), x="auroc", y="strategy", orientation="h",
                     range_x=[0.80, 0.93], color_discrete_sequence=["#2563eb"],
                     labels={"auroc": "AUROC", "strategy": ""}, hover_data=["model"])
        show(fig, 220)
        st.caption("The first three keep the **model fixed** and only change the missing-data algorithm "
                   "(mean / interpolation / native-NaN) — AUROC barely moves. So **no imputation algorithm "
                   "recovers signal that isn't there**; the CO₂ gap is a sensor-repair job, not an algorithm "
                   "choice. (The fourth changes the *model*, so its gain is the algorithm, not CO₂.)")
    with c4:
        st.markdown("**What each algorithm does to the CO₂ distribution**")
        dist = B["missingness"]["distribution"]
        hist_df = pd.DataFrame(dist["histogram"]).melt(id_vars="co2", var_name="series", value_name="count")
        fig = px.line(hist_df, x="co2", y="count", color="series",
                      labels={"co2": "CO₂ (ppm)", "count": "Property-days", "series": ""})
        fig.update_layout(legend=dict(orientation="h", y=-0.25))
        show(fig, 230)
        s = dist["stats"]
        st.caption(f"Naive mean-imputation collapses the spread (std {s['observed']['std']} → "
                   f"{s['mean_imputed']['std']}); interpolation keeps it realistic "
                   f"({s['interpolated']['std']}) — but neither improves prediction.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Equity & Fairness
# ════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Subgroup equity & fairness")
    eq = pd.DataFrame(B["subgroup_equity"])
    lr = next((m for m in B["models"] if m["id"] == "logreg_robust"), None)
    rf_flat = eq.loc[eq.property_type == "flat", "auroc"].iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Model reliability (AUROC) by property type**")
        fig = px.bar(eq, x="property_type", y="auroc", range_y=[0.5, 1.0],
                     category_orders={"property_type": PT_ORDER}, color="auroc",
                     color_continuous_scale=["#b42318", "#9a6700", "#2563eb"],
                     labels={"auroc": "AUROC", "property_type": ""},
                     hover_data=["n_properties", "cold_base_rate"])
        fig.update_layout(coloraxis_showscale=False)
        show(fig, 300)
        if lr:
            st.success(f"**Model choice fixed the fairness gap.** A logistic model scored flats just "
                       f"**{lr['per_type_auroc']['flat']}**; the deployed Random Forest lifts flats to "
                       f"**{rf_flat}** — the gap vs houses shrinks from ~0.15 to ~0.04.")
    with c2:
        st.markdown("**Cold base rate by property type**")
        fig = px.bar(eq, x="property_type", y="cold_base_rate", category_orders={"property_type": PT_ORDER},
                     color_discrete_sequence=["#9a6700"],
                     labels={"cold_base_rate": "Share of days below 19°C", "property_type": ""})
        fig.update_layout(yaxis_tickformat=".0%")
        show(fig, 300)
        st.info(f"**Flats are genuinely warmer** (cold rate "
                f"{B['dataset']['cold_rate_by_type']['flat']*100:.0f}% vs "
                f"~{B['dataset']['cold_rate_by_type']['terraced']*100:.0f}% for houses) because they share "
                f"walls and hold heat. So a single list favouring houses is **correct, not biased** — but we "
                f"still rank flats within their own type so the coldest flats aren't overlooked.")

    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**High-risk flag rate by group**")
        fair = pd.DataFrame(B["fairness"]["disparity_findings"])
        overall = float(fair["overall_rate"].iloc[0]) if len(fair) else 0.0
        fig = px.bar(fair.sort_values("high_risk_rate", ascending=False), x="group", y="high_risk_rate",
                     color_discrete_sequence=["#9a6700"],
                     labels={"high_risk_rate": "Flagged high-risk", "group": ""}, hover_data=["model_auroc", "n"])
        fig.add_hline(y=overall, line_dash="dash", line_color="#111")
        fig.update_layout(yaxis_tickformat=".0%")
        show(fig, 260)
        st.caption("Dashed line = estate-wide rate. Flag-rate gaps mirror true cold differences, not unfairness.")
    with c4:
        st.markdown("**What drives the score (deployed model)**")
        imp = pd.DataFrame(B["explainability_deployed"])
        imp["feature"] = imp["feature"].map(lambda f: FEAT_LABEL.get(f, f))
        fig = px.bar(imp.sort_values("importance"), x="importance", y="feature", orientation="h",
                     color_discrete_sequence=["#2563eb"], labels={"importance": "Feature importance", "feature": ""})
        show(fig, 260)
        st.caption("Random-forest importances. **Season** (time of year) and **energy use** dominate; "
                   "CO₂ is absent by design.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — Benchmark & Evidence
# ════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Model benchmark & evidence")
    comp = pd.DataFrame([{"model": m["label"], "AUROC": m["metrics"]["auroc"],
                          "flat AUROC": m["per_type_auroc"].get("flat", 0)} for m in B["models"]])
    perf = comp.melt(id_vars=["model"], value_vars=["AUROC", "flat AUROC"], var_name="metric", value_name="score")
    st.markdown("**Six models benchmarked — overall accuracy and fairness to flats**")
    fig = px.bar(perf, x="score", y="model", color="metric", barmode="group", orientation="h",
                 range_x=[0.5, 0.95], color_discrete_map={"AUROC": "#2563eb", "flat AUROC": "#9a6700"},
                 labels={"score": "AUROC (5-fold property CV)", "model": "", "metric": ""})
    fig.update_layout(legend=dict(orientation="h", y=-0.18))
    show(fig, 340)

    st.divider()
    st.markdown("#### 🔬 Benchmark a model")
    pick = st.selectbox("Choose a model", [m["label"] for m in B["models"]])
    M = next(m for m in B["models"] if m["label"] == pick)
    st.markdown(f"{badge(M['verdict'])} &nbsp; <span class='small'>missingness: {M['missingness']} · "
                f"interpretability: {M['interpretable']}</span>", unsafe_allow_html=True)
    prof = pd.DataFrame([{"metric": lab, "value": M["metrics"][kk]} for kk, lab in
                         [("f1", "F1"), ("npv", "NPV"), ("ppv", "PPV"), ("specificity", "Specificity"),
                          ("sensitivity", "Sensitivity"), ("auroc", "AUROC")]])
    pcol, tcol = st.columns(2)
    with pcol:
        st.markdown("**Metric profile**")
        fig = px.bar(prof, x="value", y="metric", orientation="h", range_x=[0, 1],
                     color_discrete_sequence=["#2563eb"], labels={"value": "", "metric": ""})
        show(fig, 240)
    with tcol:
        pt_df = pd.DataFrame([{"property_type": t, "auroc": M["per_type_auroc"][t]} for t in PT_ORDER
                              if t in M["per_type_auroc"]])
        if len(pt_df):
            st.markdown("**AUROC by property type**")
            fig = px.bar(pt_df, x="property_type", y="auroc", range_y=[0.5, 1.0],
                         category_orders={"property_type": PT_ORDER}, color="auroc",
                         color_continuous_scale=["#b42318", "#9a6700", "#2563eb"],
                         labels={"auroc": "AUROC", "property_type": ""})
            fig.update_layout(coloraxis_showscale=False)
            show(fig, 240)
    st.markdown(f"**Assessment:** {M['narrative']}")
    with st.expander("Deployment questions (q1–q8)"):
        QLABEL = {"q1": "How many cold properties will it miss?", "q2": "When it flags, how often is it right?",
                  "q3": "Is an all-clear safe to skip?", "q4": "How well does it separate cold from warm?",
                  "q5": "Consistent across property types?", "q6": "Effect of CO₂ sensor dropout?",
                  "q7": "Cost of a false negative?", "q8": "Recommend for upgrade allocation?"}
        for q, qa in M["deployment_questions"].items():
            st.markdown(f"**{QLABEL.get(q, q)}**  \n{qa}")

