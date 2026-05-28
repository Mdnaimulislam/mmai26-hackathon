# MultimodalAI'26 Hackathon — Housing Strand Guide — OMAIB

## The Challenge: "Can You Trust a Dataset Used for Housing Decisions?"

---

## 1. The Scenario

A council housing team is trying to decide which of its 250 social housing properties should receive a boiler upgrade this winter. They have two years of daily sensor readings — indoor temperature, humidity, and CO₂ concentration — from a smart sensor network installed across the estate.

The data looks comprehensive. But a data manager notices something: for 40 of the properties, the CO₂ sensor stopped working for weeks at a time. These properties are not a random sample — they tend to be older, in higher-deprivation areas, and more likely to be in genuine need of an upgrade. The model trained on this dataset will be least reliable for the very households it is most important to get right.

Before anyone uses this dataset to make decisions about which households receive a boiler upgrade, someone must answer a hard question: is this data safe to use?

When datasets like this are used without scrutiny, the failures are predictable:

- **Data gap bias** — Properties whose sensors failed most often are systematically under-scored. The households most likely to be cold are the hardest to identify.
- **Leakage failure** — A model trained without careful split design may have seen future information during training. It will appear accurate in testing but fail on new properties.
- **Property-type bias** — A model that cannot distinguish between property types may perform differently across the estate — systematically over- or under-predicting risk for specific property groups and skewing the upgrade ranking.

**Your job today is to find those failures — and make that evidence visible, actionable, and honest.**

---

## 2. Your Role in This Hackathon

Each team builds a solution grounded in the housing dataset and produces a structured set of evidence deliverables that a council, housing association, or social-impact organisation could act on. The problem is defined, the dataset is provided, and the output format is specified — but what you build on top, and how you communicate what you find, is entirely your team's.

### What You Build

**A. The solution** — a runnable tool with a clear intended user and a working demonstration of its core function.

**B. OMAIB Pathway Manifest** — `reference/omaib_pathway.json` — a structured JSON manifest containing per-model verdicts and metrics for all the models you built and evaluated.

**C. Housing Benchmark Card** — `reference/housing_benchmark_card.json` — a structured JSON report containing the full dataset and model assessment: narrative, subgroup analysis, deployment questions, component verdicts, and option-specific evidence.

**D. Evidence Dashboard** — five analytical views populated through your chosen tools and workflows: sensor data quality, MNAR analysis, subgroup equity, leakage audit, and dataset audit.

**E. Option-specific deliverable** — a JSON section (`option_specific`) embedded within item C, with content specific to the challenge idea your team chose.

### What Your Team Does Not Produce

- The dataset — `housing_properties_daily.csv` is provided ready-to-use; do not modify it.
- The JSON schema — output schemas are fixed and will be validated at submission.

The aim is not to produce the most complex solution. The aim is to produce clear, honest, deployable evidence of whether this housing dataset — and the models trained on it — can be trusted to make decisions that affect real households.

---

## 3. Understanding the Dataset and Your Evaluation Task

Before writing any code, understand the data and begin planning the models your team will build. The dataset is provided ready-to-use; everything else — the models, the architectures, the feature choices — is your team's decision.

### (a) What the dataset contains

`housing_properties_daily.csv` contains **250 properties × 731 days = 182,750 rows of daily averages, covering 1 January 2023 to 31 December 2024 (2024 is a leap year: 365 + 366 = 731 days)**. The outcome label is `cold_risk` (1 = mean indoor temperature fell below 19.0°C that day — the WHO minimum indoor temperature for social housing). Approximately **30–34% of property-days are cold-risk positive**.

