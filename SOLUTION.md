# SCA-dream-soultion — Cold-Home Triage & Dataset Trust Auditor

**MultimodalAI'26 · Housing Strand · "Can you trust a dataset used for housing decisions?"**

This is a **tool + evidence** solution, not a modelling contest. It fuses all three suggested
challenges into one product and produces every required deliverable.

---

## TL;DR — how to run

```bash
pip install -r requirements.txt          # pandas, scikit-learn, streamlit, joblib, ...
python build_submission.py               # trains models, fills JSONs, writes the website bundle
streamlit run app.py                      # the interactive website (inputs -> outputs + charts)
python validate_submission.py            # confirms the two JSONs pass (currently: PASS, 0 warnings)
```

`notebooks/data_exploration_training.ipynb` runs the same flow top-to-bottom.
`python demo/app.py` runs the original starter pipeline (now wired to `src/`).

---

## The idea

One web tool with a clear user (a council asset-management / housing officer) that:

1. **Ranks** all 250 properties for a boiler upgrade (Challenge 1 — Cold Home Intelligence).
2. **Audits** the sensor data quality and flags CO₂ dropout (Challenge 2 — Sensor Health & MNAR).
3. **Proves fairness** across property types with an explainability layer (Challenge 3 — Fairness).

…and is **honest about where the data cannot support a confident decision** — that honesty is the
point of the whole strand.

## The three models (chosen to surface the truth, not to win)

| Model | Features | Verdict | Why |
|---|---|---|---|
| **A — Sensor-robust (deployed)** | humidity, energy, noise, season, property type | **CONDITIONAL** | The honest, deployable ranking engine. AUROC ≈ 0.84. CONDITIONAL because it is less reliable for flats. |
| **B — Multimodal incl. CO₂** | A + CO₂ (imputed + missingness flag) | **NOT READY** | CO₂ is 38% MNAR-missing yet adds only **+0.0015** AUROC. A fragile dependency for no benefit. |
| **C — Nowcast incl. `lag_temp`** | A + yesterday's indoor temperature | **NOT READY** | `lag_temp` inflates AUROC to 0.93 (**+0.09**) but it is ~yesterday's value of the target — **target leakage**, not skill. |

**Key honest findings (we did not chase a better model):**
- The feared CO₂/MNAR *bias* is weak in this data (CO₂ adds ~0 predictive value) — so the 40 broken
  sensors are an **asset-management** problem, not a ranking-bias problem. We say so plainly.
- The real equity issue is **property type**: flat AUROC **0.68** vs ~**0.83** for houses (flats are
  genuinely warmer — 10.5% vs ~37% cold base rate). Fix: rank within type.
- `lag_temp` is **target leakage**; we exclude it and report the honest 0.84.

## Architecture

```
src/
  data_pipeline.py   load_and_merge, feature engineering, PROPERTY-level split (no leakage)
  evaluate.py        compute_metrics (auroc/auprc/brier/sens/spec/ppv/npv/f1 + counts)
  evidence.py        the 5 Evidence Dashboard views + dataset-audit aggregator
  models.py          model factory (interpretable logistic) + explainability + triage router
build_submission.py  orchestrator: trains A/B/C with 5-fold property-level CV, computes evidence,
                     fills both reference JSONs, writes reports/app_bundle.json
app.py               the website (Streamlit + Altair) — reads the bundle, never retrains in-browser
notebooks/data_exploration_training.ipynb   runnable exploration + training flow
```

## Where the deliverables live

| Deliverable | File |
|---|---|
| **A. Runnable solution** | `app.py` (website) + `src/` + `build_submission.py` |
| **B. OMAIB Pathway Manifest** | `reference/omaib_pathway.json` (3 models, verdicts, metrics) |
| **C. Housing Benchmark Card** | `reference/housing_benchmark_card.json` (q1–q8, component verdicts, `option_specific`) |
| **D. Evidence Dashboard** (5 views) | `reports/evidence_dashboard.json` + the website's "Evidence Dashboard" tab |
| **E. Option-specific** | `option_specific` in the card — `coverage_report` **plus** embedded `threshold_sensitivity_report` (Ch2) and `fairness_disparity_summary` (Ch3) = all three challenges in one |
| Plain-language summary | `reports/PLAIN_LANGUAGE_SUMMARY.md` |
| Full upgrade ranking | `reports/upgrade_ranking.csv` |

### The website's five tabs map to the five Evidence Dashboard views
🏠 Upgrade Triage · 📡 Sensor Health & MNAR · ⚖️ Equity & Fairness · 🔬 Evidence Dashboard ·
📋 Model Cards & Governance. Interactive inputs: **upgrade-budget slider, CO₂-dropout-threshold
slider, decision-threshold sweep, property lookup, and a live "what-if" predictor.**

## Overall verdict: **CONDITIONAL**

Deploy **Model A** for the winter ranking **if**: (1) rank within property type; (2) treat the 40
CO₂-dropout properties as a sensor-repair workstream; (3) re-audit after one heating season.
Reject Model B (MNAR, no lift) and Model C (leakage).

## How we used generative AI

Used to scaffold the pipeline, the evidence views, and the website, and to draft narratives.
Where it fell short: its first instinct was to **engineer the data to make failure modes appear**
(a model bake-off). Human judgement corrected course — we **measured the real relationships**,
found the feared CO₂ bias was weak and the true risk was property-type reliability + `lag_temp`
leakage, and **reported that honestly** rather than telling a tidier-but-false story.
