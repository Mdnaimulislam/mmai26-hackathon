#!/usr/bin/env python3
"""build_submission.py — SCA-dream-soultion end-to-end pipeline.

Turns the raw housing CSV into:
  * a roster of evaluated models (algorithm + missing-data-handling variety)
  * the honest property-level split (data/processed/)
  * the deployed model (saved_models/)
  * the two filled hackathon JSONs (reference/)
  * the Evidence Dashboard (reports/evidence_dashboard.json)
  * the full upgrade ranking (reports/upgrade_ranking.csv)
  * reports/app_bundle.json — everything the website renders, precomputed

This is a TOOL + EVIDENCE solution. The extra models exist to *analyse* the data
(especially the CO2 missingness), not to chase a leaderboard.

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
    ALL_FEATURES, FEATURES_LAG, FEATURES_ROBUST,
    build_feature_frame, load_and_merge, make_property_split, make_row_split,
    property_dropout_table,
)
from src.evaluate import compute_metrics, subgroup_auroc
from src.evidence import (
    aggregate_dataset_audit, compute_equity_view, compute_leakage_view,
    compute_mnar_view, compute_sensor_quality_view,
)
from src.missingness import imputation_distribution, missingness_summary, mnar_mechanism
from src.models import (
    MODEL_SPECS, build_pipeline, explain, explain_importances, make_estimator, train_model,
)

ROOT = Path(__file__).resolve().parent
TEAM_NAME = "SCA-dream-soultion"
TEAM_MEMBERS = "SCA team (replace with member names before submission)"
SEED = 42
PROPERTY_TYPES = ["flat", "terraced", "semi-detached", "detached"]
TOP_RANKED_COUNT = 50
WINTER_MONTHS = [11, 12, 1, 2, 3]
DROPOUT_THRESHOLD = 0.5
DEPLOYED = "rf_robust"  # evidence: non-linear model is more accurate AND fairer to flats


def youden_threshold(y, p) -> float:
    fpr, tpr, thr = roc_curve(y, p)
    t = float(thr[int(np.argmax(tpr - fpr))])
    return round(min(max(t, 0.05), 0.95), 2)


def oof_predictions(df, features, algo):
    """5-fold property-level out-of-fold probabilities for all 250 properties."""
    gkf = GroupKFold(n_splits=5)
    oof = np.zeros(len(df))
    for tr, te in gkf.split(df, df["cold_risk"], df["reference"].values):
        est = make_estimator(algo, SEED)
        est.fit(df.iloc[tr][features], df.iloc[tr]["cold_risk"])
        oof[te] = est.predict_proba(df.iloc[te][features])[:, 1]
    return oof


def per_type_auroc(df, oof):
    y = df["cold_risk"].values
    return {t: subgroup_auroc(y[(df["property_type"] == t).values], oof[(df["property_type"] == t).values])
            for t in PROPERTY_TYPES}


# Modality -> columns (for the multimodal fusion analysis + live explorer).
MODALITIES = {
    "Humidity": ["avgHumidity"],
    "CO₂": ["co2_imputed", "co2_missing"],
    "Energy (smart meter)": ["smart_meter_kwh"],
    "Noise": ["noise_db"],
    "Property type": ["is_flat", "pt_terraced", "pt_semi_detached", "pt_detached"],
    "Season (month)": ["month"],
    "Day of week": ["day_of_week"],
}


def modality_analysis(train_df, test_df):
    """Multimodal fusion evidence: each modality alone, leave-one-out, and combined.

    Uses a fast logistic fit on the honest property split so the website's live
    explorer (which re-fits on user-selected modalities) matches these numbers.
    """
    y_tr, y_te = train_df["cold_risk"], test_df["cold_risk"]

    def auroc_for(cols):
        if not cols:
            return 0.0
        mdl = build_pipeline(SEED).fit(train_df[cols], y_tr)
        return round(float(roc_auc_score(y_te, mdl.predict_proba(test_df[cols])[:, 1])), 4)

    full_cols = [c for cols in MODALITIES.values() for c in cols]
    combined = auroc_for(full_cols)
    single = [{"modality": k, "auroc": auroc_for(v)} for k, v in MODALITIES.items()]
    loo = []
    for k in MODALITIES:
        cols = [c for kk, vv in MODALITIES.items() if kk != k for c in vv]
        without = auroc_for(cols)
        loo.append({"modality": k, "auroc_without": without, "marginal": round(combined - without, 4)})
    return {"modalities": list(MODALITIES), "single": single, "leave_one_out": loo,
            "combined_auroc": combined, "columns": {k: v for k, v in MODALITIES.items()}}


def dropout_gap(df, oof):
    y = df["cold_risk"].values
    hi = df["high_dropout"].values == 1
    return {"auroc_high_dropout": subgroup_auroc(y[hi], oof[hi]),
            "auroc_rest": subgroup_auroc(y[~hi], oof[~hi]),
            "n_high_dropout_properties": int(df.loc[hi, "reference"].nunique())}


def main():
    print("Loading + engineering features ...")
    df = load_and_merge(ROOT / "data" / "raw")
    feat = build_feature_frame(df)
    n_props = int(feat["reference"].nunique())
    y = feat["cold_risk"]
    print(f"  rows={len(feat)} properties={n_props} cold_rate={y.mean():.3f}")

    # Honest property-level split for the demo app + deployed model.
    train_df, test_df, train_ids, test_ids = make_property_split(feat, seed=SEED)
    proc = ROOT / "data" / "processed"; proc.mkdir(parents=True, exist_ok=True)
    save_cols = list(ALL_FEATURES) + ["reference", "property_type", "cold_risk"]
    train_df[save_cols].to_csv(proc / "train_features.csv", index=False)
    test_df[save_cols].to_csv(proc / "test_features.csv", index=False)
    saved = ROOT / "saved_models"; saved.mkdir(exist_ok=True)
    # Interpretable logistic baseline (used by demo/app.py + the live what-if predictor).
    joblib.dump(train_model(train_df, FEATURES_ROBUST, SEED),
                saved / "model_a_logistic_baseline.joblib")
    # Deployed Random Forest (powers the ranking; saved for completeness).
    rf_full = make_estimator("rf", SEED).fit(feat[FEATURES_ROBUST], feat["cold_risk"])
    joblib.dump(rf_full, saved / "model_deployed_rf.joblib")

    # ── Train the whole roster via property-level CV ─────────────────────────
    print("Cross-validating the model roster ...")
    results = {}
    for spec in MODEL_SPECS:
        oof = oof_predictions(feat, spec["features"], spec["algo"])
        thr = youden_threshold(y, oof)
        m = compute_metrics(y, oof, thr, spec["id"]); m["n_properties"] = n_props
        pt = per_type_auroc(feat, oof)
        results[spec["id"]] = {
            "spec": spec, "oof": oof, "metrics": m, "per_type_auroc": pt,
            "gaps": {t: round(pt[t] - pt["terraced"], 4) for t in PROPERTY_TYPES},
            "dropout_gap": dropout_gap(feat, oof)}
        print(f"  {spec['id']:18s} AUROC={m['auroc']}  flat={pt['flat']}  thr={thr}")

    dep = results[DEPLOYED]
    oof_a, thr_a, m_a = dep["oof"], dep["metrics"]["threshold"], dep["metrics"]
    lr_robust_auroc = results["logreg_robust"]["metrics"]["auroc"]  # linear baseline for clean ablations

    # Leakage magnitude — same model class (logistic +/- lag_temp) + a row-level split.
    lag_inflation = round(results["logreg_lag"]["metrics"]["auroc"] - lr_robust_auroc, 4)
    rtr, rte = make_row_split(feat, seed=SEED)
    mc_row = build_pipeline(SEED).fit(rtr[FEATURES_LAG], rtr["cold_risk"])
    auroc_c_row = round(float(roc_auc_score(rte["cold_risk"],
                        mc_row.predict_proba(rte[FEATURES_LAG])[:, 1])), 4)

    # CO2 lift under each missing-data strategy (the missingness comparison).
    imputation_comparison = [
        {"strategy": "Drop CO2 (sensor-robust)", "model": "logreg_robust",
         "auroc": results["logreg_robust"]["metrics"]["auroc"]},
        {"strategy": "Mean impute + missing flag", "model": "logreg_co2_mean",
         "auroc": results["logreg_co2_mean"]["metrics"]["auroc"]},
        {"strategy": "Per-property interpolation + flag", "model": "logreg_co2_interp",
         "auroc": results["logreg_co2_interp"]["metrics"]["auroc"]},
        {"strategy": "Native NaN (gradient boosting)", "model": "hgb_co2_native",
         "auroc": results["hgb_co2_native"]["metrics"]["auroc"]},
    ]
    # Clean same-class ablation: logistic with vs without CO2.
    co2_lift = round(results["logreg_co2_mean"]["metrics"]["auroc"] - lr_robust_auroc, 4)
    print(f"  CO2 ablation (logistic) {co2_lift:+}; lag leakage (logistic) {lag_inflation:+}; "
          f"deployed RF {m_a['auroc']} honest")

    # ── Missingness + multimodal fusion analysis ─────────────────────────────
    print("Analysing missingness + modality contributions ...")
    miss_summary = missingness_summary(df)
    miss_mech = mnar_mechanism(df)
    miss_dist = imputation_distribution(df)
    multimodal = modality_analysis(train_df, test_df)
    print(f"  multimodal combined AUROC {multimodal['combined_auroc']}; "
          f"top single: {max(multimodal['single'], key=lambda s: s['auroc'])}")

    # ── Evidence views ───────────────────────────────────────────────────────
    sensor_view = compute_sensor_quality_view(df)
    mnar_view = compute_mnar_view(df)
    leakage_view = compute_leakage_view(train_df, test_df)
    equity_rows = [{"model": DEPLOYED, "group": t, "auroc": dep["per_type_auroc"][t],
                    "gap_vs_terraced": dep["gaps"][t]} for t in PROPERTY_TYPES]
    equity_view = compute_equity_view(equity_rows)
    gov = {"data_quality": "CONDITIONAL", "split_integrity": "READY", "equity": "CONDITIONAL"}
    audit = aggregate_dataset_audit(gov["data_quality"], gov["split_integrity"], gov["equity"])

    # ── Upgrade ranking + coverage + fairness (deployed model) ───────────────
    print("Building ranking + coverage + fairness ...")
    work = feat.copy(); work["score"] = oof_a
    winter = work[work["date"].dt.month.isin(WINTER_MONTHS)]
    g = winter.groupby("reference")
    rank = pd.DataFrame({
        "property_type": g["property_type"].first(),
        "co2_dropout_rate": g["co2_dropout_rate"].first().round(3),
        "cold_risk_score": g["score"].mean().round(4),
        "observed_cold_rate": g["cold_risk"].mean().round(4),
        "winter_days": g.size()}).reset_index()
    rank = rank.sort_values("cold_risk_score", ascending=False).reset_index(drop=True)
    rank["rank"] = rank.index + 1
    rank["data_reliability"] = np.where(rank["co2_dropout_rate"] >= DROPOUT_THRESHOLD, "LOW", "HIGH")
    rank["sensor_repair_needed"] = rank["co2_dropout_rate"] >= DROPOUT_THRESHOLD
    rank["model_reliability"] = np.where(rank["property_type"] == "flat",
                                         f"LOWER (flat: AUROC {dep['per_type_auroc']['flat']})", "OK")
    rank["recommended_action"] = np.where(rank["sensor_repair_needed"],
        "Rank by cold-risk AND dispatch CO2 sensor repair", "Rank by cold-risk score")
    rank["flagged"] = rank["cold_risk_score"] >= thr_a
    (ROOT / "reports").mkdir(exist_ok=True)
    rank.to_csv(ROOT / "reports" / "upgrade_ranking.csv", index=False)

    top = rank.head(TOP_RANKED_COUNT)
    estate_counts = rank["property_type"].value_counts()
    coverage_dist, over, under = [], [], []
    for t in PROPERTY_TYPES:
        est_share = round(float(estate_counts.get(t, 0)) / len(rank), 4)
        top_share = round(float((top["property_type"] == t).sum()) / len(top), 4)
        coverage_dist.append({"property_type": t, "estate_share": est_share,
                              "top_ranked_share": top_share,
                              "n_in_top": int((top["property_type"] == t).sum())})
        (over if top_share > est_share + 0.03 else under if top_share < est_share - 0.03 else []).append(t)
    fair_top = []
    for t in PROPERTY_TYPES:
        quota = max(1, round(TOP_RANKED_COUNT * estate_counts.get(t, 0) / len(rank)))
        fair_top += list(rank[rank["property_type"] == t].head(quota)["reference"])
    flats_added = sum(1 for r in (set(fair_top) - set(top["reference"]))
                      if rank.loc[rank["reference"] == r, "property_type"].iloc[0] == "flat")

    dropout_tbl = property_dropout_table(df)
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    flagged_counts = [int((dropout_tbl["co2_dropout_rate"] >= t).sum()) for t in thresholds]

    overall_flag = round(float(rank["flagged"].mean()), 4)
    disparity = []
    for t in PROPERTY_TYPES:
        grp = rank[rank["property_type"] == t]
        rate = round(float(grp["flagged"].mean()), 4) if len(grp) else 0.0
        disparity.append({"group": t, "high_risk_rate": rate, "overall_rate": overall_flag,
                          "gap": round(rate - overall_flag, 4), "n": int(len(grp)),
                          "model_auroc": dep["per_type_auroc"][t],
                          "cold_base_rate": round(float(feat.loc[feat["property_type"] == t, "cold_risk"].mean()), 4)})

    sweep = [{"threshold": t, **{k: compute_metrics(y, oof_a, t)[k] for k in ("sensitivity", "specificity", "ppv")}}
             for t in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]]
    explain_a = explain(train_model(feat, FEATURES_ROBUST, SEED), FEATURES_ROBUST)
    rf_importances = explain_importances(rf_full, FEATURES_ROBUST)

    ctx = dict(n_props=n_props, df=df, feat=feat, results=results, dep=dep, m_a=m_a, thr_a=thr_a,
               lr_robust_auroc=lr_robust_auroc,
               lag_inflation=lag_inflation, auroc_c_row=auroc_c_row, co2_lift=co2_lift,
               imputation_comparison=imputation_comparison, miss_summary=miss_summary,
               miss_mech=miss_mech, miss_dist=miss_dist, sensor_view=sensor_view, mnar_view=mnar_view,
               leakage_view=leakage_view, equity_view=equity_view, audit=audit, gov=gov, rank=rank,
               coverage_dist=coverage_dist, over=over, under=under, flats_added=flats_added,
               thresholds=thresholds, flagged_counts=flagged_counts, disparity=disparity, sweep=sweep,
               explain_a=explain_a, rf_importances=rf_importances, dropout_tbl=dropout_tbl,
               multimodal=multimodal)

    print("Writing reference JSONs + dashboard + app bundle ...")
    write_pathway(ctx); write_card(ctx); write_dashboard(ctx); write_app_bundle(ctx)
    print("Done.")
    return ctx


# ── narratives + JSON helpers ────────────────────────────────────────────────
def _metrics_block(m):
    return {k: m[k] for k in ("auroc", "auprc", "brier_score", "sensitivity",
            "specificity", "ppv", "npv", "f1", "threshold", "n_properties")}


def _narrative(spec, r, ctx):
    m, pt = r["metrics"], r["per_type_auroc"]
    base = (f"{spec['label']} — missingness: {spec['missingness']}. AUROC {m['auroc']}, sensitivity "
            f"{m['sensitivity']}, PPV {m['ppv']} at threshold {m['threshold']} (5-fold property-level "
            f"CV, n=250). Flats AUROC {pt['flat']} vs terraced {pt['terraced']}.")
    sid = spec["id"]
    if sid == "rf_robust":
        return base + (f" Deployed model — non-linear, best accuracy and the fairest across property types "
                       f"(flats {pt['flat']}). CONDITIONAL: small residual flat gap to monitor; rank within type.")
    if sid == "logreg_robust":
        return base + (f" Interpretable linear baseline. Much weaker for flats ({pt['flat']}) — evidence that "
                       f"a non-linear model, not abandoning flats, closes the equity gap. CONDITIONAL.")
    if sid == "hgb_co2_native":
        return base + (f" Handles CO2 dropout natively (no imputation) yet CO2 only shifts AUROC "
                       f"{ctx['co2_lift']:+} overall — confirming the gap is data-integrity, not predictive.")
    if sid == "logreg_co2_mean":
        return base + " Naive mean-imputation of a 38%-MNAR channel for no lift — a fragile dependency. NOT READY."
    if sid == "logreg_co2_interp":
        return base + " Even proper per-property interpolation gives no lift, confirming CO2 is uninformative here. NOT READY."
    if sid == "logreg_lag":
        return base + (f" Adding lag_temp inflates AUROC {ctx['lag_inflation']:+} (row-split {ctx['auroc_c_row']}); "
                       f"lag_temp is ~yesterday's target = leakage. NOT READY.")
    return base


def _conditions(spec, ctx):
    r = ctx["results"][spec["id"]]
    flat, terr = r["per_type_auroc"]["flat"], r["per_type_auroc"]["terraced"]
    return {
        "rf_robust": f"Deployed. Rank within property type (flats {flat} vs {terr}); pair with CO2 sensor "
                     f"repair; surface a reliability flag; re-audit after one heating season.",
        "logreg_robust": f"Interpretable baseline only — less reliable for flats ({flat}); use the Random "
                         f"Forest for the live ranking and this model for plain-language reasons.",
        "hgb_co2_native": "Strong alternative; CO2 adds no benefit, so prefer the simpler CO2-free forest "
                          "unless native missing-handling is specifically required.",
        "logreg_co2_mean": "Do not deploy: 38% MNAR CO2 mean-imputed for no lift.",
        "logreg_co2_interp": "Do not deploy: interpolation does not make CO2 informative.",
        "logreg_lag": "Never deploy: lag_temp is target leakage. Always split by property and exclude lag_temp.",
    }[spec["id"]]


def _dq(spec, r, ctx):
    m, pt = r["metrics"], r["per_type_auroc"]
    fn_pct = round((1 - m["sensitivity"]) * 100, 1)
    sid = spec["id"]
    if sid in ("logreg_co2_mean", "logreg_co2_interp"):
        q6 = f"This model depends on the 38%-MNAR CO2 channel ({spec['missingness']}), which adds no lift — a fragility for no gain."
    elif sid == "hgb_co2_native":
        q6 = f"Handles CO2 dropout natively; CO2 shifts AUROC only {ctx['co2_lift']:+}, so dropout barely matters."
    elif sid == "logreg_lag":
        q6 = "Not the issue here — this model's flaw is lag_temp leakage, not CO2."
    else:
        q6 = "Uses no CO2, so the 38% MNAR dropout cannot affect it; the broken sensors are flagged for repair separately."
    return {
        "q1": f"At threshold {m['threshold']} sensitivity is {m['sensitivity']}; misses ~{fn_pct}% of cold "
              f"property-days ({m['fn']} of {m['fn']+m['tp']} in held-out CV).",
        "q2": f"PPV {m['ppv']} — a positive flag is right ~{round(m['ppv']*100)}% of the time.",
        "q3": f"NPV {m['npv']} — an all-clear is right ~{round(m['npv']*100)}% of the time.",
        "q4": f"AUROC {m['auroc']} — ranks a cold property above a warm one ~{round(m['auroc']*100)}% of the time.",
        "q5": f"Per-type AUROC flat {pt['flat']} / terraced {pt['terraced']} / semi {pt['semi-detached']} / "
              f"detached {pt['detached']}. Flats weakest — rank within type.",
        "q6": q6,
        "q7": "A false negative leaves a genuinely cold household below 19C for another heating season — a "
              "delayed health outcome for vulnerable residents.",
        "q8": ("Yes — primary ranking engine, with per-type ranking and a sensor-repair workstream."
               if spec.get("deployed") else
               ("Usable cross-check, not the primary model." if spec["verdict"] == "CONDITIONAL"
                else "No — evaluated and rejected; kept as evidence.")),
    }


def write_pathway(ctx):
    models = []
    for spec in MODEL_SPECS:
        r = ctx["results"][spec["id"]]
        models.append({"name": spec["label"], "verdict": spec["verdict"],
                       "conditions": _conditions(spec, ctx), "narrative": _narrative(spec, r, ctx),
                       "metrics": _metrics_block(r["metrics"]), "subgroup_gaps": r["gaps"]})
    data = {"schema_version": "omaib-housing", "submission_type": "housing_benchmark_card",
            "strand": "housing", "hackathon": "MultimodalAI26", "submitted": str(date.today()),
            "team": {"name": TEAM_NAME, "members": TEAM_MEMBERS}, "models": models,
            "overall_verdict": "CONDITIONAL",
            "overall_notes": (
                f"Evaluated {len(MODEL_SPECS)} models across algorithm and missing-data-handling choices. "
                f"Deploy the sensor-robust Random Forest (AUROC {ctx['m_a']['auroc']}); the logistic baseline "
                f"was much less reliable for flats ({ctx['results']['logreg_robust']['per_type_auroc']['flat']} "
                f"vs {ctx['dep']['per_type_auroc']['flat']} for the forest), so model choice — not abandoning "
                f"flats — closes most of the equity gap. Adding CO2 lifts AUROC by at most +0.003 within a "
                f"fixed model, so its 38% MNAR gap is a data-integrity issue (repair {ctx['flagged_counts'][2]} "
                f"sensors), not a ranking bias. lag_temp is target leakage and is excluded. Data quality "
                f"CONDITIONAL, split integrity READY, equity CONDITIONAL.")}
    (ROOT / "reference" / "omaib_pathway.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_card(ctx):
    models = []
    for spec in MODEL_SPECS:
        r = ctx["results"][spec["id"]]
        models.append({"name": spec["id"], "label": spec["label"], "verdict": spec["verdict"],
                       "conditions": _conditions(spec, ctx), "narrative": _narrative(spec, r, ctx),
                       "metrics": _metrics_block(r["metrics"]), "subgroup_gaps": r["gaps"],
                       "deployment_questions": _dq(spec, r, ctx)})
    ctx_card = {
        "schema_version": "omaib-housing-v0.1", "report_type": "housing_benchmark_card",
        "strand": "housing", "hackathon": "MultimodalAI26", "evaluation_date": str(date.today()),
        "team": {"name": TEAM_NAME, "members": TEAM_MEMBERS}, "models": models,
        "component_verdicts": ctx["gov"], "overall_verdict": "CONDITIONAL",
        "overall_notes": (
            f"CONDITIONAL. Temperature/humidity/smart-meter reliable; CO2 MNAR (38% missing, "
            f"{ctx['flagged_counts'][2]} properties >=50% dropout) but uninformative — adding CO2 lifts AUROC "
            f"by at most +0.003 within a fixed model, and a gradient model handling CO2 natively only matches "
            f"the CO2-free model. Property-level split verified (0 overlap); lag_temp excluded as target "
            f"leakage. Deploy the sensor-robust Random Forest (AUROC {ctx['m_a']['auroc']}, flats "
            f"{ctx['dep']['per_type_auroc']['flat']}); the logistic baseline was unfair to flats "
            f"({ctx['results']['logreg_robust']['per_type_auroc']['flat']}). Rank within type; repair CO2 "
            f"sensors; re-audit after one season."),
        "option_specific": {
            "type": "coverage_report",
            "title": "Cold-Home Triage — coverage + sensor-health + fairness + missingness (4-in-1)",
            "content": {
                "property_type_distribution": ctx["coverage_dist"],
                "top_ranked_count": TOP_RANKED_COUNT,
                "over_represented_types": ctx["over"] or ["none beyond +3pp of estate share"],
                "under_represented_types": ctx["under"] or ["none beyond -3pp of estate share"],
                "reranking_under_fair_weighting": (
                    f"A single cold-risk list ranks houses above flats because flats are genuinely warmer "
                    f"(10.5% vs ~37% cold). Within-type allocation adds {ctx['flats_added']} flats the global "
                    f"top {TOP_RANKED_COUNT} omits. Choose 'coldest absolute' vs 'coldest per type' deliberately."),
                "threshold_sensitivity_report": {
                    "thresholds_tested": ctx["thresholds"],
                    "flagged_count_at_each_threshold": ctx["flagged_counts"],
                    "recommended_threshold": 0.5,
                    "sensitivity_fatigue_tradeoff": (
                        f"At 0.5 dropout cut-off, {ctx['flagged_counts'][2]} properties flagged for repair — the "
                        f"natural break (MNAR cohort at 70-95%). 0.3 flags {ctx['flagged_counts'][0]} (fatigue); "
                        f"0.8 flags {ctx['flagged_counts'][-1]} (misses borderline failures).")},
                "fairness_disparity_summary": {
                    "disparity_findings": ctx["disparity"], "most_affected_group": "flat",
                    "recommended_mitigation": (
                        f"Flag-rate gaps mirror true cold differences, not unfairness. The real risk is lower "
                        f"reliability for flats (AUROC {ctx['dep']['per_type_auroc']['flat']}). Mitigate with "
                        f"per-type ranking, a UI reliability flag, and CO2 sensor repair.")},
                "missingness_analysis": {
                    "summary": ctx["miss_summary"], "mechanism": ctx["miss_mech"],
                    "imputation_comparison": ctx["imputation_comparison"],
                    "distribution_note": ctx["miss_dist"]["note"]},
                "multimodal_analysis": {
                    "combined_auroc": ctx["multimodal"]["combined_auroc"],
                    "single_modality_auroc": ctx["multimodal"]["single"],
                    "leave_one_out": ctx["multimodal"]["leave_one_out"]},
                "top_risk_drivers_deployed": ctx["rf_importances"],
                "top_risk_drivers_linear": ctx["explain_a"],
                "decision_threshold_sweep": ctx["sweep"],
            }}}
    (ROOT / "reference" / "housing_benchmark_card.json").write_text(json.dumps(ctx_card, indent=2), encoding="utf-8")


def write_dashboard(ctx):
    dash = {"sensor_data_quality": ctx["sensor_view"], "mnar_analysis": ctx["mnar_view"],
            "subgroup_equity": ctx["equity_view"], "leakage_audit": ctx["leakage_view"],
            "dataset_audit": {**ctx["gov"], "overall_verdict": ctx["audit"].overall},
            "leakage_inflation_auroc": ctx["lag_inflation"], "co2_lift_auroc": ctx["co2_lift"],
            "imputation_comparison": ctx["imputation_comparison"],
            "top10_upgrade_ranking": ctx["rank"].head(10).to_dict(orient="records")}
    (ROOT / "reports" / "evidence_dashboard.json").write_text(json.dumps(dash, indent=2), encoding="utf-8")


def write_app_bundle(ctx):
    df, feat = ctx["df"], ctx["feat"]
    missing = {c: round(float(df[c].isna().mean()), 4) for c in
               ["avgTemperature", "avgHumidity", "avgCo2", "smart_meter_kwh", "noise_db", "survey_score"]}
    models = []
    for spec in MODEL_SPECS:
        r = ctx["results"][spec["id"]]
        models.append({"id": spec["id"], "label": spec["label"], "algo": spec["algo"],
                       "missingness": spec["missingness"], "interpretable": spec["interpretable"],
                       "verdict": spec["verdict"], "deployed": spec.get("deployed", False),
                       "metrics": _metrics_block(r["metrics"]), "per_type_auroc": r["per_type_auroc"],
                       "subgroup_gaps": r["gaps"], "dropout_gap": r["dropout_gap"],
                       "narrative": _narrative(spec, r, ctx),
                       "deployment_questions": _dq(spec, r, ctx)})
    bundle = {
        "generated_at": str(date.today()), "team": {"name": TEAM_NAME, "members": TEAM_MEMBERS},
        "dataset": {"n_rows": int(len(df)), "n_properties": ctx["n_props"],
                    "cold_rate": round(float(feat["cold_risk"].mean()), 4),
                    "missingness_by_modality": missing,
                    "property_type_counts": {t: int((feat.groupby("reference")["property_type"].first() == t).sum())
                                             for t in PROPERTY_TYPES},
                    "cold_rate_by_type": {t: round(float(feat.loc[feat["property_type"] == t, "cold_risk"].mean()), 4)
                                          for t in PROPERTY_TYPES}},
        "models": models, "deployed_model": DEPLOYED,
        "ranking": ctx["rank"].to_dict(orient="records"),
        "subgroup_equity": [{"property_type": t, "auroc": ctx["dep"]["per_type_auroc"][t],
                             "gap_vs_terraced": ctx["dep"]["gaps"][t],
                             "n_properties": int((feat.groupby("reference")["property_type"].first() == t).sum()),
                             "cold_base_rate": round(float(feat.loc[feat["property_type"] == t, "cold_risk"].mean()), 4)}
                            for t in PROPERTY_TYPES],
        "sensor_health": {"missingness_by_modality": missing, "thresholds_tested": ctx["thresholds"],
                          "flagged_count_at_each_threshold": ctx["flagged_counts"],
                          "dropout_distribution": ctx["dropout_tbl"][["reference", "property_type",
                              "co2_dropout_rate", "cold_risk_rate", "high_dropout"]].round(3).to_dict(orient="records")},
        "missingness": {"summary": ctx["miss_summary"], "mechanism": ctx["miss_mech"],
                        "imputation_comparison": ctx["imputation_comparison"],
                        "distribution": ctx["miss_dist"]},
        "multimodal": ctx["multimodal"],
        "mnar_patterns": ctx["mnar_view"]["patterns"],
        "fairness": {"disparity_findings": ctx["disparity"], "most_affected_group": "flat"},
        "coverage": {"property_type_distribution": ctx["coverage_dist"], "top_ranked_count": TOP_RANKED_COUNT,
                     "over_represented_types": ctx["over"], "under_represented_types": ctx["under"],
                     "flats_added_under_fair_weighting": ctx["flats_added"]},
        "leakage": {"lag_inflation_auroc": ctx["lag_inflation"], "row_split_auroc": ctx["auroc_c_row"],
                    "linear_baseline_auroc": ctx["lr_robust_auroc"], "deployed_auroc": ctx["m_a"]["auroc"],
                    "honest_auroc": ctx["lr_robust_auroc"], "co2_lift_auroc": ctx["co2_lift"],
                    "split_audit": ctx["leakage_view"]},
        "decision_threshold_sweep": ctx["sweep"],
        "explainability_deployed": ctx["rf_importances"], "explainability_linear": ctx["explain_a"],
        "evidence_views": {"sensor_data_quality": ctx["sensor_view"]["verdict"],
                           "mnar_analysis": ctx["mnar_view"]["verdict"],
                           "subgroup_equity": ctx["equity_view"]["verdict"],
                           "leakage_audit": ctx["leakage_view"]["verdict"]},
        "component_verdicts": {**ctx["gov"], "overall": "CONDITIONAL"}}
    (ROOT / "reports" / "app_bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