| Modality | Column(s) | Notes |
|---|---|---|
| Property metadata | `reference`, `Sub-building`, `address`, `postcode`, `property_type` (flat / terraced / semi-detached / detached — 70 / 100 / 55 / 25 properties), `is_flat` | Flats are 2–3°C warmer in winter due to shared walls (thermal mass) |
| Indoor temperature | `avgTemperature` — daily mean indoor temperature (°C) | ~3% missing |
| Indoor humidity | `avgHumidity` — daily mean indoor humidity (%) | ~5% missing |
| CO₂ concentration | `avgCo2` — daily mean CO₂ (ppm) | ~38% missing overall — MNAR: 40 properties have 70–95% dropout due to sensor hardware failure, concentrated in worse-condition properties; some gaps exceed 30 consecutive days |
| Smart meter | `smart_meter_kwh` — daily energy consumption (kWh) | ~2.6% missing (meter communication dropout); increases sharply in winter; correlates inversely with temperature |
| Ambient noise | `noise_db` — daily mean ambient sound level (dB) | ~8% missing; flats typically 5–10 dB louder than detached properties due to shared walls |
| Resident survey | `survey_score` — resident thermal comfort score (1.0–5.0) | ~96–98% missing (sparse: ~1 response per property per month on average); MNAR — cold and higher-deprivation properties respond less often and report lower scores |
| Temporal | `year`, `month`, `day` | Calendar date split across three columns; teams should engineer `lag_temp` and `day_of_week` as needed — `lag_temp` creates property-level data-leakage risk if the dataset is split naively by row |

The full column reference is in Section 12C.

### (b) What your team must build

Each team must design and build at least three AI models to enable a meaningful comparison and evaluation. There is no prescribed architecture — the design choices are yours.

| Design question | Guidance |
|---|---|
| How many models? | At least three — enough to compare modality combinations and find genuine failure modes. Three is a natural number for a structured evaluation. |
| What modalities? | The dataset has eight feature groups: property metadata, indoor temperature, humidity, CO₂ concentration, smart meter energy, ambient noise, resident survey, and temporal features. |
| What architectures? | Choose architectures appropriate to the feature count and the interpretability requirement for housing decisions. |
| How to create useful failure modes? | Think about how different model designs — in terms of feature choice and missing-data handling — will produce different failure profiles worth evaluating and comparing. |
| What to do with missing data? | `co2_ppm` is absent for approximately 38% of property-days (MNAR) — concentrated in properties with sensor hardware failures. How your models handle this pattern is one of the most important design decisions and a key target for evaluation. |

The models you build become the subject of your OMAIB Pathway Manifest and Housing Benchmark Card. Every verdict you assign in those documents refers to a model your team designed, trained, and is prepared to defend.

---

## 4. The Five Deliverables

### A. The Solution

A runnable tool with a clear intended user and a working demonstration of its core function. Your team may choose one of the suggested ideas below, or define your own compelling problem grounded in the housing dataset. Whatever you build, it must be deployable in spirit — a real housing officer or council governance team should be able to picture using it.

**Suggested challenge ideas (or define your own grounded in the dataset):**

- **Cold home intelligence service** — an AI-powered service that ranks properties by cold-risk score for a housing provider's asset management team.
- **Sensor network health and MNAR audit** — an estate-wide sensor health monitor that tracks CO₂ dropout rates per property over time and detects continuous data gaps beyond a configurable threshold, designed for use by a housing data manager.
- **Heating failure prediction and fairness audit** — an AI-powered predictive tool that combines sensor time-series data with property metadata to identify households at imminent risk of heating system failure, with an explainability layer and a fairness check that flags whether high-risk scores are disproportionately concentrated among particular property types.

### B. OMAIB Pathway Manifest (`omaib_pathway.json`)

A structured JSON manifest containing per-model verdicts and metrics for all models your team built and evaluated. Must include: team name and members; evaluation date; per-model verdict (READY / CONDITIONAL / NOT READY), full metrics, conditions, and narrative; and an overall verdict with notes.

The schema is provided — your team fills in the verdict, conditions, narrative, and metric fields before export. A missing verdict or missing `overall_verdict` field causes the file to be rejected at submission.

### C. Housing Benchmark Card (`housing_benchmark_card.json`)

