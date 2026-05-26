# MultimodalAI'26 Hackathon — Clinical Strand Guide — OMAIB

## The Challenge: "Can You Trust an AI in the ICU?"

---

## 1. The Scenario

It is 3 a.m. on an intensive care unit. A nurse is managing eight patients simultaneously. A patient in bed 6 has been stable for hours — but in the next six hours, they will deteriorate sharply. Their heart rate is slightly elevated. Their lactate is creeping up. A brief note from the evening team mentioned "looks a bit off." None of these signals, alone, would trigger an alarm.

An AI system reviews all 2,000 patients and flags the ones it predicts will deteriorate in the next 24 hours. The nurse sees the alert and acts. Or the AI misses the patient entirely, and the nurse doesn't know to look twice.

**This is not hypothetical.** Early warning AI systems are being deployed in ICUs across the UK, US, and Europe right now. The question is not whether they will be used — it is whether the teams deploying them have genuinely evaluated whether they are safe.

When these models fail, the costs are asymmetric:

- A **false negative** (missed deterioration) means a patient who could have been saved is not treated in time. In an ICU, hours matter. Mortality rises sharply with delayed intervention.
- A **false positive** (unnecessary alert) means nurses respond to phantom alarms, eroding trust in the system and eventually causing real alerts to be ignored.
- A **subgroup failure** means a model that works well on average but fails on a specific patient group — those patients bear the risk silently, invisible in aggregate statistics.

Your job today is to find those failures — and make that evidence visible, actionable, and honest.

---

## 2. Your Role in This Hackathon

Each team builds a solution grounded in the clinical dataset and produces a structured set of evidence deliverables that a clinical governance board could act on. The problem is defined, the dataset is provided, and the output format is specified — but what you build on top, and how you communicate what you find, is entirely your team's.

### What You Build

**A. The solution** — a runnable tool with a clear intended user and a working demonstration of its core function. Your team may choose one of the suggested challenge ideas or define your own compelling problem grounded in the dataset.

**B. OMAIB Pathway Manifest** — `omaib_pathway.json` — a structured JSON manifest containing per-model verdicts and metrics for all three ICU models.

**C. Model Safety Report** — `model_safety_report.json` — a structured JSON report containing the full safety assessment: narrative, subgroup analysis, deployment questions, and option-specific evidence.

**D. Evidence Dashboard** — five analytical views populated through your chosen tools and workflows: model performance, subgroup equity, explainability, failure mode catalogue, and clinical deployment assessment.

**E. Option-specific deliverable** — a JSON section (`option_specific`) embedded within item C, with content specific to the challenge idea your team chose.

### What Your Team Does Not Produce

- The dataset — `icu_patients.csv` is provided ready-to-use; do not modify it.
- The JSON schema — output schemas are fixed and will be validated at submission.

The aim is not to produce the most complex solution. The aim is to produce clear, honest, deployable evidence that the AI models your team builds and evaluates are safe for clinical use.

---

## 3. Understanding the Dataset and Your Models

Before writing any code, understand the dataset and decide what AI models your team will build. The dataset is provided ready-to-use; everything else — the models, the architectures, the modality choices — is your team's decision.

### (a) What the dataset contains

`icu_patients.csv` contains **2,000 synthetic post-surgical ICU patients, one row per patient, 182 columns**. The primary outcome label is `deteriorated_24h` (1 = patient deteriorated within 24 hours of ICU admission). Approximately **42% of patients deteriorated**. A secondary outcome `major_complication_30d` (~28%) is also present.

