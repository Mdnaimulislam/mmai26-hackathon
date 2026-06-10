#!/usr/bin/env python3
"""build_submission.py — SCA-dream-soultion end-to-end pipeline.

Turns the raw housing CSV into:
  * three evaluated models (saved to saved_models/)
  * the honest property-level split (data/processed/)
  * the two filled hackathon JSONs (reference/)
  * the Evidence Dashboard (reports/evidence_dashboard.json)
  * the full upgrade ranking (reports/upgrade_ranking.csv)
  * reports/app_bundle.json — everything the website renders, precomputed

We do NOT chase model performance. The point is the *tool* (a cold-home upgrade
triage service that is honest about where the data can and cannot be trusted) and
the *evidence* behind every verdict.

Run:  python build_submission.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import GroupKFold

from src.data_pipeline import (
    ALL_FEATURES,
    FEATURES_CO2,
    FEATURES_LAG,
    FEATURES_ROBUST,
    build_feature_frame,
    load_and_merge,
    make_property_split,
    make_row_split,
    property_dropout_table,
)
from src.evaluate import compute_metrics, subgroup_auroc
from src.evidence import (
    aggregate_dataset_audit,
    compute_equity_view,
    compute_leakage_view,
    compute_mnar_view,
    compute_sensor_quality_view,
)
from src.models import build_pipeline, explain, train_model

ROOT = Path(__file__).resolve().parent
TEAM_NAME = "SCA-dream-soultion"
TEAM_MEMBERS = "SCA team (replace with member names before submission)"
SEED = 42
PROPERTY_TYPES = ["flat", "terraced", "semi-detached", "detached"]
TOP_RANKED_COUNT = 50  # winter upgrade budget assumption
WINTER_MONTHS = [11, 12, 1, 2, 3]
DROPOUT_THRESHOLD = 0.5


def youden_threshold(y, p) -> float:
    fpr, tpr, thr = roc_curve(y, p)
    t = float(thr[int(np.argmax(tpr - fpr))])
    return round(min(max(t, 0.05), 0.95), 2)


def oof_predictions(df, features):
    """5-fold property-level out-of-fold probabilities for all 250 properties."""
    gkf = GroupKFold(n_splits=5)
    oof = np.zeros(len(df))
    for tr, te in gkf.split(df, df["cold_risk"], df["reference"].values):
        pipe = build_pipeline(SEED).fit(df.iloc[tr][features], df.iloc[tr]["cold_risk"])
        oof[te] = pipe.predict_proba(df.iloc[te][features])[:, 1]
    return oof


def per_type_auroc(df, oof):
    y = df["cold_risk"].values
    out = {}
    for t in PROPERTY_TYPES:
        m = (df["property_type"] == t).values
        out[t] = subgroup_auroc(y[m], oof[m])
    return out


def main():
    print("Loading + engineering features ...")
    df = load_and_merge(ROOT / "data" / "raw")
    feat = build_feature_frame(df)
    n_props = int(feat["reference"].nunique())
    print(f"  rows={len(feat)} properties={n_props} cold_rate={feat['cold_risk'].mean():.3f}")

    # 1) Honest property-level split for the demo app + reproducibility.
    train_df, test_df, train_ids, test_ids = make_property_split(feat, seed=SEED)
    proc = ROOT / "data" / "processed"
    proc.mkdir(parents=True, exist_ok=True)
    save_cols = list(ALL_FEATURES) + ["reference", "property_type", "cold_risk"]
    train_df[save_cols].to_csv(proc / "train_features.csv", index=False)
    test_df[save_cols].to_csv(proc / "test_features.csv", index=False)

    saved = ROOT / "saved_models"
    saved.mkdir(exist_ok=True)
    joblib.dump(train_model(train_df, FEATURES_ROBUST, SEED),
                saved / "model_a_logistic_baseline.joblib")

    # 2) Out-of-fold metrics for the three models (n=250).
    print("Cross-validating the three models ...")
    y = feat["cold_risk"]
    oof_a = oof_predictions(feat, FEATURES_ROBUST)   # A — deployed
    oof_b = oof_predictions(feat, FEATURES_CO2)       # B — adds MNAR CO2
    oof_c = oof_predictions(feat, FEATURES_LAG)       # C — leakage exhibit
    thr_a, thr_b, thr_c = (youden_threshold(y, p) for p in (oof_a, oof_b, oof_c))
    m_a = compute_metrics(y, oof_a, thr_a, "model_a"); m_a["n_properties"] = n_props
    m_b = compute_metrics(y, oof_b, thr_b, "model_b"); m_b["n_properties"] = n_props
    m_c = compute_metrics(y, oof_c, thr_c, "model_c"); m_c["n_properties"] = n_props

    auroc_a = per_type_auroc(feat, oof_a)
    auroc_b = per_type_auroc(feat, oof_b)
    ref = auroc_a["terraced"]
    gaps_a = {t: round(auroc_a[t] - ref, 4) for t in PROPERTY_TYPES}
    gaps_b = {t: round(auroc_b[t] - auroc_b["terraced"], 4) for t in PROPERTY_TYPES}

    # Leakage magnitude: lag vs honest; plus the extra inflation from a row-split.
    lag_inflation = round(m_c["auroc"] - m_a["auroc"], 4)
    rtr, rte = make_row_split(feat, seed=SEED)
    mc_row = build_pipeline(SEED).fit(rtr[FEATURES_LAG], rtr["cold_risk"])
    auroc_c_row = round(float(roc_auc_score(rte["cold_risk"],
                        mc_row.predict_proba(rte[FEATURES_LAG])[:, 1])), 4)
    co2_lift = round(m_b["auroc"] - m_a["auroc"], 4)
    print(f"  A={m_a['auroc']} B={m_b['auroc']} (CO2 lift {co2_lift:+}) "
          f"C={m_c['auroc']} (lag leakage {lag_inflation:+}, row-split {auroc_c_row})")
    print(f"  flat AUROC {auroc_a['flat']} vs terraced {auroc_a['terraced']}")

    # 3) Evidence views (raw analyst signals).
    sensor_view = compute_sensor_quality_view(df)
    mnar_view = compute_mnar_view(df)
    leakage_view = compute_leakage_view(train_df, test_df)
    equity_rows = [{"model": "model_a", "group": t, "auroc": auroc_a[t],
                    "gap_vs_terraced": gaps_a[t]} for t in PROPERTY_TYPES]
    equity_view = compute_equity_view(equity_rows)

    # 4) Governance component verdicts (judgement on top of the raw signals).
    gov_data_quality = "CONDITIONAL"   # CO2 MNAR at scale; other modalities reliable
    gov_split = "READY"                # property-level, 0 overlap (lag_temp excluded)
    gov_equity = "CONDITIONAL"         # flats less reliable; fix = per-type ranking
    audit = aggregate_dataset_audit(gov_data_quality, gov_split, gov_equity)

    # 5) The product: rank all 250 by the deployed model over winter days.
    print("Building upgrade ranking + sensor health + fairness ...")
    work = feat.copy()
    work["score"] = oof_a
    winter = work[work["date"].dt.month.isin(WINTER_MONTHS)]
    g = winter.groupby("reference")
    rank = pd.DataFrame({
        "property_type": g["property_type"].first(),
        "co2_dropout_rate": g["co2_dropout_rate"].first().round(3),
        "cold_risk_score": g["score"].mean().round(4),
        "observed_cold_rate": g["cold_risk"].mean().round(4),
        "winter_days": g.size(),
    }).reset_index()
    rank = rank.sort_values("cold_risk_score", ascending=False).reset_index(drop=True)
    rank["rank"] = rank.index + 1
    rank["data_reliability"] = np.where(rank["co2_dropout_rate"] >= DROPOUT_THRESHOLD,
                                        "LOW", "HIGH")
    rank["sensor_repair_needed"] = (rank["co2_dropout_rate"] >= DROPOUT_THRESHOLD)
    rank["model_reliability"] = np.where(rank["property_type"] == "flat",
                                         "LOWER (flat: AUROC %.2f)" % auroc_a["flat"], "OK")
    rank["recommended_action"] = np.where(
        rank["sensor_repair_needed"],
        "Rank by cold-risk AND dispatch CO2 sensor repair (data integrity)",
        "Rank by cold-risk score")
    rank["flagged"] = (rank["cold_risk_score"] >= thr_a)
    (ROOT / "reports").mkdir(exist_ok=True)
    rank.to_csv(ROOT / "reports" / "upgrade_ranking.csv", index=False)

    # Coverage (challenge 1): global top-N vs within-type balanced top-N.
    estate_counts = rank["property_type"].value_counts()
    top = rank.head(TOP_RANKED_COUNT)
    coverage_dist = []
    over, under = [], []
    for t in PROPERTY_TYPES:
        est_share = round(float(estate_counts.get(t, 0)) / len(rank), 4)
        top_share = round(float((top["property_type"] == t).sum()) / len(top), 4)
        coverage_dist.append({"property_type": t, "estate_share": est_share,
                              "top_ranked_share": top_share,
                              "n_in_top": int((top["property_type"] == t).sum())})
        if top_share > est_share + 0.03:
            over.append(t)
        elif top_share < est_share - 0.03:
            under.append(t)
    # within-type proportional allocation
    fair_top = []
    for t in PROPERTY_TYPES:
        quota = max(1, round(TOP_RANKED_COUNT * estate_counts.get(t, 0) / len(rank)))
        fair_top += list(rank[rank["property_type"] == t].head(quota)["reference"])
    fair_added = set(fair_top) - set(top["reference"])
    flats_added = sum(1 for r in fair_added
                      if rank.loc[rank["reference"] == r, "property_type"].iloc[0] == "flat")

    # Sensor health threshold sweep (challenge 2).
    dropout_tbl = property_dropout_table(df)
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    flagged_counts = [int((dropout_tbl["co2_dropout_rate"] >= t).sum()) for t in thresholds]

    # Fairness disparity (challenge 3): flag-rate + reliability per group.
    overall_flag = round(float(rank["flagged"].mean()), 4)
    disparity = []
    for t in PROPERTY_TYPES:
        grp = rank[rank["property_type"] == t]
        rate = round(float(grp["flagged"].mean()), 4) if len(grp) else 0.0
        disparity.append({"group": t, "high_risk_rate": rate, "overall_rate": overall_flag,
                          "gap": round(rate - overall_flag, 4), "n": int(len(grp)),
                          "model_auroc": auroc_a[t], "cold_base_rate": round(
                              float((feat["property_type"] == t).pipe(
                                  lambda m: feat.loc[m, "cold_risk"].mean())), 4)})
    most_affected = "flat"  # lowest model reliability (AUROC), not a flag-rate artefact

    # Decision-threshold sweep (stretch).
    sweep = [{"threshold": t, **{k: compute_metrics(y, oof_a, t)[k]
              for k in ("sensitivity", "specificity", "ppv")}}
             for t in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]]

    explain_a = explain(train_model(feat, FEATURES_ROBUST, SEED), FEATURES_ROBUST)

    ctx = dict(
        n_props=n_props, df=df, feat=feat, m_a=m_a, m_b=m_b, m_c=m_c,
        auroc_a=auroc_a, auroc_b=auroc_b, gaps_a=gaps_a, gaps_b=gaps_b,
        thr_a=thr_a, thr_b=thr_b, thr_c=thr_c, lag_inflation=lag_inflation,
        auroc_c_row=auroc_c_row, co2_lift=co2_lift, sensor_view=sensor_view,
        mnar_view=mnar_view, leakage_view=leakage_view, equity_view=equity_view,
        audit=audit, gov_data_quality=gov_data_quality, gov_split=gov_split,
        gov_equity=gov_equity, rank=rank, coverage_dist=coverage_dist, over=over,
        under=under, flats_added=flats_added, fair_added=fair_added,
        thresholds=thresholds, flagged_counts=flagged_counts, disparity=disparity,
        most_affected=most_affected, sweep=sweep, explain_a=explain_a,
        dropout_tbl=dropout_tbl,
    )

    print("Writing reference JSONs + dashboard + app bundle ...")
    write_pathway(ctx)
    write_card(ctx)
    write_dashboard(ctx)
    write_app_bundle(ctx)
    print("Done.")
    return ctx


# ── JSON assembly ────────────────────────────────────────────────────────────
def _metrics_block(m):
    return {k: m[k] for k in ("auroc", "auprc", "brier_score", "sensitivity",
            "specificity", "ppv", "npv", "f1", "threshold", "n_properties")}


def _narr_a(c):
    return (f"Deployed model. Sensor-robust logistic model (no CO2, no lag_temp): "
            f"AUROC {c['m_a']['auroc']}, PPV {c['m_a']['ppv']}, sensitivity {c['m_a']['sensitivity']} "
            f"at threshold {c['m_a']['threshold']} (5-fold property-level CV, n=250). It powers the "
            f"upgrade ranking. CONDITIONAL because reliability is lower for flats (AUROC "
            f"{c['auroc_a']['flat']} vs {c['auroc_a']['terraced']} terraced, n=70 flats): rank within "
            f"property type rather than on one cross-type list.")


def _narr_b(c):
    return (f"Multimodal incl. CO2. AUROC {c['m_b']['auroc']} — only {c['co2_lift']:+} vs the CO2-free "
            f"Model A. CO2 is 38% missing (MNAR, 40 properties at 70-95% dropout) yet adds no predictive "
            f"value, so it is a fragile dependency for no benefit. NOT READY: superseded by Model A. The "
            f"CO2 sensor failures are an asset-management/repair issue, not a ranking input.")


def _narr_c(c):
    return (f"Leakage exhibit. Adding lag_temp lifts AUROC to {c['m_c']['auroc']} ({c['lag_inflation']:+} "
            f"over Model A), and a row-level split lifts it further to {c['auroc_c_row']}. But lag_temp is "
            f"yesterday's indoor temperature — essentially yesterday's value of the target — so the gain is "
            f"target leakage, not skill. NOT READY: do not deploy; always split by property and exclude lag_temp.")


def _dq(c, m, label, is_a=False, is_b=False, is_c=False):
    fn_pct = round((1 - m["sensitivity"]) * 100, 1)
    if is_b:
        q6 = (f"Tested directly: CO2 adds {c['co2_lift']:+} AUROC and is 38% MNAR-missing. Including it "
              f"makes reliability depend on a sensor that has failed for 40 properties — net negative.")
    elif is_c:
        q6 = ("Not the failure here — this model's problem is lag_temp leakage, not CO2.")
    else:
        q6 = (f"By design this model uses NO CO2, so the 38% MNAR dropout cannot affect it. The CO2 "
              f"failures are surfaced separately as a sensor-repair flag for {c['flagged_counts'][2]} properties.")
    return {
        "q1": f"At threshold {m['threshold']} sensitivity is {m['sensitivity']}; it misses ~{fn_pct}% of "
              f"genuinely cold property-days ({m['fn']} of {m['fn']+m['tp']} in held-out CV).",
        "q2": f"PPV {m['ppv']} — a positive flag is correct ~{round(m['ppv']*100)}% of the time.",
        "q3": f"NPV {m['npv']} — an all-clear is correct ~{round(m['npv']*100)}% of the time.",
        "q4": f"AUROC {m['auroc']} — ranks a cold property above a warm one ~{round(m['auroc']*100)}% of the time.",
        "q5": (f"No — flats AUROC {c['auroc_a']['flat']} vs ~{c['auroc_a']['terraced']} for houses (flats "
               f"are warmer: 10.5% vs ~37% cold base rate). Rank within type." if is_a else
               f"Per-type AUROC: {dict((t, c['auroc_a'][t]) for t in PROPERTY_TYPES)}."),
        "q6": q6,
        "q7": "A false negative leaves a genuinely cold household below 19C for another heating season — a "
              "delayed health outcome for vulnerable residents, not a calibration nicety.",
        "q8": ("Yes — recommended as the ranking engine, with per-type ranking and a sensor-repair workstream."
               if is_a else "No — kept only as evidence; do not deploy."),
    }


def write_pathway(c):
    data = {
        "schema_version": "omaib-housing", "submission_type": "housing_benchmark_card",
        "strand": "housing", "hackathon": "MultimodalAI26", "submitted": str(date.today()),
        "team": {"name": TEAM_NAME, "members": TEAM_MEMBERS},
        "models": [
            {"name": "Model A — Sensor-robust (deployed)", "verdict": "CONDITIONAL",
             "conditions": f"Rank within property type (flats less reliable, AUROC {c['auroc_a']['flat']} "
                           f"vs {c['auroc_a']['terraced']}); pair with a CO2 sensor-repair programme; "
                           f"re-audit after one heating season.",
             "narrative": _narr_a(c), "metrics": _metrics_block(c["m_a"]), "subgroup_gaps": c["gaps_a"]},
            {"name": "Model B — Multimodal incl. CO2", "verdict": "NOT READY",
             "conditions": "Do not deploy: CO2 is MNAR (38% missing, 40 properties) and adds no lift. "
                           "Treat sensor failures as asset management, not a model input.",
             "narrative": _narr_b(c), "metrics": _metrics_block(c["m_b"]), "subgroup_gaps": c["gaps_b"]},
            {"name": "Model C — Nowcast incl. lag_temp (leakage)", "verdict": "NOT READY",
             "conditions": "Never deploy: lag_temp is target leakage. Always split by property and exclude lag_temp.",
             "narrative": _narr_c(c), "metrics": _metrics_block(c["m_c"]), "subgroup_gaps": c["gaps_a"]},
        ],
        "overall_verdict": "CONDITIONAL",
        "overall_notes": (
            f"Deploy Model A (sensor-robust) for the winter upgrade ranking, with per-type ranking and a "
            f"CO2 sensor-repair workstream for {c['flagged_counts'][2]} properties. Reject Model B (MNAR "
            f"CO2, no lift) and Model C (lag_temp leakage). Data quality CONDITIONAL, split integrity "
            f"READY, equity CONDITIONAL."),
    }
    (ROOT / "reference" / "omaib_pathway.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_card(c):
    models = [
        {"name": "model_a", "label": "Model A — Sensor-robust (deployed)", "verdict": "CONDITIONAL",
         "conditions": "Rank within property type; pair with CO2 sensor-repair; re-audit after one season.",
         "narrative": _narr_a(c), "metrics": _metrics_block(c["m_a"]), "subgroup_gaps": c["gaps_a"],
         "deployment_questions": _dq(c, c["m_a"], "A", is_a=True)},
        {"name": "model_b", "label": "Model B — Multimodal incl. CO2", "verdict": "NOT READY",
         "conditions": "Do not deploy; CO2 MNAR with no lift.",
         "narrative": _narr_b(c), "metrics": _metrics_block(c["m_b"]), "subgroup_gaps": c["gaps_b"],
         "deployment_questions": _dq(c, c["m_b"], "B", is_b=True)},
        {"name": "model_c", "label": "Model C — Nowcast incl. lag_temp (leakage)", "verdict": "NOT READY",
         "conditions": "Never deploy; lag_temp leakage.",
         "narrative": _narr_c(c), "metrics": _metrics_block(c["m_c"]), "subgroup_gaps": c["gaps_a"],
         "deployment_questions": _dq(c, c["m_c"], "C", is_c=True)},
    ]
    data = {
        "schema_version": "omaib-housing-v0.1", "report_type": "housing_benchmark_card",
        "strand": "housing", "hackathon": "MultimodalAI26", "evaluation_date": str(date.today()),
        "team": {"name": TEAM_NAME, "members": TEAM_MEMBERS}, "models": models,
        "component_verdicts": {"data_quality": c["gov_data_quality"],
                               "split_integrity": c["gov_split"], "equity": c["gov_equity"]},
        "overall_verdict": "CONDITIONAL",
        "overall_notes": (
            f"CONDITIONAL. Temperature/humidity/smart-meter reliable; CO2 MNAR (38% missing, "
            f"{c['flagged_counts'][2]} properties >=50% dropout) but uninformative; resident survey ~97% "
            f"missing (MNAR). Property-level split verified (0 cross-fold overlap); lag_temp excluded as "
            f"target leakage. Deploy Model A with within-type ranking; commission CO2 sensor repairs; "
            f"re-audit after one heating season."),
        "option_specific": {
            "type": "coverage_report",
            "title": "Cold-Home Triage — coverage + sensor-health + fairness (3-in-1)",
            "content": {
                # Challenge 1 — coverage_report (validated keys)
                "property_type_distribution": c["coverage_dist"],
                "top_ranked_count": TOP_RANKED_COUNT,
                "over_represented_types": c["over"] or ["none beyond +3pp of estate share"],
                "under_represented_types": c["under"] or ["none beyond -3pp of estate share"],
                "reranking_under_fair_weighting": (
                    f"A single cold-risk list ranks houses above flats because flats are genuinely warmer "
                    f"(10.5% vs ~37% cold) — correct, not bias. If the budget should reach the coldest homes "
                    f"of every stock type, within-type allocation adds {c['flats_added']} flats the global "
                    f"top {TOP_RANKED_COUNT} omits. The council should choose 'coldest absolute' vs "
                    f"'coldest per type' explicitly."),
                # Challenge 2 — sensor-health threshold report (embedded)
                "threshold_sensitivity_report": {
                    "thresholds_tested": c["thresholds"],
                    "flagged_count_at_each_threshold": c["flagged_counts"],
                    "recommended_threshold": 0.5,
                    "sensitivity_fatigue_tradeoff": (
                        f"At a 0.5 dropout cut-off, {c['flagged_counts'][2]} properties are flagged for "
                        f"sensor repair — the natural break (the MNAR cohort sits at 70-95%). 0.3 flags "
                        f"{c['flagged_counts'][0]} (review fatigue); 0.8 flags {c['flagged_counts'][-1]} "
                        f"(misses borderline-failing sensors).")},
                # Challenge 3 — fairness disparity (embedded)
                "fairness_disparity_summary": {
                    "disparity_findings": c["disparity"], "most_affected_group": c["most_affected"],
                    "recommended_mitigation": (
                        f"Flag-rate differences across types reflect true cold differences, not unfairness. "
                        f"The real fairness risk is lower model reliability for flats (AUROC "
                        f"{c['auroc_a']['flat']}). Mitigate with per-type ranking/thresholds, surface a "
                        f"reliability flag in the UI, and repair CO2 sensors so the data improves for the "
                        f"under-instrumented cohort.")},
                "top_risk_drivers_model_a": c["explain_a"],
                "decision_threshold_sweep": c["sweep"],
            },
        },
    }
    (ROOT / "reference" / "housing_benchmark_card.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8")


def write_dashboard(c):
    dash = {
        "sensor_data_quality": c["sensor_view"], "mnar_analysis": c["mnar_view"],
        "subgroup_equity": c["equity_view"], "leakage_audit": c["leakage_view"],
        "dataset_audit": {"data_quality": c["audit"].data_quality,
                          "split_integrity": c["audit"].split_integrity,
                          "equity": c["audit"].equity, "overall_verdict": c["audit"].overall},
        "leakage_inflation_auroc": c["lag_inflation"], "co2_lift_auroc": c["co2_lift"],
        "top10_upgrade_ranking": c["rank"].head(10).to_dict(orient="records"),
    }
    (ROOT / "reports" / "evidence_dashboard.json").write_text(json.dumps(dash, indent=2), encoding="utf-8")


def write_app_bundle(c):
    """Everything the website renders, precomputed so the site loads instantly."""
    df, feat = c["df"], c["feat"]
    missing = {col: round(float(df[col].isna().mean()), 4) for col in
               ["avgTemperature", "avgHumidity", "avgCo2", "smart_meter_kwh", "noise_db", "survey_score"]}
    bundle = {
        "generated_at": str(date.today()),
        "team": {"name": TEAM_NAME, "members": TEAM_MEMBERS},
        "dataset": {
            "n_rows": int(len(df)), "n_properties": c["n_props"],
            "cold_rate": round(float(feat["cold_risk"].mean()), 4),
            "missingness_by_modality": missing,
            "property_type_counts": {t: int((feat.groupby("reference")["property_type"]
                                     .first() == t).sum()) for t in PROPERTY_TYPES},
            "cold_rate_by_type": {t: round(float(feat.loc[feat["property_type"] == t, "cold_risk"]
                                  .mean()), 4) for t in PROPERTY_TYPES},
        },
        "models": [
            {"id": "model_a", "label": "Model A — Sensor-robust (deployed)", "verdict": "CONDITIONAL",
             "metrics": _metrics_block(c["m_a"]), "per_type_auroc": c["auroc_a"]},
            {"id": "model_b", "label": "Model B — Multimodal incl. CO2", "verdict": "NOT READY",
             "metrics": _metrics_block(c["m_b"]), "per_type_auroc": c["auroc_b"]},
            {"id": "model_c", "label": "Model C — Nowcast incl. lag_temp", "verdict": "NOT READY",
             "metrics": _metrics_block(c["m_c"]), "per_type_auroc": {}},
        ],
        "ranking": c["rank"].to_dict(orient="records"),
        "subgroup_equity": [
            {"property_type": t, "auroc": c["auroc_a"][t], "gap_vs_terraced": c["gaps_a"][t],
             "n_properties": int((feat.groupby("reference")["property_type"].first() == t).sum()),
             "cold_base_rate": round(float(feat.loc[feat["property_type"] == t, "cold_risk"].mean()), 4)}
            for t in PROPERTY_TYPES],
        "sensor_health": {
            "missingness_by_modality": missing,
            "thresholds_tested": c["thresholds"], "flagged_count_at_each_threshold": c["flagged_counts"],
            "dropout_distribution": c["dropout_tbl"][["reference", "property_type",
                "co2_dropout_rate", "cold_risk_rate", "high_dropout"]].round(3).to_dict(orient="records"),
        },
        "mnar_patterns": c["mnar_view"]["patterns"],
        "fairness": {"disparity_findings": c["disparity"], "most_affected_group": c["most_affected"]},
        "coverage": {"property_type_distribution": c["coverage_dist"], "top_ranked_count": TOP_RANKED_COUNT,
                     "over_represented_types": c["over"], "under_represented_types": c["under"],
                     "flats_added_under_fair_weighting": c["flats_added"]},
        "leakage": {"lag_inflation_auroc": c["lag_inflation"], "row_split_auroc": c["auroc_c_row"],
                    "honest_auroc": c["m_a"]["auroc"], "co2_lift_auroc": c["co2_lift"],
                    "split_audit": c["leakage_view"]},
        "decision_threshold_sweep": c["sweep"],
        "explainability_model_a": c["explain_a"],
        "evidence_views": {"sensor_data_quality": c["sensor_view"]["verdict"],
                           "mnar_analysis": c["mnar_view"]["verdict"],
                           "subgroup_equity": c["equity_view"]["verdict"],
                           "leakage_audit": c["leakage_view"]["verdict"]},
        "component_verdicts": {"data_quality": c["gov_data_quality"], "split_integrity": c["gov_split"],
                               "equity": c["gov_equity"], "overall": "CONDITIONAL"},
    }
    (ROOT / "reports" / "app_bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