A structured JSON report containing the full dataset and model assessment. Must include: `schema_version`, `report_type`, `strand`, `team`, `evaluation_date`; a `models` array with per-model verdict, test-set metrics, conditions, narrative, and responses to all eight deployment questions; `component_verdicts` for each of data quality, split integrity, and equity; and `overall_verdict` with notes.

JSON is required so the file can be validated against the hackathon's centralised reporting schema and ingested directly into the OMAIB platform. Judges verify during the demo that response fields are not left blank.

The deployment question fields (`q1`–`q8`) and the failure analysis narrative fields have no prescribed answers — your team derives every response from your own evaluation findings. Each response should reference at least one quantified result from the Evidence Dashboard. There are no correct values for these fields: what matters is that your answers are grounded in evidence and specific enough to act on.

### D. Evidence Dashboard

Five analytical views that constitute the evidence behind items B and C. Each view must be completed and its findings must be reflected in the exported JSON:

| View | What to produce | Key output |
|---|---|---|
| Sensor data quality | Missingness rates, dropout patterns, and distributional properties per modality across all 250 properties | Written PASS / CONDITIONAL / FAIL verdict with supporting statistics |
| MNAR analysis | At least two documented patterns of Missing Not At Random data with supporting sensor time-series evidence | Named MNAR patterns with evidence (which properties, which sensor, mechanism) |
| Subgroup equity | Model performance across at least two property-type subgroups (flat vs house, or detached vs other) with equity gaps quantified | Equity gap table showing which property types are underserved |
| Leakage audit | Documented confirmation that a property-level split was used (not row-level) and that no property reference identifier spans more than one fold | Written confirmation: split method, no cross-fold property leakage |
| Dataset audit | A READY / CONDITIONAL / NOT READY verdict for each of the three evaluation questions (data quality, split integrity, equity), aggregated to the overall card verdict | Three component verdicts plus an overall verdict with written justification |

### E. Option-Specific Deliverable

A structured JSON section (`option_specific`) embedded within item C (`housing_benchmark_card.json`). Must include: `type`, `title`, and `content` fields. The content schema is option-specific:

| Option | `type` value | Required `content` fields |
|---|---|---|
| 1. Cold home intelligence service | `coverage_report` | `property_type_distribution` array, `top_ranked_count`, `over_represented_types`, `under_represented_types`, `reranking_under_fair_weighting` |
| 2. Sensor network health and MNAR audit | `threshold_sensitivity_report` | `thresholds_tested` array, `flagged_count_at_each_threshold` array, `recommended_threshold`, `sensitivity_fatigue_tradeoff` |
| 3. Heating failure and fairness audit | `fairness_disparity_summary` | `disparity_findings` array (each with `group`, `high_risk_rate`, `overall_rate`, `gap`), `most_affected_group`, `recommended_mitigation` |

---

## 5. The OMAIB Pathway Manifest — A Governance Decision

The narrative fields in `omaib_pathway.json` are governance decisions, not form-filling. When your team writes READY, CONDITIONAL, or NOT READY for a model, you are asserting that the evidence supports that verdict — and that assertion enters the OMAIB benchmark registry.

Consider carefully what each verdict means:

**READY** — The dataset and model are suitable for use in housing allocation decisions. Good overall metrics alone are insufficient — you must account for subgroup equity, data quality, and the specific households most at risk.

**CONDITIONAL** — Suitable for use under specific stated conditions. Conditions must be concrete and actionable: not "improve the data quality" but a specific scope, affected subgroup, and the corrective step required before re-evaluation.

**NOT READY** — The dataset or model is not suitable given the evidence. You must identify the specific data quality failure or model limitation that makes the verdict necessary.

The `housing_benchmark_card.json` adds a second governance layer: what your team chooses to highlight in the evidence, and what it chooses not to explain, is equally a statement about what constitutes trustworthy housing AI evidence.

---

## 6. The Three Track Roles

Three roles divide the work across deliverables A–E. For a team of four, the fourth member joins whichever role best fits their background — a housing officer, council data manager, or domain specialist typically strengthens the Governance Lead role most.