| Modality | Key features | Notes |
|---|---|---|
| Demographics & surgical context | Age, sex, surgery type (cardiac / vascular / abdominal / orthopaedic), admission urgency, ASA class, operation duration | |
| Comorbidities | Diabetes, hypertension | |
| Intra-operative | Blood loss (mL), transfusion | Blood loss is MNAR (~36% missing) |
| Pre-operative labs | Creatinine, WBC, lactate | |
| ICU admission severity | SOFA score (0–20) | Combines six organ-system sub-scores |
| Vital signs (24 h aggregates) | Heart rate (mean, SD), respiratory rate (mean, SD), SpO₂ (mean and min), systolic BP (mean), temperature (mean) | Eight summary features |
| ICU laboratory values | Lactate, creatinine, WBC, bilirubin | At ICU admission |
| Clinical notes (NLP) | Note-presence flag; NLP-derived risk score (0–1); free-text narrative | MNAR: ~32% of patients have no note; absence correlates with shift pressure and workload |
| Hourly ICU vitals | 6 vitals × 24 hourly readings = 144 columns | Heart rate, respiratory rate, SpO₂, systolic BP, temperature, lactate — one column per vital per hour |

The full column reference with missingness details is in `data/raw/DATASET_CARD.md`.

### (b) What your team must build

Each team must design and build at least two AI models to enable a meaningful comparison and evaluation. There is no prescribed architecture — the design choices are yours.

| Design question | Guidance |
|---|---|
| How many models? | At least two — enough to compare modality combinations and find genuine failure modes. Three is a natural number for a structured evaluation. |
| What modalities? | The dataset has five modality groups: demographics, SOFA score, vital signs, laboratory values, and clinical notes. |
| What architectures? | Choose architectures appropriate to the feature count and the clinical interpretability requirement. |
| How to create useful failure modes? | Think about how different model designs — in terms of modality choice and missing-data handling — will produce different failure profiles worth evaluating and comparing. |
| What to do with missing data? | `note_risk_score` is absent for approximately 30% of patients (MNAR). How your models handle this missingness is one of the most important design decisions and a key target for evaluation. |

The models you build become the subject of your OMAIB Pathway Manifest and Model Safety Report. Every verdict you assign in those documents refers to a model your team designed, trained, and is prepared to defend.

---

## 4. The Five Deliverables

### A. The Solution

A runnable tool with a clear intended user and a working demonstration of its core function. Your team may choose one of the suggested ideas below, or define your own compelling problem grounded in the clinical dataset. Whatever you build, it must be deployable in spirit — a real clinician or clinical governance team should be able to picture using it.

**Suggested challenge ideas (or define your own grounded in the dataset):**

- **Clinical AI readiness decision support** — an AI-powered solution that helps a hospital decide whether an ICU AI model is ready for deployment, restricted use, further validation, or rejection.
- **Bedside alarm explainability product** — a product with a user interface that surfaces plain-language reasoning behind every AI-generated ICU alarm, so clinicians can accept or override with one tap and the rationale is logged. The product must also measure whether AI alerts risk overwhelming clinicians or would meaningfully improve response times.
- **Patient population drift monitor** — a lightweight monitoring service that continuously compares the incoming patient population against the model's training cohort and sends an early-warning signal when the ICU population diverges meaningfully.

### B. OMAIB Pathway Manifest (`omaib_pathway.json`)

A structured JSON manifest containing per-model verdicts and metrics for all three ICU models. Must include: team name and members; evaluation date; per-model verdict (APPROVE / CONDITIONAL / NOT APPROVED), full metrics (AUROC, AUPRC, Brier score, sensitivity, specificity, PPV, NPV, F1, threshold, n_total, n_positive), and subgroup gaps; and overall team notes.

The schema is provided — your team fills in the verdict, conditions, narrative, and metric fields before export. A missing verdict or empty metrics block for any model causes the file to be rejected at submission.

### C. Model Safety Report (`model_safety_report.json`)

A structured JSON report containing the full safety assessment for all three models. Must include: schema_version, report_type, strand, team, evaluation_date; a models array with per-model verdict, full metrics, conditions, narrative, subgroup_gaps, responses to all five clinical deployment questions, failure analysis characterisations, explainability output, and at least three failure catalogue entries; and overall_notes.

JSON is required so the file can be validated against the hackathon's centralised reporting schema and ingested. Judges verify during the demo that no narrative field reads "Not provided".

The five clinical deployment questions (`q1_miss_rate` through `q5_calibration`) and the four failure analysis characterisations have no prescribed answers — your team derives these from your own evaluation of the models. Use the field names in Section 12B as prompts for what each field should address.

