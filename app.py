"""SCA-dream-soultion — Cold-Home Triage & Dataset Trust Auditor (website).

Interactive evidence dashboard + decision tool for a council housing team deciding
which social-housing properties get a boiler upgrade this winter.

Run:  streamlit run app.py

Reads the precomputed bundle from `python build_submission.py`
(reports/app_bundle.json) plus the dataset for the live Multimodal Explorer and
what-if predictor. Self-healing: rebuilds the bundle from the committed dataset
if it is missing (e.g. a fresh cloud deploy).
"""

from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / "reports" / "app_bundle.json"
MODEL = ROOT / "saved_models" / "model_a_logistic_baseline.joblib"

VERDICT_COLOR = {"READY": "#1a7f37", "PASS": "#1a7f37", "CONDITIONAL": "#9a6700",
                 "NOT READY": "#b42318", "FAIL": "#b42318"}
PT_ORDER = ["flat", "terraced", "semi-detached", "detached"]
PT_COLORS = ["#2563eb", "#16a34a", "#9a6700", "#b42318"]

st.set_page_config(page_title="Cold-Home Triage — SCA-dream-soultion", page_icon="🏠", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.4rem;}
.badge {display:inline-block;padding:3px 12px;border-radius:14px;color:#fff;font-weight:700;
        font-size:0.85rem;letter-spacing:.3px;}