Roles run in parallel from the start. The critical convergence point is the Evidence Dashboard (D) — the Analyst's findings must be complete before the Governance Lead can write credible verdicts and narratives.

| Role | Primary deliverables |
|---|---|
| **The Builder** | A — solution, E — option-specific JSON |
| **The Evidence Analyst** | D — four evidence views (sensor quality, MNAR, equity, leakage) |
| **The Governance Lead** | B — manifest, C — benchmark card, D — dataset audit |
| Fourth member (optional) | Supports Analyst or Governance Lead |

---

## 7. Key Housing Concepts

| Term | Plain-English definition | In this context |
|---|---|---|
| **AUROC** | Area Under the Receiver Operating Curve (0.5 = chance; 1.0 = perfect). | AUROC 0.85 means the model ranks a cold property above a warm one 85% of the time. |
| **Cold-risk label** | 1 = mean indoor temperature fell below 19.0°C that day. | The WHO minimum for social housing. A false negative means a cold household is not identified for an upgrade. |
| **Sensitivity** | Of all property-days that were genuinely cold, what fraction did the model flag? | Low sensitivity = missed cold properties — the dangerous housing error. |
| **Specificity** | Of all warm property-days, what fraction did the model correctly leave unflagged? | Low specificity = too many false alarms — wastes upgrade budget on warm properties. |
| **PPV** | Of all properties flagged as cold-risk, what fraction actually were cold? | Tells you how much to trust a positive alert in the upgrade ranking. |
| **NPV** | Of all properties cleared by the model, what fraction truly were not cold? | Tells you how safe it is to skip a property based on a negative prediction. |
| **Subgroup equity** | Does the model perform equally across property types (flat, terraced, detached)? | A model accurate on average but over-predicting for flats wastes budget on properties that do not need upgrades, while missing detached houses that do. |
| **MNAR** | Missing Not At Random — data is absent for reasons correlated with the outcome. | CO₂ dropout is concentrated in older, higher-deprivation properties — the very households most likely to need intervention. A model that depends on CO₂ readings will be least reliable for these properties. |
| **Property-level split** | The train/test split is made at the property level, not the row level. | Each property contributes 731 daily rows. A row-level split leaks yesterday's temperature into the test set via the `lag_temp` feature. Always split by property. |
| **Leakage** | The model sees information during training that it would not have at prediction time. | Row-level splitting causes `lag_temp` leakage. A property reference appearing in both train and test folds also constitutes leakage. |
| **Component verdict** | A READY / CONDITIONAL / NOT READY decision for one aspect of the dataset audit. | Three components: data quality, split integrity, and equity. All three feed into `overall_verdict` in `housing_benchmark_card.json`. |

---

## 8. Submission Checklist and Demo

The submission is a 2.5-minute live demo covering the solution and evidence, followed by a 2.5-minute team presentation at the Workshop on 11 June.

### Pre-Submission Checklist

All items must be complete before the demo session begins.

| Item | Owner |
|---|---|
| Solution (A) is runnable from the repository without modification | Builder |
| `omaib_pathway.json` present in `reference/` — all model verdicts and `overall_verdict` populated, no empty metrics blocks | Governance Lead |
| `housing_benchmark_card.json` present in `reference/` — all narrative, condition, deployment-question, and component-verdict fields completed (none left blank) | Governance Lead |
| All five Evidence Dashboard views completed and findings reflected in the JSON exports | Evidence Analyst |
| `option_specific` section completed within `housing_benchmark_card.json` | Builder |
| Team name in JSON files matches the GitHub branch name | All |
| PR open against the `housing` branch on GitHub | All |

### Final Presentation

Each team gives a 2.5-minute presentation to the group. Cover:

- **What you built** — show the solution and explain the concept and intended user.
- **Why it is designed this way** — explain your design choices and what makes your approach distinctive.
- **What the data showed** — present the most important data quality and model metric findings with sample sizes.
- **Your most important subgroup or MNAR finding** — name the property group or sensor gap, give the magnitude, explain the mechanism and the consequence for real households.
- **Your overall verdict** — explain READY / CONDITIONAL / NOT READY for each model and any conditions attached.
- **How you used generative AI** — where it helped, where it fell short, and what human judgement your team provided.