### D. Evidence Dashboard

Five analytical views that constitute the evidence behind items B and C. Each view must be completed, and its findings must be reflected in the exported JSON:

| View | What to produce | Key output |
|---|---|---|
| Model performance | AUROC, AUPRC, Brier score, and confusion matrix at a clinically meaningful threshold for each model | Metrics table per model with clinical interpretation |
| Subgroup equity | Performance across at least two patient subgroups (age band, admission type) with AUROC gaps quantified | Equity gap table showing which groups are underserved |
| Explainability | At least one SHAP summary plot or feature importance ranking per model | Visual showing which features drive each model's predictions |
| Failure mode catalogue | At least three specific failure modes documented with supporting examples from the dataset | Named failure modes with evidence (subgroup, mechanism, clinical consequence) |
| Clinical deployment assessment | Ward simulation counts (TP/FN/FP/TN per 100 patients) and all five deployment questions answered per model | Clinical interpretation of performance at the chosen threshold |

### E. Option-Specific Deliverable

A structured JSON section (`option_specific`) embedded within item C (`model_safety_report.json`). Must include: `type`, `title`, and `content` fields. The content schema is option-specific:

| Option | `type` value | Required `content` fields |
|---|---|---|
| 1. Readiness decision support | `scoring_rubric` | `per_model` array — each entry with `model`, `thresholds_applied`, `weights`, and `evidence_summary` |
| 2. Bedside alarm product | `alert_burden_analysis` | `alerts_per_patient_hour`, `override_rate`, `simulation_window`, `interpretation` |
| 3. Drift monitor | `threshold_sensitivity_report` | `thresholds_tested` array, `signal_at_each_threshold` array, `recommended_threshold`, `rationale` |

---

## 5. The OMAIB Pathway Manifest — A Governance Decision

The narrative fields in `omaib_pathway.json` are governance decisions, not form-filling. When your team writes APPROVE, CONDITIONAL, or NOT APPROVED for a model, you are asserting that the evidence supports that verdict — and that assertion enters the OMAIB benchmark registry.

Consider carefully what each verdict means:

**APPROVE** — Endorses clinical deployment. High AUROC alone is insufficient — you must account for subgroup equity, calibration, and alert burden at the chosen threshold.

**CONDITIONAL** — Endorses deployment under specific stated conditions. Conditions must be concrete and actionable: not "improve the model" but a specific constraint grounded in the failure mode your team found.

**NOT APPROVED** — Deployment is unsafe given the evidence. You must identify the specific failure mode that makes the verdict necessary.

The `model_safety_report.json` adds a second governance layer: what your team chooses to highlight in the evidence, and what it chooses not to explain, is equally a statement about what constitutes trustworthy clinical AI evidence.

---

## 6. The Three Track Roles

Three roles divide the work across deliverables A–E. For a team of four, the fourth member joins the role that best fits their background. A detailed breakdown of each role's responsibilities, convergence points, and contribution checklist is available in the strand leads' supplementary guide.

| Role | Primary deliverables |
|---|---|
| **The Builder** | A — solution, E — option-specific JSON |
| **The Evidence Analyst** | D — four evidence views (performance, equity, explainability, failures) |
| **The Governance Lead** | B — manifest, C — report, D — deployment assessment |
| Fourth member (optional) | Supports Analyst or Governance Lead |

Roles run in parallel from the start. The Evidence Analyst's findings must be complete before the Governance Lead can write credible verdicts and narratives.

---

## 7. Key Clinical Concepts