.small {color:#6b7280;font-size:0.85rem;}
.card {border:1px solid #e5e7eb;border-radius:12px;padding:12px 14px;background:#fff;}
h1,h2,h3 {letter-spacing:-.01em;}
</style>
""", unsafe_allow_html=True)


# ── data loading (self-healing) ──────────────────────────────────────────────
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
    """Engineered frame + honest property split — for the live Multimodal Explorer."""
    from src.data_pipeline import build_feature_frame, load_and_merge, make_property_split
    feat = build_feature_frame(load_and_merge(ROOT / "data" / "raw"))
    tr, te, _, _ = make_property_split(feat, seed=42)
    return tr, te


@st.cache_data(show_spinner=False)
def fit_eval(cols_tuple):
    """Fit a logistic model on the chosen modality columns; return AUROC + per-type."""
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


def pt_scale():
    return alt.Scale(domain=PT_ORDER, range=PT_COLORS)


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
    st.caption("Dataset Trust Auditor · Housing Strand")
    st.markdown(f"**Team:** {B['team']['name']}")
    st.divider()
    ov = B["component_verdicts"]["overall"]
    st.markdown(f"<div class='card'>Overall dataset verdict &nbsp; {badge(ov)}</div>", unsafe_allow_html=True)
    cv = B["component_verdicts"]
    st.markdown(
        f"<div style='margin-top:8px'>"
        f"<span class='small'>Data quality</span> {badge(cv['data_quality'])}<br>"
        f"<span class='small'>Split integrity</span> {badge(cv['split_integrity'])}<br>"
        f"<span class='small'>Equity</span> {badge(cv['equity'])}</div>", unsafe_allow_html=True)
    st.divider()
    SHOW_TABLES = st.checkbox("📋 Also show data tables under charts", value=False)
    st.markdown(f"**Deployed:** {DEP['label']}")
    st.caption(f"Generated {B['generated_at']} · {B['dataset']['n_properties']} properties · "
               f"{B['dataset']['n_rows']:,} property-days · {len(B['models'])} models")


def maybe_table(df, hide_index=True):
    if SHOW_TABLES:
        st.dataframe(df, use_container_width=True, hide_index=hide_index)


# ── header KPIs ──────────────────────────────────────────────────────────────
st.title("Cold-Home Triage & Dataset Trust Auditor")
st.markdown("Rank homes for a boiler upgrade, **fuse multimodal sensor data**, **audit the gaps**, and "
            "**prove the ranking is fair** — honest about what it can't trust.")
k = st.columns(5)
k[0].metric("Properties", B["dataset"]["n_properties"])
k[1].metric("Cold-risk rate", f"{B['dataset']['cold_rate']*100:.1f}%")
k[2].metric("CO₂ missing (MNAR)", f"{B['dataset']['missingness_by_modality']['avgCo2']*100:.0f}%")
k[3].metric("Sensor-repair flags", f"{B['sensor_health']['flagged_count_at_each_threshold'][2]}")
k[4].metric("Deployed AUROC", f"{DEP['metrics']['auroc']:.2f}")

tabs = st.tabs(["🏠 Upgrade Triage", "🔀 Multimodal Explorer", "📡 Sensor Health & MNAR",
                "⚖️ Equity & Fairness", "🧩 Missingness Lab", "🔬 Evidence Dashboard",
                "📋 Models & Governance"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Upgrade Triage
# ════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Winter upgrade priority list")
    c1, c2 = st.columns([3, 2])
    with c1:
        budget = st.slider("Upgrade budget (top N properties)", 10, 250,
                           B["coverage"]["top_ranked_count"], step=5)
        only_reliable = st.checkbox("Only show properties with reliable sensor data", False)
        view = rank_df[rank_df["data_reliability"] == "HIGH"] if only_reliable else rank_df
        top = view.head(budget)
        st.altair_chart(alt.Chart(top.head(20)).mark_bar().encode(
            x=alt.X("cold_risk_score:Q", scale=alt.Scale(domain=[0, 1]), title="Cold-risk score (0–1)"),
            y=alt.Y("reference:N", sort="-x", title=None),
            color=alt.Color("data_reliability:N", scale=alt.Scale(domain=["HIGH", "LOW"],
                            range=["#1a7f37", "#b42318"]), legend=alt.Legend(title="Sensor data")),
            tooltip=["rank", "reference", "property_type", "cold_risk_score", "co2_dropout_rate",
                     "data_reliability", "recommended_action"],
        ).properties(height=460, title=f"Top 20 of {len(top)} prioritised properties"),
            use_container_width=True)
        maybe_table(top.head(budget))
    with c2:
        st.markdown("**Estate mix vs upgrade-list mix**")
        est = pd.DataFrame([{"property_type": t, "n": B["dataset"]["property_type_counts"][t]}
                            for t in PT_ORDER])
        topmix = pd.DataFrame([{"property_type": d["property_type"], "n": d["n_in_top"]}
                               for d in B["coverage"]["property_type_distribution"]])
        d1, d2 = st.columns(2)
        d1.altair_chart(alt.Chart(est).mark_arc(innerRadius=45).encode(
            theta=alt.Theta("n:Q", stack=True), color=alt.Color("property_type:N", scale=pt_scale(),
            legend=alt.Legend(orient="bottom", title=None)), tooltip=["property_type", "n"]
        ).properties(height=210, title="Whole estate"), use_container_width=True)
        d2.altair_chart(alt.Chart(topmix).mark_arc(innerRadius=45).encode(
            theta=alt.Theta("n:Q", stack=True), color=alt.Color("property_type:N", scale=pt_scale(),
            legend=alt.Legend(orient="bottom", title=None)), tooltip=["property_type", "n"]
        ).properties(height=210, title=f"Top {B['coverage']['top_ranked_count']}"), use_container_width=True)
        st.info(f"**Fair re-ranking:** within-type allocation adds "
                f"**{B['coverage']['flats_added_under_fair_weighting']} flats** the global top "
                f"{B['coverage']['top_ranked_count']} omits. Flats are genuinely warmer (cold rate "
                f"{B['dataset']['cold_rate_by_type']['flat']*100:.0f}% vs "
                f"~{B['dataset']['cold_rate_by_type']['terraced']*100:.0f}% for houses) — a single list "
                f"favouring houses is *correct*, not biased.")
    st.download_button("⬇ Download full ranked list (CSV)", rank_df.to_csv(index=False),
                       "upgrade_ranking.csv", "text/csv")
    st.divider()
    lc, rc = st.columns(2)
    with lc:
        st.markdown("#### 🔎 Inspect a property")
        ref = st.selectbox("Property reference", rank_df["reference"].tolist())
        row = rank_df[rank_df["reference"] == ref].iloc[0]
        st.markdown(f"**Rank #{int(row['rank'])} of {len(rank_df)}** · {row['property_type']}")
        m = st.columns(3)
        m[0].metric("Cold-risk score", f"{row['cold_risk_score']:.2f}")
        m[1].metric("Observed cold rate", f"{row['observed_cold_rate']*100:.0f}%")
        m[2].metric("CO₂ dropout", f"{row['co2_dropout_rate']*100:.0f}%")
        st.markdown(f"- **Sensor data reliability:** {'🟢 HIGH' if row['data_reliability']=='HIGH' else '🔴 LOW'}")
        st.markdown(f"- **Recommended action:** {row['recommended_action']}")
        if row["sensor_repair_needed"]:
            st.warning("CO₂ sensor has failed for this property — dispatch a repair so future audits are complete.")
    with rc:
        st.markdown("#### 🧪 What-if predictor")
        st.caption("Interpretable logistic baseline — type conditions for a property-day and it scores it live.")
        model = load_model()
        if model is None:
            st.warning("Baseline model not found — run build_submission.py.")
        else:
            pt = st.selectbox("Property type", PT_ORDER, key="wf_pt")
            mo = st.slider("Month", 1, 12, 1, key="wf_mo")
            hum = st.slider("Indoor humidity (%)", 30.0, 90.0, 60.0, key="wf_h")
            kwh = st.slider("Energy use (kWh/day)", 0.0, 60.0, 18.0, key="wf_k")
            noise = st.slider("Ambient noise (dB)", 20.0, 80.0, 40.0, key="wf_n")
            dow = st.select_slider("Day of week", options=list(range(7)), value=2,
                                   format_func=lambda d: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][d], key="wf_d")
            fr = pd.DataFrame([{"avgHumidity": hum, "smart_meter_kwh": kwh, "noise_db": noise,
                                "day_of_week": dow, "month": mo, "is_flat": int(pt == "flat"),
                                "pt_terraced": int(pt == "terraced"),
                                "pt_semi_detached": int(pt == "semi-detached"),
                                "pt_detached": int(pt == "detached")}])
            prob = float(model.predict_proba(fr)[:, 1][0])
            st.metric("Predicted cold-risk probability", f"{prob*100:.0f}%")
            st.progress(min(max(prob, 0.0), 1.0))

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Multimodal Explorer
# ════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("Multimodal Fusion Explorer")
    st.markdown("This is a **multimodal** problem: the cold-risk score fuses several sensor + metadata "
                "streams. Below, see how much each modality contributes — then **build your own fusion** "
                "and watch the model re-train live.")
    mm = B["multimodal"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Each modality on its own** (AUROC)")
        sdf = pd.DataFrame(mm["single"])
        st.altair_chart(alt.Chart(sdf).mark_bar(color="#2563eb").encode(
            x=alt.X("auroc:Q", scale=alt.Scale(domain=[0.5, 0.85]), title="AUROC alone"),
            y=alt.Y("modality:N", sort="-x", title=None), tooltip=["modality", "auroc"]
        ).properties(height=280), use_container_width=True)
        maybe_table(sdf)
    with c2:
        st.markdown("**Marginal value when fused** (leave-one-out)")
        ldf = pd.DataFrame(mm["leave_one_out"])
        st.altair_chart(alt.Chart(ldf).mark_bar().encode(
            x=alt.X("marginal:Q", title="AUROC lost if this modality is removed"),
            y=alt.Y("modality:N", sort="-x", title=None),
            color=alt.condition(alt.datum.marginal >= 0.02, alt.value("#16a34a"), alt.value("#94a3b8")),
            tooltip=["modality", "marginal", "auroc_without"]).properties(height=280), use_container_width=True)
        maybe_table(ldf)
    st.info(f"**Fusion beats any single stream:** the combined model reaches AUROC "
            f"**{mm['combined_auroc']}** vs the best single modality "
            f"(**{max(mm['single'], key=lambda s: s['auroc'])['modality']}**, "
            f"{max(s['auroc'] for s in mm['single'])}). Energy and humidity carry the signal; **CO₂'s marginal "
            f"value is only {[l['marginal'] for l in mm['leave_one_out'] if l['modality']=='CO₂'][0]:+}** — the "
            f"same conclusion the Missingness Lab reaches from a different angle.")

    st.divider()
    st.markdown("#### 🛠 Build your own fusion (live)")
    st.caption("Pick which modalities to feed the model. It re-fits on the held-out property split instantly.")
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
            st.metric("AUROC (your fusion)", f"{auroc:.3f}",
                      delta=round(auroc - mm["combined_auroc"], 3))
            st.caption(f"vs full multimodal fusion ({mm['combined_auroc']})")
            if use_lag:
                st.error("Leakage on: the jump comes from ~yesterday's value of the target, not real skill.")
        with b2:
            pdf = pd.DataFrame([{"property_type": t, "auroc": per[t]} for t in PT_ORDER if per[t] is not None])
            st.altair_chart(alt.Chart(pdf).mark_bar().encode(
                x=alt.X("property_type:N", sort=PT_ORDER, title=None),
                y=alt.Y("auroc:Q", scale=alt.Scale(domain=[0.5, 1.0]), title="AUROC"),
                color=alt.condition(alt.datum.auroc < 0.75, alt.value("#b42318"), alt.value("#2563eb")),
                tooltip=["property_type", "auroc"]).properties(height=240, title="Your fusion — AUROC by type"),
                use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Sensor Health & MNAR
# ════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Estate-wide sensor data-quality monitor")
    miss = pd.DataFrame([{"modality": k2, "missing": v}
                         for k2, v in B["sensor_health"]["missingness_by_modality"].items()])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Missingness by modality**")
        st.altair_chart(alt.Chart(miss).mark_bar().encode(
            x=alt.X("missing:Q", axis=alt.Axis(format="%"), title="% missing"),
            y=alt.Y("modality:N", sort="-x", title=None),
            color=alt.condition(alt.datum.missing > 0.3, alt.value("#b42318"), alt.value("#1a7f37")),
            tooltip=["modality", alt.Tooltip("missing:Q", format=".1%")]).properties(height=260),
            use_container_width=True)
        maybe_table(miss)
        st.caption("Temperature, humidity, smart-meter, noise are reliable. CO₂ (38%) and the resident "
                   "survey (97%) are Missing **Not** At Random.")
    with c2:
        st.markdown("**Configurable dropout threshold**")
        thr = st.slider("Flag properties with CO₂ dropout ≥", 0.1, 0.95, 0.5, step=0.05)
        drop = pd.DataFrame(B["sensor_health"]["dropout_distribution"])
        st.metric("Properties flagged for sensor repair", int((drop["co2_dropout_rate"] >= thr).sum()))
        hist = alt.Chart(drop).mark_bar().encode(
            x=alt.X("co2_dropout_rate:Q", bin=alt.Bin(maxbins=20), title="CO₂ dropout rate per property"),
            y=alt.Y("count()", title="Properties"),
            color=alt.condition(alt.datum.co2_dropout_rate >= thr, alt.value("#b42318"), alt.value("#94a3b8")))
        rule = alt.Chart(pd.DataFrame({"t": [thr]})).mark_rule(color="#111", strokeDash=[4, 4]).encode(x="t:Q")
        st.altair_chart((hist + rule).properties(height=230), use_container_width=True)
    sweep = pd.DataFrame({"threshold": B["sensor_health"]["thresholds_tested"],
                          "flagged": B["sensor_health"]["flagged_count_at_each_threshold"]})
    st.markdown("**Threshold sensitivity**")
    st.altair_chart(alt.Chart(sweep).mark_line(point=True).encode(
        x=alt.X("threshold:Q", title="Dropout threshold"), y=alt.Y("flagged:Q", title="Properties flagged"),
        tooltip=["threshold", "flagged"]).properties(height=220), use_container_width=True)
    st.info("Recommended cut-off **0.5** → 40 properties (the natural break; the MNAR cohort sits at 70–95%). "
            "0.3 → 140 (fatigue); 0.8 → 24 (misses borderline failures).")
    st.markdown("#### MNAR patterns found")
    for p in B["mnar_patterns"]:
        with st.expander(f"🔸 {p['name']}  ·  sensor: {p['sensor']}"):
            st.markdown(f"**Mechanism:** {p['mechanism']}")
            st.json(p["evidence"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Equity & Fairness
# ════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Subgroup equity & fairness audit")
    eq = pd.DataFrame(B["subgroup_equity"])
    lr = next((m for m in B["models"] if m["id"] == "logreg_robust"), None)
    rf_flat = eq.loc[eq.property_type == "flat", "auroc"].iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Deployed model AUROC by property type**")
        st.altair_chart(alt.Chart(eq).mark_bar().encode(
            x=alt.X("property_type:N", sort=PT_ORDER, title=None),
            y=alt.Y("auroc:Q", scale=alt.Scale(domain=[0.5, 1.0]), title="AUROC"),
            color=alt.condition(alt.datum.auroc < 0.75, alt.value("#b42318"), alt.value("#2563eb")),
            tooltip=["property_type", "auroc", "n_properties", "cold_base_rate"]).properties(height=300),
            use_container_width=True)
        if lr:
            st.success(f"**Model choice fixed the equity gap.** The logistic baseline scored flats just "
                       f"**{lr['per_type_auroc']['flat']}**; the deployed Random Forest lifts flats to "
                       f"**{rf_flat}** — the gap vs houses shrinks from ~0.15 to ~0.04.")
    with c2:
        st.markdown("**Cold base rate by property type**")
        st.altair_chart(alt.Chart(eq).mark_bar(color="#9a6700").encode(
            x=alt.X("property_type:N", sort=PT_ORDER, title=None),
            y=alt.Y("cold_base_rate:Q", axis=alt.Axis(format="%"), title="Cold-risk base rate"),
            tooltip=["property_type", alt.Tooltip("cold_base_rate:Q", format=".1%")]).properties(height=300),
            use_container_width=True)
        st.caption("Flats share walls (thermal mass) and stay ~3°C warmer — why flats are still ranked within type.")
    st.markdown("**Fairness disparity — high-risk flag rate by group**")
    fair = pd.DataFrame(B["fairness"]["disparity_findings"])
    overall = float(fair["overall_rate"].iloc[0]) if len(fair) else 0.0
    fbar = alt.Chart(fair).mark_bar().encode(
        x=alt.X("group:N", sort="-y", title=None),
        y=alt.Y("high_risk_rate:Q", axis=alt.Axis(format="%"), title="Flagged high-risk"),
        color=alt.condition(alt.datum.high_risk_rate >= overall, alt.value("#9a6700"), alt.value("#94a3b8")),
        tooltip=["group", alt.Tooltip("high_risk_rate:Q", format=".1%"), "model_auroc", "n"])
    orule = alt.Chart(pd.DataFrame({"y": [overall]})).mark_rule(color="#111", strokeDash=[5, 5]).encode(y="y:Q")
    st.altair_chart((fbar + orule).properties(height=260), use_container_width=True)
    maybe_table(fair)
    st.caption(f"Dashed line = estate-wide flag rate ({overall*100:.0f}%). Flag-rate gaps mirror true cold "
               f"differences, not unfairness — the real risk is reliability, fixed by per-type ranking.")
    st.divider()
    e1, e2 = st.columns(2)
    with e1:
        st.markdown("#### 🧠 What drives the score (deployed model)")
        imp = pd.DataFrame(B["explainability_deployed"])
        st.altair_chart(alt.Chart(imp).mark_bar(color="#2563eb").encode(
            x=alt.X("importance:Q", title="Feature importance"),
            y=alt.Y("feature:N", sort="-x", title=None), tooltip=["feature", "importance"]
        ).properties(height=260), use_container_width=True)
        st.caption("Random-forest importances. Season and energy dominate; CO₂ is absent by design.")
    with e2:
        st.markdown("#### 🎚 Decision-threshold sweep")
        sw = pd.DataFrame(B["decision_threshold_sweep"]).melt(id_vars="threshold", var_name="metric", value_name="value")
        st.altair_chart(alt.Chart(sw).mark_line(point=True).encode(
            x=alt.X("threshold:Q"), y=alt.Y("value:Q"),
            color=alt.Color("metric:N", legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["threshold", "metric", "value"]).properties(height=260), use_container_width=True)
        st.caption("Cold-home false negatives are costly, so the operating threshold favours sensitivity.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — Missingness Lab
# ════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Missingness Lab — analysing the gaps, not just reporting them")
    mech = B["missingness"]["mechanism"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Is the CO₂ dropout random or patterned?**")
        st.metric("Predictability of dropout from property type (AUROC)",
                  f"{mech['predict_high_dropout_auroc']:.2f}")
        st.markdown(f"- {mech['mechanism_verdict']}")
        st.markdown(f"- Correlation of dropout with cold-risk: **{mech['corr_dropout_vs_cold_rate']}**")
        st.caption(mech["outcome_note"])
    with c2:
        st.markdown("**High-dropout share by property type**")
        shr = pd.DataFrame([{"property_type": k2, "share": v}
                            for k2, v in mech["high_dropout_share_by_type"].items()])
        st.altair_chart(alt.Chart(shr).mark_bar(color="#7c3aed").encode(
            x=alt.X("property_type:N", sort=PT_ORDER, title=None),
            y=alt.Y("share:Q", axis=alt.Axis(format="%"), title="% of type with >50% dropout"),
            tooltip=["property_type", alt.Tooltip("share:Q", format=".1%")]).properties(height=260),
            use_container_width=True)
    st.markdown("#### Does *fixing* the missingness help? (four strategies)")
    imp_cmp = pd.DataFrame(B["missingness"]["imputation_comparison"])
    st.altair_chart(alt.Chart(imp_cmp).mark_bar(color="#2563eb").encode(
        x=alt.X("auroc:Q", scale=alt.Scale(domain=[0.80, 0.93]), title="AUROC"),
        y=alt.Y("strategy:N", sort="-x", title=None), tooltip=["strategy", "model", "auroc"]
    ).properties(height=200), use_container_width=True)
    maybe_table(imp_cmp)
    st.info("First three hold the **model fixed** (logistic) and only change CO₂ handling — AUROC barely moves "
            "(≈0.84). The fourth changes the *model* (gradient boosting, native NaN) — its gain is the algorithm, "
            "not CO₂. Conclusion: the CO₂ gap is a **data-integrity** issue to repair, not a predictive loss.")
    st.markdown("#### What each imputation does to the CO₂ distribution")
    dist = B["missingness"]["distribution"]
    hist_df = pd.DataFrame(dist["histogram"]).melt(id_vars="co2", var_name="series", value_name="count")
    st.altair_chart(alt.Chart(hist_df).mark_line().encode(
        x=alt.X("co2:Q", title="CO₂ (ppm)"), y=alt.Y("count:Q", title="Property-days"),
        color=alt.Color("series:N", legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["co2", "series", "count"]).properties(height=280), use_container_width=True)
    s = dist["stats"]
    m = st.columns(3)
    m[0].metric("Observed CO₂ std", s["observed"]["std"])
    m[1].metric("Mean-imputed std", s["mean_imputed"]["std"], delta=round(s["mean_imputed"]["std"]-s["observed"]["std"],1))
    m[2].metric("Interpolated std", s["interpolated"]["std"], delta=round(s["interpolated"]["std"]-s["observed"]["std"],1))
    st.caption(dist["note"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 6 — Evidence Dashboard
# ════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("Evidence Dashboard — five required views")
    v = B["evidence_views"]
    cols = st.columns(5)
    labels = [("sensor_data_quality", "Sensor quality"), ("mnar_analysis", "MNAR"),
              ("subgroup_equity", "Subgroup equity"), ("leakage_audit", "Leakage audit"),
              ("dataset_audit", "Dataset audit")]
    for col, (key, lab) in zip(cols, labels):
        verdict = B["component_verdicts"]["overall"] if key == "dataset_audit" else v[key]
        col.markdown(f"<div class='card'><div class='small'>{lab}</div>{badge(verdict)}</div>",
                     unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 4 · Leakage audit — why we excluded `lag_temp`")
    lk = B["leakage"]
    leak_df = pd.DataFrame({
        "model": ["No lag (honest)", "+ lag_temp", "+ lag_temp + row-split"],
        "order": [0, 1, 2],
        "auroc": [lk["linear_baseline_auroc"], lk["linear_baseline_auroc"] + lk["lag_inflation_auroc"],
                  lk["row_split_auroc"]]})
    bars = alt.Chart(leak_df).mark_bar(color="#7c3aed").encode(
        x=alt.X("auroc:Q", scale=alt.Scale(domain=[0.5, 1.0]), title="AUROC (0.5 = chance)"),
        y=alt.Y("model:N", sort=alt.SortField("order"), title=None), tooltip=["model", "auroc"])
    txt = alt.Chart(leak_df).mark_text(align="left", dx=4, color="#111").encode(
        x="auroc:Q", y=alt.Y("model:N", sort=alt.SortField("order")),
        text=alt.Text("auroc:Q", format=".3f"))
    st.altair_chart((bars + txt).properties(height=200), use_container_width=True)
    maybe_table(leak_df.drop(columns="order"))
    st.markdown(f"Within the same (logistic) model, adding `lag_temp` inflates AUROC by "
                f"**+{lk['lag_inflation_auroc']}** — but it is ~yesterday's value of the target, so the gain is "
                f"**target leakage, not skill**. The deployed Random Forest reaches **{lk['deployed_auroc']}** "
                f"honestly without it. Split is **property-level** "
                f"({lk['split_audit']['n_train_properties']} train / {lk['split_audit']['n_test_properties']} "
                f"test, {lk['split_audit']['n_overlap_properties']} overlapping properties).")
    st.markdown("#### 1 · Data quality & 2 · MNAR")
    st.markdown(f"CO₂ adds only **{lk['co2_lift_auroc']:+}** AUROC within a fixed model — the dropout is an "
                "**asset-management** problem (repair sensors), not a ranking-bias problem. See the Missingness Lab.")
    st.markdown("#### 3 · Subgroup equity — AUROC gap vs terraced reference")
    eqd = pd.DataFrame(B["subgroup_equity"])
    st.altair_chart(alt.Chart(eqd).mark_bar().encode(
        x=alt.X("gap_vs_terraced:Q", title="AUROC gap vs terraced", axis=alt.Axis(format="+.2f")),
        y=alt.Y("property_type:N", sort=PT_ORDER, title=None),
        color=alt.condition(alt.datum.gap_vs_terraced <= -0.05, alt.value("#9a6700"), alt.value("#1a7f37")),
        tooltip=["property_type", "auroc", "gap_vs_terraced", "n_properties", "cold_base_rate"]
    ).properties(height=200), use_container_width=True)
    maybe_table(eqd)
    st.caption("All groups within ~0.04 of the terraced reference under the deployed model.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 7 — Models & Governance
# ════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("Model evidence cards & governance verdicts")
    comp = pd.DataFrame([{"model": m["label"], "AUROC": m["metrics"]["auroc"],
                          "flat AUROC": m["per_type_auroc"].get("flat", 0),
                          "sensitivity": m["metrics"]["sensitivity"], "PPV": m["metrics"]["ppv"],
                          "verdict": m["verdict"]} for m in B["models"]])
    vscale = alt.Scale(domain=list(VERDICT_COLOR.keys()), range=list(VERDICT_COLOR.values()))
    perf = comp.melt(id_vars=["model", "verdict"], value_vars=["AUROC", "flat AUROC"],
                     var_name="metric", value_name="score")
    cc1, cc2 = st.columns([3, 2])
    with cc1:
        st.markdown("**Overall vs flat AUROC, per model**")
        st.altair_chart(alt.Chart(perf).mark_bar().encode(
            y=alt.Y("model:N", sort="-x", title=None), yOffset="metric:N",
            x=alt.X("score:Q", scale=alt.Scale(domain=[0.5, 0.95]), title="AUROC"),
            color=alt.Color("metric:N", scale=alt.Scale(domain=["AUROC", "flat AUROC"],
                            range=["#2563eb", "#9a6700"]), legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["model", "metric", "score"]).properties(height=320), use_container_width=True)
    with cc2:
        st.markdown("**Verdict mix across models**")
        vc = comp["verdict"].value_counts().reset_index()
        vc.columns = ["verdict", "n"]
        st.altair_chart(alt.Chart(vc).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("n:Q", stack=True),
            color=alt.Color("verdict:N", scale=vscale, legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["verdict", "n"]).properties(height=300), use_container_width=True)
    maybe_table(comp)

    st.divider()
    st.markdown("#### 🔽 Inspect a model")
    pick = st.selectbox("Choose a model", [m["label"] for m in B["models"]])
    M = next(m for m in B["models"] if m["label"] == pick)
    st.markdown(f"{badge(M['verdict'])} &nbsp; <span class='small'>missingness: {M['missingness']} · "
                f"interpretability: {M['interpretable']}</span>", unsafe_allow_html=True)
    prof = pd.DataFrame([{"metric": lab, "value": M["metrics"][kk]} for kk, lab in
                         [("auroc", "AUROC"), ("sensitivity", "Sensitivity"), ("specificity", "Specificity"),
                          ("ppv", "PPV"), ("npv", "NPV"), ("f1", "F1")]])
    pcol, tcol = st.columns(2)
    with pcol:
        st.markdown("**Metric profile**")
        st.altair_chart(alt.Chart(prof).mark_bar(color="#2563eb").encode(
            x=alt.X("value:Q", scale=alt.Scale(domain=[0, 1]), title=None),
            y=alt.Y("metric:N", sort=["AUROC", "Sensitivity", "Specificity", "PPV", "NPV", "F1"], title=None),
            tooltip=["metric", "value"]).properties(height=240), use_container_width=True)
    with tcol:
        pt_df = pd.DataFrame([{"property_type": t, "auroc": M["per_type_auroc"][t]} for t in PT_ORDER
                              if t in M["per_type_auroc"]])
        if len(pt_df):
            st.markdown("**AUROC by property type**")
            st.altair_chart(alt.Chart(pt_df).mark_bar().encode(
                x=alt.X("property_type:N", sort=PT_ORDER, title=None),
                y=alt.Y("auroc:Q", scale=alt.Scale(domain=[0.5, 1.0]), title=None),
                color=alt.condition(alt.datum.auroc < 0.75, alt.value("#b42318"), alt.value("#2563eb")),
                tooltip=["property_type", "auroc"]).properties(height=240), use_container_width=True)
    st.markdown(f"**Assessment:** {M['narrative']}")
    with st.expander("Deployment questions (q1–q8)"):
        QLABEL = {"q1": "How many cold properties will it miss?", "q2": "When it flags, how often is it right?",
                  "q3": "Is an all-clear safe to skip?", "q4": "How well does it separate cold from warm?",
                  "q5": "Consistent across property types?", "q6": "Effect of CO₂ sensor dropout?",
                  "q7": "Cost of a false negative?", "q8": "Recommend for upgrade allocation?"}
        for q, qa in M["deployment_questions"].items():
            st.markdown(f"**{QLABEL.get(q, q)}**  \n{qa}")

    st.divider()
    st.markdown("#### Component verdicts")
    cc = st.columns(4)
    for col, (k2, lab) in zip(cc, [("data_quality", "Data quality"), ("split_integrity", "Split integrity"),
                                   ("equity", "Equity"), ("overall", "OVERALL")]):
        col.markdown(f"**{lab}**<br>{badge(B['component_verdicts'][k2])}", unsafe_allow_html=True)
    st.caption("Files: reference/omaib_pathway.json · reference/housing_benchmark_card.json — "
               "validated by `python validate_submission.py`.")