The strongest presentations will not simply show that something works. They will explain why the team made specific evidence-based choices and what a housing provider or council should do next.

### Submitting Your Work

Submission is via a **Pull Request** from your team branch to the `housing` strand branch.

```bash
git add .
git commit -m "Team <your-team-name>: final housing strand submission"
git push origin your-team-name
```

Then open a PR on GitHub: `your-team-name → housing`
Title: `"Team <your-team-name> — Housing Strand Submission"`

> **The PR must be open by 18:00 on 10 June.** Do not push directly to the `housing` branch — all team work goes on your named team branch.

---

## 9. What Does a Strong Submission Look Like?

The difference between a weak and a strong submission is specificity, honesty, and actionability. A strong team does not just report numbers — it explains what those numbers mean for a housing officer deciding which 50 properties get boiler upgrades this winter.

**Weak subgroup finding:**
> "One of our models performs worse on flats."

**Strong subgroup finding:**
> "[Model name] sensitivity for flats is [X] vs [Y] for [reference property type] (n = [N] flats, n = [N] [reference type] in the test set). The false negatives in this group share a common pattern: [mechanism]. This is consistent with [property characteristic — e.g., thermal mass, wall-sharing]. We recommend [Model name] is not used to rank properties for upgrade across property types without a [specific correction or safeguard]."

**Weak governance verdict:**
> "One of our models should not be used for some properties."

**Strong governance verdict:**
> "[Model name] is NOT READY for the [N] high-dropout properties. CO₂ was absent more than [X]% of the time for these properties — concentrated in [older/higher-deprivation] stock. [Model name] AUROC falls from [Y] overall to [Z] for these properties. This is not random — [mechanism: the sensor fails for reasons correlated with housing condition]. We recommend: (1) [specific intervention]; (2) a re-evaluation is conducted after one heating season of repairs to confirm [condition]."

**Weak data quality verdict:**
> "The dataset has some quality issues but can probably be used."

**Strong data quality verdict:**
> "Data quality: CONDITIONAL — temperature and humidity are reliable ([X]% and [Y]% missingness respectively), but CO₂ is MNAR at scale ([Z]% overall, concentrated in [N] high-dropout properties). Split integrity: READY — we confirmed a property-level stratified split with no cross-fold leakage. Equity: CONDITIONAL — [Model name] systematically disadvantages [property type]; [Model name] is unreliable for the [N] highest-deprivation properties (CO₂ absent >[X]% of days). Overall verdict: CONDITIONAL. The dataset can support housing decisions only if [Model name] is not used for high-dropout properties and [Model name] is not used for cross-property-type comparisons without correction."

Judges will ask questions during the demo. Vague findings cannot be defended. Named findings with sample sizes, mechanisms, and specific recommendations always can.

All findings — subgroup gaps, failure mode narratives, deployment conditions, and verdicts — must be recorded in `housing_benchmark_card.json`. The narrative and deployment-question fields in that file are the primary evidence record that judges review.

---

## 10. Your First 30 Minutes

### All roles — first 10 minutes (everyone, together)

- Read this guide in full and agree on which challenge idea to pursue.
- Open `housing_properties_daily.csv` — confirm approximately 182,750 rows, check the cold-risk rate (~30–34%), count NaN values in `co2_ppm` (~38%).
- Compute per-property CO₂ dropout rates — identify which properties have the highest missingness and note whether they cluster by property type or postcode.
- Look at the property type distribution and consider how this affects subgroup sample sizes and what a meaningful train/test split looks like.
- Decide what models your team will build — agree on at least three. Sketch which features each model will use and how missing `co2_ppm` values will be handled in each.
- Assign roles: Builder, Evidence Analyst, Governance Lead (and fourth member if present).

### Minutes 10–25 — parallel work