| Term | Plain-English definition | In this context |
|---|---|---|
| **AUROC** | Area Under the Receiver Operating Curve (0.5 = chance; 1.0 = perfect). | AUROC 0.85 means the model ranks a deteriorating patient above a stable one 85% of the time. |
| **Sensitivity** | Of all patients who deteriorated, what fraction did the model flag? | Low sensitivity = missed deteriorations — the dangerous ICU error. |
| **Specificity** | Of all stable patients, what fraction did the model correctly leave unflagged? | Low specificity = too many false alarms — causes alert fatigue. |
| **PPV** | Of all flagged patients, what fraction actually deteriorated? | Tells you how much to trust a positive alert. |
| **NPV** | Of all unflagged patients, what fraction truly did not deteriorate? | Tells you how safe it is to rely on a negative outcome. |
| **Calibration / Brier Score** | Does the model's stated confidence match reality? Brier Score = mean squared probability error (lower is better). | A well-calibrated model can be used to prioritise. A poorly calibrated model cannot. |
| **Subgroup equity** | Does the model perform equally across patient groups (age, sex, admission type)? | A model accurate on average but failing for a specific patient group transfers risk silently. |
| **MNAR** | Missing Not At Random — data is absent for reasons correlated with the outcome. | Clinical notes are absent more often during busy shifts. Any model using note features will be systematically less reliable when notes are absent — evaluating the note-absent subgroup is essential. |
| **Decision threshold** | The probability cut-off that converts a risk score into a binary flag. | Choosing a threshold is a clinical governance decision, not a modelling decision. For ICU deterioration, a threshold lower than 0.50 is typically more appropriate — the cost of a missed deterioration is higher than the cost of a false alarm. Your team must choose and justify the threshold for each model you build. |

---

## 8. Submission Checklist and Demo

The submission is a 2.5-minute live demo covering the solution and evidence, followed by a 2.5-minute team presentation at the Workshop on 11 June.

### Pre-Submission Checklist

All items must be complete before the demo session begins.

| Item | Owner |
|---|---|
| Solution (A) is runnable from the repository without modification | Builder |
| `omaib_pathway.json` present in `reference/` — all three model verdicts populated, no empty metrics blocks | Governance Lead |
| `model_safety_report.json` present in `reference/` — all narrative, condition, and deployment-question fields completed (none reading "Not provided") | Governance Lead |
| All five Evidence Dashboard views completed and findings reflected in the JSON exports | Evidence Analyst |
| `option_specific` section completed within `model_safety_report.json` | Builder |
| Team name in JSON files matches the GitHub branch name | All |
| PR open against the `clinical` branch on GitHub | All |

### Final Presentation

Each team gives a 2.5-minute presentation to the group. Cover:

- **What you built** — show the solution and explain the concept and intended user.
- **Why it is designed this way** — explain your design choices and what makes your approach distinctive.
- **What the data showed** — present the most important metric findings with sample sizes.
- **Your most important subgroup finding** — name the group, give the gap, explain the mechanism.
- **Your deployment verdict** — explain APPROVE / CONDITIONAL / NOT APPROVED for each model and any conditions attached.
- **The failure modes you found** — name at least one failure mode, give the evidence, and explain its clinical consequence.
- **How you used generative AI** — where it helped, where it fell short, and what human judgement your team provided.

The strongest presentations will not simply show that something works. They will explain why the team made specific evidence-based choices and what a clinical governance board should do next.

### Submitting Your Work

Submission is via a **Pull Request** from your team branch to the `clinical` strand branch.

```bash
git add .
git commit -m "Team <your-team-name>: final clinical strand submission"
git push origin your-team-name
```

Then open a PR on GitHub: `your-team-name → clinical`
Title: `"Team <your-team-name> — Clinical Strand Submission"`

> **The PR must be open by 18:00 on 10 June.** Do not push directly to the `clinical` branch — all team work goes on your named team branch.

---

## 9. What Does a Strong Submission Look Like?

The difference between a weak and a strong submission is specificity, honesty, and actionability. A strong team does not just report numbers — it explains what those numbers mean for a nurse making a decision at 3 a.m.

**Weak subgroup finding:**
> "Model B performs worse on some patients."

**Strong subgroup finding:**
> "Model B sensitivity drops from [X] in [reference subgroup] to [Y] in [affected subgroup] (n=[N]). The false negatives in this group share a common pattern: [clinical mechanism]. This is consistent with [clinical knowledge]. We recommend Model B is not deployed for [patient scope] without [specific safeguard]."

