"""SCA-dream-soultion — Cold-Home Triage & Dataset Trust Auditor (website).

An interactive evidence dashboard + decision tool for a council housing team
deciding which social-housing properties get a boiler upgrade this winter.

Run:
    streamlit run app.py

It reads the precomputed bundle written by `python build_submission.py`
(reports/app_bundle.json) plus the saved model for the live "what-if" predictor,
so the site loads instantly and never retrains in the browser.
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

VERDICT_COLOR = {
    "READY": "#1a7f37", "PASS": "#1a7f37",
    "CONDITIONAL": "#9a6700",
    "NOT READY": "#b42318", "FAIL": "#b42318",
}
PT_ORDER = ["flat", "terraced", "semi-detached", "detached"]

st.set_page_config(page_title="Cold-Home Triage — SCA-dream-soultion",
                   page_icon="🏠", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem;}
.badge {display:inline-block;padding:3px 12px;border-radius:14px;color:#fff;
        font-weight:700;font-size:0.85rem;letter-spacing:.3px;}
.small {color:#6b7280;font-size:0.85rem;}
.card {border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;background:#fff;}
h1,h2,h3 {letter-spacing:-.01em;}
</style>
""", unsafe_allow_html=True)


# ── data loading ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="First run: building models & evidence from the dataset…")
def bootstrap() -> str:
    """Ensure artifacts exist; build them from the raw CSV if missing.

    On a fresh cloud deploy (Streamlit Community Cloud, Hugging Face Spaces) the
    git-ignored model/splits are absent, so we regenerate them from the committed
    dataset. Rebuilding (rather than shipping a pickle) also avoids scikit-learn
    version-mismatch errors when unpickling.
    """
    if BUNDLE.exists() and MODEL.exists():
        return "ok"
    try:
        from build_submission import main as build_main
        build_main()
        return "ok"
    except Exception as exc:  # surfaced to the user instead of a blank page
        return f"build failed: {exc}"


@st.cache_data
def load_bundle():
    if not BUNDLE.exists():
        return None
    return json.loads(BUNDLE.read_text(encoding="utf-8"))


@st.cache_resource
def load_model():
    import joblib
    try:
        return joblib.load(MODEL)
    except Exception:
        # Missing or version-incompatible pickle -> rebuild from source, then retry.
        try:
            from build_submission import main as build_main
            build_main()
            return joblib.load(MODEL)
        except Exception:
            return None


def badge(verdict: str) -> str:
    c = VERDICT_COLOR.get(verdict, "#475467")
    return f'<span class="badge" style="background:{c}">{verdict}</span>'


_status = bootstrap()
B = load_bundle()
if B is None:
    st.error(f"Could not load app data ({_status}). Run `python build_submission.py` locally, "
             f"or check that data/raw/housing_properties_daily.csv is present.")
    st.stop()

rank_df = pd.DataFrame(B["ranking"])


# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏠 Cold-Home Triage")
    st.caption("Dataset Trust Auditor · Housing Strand")
    st.markdown(f"**Team:** {B['team']['name']}")
    st.divider()
    st.markdown("**Overall dataset verdict**")
    st.markdown(badge(B["component_verdicts"]["overall"]), unsafe_allow_html=True)
    cv = B["component_verdicts"]
    for k, lab in [("data_quality", "Data quality"), ("split_integrity", "Split integrity"),
                   ("equity", "Equity")]:
        st.markdown(f"<span class='small'>{lab}</span> &nbsp; {badge(cv[k])}",
                    unsafe_allow_html=True)
    st.divider()
    st.caption(f"Generated {B['generated_at']} · {B['dataset']['n_properties']} properties · "
               f"{B['dataset']['n_rows']:,} property-days")


# ── header KPIs ──────────────────────────────────────────────────────────────
st.title("Cold-Home Triage & Dataset Trust Auditor")
st.markdown("One tool, three jobs: **rank properties for a boiler upgrade**, **audit the "
            "sensor data it relies on**, and **prove the ranking is fair** — and it is honest "
            "about which properties the data cannot confidently rank.")