| Role | Task | Goal by minute 25 |
|---|---|---|
| **Builder** | Sketch the architecture of the chosen solution. Set up the repository structure and begin implementing the core user-facing component. | A running stub of the solution — even a placeholder UI or CLI is enough to start iterating. |
| **Evidence Analyst** | Load `housing_properties_daily.csv`. Compute missingness rates per modality. Identify the high-dropout properties and check whether they cluster by property type or postcode. Begin designing the first model and the train/test split. | Sensor quality summary table complete; first MNAR pattern identified and named; split methodology confirmed as property-level. |
| **Governance Lead** | Open the JSON schema reference (Section 12). Draft the three evaluation questions for the dataset audit view. Frame the component verdicts: what evidence would make each one READY vs CONDITIONAL vs NOT READY? Begin sketching what deployment question answers will look like once the Analyst has findings. | Component verdict criteria drafted; deployment question framework ready. |

### Minutes 25–30 — quick team sync

- Evidence Analyst shares the first MNAR finding — does the Governance Lead agree it is a CONDITIONAL or NOT READY data quality signal?
- Governance Lead confirms the component verdict framework is consistent with what the Analyst is finding.
- Builder reports on solution progress — any blockers that need the team's help?
- All agree on the most important failure mode to investigate in Phase 2.

The implementation phase is done when all five Evidence Dashboard views are complete and both JSON files are exported. Only then does demo preparation begin.

---

## 11. Judging Criteria

All strands are judged on four criteria. Judges will ask questions during the demo — your team must understand what you built and why you made the decisions you made.

| Criterion | Weight | Weak | Strong |
|---|---|---|---|
| **Creativity** | 15% | Predictable framing; solution does what was expected with no distinctive angle | Original approach with a clear point of view; the solution and evidence framing say something distinctive about the team's perspective and the housing problem |
| **Evidence quality** | 35% | Metric reported without sample size or without identifying the MNAR mechanism | Metric with property count, dropout rate, mechanism explained, and comparison to what a property-type-aware or sensor-reliable baseline would achieve |
| **Clarity** | 25% | Finding interpretable only by a data scientist | Finding interpretable by a housing officer, council committee member, or tenant — naming is specific, consequences stated in plain English for real households |
| **Deployability** | 25% | Recommendation is "improve the data" without specifics | Recommendation states the exact scope, affected property types, required sensor replacement or imputation validation, and what a re-audit after one heating season should check |

**Top submissions will:**
- Identify at least one MNAR pattern that is policy-relevant — not just statistically significant
- Offer an overall dataset verdict a real housing governance board could act on
- Present findings that would not be obvious from summary statistics alone
- Show genuine creativity in how they framed the problem or communicated the evidence

The goal is not to find the "best" model. The goal is to tell the truth about each model you built and the dataset it was trained on — and to do it in a way that is useful to someone who has to decide which households get a boiler upgrade.

---

## 12. Housing Strand Reference

Keep this section open during the build. Field names and validation rules match the submission schema exactly.

### 12A. `omaib_pathway.json` — Field Reference