The strong version names the subgroup, gives sample size, identifies the mechanism, ties it to clinical knowledge, and makes a specific recommendation.

**Weak governance recommendation:**
> "Model C should be improved before deployment."

**Strong governance recommendation:**
> "Model C is NOT APPROVED for standalone clinical deployment. Among [affected subgroup] (n=[N]), sensitivity falls from [X] to [Y]. This is not random — [mechanism]. We recommend: (1) [specific intervention]; (2) a prospective audit is conducted after 30 days of deployment to confirm [condition]."

Judges will ask questions during the demo. Vague findings cannot be defended. Named findings with sample sizes, mechanisms, and specific recommendations always can.

All findings — subgroup gaps, failure mode narratives, deployment conditions, and verdicts — must be recorded in `model_safety_report.json`. The narrative and deployment-question fields in that file are the primary evidence record that judges review.

---

## 10. Your First 30 Minutes

### All roles — first 10 minutes (everyone, together)

- Read this guide in full and agree on which challenge idea to pursue.
- Open `icu_patients.csv` — confirm 2,000 rows and 182 columns, check the deterioration rate (`deteriorated_24h`, ~42%), count NaN values in `note_risk_score` (~32% of patients) and `blood_loss_ml` (~36%).
- Decide what models your team will build — agree on at least two. Sketch which features each model will use and how missing `note_risk_score` and `blood_loss_ml` values will be handled in each.
- Explore the `surgery_type` and `admission_urgency` distributions — note which surgical types and urgency categories have the highest missingness in notes and blood loss.
- Decide your decision threshold — or agree to compare several. This choice drives the clinical deployment assessment in item D.
- Assign roles: Builder, Evidence Analyst, Governance Lead (and fourth member if present).

### Minutes 10–25 — parallel work

| Role | Task | Goal by minute 25 |
|---|---|---|
| **Builder** | Design the architecture of the chosen solution. In parallel, implement the training pipeline for the first model — load the dataset, define features, set up the train/val/test split. | Solution skeleton started; first model training pipeline ready to run. |
| **Evidence Analyst** | Explore the dataset: distributions, missingness patterns, deterioration rate by subgroup, admission-type breakdown. Implement the metric computation functions in `src/evaluate.py`. | Dataset fully profiled; metric functions implemented and tested on synthetic arrays. |
| **Governance Lead** | Study the deployment question fields in the JSON reference (Section 12B). Draft the ward simulation framework — what do TP, FN, FP, TN mean per 100 patients at the chosen threshold? Understand what each verdict requires as supporting evidence. | Ward simulation framework ready; deployment questions drafted. |

### Minutes 25–30 — quick team sync

- Builder reports which model(s) will be trained first and the expected training time.
- Evidence Analyst confirms metric functions are working (tested on a dummy probability array).
- Governance Lead shares the ward simulation at the chosen threshold — does the implied false-alarm rate feel clinically defensible to the team?
- All agree on which model to evaluate first and which subgroup to investigate as the primary failure-mode target.

The implementation phase is done when all five Evidence Dashboard views are complete and both JSON files are exported. Only then does demo preparation begin.

---

## 11. Judging Criteria

All strands are judged on four criteria. Judges will ask questions during the demo — your team must understand what you built and why you made the decisions you made.

| Criterion | Weight | Weak | Strong |
|---|---|---|---|
| **Creativity** | 15% | Predictable framing; solution does what was expected with no distinctive angle | Original approach with a clear point of view; the solution and evidence framing say something distinctive about the team's perspective and the clinical problem |
| **Evidence quality** | 35% | Metric reported without sample size or comparison to a baseline | Metric with subgroup n, mechanism explained, and comparison to what a treat-all or random baseline would achieve |
| **Clarity** | 25% | Finding interpretable only by a data scientist | Finding interpretable by a clinician, NHS manager, or patient with no statistics training — naming is specific, consequences are stated in plain English |
| **Deployability** | 25% | Recommendation is "improve the model" without specifics | Recommendation states the exact threshold, patient scope, monitoring conditions, escalation criteria, and what a re-evaluation after 30 days should check |