k = st.columns(5)
k[0].metric("Properties", B["dataset"]["n_properties"])
k[1].metric("Cold-risk rate", f"{B['dataset']['cold_rate']*100:.1f}%")
k[2].metric("CO₂ missing (MNAR)", f"{B['dataset']['missingness_by_modality']['avgCo2']*100:.0f}%")
k[3].metric("Sensor-repair flags", f"{B['sensor_health']['flagged_count_at_each_threshold'][2]}")
k[4].metric("Deployed model AUROC", f"{B['models'][0]['metrics']['auroc']:.2f}")

tabs = st.tabs(["🏠 Upgrade Triage", "📡 Sensor Health & MNAR", "⚖️ Equity & Fairness",
                "🔬 Evidence Dashboard", "📋 Model Cards & Governance"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Upgrade Triage  (challenge 1)
# ════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Winter upgrade priority list")
    c1, c2 = st.columns([3, 2])
    with c1:
        budget = st.slider("Upgrade budget (top N properties)", 10, 250,
                           B["coverage"]["top_ranked_count"], step=5)
        only_reliable = st.checkbox("Only show properties with reliable sensor data", False)
        view = rank_df.copy()
        if only_reliable:
            view = view[view["data_reliability"] == "HIGH"]
        top = view.head(budget)

        chart = alt.Chart(top.head(40)).mark_bar().encode(
            x=alt.X("cold_risk_score:Q", title="Cold-risk score"),
            y=alt.Y("reference:N", sort="-x", title=None),
            color=alt.Color("data_reliability:N",
                            scale=alt.Scale(domain=["HIGH", "LOW"],
                                            range=["#1a7f37", "#b42318"]),
                            legend=alt.Legend(title="Sensor data")),
            tooltip=["rank", "reference", "property_type", "cold_risk_score",
                     "co2_dropout_rate", "data_reliability", "recommended_action"],
        ).properties(height=520, title=f"Top {min(budget,40)} of {budget} prioritised properties")
        st.altair_chart(chart, use_container_width=True)
    with c2:
        st.markdown("**Coverage of the upgrade list**")
        cov = pd.DataFrame(B["coverage"]["property_type_distribution"])
        cov_long = cov.melt(id_vars="property_type",
                            value_vars=["estate_share", "top_ranked_share"],
                            var_name="set", value_name="share")
        cov_chart = alt.Chart(cov_long).mark_bar().encode(
            x=alt.X("property_type:N", sort=PT_ORDER, title=None),
            xOffset="set:N",
            y=alt.Y("share:Q", axis=alt.Axis(format="%"), title="Share"),
            color=alt.Color("set:N", scale=alt.Scale(
                domain=["estate_share", "top_ranked_share"],
                range=["#9ca3af", "#2563eb"]), legend=alt.Legend(title=None, orient="bottom")),
            tooltip=["property_type", "set", alt.Tooltip("share:Q", format=".1%")],
        ).properties(height=240, title="Estate vs upgrade-list mix")
        st.altair_chart(cov_chart, use_container_width=True)
        st.info(f"**Fair re-ranking:** within-type allocation adds "
                f"**{B['coverage']['flats_added_under_fair_weighting']} flats** the global top "
                f"{B['coverage']['top_ranked_count']} omits. Flats are genuinely warmer (cold rate "
                f"{B['dataset']['cold_rate_by_type']['flat']*100:.0f}% vs "
                f"~{B['dataset']['cold_rate_by_type']['terraced']*100:.0f}% for houses) — so a single "
                f"list favouring houses is *correct*, not biased. Choose 'coldest absolute' vs "
                f"'coldest per stock type' deliberately.")

    st.download_button("⬇ Download full ranked list (CSV)",
                       rank_df.to_csv(index=False), "upgrade_ranking.csv", "text/csv")

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
        rel = "🟢 HIGH" if row["data_reliability"] == "HIGH" else "🔴 LOW"
        st.markdown(f"- **Sensor data reliability:** {rel}")
        st.markdown(f"- **Model reliability:** {row['model_reliability']}")
        st.markdown(f"- **Recommended action:** {row['recommended_action']}")
        if row["sensor_repair_needed"]:
            st.warning("CO₂ sensor has failed for this property — dispatch a repair so future "
                       "audits can confirm its data quality.")
    with rc:
        st.markdown("#### 🧪 What-if predictor (live model)")
        st.caption("Enter conditions for a property-day and the deployed model scores it.")
        model = load_model()
        if model is None:
            st.warning("Saved model not found — run build_submission.py.")
        else:
            pt = st.selectbox("Property type", PT_ORDER, key="wf_pt")
            mo = st.slider("Month", 1, 12, 1, key="wf_mo")
            hum = st.slider("Indoor humidity (%)", 30.0, 90.0, 60.0, key="wf_h")
            kwh = st.slider("Energy use (kWh/day)", 0.0, 60.0, 18.0, key="wf_k")
            noise = st.slider("Ambient noise (dB)", 20.0, 80.0, 40.0, key="wf_n")
            dow = st.select_slider("Day of week", options=list(range(7)),
                                   value=2, format_func=lambda d:
                                   ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d], key="wf_d")
            feat_row = pd.DataFrame([{
                "avgHumidity": hum, "smart_meter_kwh": kwh, "noise_db": noise,
                "day_of_week": dow, "month": mo, "is_flat": int(pt == "flat"),
                "pt_terraced": int(pt == "terraced"),
                "pt_semi_detached": int(pt == "semi-detached"),
                "pt_detached": int(pt == "detached"),
            }])
            prob = float(model.predict_proba(feat_row)[:, 1][0])
            st.metric("Predicted cold-risk probability", f"{prob*100:.0f}%")
            st.progress(min(max(prob, 0.0), 1.0))
            thr = B["models"][0]["metrics"]["threshold"]
            st.caption(f"Flagged cold-risk at threshold {thr}: "
                       + ("🔴 YES" if prob >= thr else "🟢 no"))


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Sensor Health & MNAR  (challenge 2)
# ════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("Estate-wide sensor data-quality monitor")
    miss = pd.DataFrame([{"modality": k2, "missing": v}
                         for k2, v in B["sensor_health"]["missingness_by_modality"].items()])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Missingness by modality**")
        mc = alt.Chart(miss).mark_bar().encode(
            x=alt.X("missing:Q", axis=alt.Axis(format="%"), title="% missing"),
            y=alt.Y("modality:N", sort="-x", title=None),
            color=alt.condition(alt.datum.missing > 0.3, alt.value("#b42318"), alt.value("#1a7f37")),
            tooltip=["modality", alt.Tooltip("missing:Q", format=".1%")],
        ).properties(height=260)
        st.altair_chart(mc, use_container_width=True)
        st.caption("Temperature, humidity, smart-meter and noise are reliable. CO₂ (38%) and the "
                   "resident survey (97%) are Missing **Not** At Random.")
    with c2:
        st.markdown("**Configurable dropout threshold**")
        thr = st.slider("Flag properties with CO₂ dropout ≥", 0.1, 0.95, 0.5, step=0.05)
        drop = pd.DataFrame(B["sensor_health"]["dropout_distribution"])
        n_flag = int((drop["co2_dropout_rate"] >= thr).sum())
        st.metric("Properties flagged for sensor repair", n_flag)
        hist = alt.Chart(drop).mark_bar().encode(
            x=alt.X("co2_dropout_rate:Q", bin=alt.Bin(maxbins=20),
                    title="CO₂ dropout rate per property"),
            y=alt.Y("count()", title="Properties"),
            color=alt.condition(alt.datum.co2_dropout_rate >= thr,
                                alt.value("#b42318"), alt.value("#94a3b8")),
        ).properties(height=220)
        rule = alt.Chart(pd.DataFrame({"t": [thr]})).mark_rule(color="#111", strokeDash=[4, 4]).encode(x="t:Q")
        st.altair_chart(hist + rule, use_container_width=True)

    st.markdown("**Threshold sensitivity (how many properties get flagged)**")
    sweep = pd.DataFrame({"threshold": B["sensor_health"]["thresholds_tested"],
                          "flagged": B["sensor_health"]["flagged_count_at_each_threshold"]})
    sc = alt.Chart(sweep).mark_line(point=True).encode(
        x=alt.X("threshold:Q", title="Dropout threshold"),
        y=alt.Y("flagged:Q", title="Properties flagged"),
        tooltip=["threshold", "flagged"]).properties(height=220)
    st.altair_chart(sc, use_container_width=True)
    st.info("Recommended cut-off **0.5**: 40 properties flagged — the natural break, since the MNAR "
            "cohort sits at 70–95% dropout. Lower (0.3 → 140) creates review fatigue; higher (0.8 → "
            "24) misses borderline-failing sensors.")

    st.markdown("#### MNAR patterns found")
    for p in B["mnar_patterns"]:
        with st.expander(f"🔸 {p['name']}  ·  sensor: {p['sensor']}"):
            st.markdown(f"**Mechanism:** {p['mechanism']}")
            st.json(p["evidence"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Equity & Fairness  (challenge 3)
# ════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Subgroup equity & fairness audit")
    eq = pd.DataFrame(B["subgroup_equity"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Model reliability (AUROC) by property type**")
        ec = alt.Chart(eq).mark_bar().encode(
            x=alt.X("property_type:N", sort=PT_ORDER, title=None),
            y=alt.Y("auroc:Q", scale=alt.Scale(domain=[0.5, 1.0]), title="AUROC"),
            color=alt.condition(alt.datum.auroc < 0.75, alt.value("#b42318"), alt.value("#2563eb")),
            tooltip=["property_type", "auroc", "n_properties", "cold_base_rate"],
        ).properties(height=300)
        st.altair_chart(ec, use_container_width=True)
        st.error("**Key equity finding:** the model is far less reliable for **flats** "
                 f"(AUROC {eq.loc[eq.property_type=='flat','auroc'].iloc[0]:.2f}, n=70) than houses "
                 f"(~0.83). Flats are genuinely warmer (cold rate "
                 f"{B['dataset']['cold_rate_by_type']['flat']*100:.0f}%), so this is partly base-rate, "
                 f"but it means flats should be ranked within type, not on one cross-type list.")
    with c2:
        st.markdown("**Cold base rate by property type**")
        bc = alt.Chart(eq).mark_bar(color="#9a6700").encode(
            x=alt.X("property_type:N", sort=PT_ORDER, title=None),
            y=alt.Y("cold_base_rate:Q", axis=alt.Axis(format="%"), title="Cold-risk base rate"),
            tooltip=["property_type", alt.Tooltip("cold_base_rate:Q", format=".1%")],
        ).properties(height=300)
        st.altair_chart(bc, use_container_width=True)
        st.caption("Flats share walls (thermal mass) and stay ~3°C warmer in winter — exactly the "
                   "housing-domain effect the brief describes.")

    st.markdown("**Fairness disparity — high-risk flag rate by group**")
    fair = pd.DataFrame(B["fairness"]["disparity_findings"])
    st.dataframe(fair, use_container_width=True, hide_index=True)
    st.caption(f"Most affected group (model reliability): **{B['fairness']['most_affected_group']}**. "
               "Flag-rate differences mirror true cold differences — not unfairness. The actionable "
               "risk is reliability, addressed by per-type ranking + CO₂ sensor repair.")

    st.divider()
    e1, e2 = st.columns(2)
    with e1:
        st.markdown("#### 🧠 Explainability — what drives the score")
        ex = pd.DataFrame(B["explainability_model_a"])
        exc = alt.Chart(ex).mark_bar().encode(
            x=alt.X("weight:Q", title="Coefficient (log-odds)"),
            y=alt.Y("feature:N", sort="-x", title=None),
            color=alt.condition(alt.datum.weight > 0, alt.value("#b42318"), alt.value("#1a7f37")),
            tooltip=["feature", "weight", "direction"]).properties(height=260)
        st.altair_chart(exc, use_container_width=True)
    with e2:
        st.markdown("#### 🎚 Decision-threshold sweep")
        sw = pd.DataFrame(B["decision_threshold_sweep"]).melt(
            id_vars="threshold", var_name="metric", value_name="value")
        swc = alt.Chart(sw).mark_line(point=True).encode(
            x=alt.X("threshold:Q"), y=alt.Y("value:Q"),
            color=alt.Color("metric:N", legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["threshold", "metric", "value"]).properties(height=260)
        st.altair_chart(swc, use_container_width=True)
        st.caption("Cold-home false negatives are costly (a household stays cold a whole season), so "
                   "the operating threshold favours sensitivity.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — Evidence Dashboard  (5 views)
# ════════════════════════════════════════════════════════════════════════════
with tabs[3]:
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
        "model": ["Honest (Model A, no lag)", "+ lag_temp (Model C)", "+ lag_temp + row-split"],
        "auroc": [lk["honest_auroc"], lk["honest_auroc"] + lk["lag_inflation_auroc"], lk["row_split_auroc"]],
    })
    lc = alt.Chart(leak_df).mark_bar().encode(
        x=alt.X("auroc:Q", scale=alt.Scale(domain=[0.7, 1.0]), title="AUROC"),
        y=alt.Y("model:N", sort=None, title=None),
        color=alt.value("#7c3aed"), tooltip=["model", "auroc"]).properties(height=180)
    st.altair_chart(lc, use_container_width=True)
    st.markdown(f"Adding `lag_temp` (yesterday's indoor temperature) inflates AUROC by "
                f"**+{lk['lag_inflation_auroc']}** — but it is essentially yesterday's value of the target, "
                f"so the gain is **target leakage, not skill**. We split by **property** "
                f"({lk['split_audit']['n_train_properties']} train / "
                f"{lk['split_audit']['n_test_properties']} test, "
                f"{lk['split_audit']['n_overlap_properties']} overlap) and exclude `lag_temp`.")

    st.markdown("#### 1 · Sensor data quality & 2 · MNAR")
    st.markdown(f"CO₂ adds only **{lk['co2_lift_auroc']:+}** AUROC yet is 38% MNAR-missing — so the "
                "data-gap is an **asset-management** problem (repair sensors), not a ranking-bias problem.")
    st.markdown("#### 3 · Subgroup equity")
    st.dataframe(pd.DataFrame(B["subgroup_equity"]), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — Model Cards & Governance
# ════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Model evidence cards & governance verdicts")
    mt = pd.DataFrame([{
        "Model": m["label"], "Verdict": m["verdict"], "AUROC": m["metrics"]["auroc"],
        "Sensitivity": m["metrics"]["sensitivity"], "PPV": m["metrics"]["ppv"],
        "Brier": m["metrics"]["brier_score"], "Threshold": m["metrics"]["threshold"],
    } for m in B["models"]])
    st.dataframe(mt, use_container_width=True, hide_index=True)

    for m in B["models"]:
        with st.expander(f"{m['label']}  —  verdict: {m['verdict']}"):
            st.markdown(badge(m["verdict"]), unsafe_allow_html=True)
            st.json(m["metrics"])

    st.divider()
    st.markdown("#### Component verdicts")
    cc = st.columns(4)
    for col, (k2, lab) in zip(cc, [("data_quality", "Data quality"),
                                   ("split_integrity", "Split integrity"),
                                   ("equity", "Equity"), ("overall", "OVERALL")]):
        col.markdown(f"**{lab}**<br>{badge(B['component_verdicts'][k2])}", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Deployment questions (from housing_benchmark_card.json)")
    card_path = ROOT / "reference" / "housing_benchmark_card.json"
    if card_path.exists():
        card = json.loads(card_path.read_text(encoding="utf-8"))
        model_pick = st.selectbox("Model", [m["label"] for m in card["models"]])
        cm = next(m for m in card["models"] if m["label"] == model_pick)
        QLABEL = {"q1": "How many cold properties will it miss?",
                  "q2": "When it flags, how often is it right?",
                  "q3": "Is an all-clear safe to skip?",
                  "q4": "How well does it separate cold from warm?",
                  "q5": "Consistent across property types?",
                  "q6": "Effect of CO₂ sensor dropout?",
                  "q7": "Cost of a false negative?",
                  "q8": "Recommend for upgrade allocation?"}
        for q, qa in cm["deployment_questions"].items():
            st.markdown(f"**{QLABEL.get(q, q)}**  \n{qa}")
        st.success(f"**Overall:** {card['overall_verdict']} — {card['overall_notes']}")

    st.caption("Files: reference/omaib_pathway.json · reference/housing_benchmark_card.json — "
               "validated by `python validate_submission.py`.")