All fields are required. A single missing or empty field causes the manifest to be rejected at submission.

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Always `"omaib-housing"` |
| `submission_type` | string | Always `"housing_benchmark_card"` |
| `strand` | string | Always `"housing"` |
| `hackathon` | string | Always `"MultimodalAI26"` |
| `submitted` | string (ISO date) | Date of export |
| `team.name` | string | Your team name — must match your GitHub branch name |
| `team.members` | string | Comma-separated list of team member names |
| `models[].name` | string | A descriptive name your team assigns (e.g. "Multimodal LightGBM", "Temporal LR", "CO₂-aware model"). Must be unique within the submission. |
| `models[].verdict` | string | `READY`, `CONDITIONAL`, or `NOT READY` |
| `models[].conditions` | string | Deployment conditions — required if verdict is `CONDITIONAL` or `NOT READY` |
| `models[].narrative` | string | Assessment narrative — must reference at least one quantified finding |
| `models[].metrics.auroc` | float | Area Under ROC curve |
| `models[].metrics.auprc` | float | Area Under Precision-Recall curve |
| `models[].metrics.brier_score` | float | Mean squared probability error (lower is better) |
| `models[].metrics.sensitivity` | float | Recall at the chosen threshold |
| `models[].metrics.specificity` | float | True negative rate at the chosen threshold |
| `models[].metrics.ppv` | float | Positive Predictive Value (Precision) |
| `models[].metrics.npv` | float | Negative Predictive Value |
| `models[].metrics.f1` | float | F1 score at the chosen threshold |
| `models[].metrics.threshold` | float | Decision threshold used |
| `models[].metrics.n_properties` | int | Total properties in the test set |
| `models[].subgroup_gaps` | object | Per property-type AUROC gap relative to the reference group. Keys must match subgroups reported in the Evidence Dashboard. |
| `overall_verdict` | string | `READY`, `CONDITIONAL`, or `NOT READY` — aggregated across all models and components |
| `overall_notes` | string | Team's overall assessment notes |

### 12B. `housing_benchmark_card.json` — Field Reference

All fields required. The `models` array must contain entries for all models your team built and evaluated — at minimum three.

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | `"omaib-housing-v0.1"` |
| `report_type` | string | `"housing_benchmark_card"` |
| `strand` / `hackathon` / `team` / `evaluation_date` | various | Same as `omaib_pathway.json` |
| `models[].verdict` / `metrics` / `conditions` / `narrative` / `subgroup_gaps` | various | Same as `omaib_pathway.json` — replicated here for the full report context |
| `models[].deployment_questions.q1` | string | How many cold properties will this model miss? |
| `models[].deployment_questions.q2` | string | When the model flags a property, how often is it actually cold? |
| `models[].deployment_questions.q3` | string | When the model gives the all-clear, is it safe to skip the property? |
| `models[].deployment_questions.q4` | string | How well does the model separate cold from warm properties? |
| `models[].deployment_questions.q5` | string | Is model performance consistent across property types? |
| `models[].deployment_questions.q6` | string | How does CO₂ sensor dropout affect model reliability for affected properties? |
| `models[].deployment_questions.q7` | string | What is the consequence of a false negative in this housing context? |
| `models[].deployment_questions.q8` | string | Would you recommend this model for use in the upgrade allocation process? |
| `component_verdicts.data_quality` | string | `READY`, `CONDITIONAL`, or `NOT READY` |
| `component_verdicts.split_integrity` | string | `READY`, `CONDITIONAL`, or `NOT READY` |
| `component_verdicts.equity` | string | `READY`, `CONDITIONAL`, or `NOT READY` |
| `overall_verdict` | string | Aggregated overall verdict — required |
| `overall_notes` | string | Summary team assessment |
| `option_specific.type` | string | `coverage_report`, `threshold_sensitivity_report`, or `fairness_disparity_summary` |
| `option_specific.title` | string | Short title for the option-specific section |
| `option_specific.content` | object | Type-specific content fields (see Section 4E) |

### 12C. `housing_properties_daily.csv` — Dataset Column Reference

Provided ready-to-use. Do not modify the file.

| Column | Type | Description |
|---|---|---|
| `reference` | str | Property identifier — structured (`U` + 6–9 digits) or free-text address shorthand |
| `Sub-building` | str | Flat label (e.g. `Flat 1A`) — blank string for non-flat properties |
| `address` | str | Street address in varied formats |
| `postcode` | str | `ZZ`-prefix fictional postcode sector |
| `property_type` | str | `flat`, `terraced`, `semi-detached`, or `detached` |
| `is_flat` | int | 1 if `property_type` is `flat`, else 0 |
| `year` | int | Year (2023 or 2024) |
| `month` | int | Calendar month (1–12) |
| `day` | int | Day of month |
| `avgTemperature` | float | Daily mean indoor temperature (°C) — ~3% missing |
| `avgHumidity` | float | Daily mean indoor humidity (%) — ~5% missing |
| `avgCo2` | float | Daily mean CO₂ concentration (ppm) — ~38% missing (MNAR) |
| `smart_meter_kwh` | float | Daily energy consumption (kWh) — ~2.6% missing |
| `noise_db` | float | Daily mean ambient sound level (dB) — ~8% missing |
| `survey_score` | float | Resident thermal comfort score (1.0–5.0 in 0.5 steps) — ~96–98% missing (MNAR) |

