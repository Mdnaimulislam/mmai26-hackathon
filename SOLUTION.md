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

## The model roster (six models, chosen to surface the truth)

We evaluate six models that vary the **algorithm** and the **missing-data strategy**, so the
comparison is real analysis, not a leaderboard. All metrics are 5-fold property-level CV (n=250).

| Model | AUROC | Flat AUROC | Verdict | Role |
|---|---|---|---|---|
| **Random Forest — Sensor-robust (deployed)** | **0.91** | **0.86** | **CONDITIONAL** | The deployed ranking engine. Best accuracy *and* fairest to flats. |
| Logistic — Sensor-robust (baseline) | 0.84 | 0.68 | CONDITIONAL | Interpretable baseline; much weaker for flats — shows why model choice matters. |
| Gradient Boosting — CO₂ native-NaN | 0.92 | 0.87 | CONDITIONAL | Handles CO₂ gaps natively; CO₂ still adds no benefit. |
| Logistic — CO₂ mean-imputed | 0.84 | 0.68 | NOT READY | Naive imputation of a 38%-MNAR channel for no lift. |
| Logistic — CO₂ time-interpolated | 0.84 | 0.68 | NOT READY | Even proper interpolation adds nothing — CO₂ is uninformative. |
| Logistic — Nowcast +`lag_temp` | 0.93 | 0.90 | NOT READY | `lag_temp` ≈ yesterday's target → **leakage**, not skill. |

**Key honest findings:**
- **Model choice fixed the equity gap.** The linear baseline was unreliable for flats (AUROC 0.68);
  the deployed Random Forest lifts flats to **0.86** — the fix was a better model, *not* dropping flats.
- **CO₂'s missingness is a data-integrity issue, not a predictive loss.** Across four strategies
  (drop / mean / per-property interpolation / native-NaN), adding CO₂ lifts AUROC by at most +0.003
  within a fixed model. So repair the 40 broken sensors; don't try to "impute around" them.
- **`lag_temp` is target leakage** (+0.09 within the logistic model); we exclude it, and the deployed
  forest reaches 0.91 honestly without it.

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
| **E. Option-specific** | `option_specific` in the card — `coverage_report` **plus** embedded `threshold_sensitivity_report` (Ch2), `fairness_disparity_summary` (Ch3), and a `missingness_analysis` block = four challenges in one |
| Plain-language summary | `reports/PLAIN_LANGUAGE_SUMMARY.md` |
| Full upgrade ranking | `reports/upgrade_ranking.csv` |

### The website's six tabs
🏠 Upgrade Triage · 📡 Sensor Health & MNAR · ⚖️ Equity & Fairness · 🧩 Missingness Lab ·
🔬 Evidence Dashboard · 📋 Models & Governance. Interactive inputs: **upgrade-budget slider,
CO₂-dropout-threshold slider, decision-threshold sweep, property lookup, a live "what-if"
predictor, and a model-picker dropdown** that compares all six models.

## Overall verdict: **CONDITIONAL**

Deploy the **Random Forest (sensor-robust)** for the winter ranking **if**: (1) rank within property
type (flats are weaker, AUROC 0.86 vs ~0.91); (2) treat the 40 CO₂-dropout properties as a
sensor-repair workstream; (3) re-audit after one heating season. The CO₂ models are rejected (MNAR,
no lift) and the `lag_temp` model is rejected (leakage).

## How we used generative AI

Used to scaffold the pipeline, the evidence views, and the website, and to draft narratives.
Where it fell short: its first instinct was to **engineer the data to make failure modes appear**
(a model bake-off). Human judgement corrected course — we **measured the real relationships**,
found the feared CO₂ bias was weak and the true risk was property-type reliability + `lag_temp`
leakage, and **reported that honestly** rather than telling a tidier-but-false story.