**Top submissions will:**
- Identify at least one failure mode that is clinically meaningful — not just statistically significant
- Offer a deployment recommendation a real clinical governance board could vote on
- Present findings that would not be obvious from summary statistics alone
- Show genuine creativity in how they framed the problem or communicated the evidence

The goal is not to find the "best" model. The goal is to tell the truth about all your models — and to do it in a way that is useful to someone who has to make a real decision.

---

## 12. Clinical Strand Reference

Keep this section open during the build. Field names and validation rules match the submission schema exactly.

### 12A. `omaib_pathway.json` — Field Reference

All fields are required. A single missing or empty field causes the manifest to be rejected at submission.

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Always `"omaib-clinical"` |
| `submission_type` | string | Always `"model_safety_report"` |
| `strand` | string | Always `"clinical"` |
| `hackathon` | string | Always `"MultimodalAI26"` |
| `submitted` | string (ISO date) | Date of export |
| `team.name` | string | Your team name — must match your GitHub branch name |
| `team.members` | string | Comma-separated list of team member names |
| `models[].name` | string | A name your team assigns to the model (e.g. "Multimodal LightGBM", "Vitals-only LR"). Must be unique within the submission. |
| `models[].verdict` | string | `APPROVE`, `CONDITIONAL`, or `NOT APPROVED` |
| `models[].conditions` | string | Deployment conditions — required if verdict is `CONDITIONAL` |
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
| `models[].metrics.n_total` | int | Total patients in the test set |
| `models[].metrics.n_positive` | int | Deteriorating patients in the test set |
| `models[].subgroup_gaps` | object | Per-subgroup AUROC gap relative to the reference group. Keys must match subgroups reported in the Evidence Dashboard. |
| `overall_notes` | string | Team's overall assessment notes |

### 12B. `model_safety_report.json` — Field Reference

All fields required. The `models` array must contain one entry per model your team built and evaluated — at minimum two.

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | `"omaib-clinical"` |
| `report_type` | string | `"model_safety_report"` |
| `strand` / `hackathon` / `team` / `evaluation_date` | various | Same as `omaib_pathway.json` |
| `models[].verdict` / `metrics` / `conditions` / `narrative` / `subgroup_gaps` | various | Same as `omaib_pathway.json` — replicated here for the full report context |
| `models[].deployment_questions.q1_miss_rate` | string | How many deteriorating patients will this model miss? |
| `models[].deployment_questions.q2_alert_precision` | string | When the model alerts, how often is it right? |
| `models[].deployment_questions.q3_clearance_safety` | string | When the model gives the all-clear, is it safe? |
| `models[].deployment_questions.q4_discrimination` | string | How well does the model separate sick from well patients? |
| `models[].deployment_questions.q5_calibration` | string | Can risk scores set care priorities? |
| `models[].failure_analysis.who_is_missed` | string | Characterisation of missed patients |
| `models[].failure_analysis.false_alarm_profile` | string | Characterisation of false positives |
| `models[].failure_analysis.feature_importance_interpretation` | string | What features drive the model's predictions |
| `models[].failure_analysis.model_disagreement` | string | Where models disagree and why |
| `models[].explainability.output_type` | string | Type of explainability output (e.g. SHAP, feature importance) |
| `models[].explainability.description` | string | Description of the explainability output |
| `models[].failure_catalogue` | array | At least three failure modes, each with `mode`, `example`, and `subgroup` |
| `models[].option_specific.type` | string | `scoring_rubric`, `alert_burden_analysis`, or `threshold_sensitivity_report` |
| `models[].option_specific.title` | string | Short title for the option-specific section |
| `models[].option_specific.content` | object | Type-specific content fields (see Section 4E) |
| `overall_notes` | string | Summary team assessment |

### 12C. `icu_patients.csv` — Dataset Column Reference

Provided ready-to-use. Do not modify the file. The full column reference with missingness details is in `data/raw/DATASET_CARD.md`. Key columns for model building:

| Column | Type | Description |
|---|---|---|
| `patient_id` | str | Unique identifier |
| `age` | int | Age in years |
| `sex` / `sex_enc` | str / int | M or F; 1 = female |
| `surgery_type` / `surgery_enc` | str / int | cardiac, vascular, abdominal, orthopaedic |
| `admission_urgency` / `urgency_enc` | str / int | elective or emergency |
| `asa_class` | int | ASA physical status 1–4 |
| `op_duration_h` | float | Operation duration (hours) |
| `has_diabetes` / `has_hypertension` | int | Comorbidity flags |
| `blood_loss_ml` | float | Estimated blood loss (mL) — MNAR, ~36% missing |
| `blood_loss_imputed` | float | Blood loss with training-set mean filled |
| `blood_loss_missing` | int | 1 = blood loss was not recorded |
| `transfused` | int | 1 = intra-operative transfusion |
| `preop_creatinine` / `preop_wbc` / `preop_lactate` | float | Pre-operative lab values |
| `sofa_score` | int | SOFA at ICU admission (0–20) |
| `hr_mean` / `hr_std` | float | Heart rate 24 h mean and SD (bpm) |
| `rr_mean` / `rr_std` | float | Respiratory rate 24 h mean and SD (breaths/min) |
| `spo2_mean` / `spo2_min` | float | SpO₂ 24 h mean and minimum (%) |
| `sbp_mean` | float | Systolic blood pressure 24 h mean (mmHg) |
| `temp_mean` | float | Body temperature 24 h mean (°C) |
| `icu_lactate` / `icu_creatinine` / `icu_wbc` / `icu_bilirubin` | float | ICU admission lab values |
| `has_notes` | int | 1 = clinical note exists |
| `note_risk_score` | float | NLP risk score (0–1); NaN when `has_notes == 0` — MNAR, ~32% missing |
| `note_text` | str | Free-text clinical note; NaN when `has_notes == 0` |
| `icu_hours` | int | Hours in ICU before step-down or event |
| `deteriorated_24h` | int | **Primary target**: 1 = deteriorated within 24 h (~42%) |
| `major_complication_30d` | int | Secondary target: 1 = major complication within 30 days (~28%) |
| `hr_h00`–`hr_h23` ... `lactate_h00`–`lactate_h23` | float | Hourly vitals (6 vitals × 24 hours = 144 columns) |

```python
# Verify dataset on load
import pandas as pd
df = pd.read_csv('data/raw/icu_patients.csv')
print(df.shape)                                    # expect (2000, 182)
print(df['deteriorated_24h'].mean())               # expect ~0.42
print(df['note_risk_score'].isna().mean())         # expect ~0.32 (MNAR)
print(df['blood_loss_missing'].mean())             # expect ~0.36 (MNAR)
print(df['surgery_type'].value_counts())
```

---

## 13. Key Clinical Facts

- **SOFA score** (Sequential Organ Failure Assessment) combines six organ system scores: respiratory, coagulation, liver, cardiovascular, renal, neurological. A SOFA of 0–5 is low severity; above 11 is associated with >50% mortality.

- **What a deteriorating ICU patient looks like:** Rising respiratory rate is often the earliest signal. Lactate rises as tissues stop receiving adequate oxygen. Blood pressure falls. Mental status changes. These signs often appear hours before a cardiac arrest — the window for intervention.

- **Why elderly patients present differently:** Elderly patients frequently take medications that suppress the normal physiological stress response. Their heart rate may not rise even when circulation is failing. Fever may be absent despite severe infection. Normal-range vitals in an elderly patient can mask significant deterioration that would be obvious in a younger patient.

- **Why notes go missing:** Clinical notes are written by busy doctors and nurses during or after shifts. Note absence is systematically correlated with shift pressure and perceived (not necessarily actual) patient stability. This means note missingness is not random — it is MNAR — and any model that uses note features will be less reliable precisely when the clinical team is under greatest workload.

---

*Questions? Speak to a clinical mentor or a technical mentor. Each team has access to both throughout the event.*