**Features your team must engineer before modelling** — these are not in the raw file:

| Feature to create | How |
|---|---|
| `cold_risk` | `(df['avgTemperature'] < 19.0).astype(int)` — the prediction target |
| `lag_temp` | Previous-day `avgTemperature` per property — NaN on day 1; creates leakage risk if split by row |
| `co2_missing` | `df['avgCo2'].isna().astype(int)` — MNAR indicator |
| `co2_imputed` | `df['avgCo2'].fillna(df['avgCo2'].mean())` — mean imputation baseline |
| `day_of_week` | `pd.to_datetime(df[['year','month','day']]).dt.dayofweek` |

```python
# Verify dataset on load
import pandas as pd
df = pd.read_csv('data/raw/housing_properties_daily.csv')
print(df.shape)                               # expect (182750, 15)
print(df['property_type'].value_counts())     # flat 70, terraced 100, semi-detached 55, detached 25

# Create cold_risk label (not pre-computed in raw file)
df['cold_risk'] = (df['avgTemperature'] < 19.0).astype(int)
print(df['cold_risk'].mean())                 # expect ~0.30–0.34

print(df['avgCo2'].isna().mean())             # expect ~0.38  (MNAR)
print(df['smart_meter_kwh'].isna().mean())    # expect ~0.026
print(df['survey_score'].notna().mean())      # expect ~0.02–0.04 (sparse MNAR)
print(df['noise_db'].isna().mean())           # expect ~0.08

# After splitting by reference, confirm no property appears in both folds
train = df[df['reference'].isin(train_ids)]
test  = df[df['reference'].isin(test_ids)]
overlap = set(train['reference']) & set(test['reference'])
print('Leakage check:', len(overlap), 'overlapping properties')  # expect 0

# Check CO₂ dropout per property
dropout = df.groupby('reference')['avgCo2'].apply(lambda x: x.isna().mean())
print('High-dropout properties (>50%):', dropout.gt(0.5).sum())  # expect ~40
```

---

## 13. Key Housing Facts

- **The 19°C threshold** — The World Health Organisation recommends a minimum indoor temperature of 19°C for social housing. Below this, the risk of respiratory illness, cardiovascular events, and hypothermia rises significantly for vulnerable residents. A cold-risk model that misses a genuinely cold property is not a statistical error — it is a household that does not receive an intervention it needed.

- **Thermal mass and flats** — Flats share walls, floors, and ceilings with neighbouring dwellings, which affects how they exchange and retain heat compared with detached or semi-detached houses in the same postcode. Property type is a candidate feature for your model. Whether the effect is large enough to matter — and in which direction it influences predictions — is for your team to establish from the data.

- **Why CO₂ sensors fail** — Sensor hardware degrades and goes offline, but not uniformly. If sensor failure is correlated with property characteristics that also affect cold risk, then missingness is not random with respect to the outcome — this is Missing Not At Random (MNAR). When MNAR is present, models trained on the observed data will be least reliable for exactly the households the data fails to capture. Your MNAR analysis is to determine whether this applies here, which sensors are affected, and what it means for model reliability.

- **What a false negative costs** — In a cold-home ranking system, a false negative means a cold property is not flagged for a boiler upgrade. In the context of a fixed upgrade budget, that household does not receive the intervention and remains at risk for another heating season. For elderly or medically vulnerable residents, this is not a minor model calibration error — it is a delayed health outcome.

---

*Questions? Speak to a technical mentor or a domain mentor. Each team has access to both throughout the event.*
