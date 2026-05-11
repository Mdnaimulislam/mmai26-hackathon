# MultimodalAI'26 Hackathon

## Clinical Strand Guide 
---
> ## The Challenge: "Can You Trust an AI in the ICU?"


---

## 1. The Scenario

It is 3 a.m. on an intensive care unit. A nurse is managing eight patients simultaneously. A patient in bed 6 has been stable for hours — but in the next six hours, they will deteriorate sharply. Their heart rate is slightly elevated. Their lactate is creeping up. A brief note from the evening team mentioned "looks a bit off." None of these signals, alone, would trigger an alarm.

An AI system reviews all 500 patients on the unit and flags the ones it predicts will deteriorate in the next 24 hours. The nurse sees the alert and acts. Or the AI misses the patient entirely, and the nurse doesn't know to look twice.

**This is not hypothetical.** Early warning AI systems are being deployed in ICUs across the UK, US, and Europe right now. The question is not whether they will be used — it is whether the teams deploying them have genuinely evaluated whether they are safe.

When these models fail, the costs are asymmetric:

- A **false negative** (missed deterioration) means a patient who could have been saved is not treated in time. In an ICU, hours matter. Mortality rises sharply with delayed intervention.
- A **false positive** (unnecessary alert) means nurses respond to phantom alarms, eroding trust in the system and adding workload — which eventually causes real alerts to be ignored.
- A model that works well on average but **fails on elderly patients** means that a specific population bears the risk silently, invisible in aggregate statistics.

Your job this today is to find those failures before they reach a patient.

---

## 2. Your Role in This Hackathon

Your team's goal is to **evaluate three AI models** and produce a **Model Safety Report** that a clinical governance board could act on. You are not doing open-ended model research — the problem is defined, the data is provided, and the output format is specified.

However, you will need to complete a small amount of implementation work before the evaluation pipeline is usable. This is intentional. The TODOs you will find in the code are not bugs or omissions — they are scaffolding. Here is exactly what needs to be done and why:

---

### What You Implement (and why it is part of the task)

**1. `src/evaluate.py` — your evaluation functions**

This file contains function signatures for the metrics your team will use: AUROC, sensitivity, calibration, subgroup analysis. The bodies are empty — marked `raise NotImplementedError`. Your team implements them.

*Why not just provide them?* Because implementing `compute_metrics()` forces you to understand what AUROC and sensitivity *actually compute*, not just what they are called. Teams that skip this step and use a pre-written library often cannot answer judges' questions about why their findings are what they are. Implementing the metrics is part of demonstrating you understand them.

**2. `models/model_b.py` AND `models/model_c.py` — both incomplete models**

Both Model B and Model C are provided as skeletons. Your team implements both. Each file contains a full design brief: the clinical context, the architectural trade-offs, and three explicit options to choose from. You are not inventing models from scratch — you are making documented design decisions and filling in the implementations.

*Why not just provide all three complete?* Because Model B and Model C each have a known clinical limitation built into their design. Implementing them ensures your team understands those limitations deeply enough to evaluate and explain them. You will evaluate all three models (A, B, and C) in the app — so all three need to be working before you launch it.

**3. `notebooks/01_explore_and_train.ipynb` — the training pipeline**

The notebook walks you through data loading, preprocessing, splitting, training all three models, and saving them. It is not fully automated — it has cells where you set parameters (your preferred train/val/test split ratios), cells that depend on `evaluate.py` being implemented, and cells that depend on Model B and C being implemented. Work through it top to bottom after completing tasks 1 and 2 above.

---

### What You Do Not Implement

- Model A is provided complete and trains immediately — use it as your reference baseline.
- The Streamlit app (`app.py`) is provided complete — you launch it, you do not modify it.
- The HTML report and OMAIB JSON generation (`src/report.py`) are provided — you fill in the narrative text in the app, you do not write the rendering code.

---

### The full task arc

| Phase | Time | What you produce |
|---|---|---|
| Implement `evaluate.py` | ~45 min | Working metrics pipeline |
| Implement Model B and Model C, train all three | ~60 min | Saved model files (model_a, model_b, model_c) |
| Run the evaluation app, analyse all three models | ~2.5 hours | Findings per model |
| **Complete the app questionnaire** (Tab 2 + Tab 4) | ~30 min | Model Performance Q&A + Failure Analysis notes |
| Write verdicts and narratives in the Report Builder | ~30 min | Model Safety Report |

Good evaluation is as technically demanding as good modelling. It is also more consequential. A flawed model that passes a poor evaluation will harm patients. A flawed model caught by rigorous evaluation will not.

---

## 3. Understanding the Data

The dataset contains **500 ICU patients, one row per patient**. The outcome label is `deteriorated` (1 = deteriorated within 24 hours, 0 = did not). Approximately **34% of patients deteriorated**.

### Demographics
| Feature | What it means |
|---|---|
| `age` | Patient age in years |
| `sex` | Biological sex (M/F) |
| `admission_type` | Why they were admitted (e.g. medical, surgical, trauma) |

### Severity Score
| Feature | What it means |
|---|---|
| `sofa` | Sequential Organ Failure Assessment score. Higher = more severe. Ranges 0–24. See Section 9. |

### Vital Signs
Measured continuously; the dataset captures summary statistics per patient over a monitoring window.

| Feature | What it measures | Clinical relevance |
|---|---|---|
| `hr_mean`, `hr_std` | Heart rate average and variability | Tachycardia (>100 bpm) or erratic HR signal distress |
| `rr_mean`, `rr_std` | Respiratory rate average and variability | Raised RR is an early deterioration signal, often missed |
| `spo2_mean`, `spo2_min` | Blood oxygen saturation (%) | Below 94% is concerning; min captures dangerous dips |
| `sbp_mean` | Systolic blood pressure average | Low SBP (hypotension) indicates circulatory failure |
| `temp_mean` | Body temperature average | Fever or hypothermia both signal sepsis |

### Laboratory Values
Blood tests ordered during the monitoring period.

| Feature | What it measures | Clinical relevance |
|---|---|---|
| `lactate` | Lactate level (mmol/L) | Elevated lactate (>2) signals poor tissue oxygenation — a key sepsis marker |
| `creatinine` | Kidney function marker | Rising creatinine indicates acute kidney injury |
| `wbc` | White blood cell count | Very high or very low WBC signals infection or immune suppression |
| `bilirubin` | Liver function marker | Elevated bilirubin indicates liver dysfunction |

### Clinical Notes
| Feature | What it means |
|---|---|
| `has_notes` | 1 if a clinical note was written for this patient, 0 if not |
| `note_risk_score` | NLP-derived risk score from the note text. **NaN for ~30% of patients** (those without notes). |

**Why are notes missing?** Notes are not always written. During busy night shifts, documentation is often deferred. Patients who are stable (or thought to be stable) may not have a note until handover. This means the absence of notes is not random — it is correlated with shift patterns, staffing, and perceived patient acuity. A model that relies on notes will behave differently depending on whether a note exists.

---

## 4. The Three Models

Each model has a different design and a known limitation. Part of your job is to find and characterise that limitation.

> **What your team implements:**
> - **Model A** — provided complete. Trains and runs immediately. Use it as your reference.
> - **Model B and Model C** — your team implements **both**. Read the design brief at the top of each model file before starting. One person leads Model B, another leads Model C — the implementations are independent and can run in parallel.
> - **`src/evaluate.py`** — **all teams implement this first**. It contains the metrics, subgroup analysis, and calibration functions the evaluation app depends on. Without it, nothing downstream works.

### Model A — Multimodal LightGBM *(provided complete)*
Model A uses all available features: demographics, SOFA score, vitals, labs, and clinical notes (with a strategy for handling missing notes). It is provided as a fully trained model. It represents a well-resourced production deployment. **Start here** to understand what good performance looks like before evaluating the other two.

### Model B — Vitals-Only Model *(skeleton — your team implements)*
Model B uses only vital signs as inputs. It has a known limitation that affects a specific patient subgroup. The design brief in `models/model_b.py` gives you the clinical context and three architectural options to choose from. Your task is to choose an approach, implement it, train the model, and then evaluate it alongside Model A. Consider: are there patient groups whose physiology means vital signs alone are misleading?

### Model C — Notes-Dependent Model *(skeleton — your team implements)*
Model C incorporates clinical note risk scores as a primary input signal. It has a known limitation related to data completeness. The design brief in `models/model_c.py` describes three strategies for handling the ~30% of patients with no notes — each with different clinical consequences. Your task is to choose a strategy, implement it, train the model, and then evaluate it alongside the others.

---

## 5. Your Track Role

Each team of three assigns one person to each role. Roles are complementary — findings must be integrated into the final Model Safety Report.

### The Explainer
You make the models interpretable. Your audience is a clinical governance board — not data scientists.

**Phase 1 (first hour):** Run all three models, generate predictions for all 500 patients, compute overall AUROC and calibration plots.

**Phase 2:** Use feature importance or SHAP values to identify which features drive predictions. Build one visualisation per model showing "what does this model pay attention to?"

**Phase 3:** Write the plain-English model descriptions for the Safety Report. For each model: what does it do, what does it use, and what should a clinician know before trusting it?

**Deliverable:** Three one-page model cards in plain English.

---

### The Failure Hunter
You find where the models are wrong, and who pays the price.

**Phase 1:** Compute sensitivity and specificity overall. Then split the patient population into subgroups: age bands (under 65, 65–80, over 80), admission type, SOFA quartiles, notes present vs absent.

**Phase 2:** Compute sensitivity and specificity within each subgroup. Flag any subgroup where sensitivity drops below 0.70 (i.e. the model misses more than 30% of deteriorating patients in that group).

**Phase 3:** For the most concerning subgroup, characterise the false negatives. What do these patients look like? What did the model miss? Can you explain why?

**Deliverable:** A subgroup equity table and a narrative explaining the most clinically dangerous failure mode found.

---

### The Gatekeeper
You make the deployment decision and set the threshold.

**Phase 1:** Understand the operating context. An ICU nurse can respond to approximately 3–4 alerts per shift without alert fatigue. With 500 patients, what does that imply about your acceptable false positive rate?

**Phase 2:** For each model, plot the precision-recall curve. Choose a decision threshold for each model. Justify your choice using both statistical metrics and clinical reasoning.

**Phase 3:** Write the deployment recommendation. For each model: deploy, conditional deploy (with stated mitigations), or do not deploy. A "conditional deploy" recommendation must state exactly what conditions must be met.

**Deliverable:** Decision thresholds, a deployment recommendation table, and a governance checklist.

---

## 6. Clinical Concepts Explained

| Term | Plain-English Definition | In this context |
|---|---|---|
| **AUROC** | Area Under the Receiver Operating Curve. Ranges 0.5 (no better than chance) to 1.0 (perfect). Measures overall discrimination ability. | An AUROC of 0.85 means the model correctly ranks a deteriorating patient above a stable one 85% of the time. |
| **Sensitivity** | Of all patients who actually deteriorated, what fraction did the model flag? Also called Recall. | Low sensitivity = the model misses deteriorating patients. In an ICU, this is the dangerous error. |
| **Specificity** | Of all patients who did not deteriorate, what fraction did the model correctly leave unflagged? | Low specificity = too many false alarms. This causes alert fatigue. |
| **PPV (Positive Predictive Value)** | Of all patients the model flagged, what fraction actually deteriorated? Also called Precision. | Tells you how much to trust a positive alert. |
| **NPV (Negative Predictive Value)** | Of all patients the model did not flag, what fraction truly did not deteriorate? | Tells you how safe it is to rely on a negative (no alert). |
| **Calibration** | Does the model's stated confidence match reality? If it says 70% risk, does deterioration occur ~70% of the time? | A well-calibrated model can be used to prioritise. A poorly calibrated model cannot. |
| **False Negative** | A deteriorating patient the model did not flag. | In this context: a patient who did not receive timely intervention and may die or suffer permanent harm as a result. |
| **Subgroup Equity** | Does the model perform equally well across different patient groups (age, sex, admission type)? | A model that is accurate on average but fails on elderly patients is not equitable — it transfers risk to a vulnerable group. |

---

## 7. What Does a Strong Submission Look Like?

The difference between a weak and strong finding is specificity, evidence, and actionability.

**Weak finding:**
> "Model B performs worse on elderly patients."

**Strong finding:**
> "Model B sensitivity drops from 0.81 in patients under 65 to 0.54 in patients over 80 (n=87). The 40 false negatives in the over-80 group share a common pattern: near-normal heart rate despite elevated lactate (mean 3.1 mmol/L) and low systolic BP (mean 91 mmHg). This is consistent with the known phenomenon of blunted tachycardia in elderly patients on beta-blockers, where heart rate fails to rise in response to physiological stress. Model B, using vitals only, cannot detect this pattern. We recommend Model B is not deployed for patients over 75 without supplementary lab-based override rules."

The strong version names the subgroup, gives sample size, identifies the mechanism, ties it to clinical knowledge, and makes a specific recommendation.

**Weak governance recommendation:**
> "Model C should be improved before deployment."

**Strong governance recommendation:**
> "Model C should not be deployed as a standalone alert system until note missingness is addressed. In the current dataset, 31% of patients have no notes. Among patients without notes, Model C sensitivity is 0.47 compared to 0.79 in patients with notes. We recommend (1) Model C predictions are suppressed and replaced by Model A predictions when notes are absent, and (2) a prospective audit is conducted after 30 days of deployment to verify the missingness rate is stable."

---

## 8. The App Questionnaire — Complete Before Exporting the Report

> **Important:** The HTML report and OMAIB JSON are generated from text your team writes inside the app. The questionnaire fields in **Tab 2** and **Tab 4** are not optional commentary — they are the primary record of your team's clinical evaluation. Fill them in before you click "Generate HTML report" in Tab 5.

---

### Tab 2 — Model Performance: five clinical deployment questions per model

Open **Tab 2 → Model Performance** and expand each model. Underneath the ward simulation counts you will find five text fields. For each model, your team must write a response to all five:

| Question | What your answer should address |
|---|---|
| **Q1 — How many deteriorating patients will this model miss?** | State how many patients are missed per 100 and whether that miss rate is clinically acceptable. Consider the severity of delayed intervention — in an ICU, hours matter. |
| **Q2 — When the model raises an alert, how often is it right?** | State the PPV and interpret it: how many alerts require genuine clinical action, and is the false alarm rate sustainable for the available nursing resource? |
| **Q3 — When the model gives the all-clear, is it safe?** | State the NPV and interpret it: can a cleared patient safely remain unmonitored, or should a clinical override protocol apply? |
| **Q4 — How well does the model separate sick from well patients?** | Interpret the AUROC: is the model's ability to rank deteriorating patients above stable ones sufficient for priority review? |
| **Q5 — Can risk scores set care priorities?** | Interpret the Brier score: are the model's probability outputs reliable enough to prioritise nursing interventions, or should scores be treated as ranks only? |

> Each text field shows placeholder text indicating the format expected. Your answer does not need to be long — one or two clear sentences per question is sufficient. The placeholder disappears as soon as you start typing.

---

### Tab 4 — Failure Analysis: four characterisation questions per model

Open **Tab 4 → Failure Analysis** and select each model in turn. After each analysis section you will find a text field. Complete all four:

| Question | What your answer should address |
|---|---|
| **Who does this model miss?** | Is the miss rate systematic or random? Are missed patients concentrated by age band, admission type, SOFA quartile, or notes availability? What clinical risk does this blind spot create? |
| **What do false alarms look like?** | Do false alarms share common clinical characteristics (e.g. high SOFA but stable trajectory, post-operative noise)? What is the alert fatigue cost of this false alarm profile for nursing staff? |
| **What is the model using to make predictions?** | Are the most important features clinically plausible? Does any unexpected feature (e.g. an administrative field ranking above lactate or respiratory rate) suggest a data artefact rather than physiology? |
| **Where do the models disagree?** | Which patients does one model flag that another misses? Is disagreement explained by notes being absent (exposes Model C) or by age > 75 (exposes Model B)? Or is it purely a probability difference with no structural clinical cause? |

---

### Tab 5 — Report Builder: checklist and narratives

After completing Tabs 2 and 4, open **Tab 5 → Report Builder**. For each model:

1. **Work through the clinical deployment checklist** — five radio-button questions on miss rate, false alarm rate, PPV, NPV, and calibration adequacy.
2. **Select your verdict** — APPROVE, CONDITIONAL, or NOT APPROVED.
3. **Write conditions** — if CONDITIONAL, state exactly what must be true before deployment. Be specific: "Model B must not be used as a standalone alert for patients over 75 — supplementary lab-based override rules are required" is deployable guidance; "model needs improvement" is not.
4. **Write your assessment narrative** — summarise the key failure modes and why you reached this verdict. Reference the subgroup finding and the failure analysis characterisation.

> **The HTML report is only as good as what you put in.** Team responses from Tabs 2 and 4 appear automatically alongside the computed metrics in the exported report. Fields left blank show "Not provided" in the final document seen by the judges.

---

## 9. Your First 30 Minutes

> After completing the implementation phases below, return to **Section 8** and work through the questionnaire in Tabs 2 and 4 before generating the final report.

### All roles — first 10 minutes (everyone does this together)
- [ ] Read this guide in full
- [ ] Open the notebook `notebooks/01_explore_and_train.ipynb` and run the setup cell
- [ ] Open the dataset; confirm you have 500 rows and can see the `deteriorated` label
- [ ] Check the deterioration rate (expect ~34%) and the NaN count in `note_risk_score` (expect ~150 patients)
- [ ] **Open `src/evaluate.py`** — read the function signatures and docstrings. This is what you implement before anything else. Without it, the app shows `NotImplementedError` everywhere.
- [ ] **Divide the work:** assign one person to start `src/evaluate.py` while the others read the model design briefs

### All roles — divide the implementation work (minutes 10–25)
Three things need to be built before the evaluation app is usable. Split them across the team immediately:

**Person 1 — `src/evaluate.py`** (the metrics engine; everything depends on this)

| Function | Difficulty | Needed for |
|---|---|---|
| `compute_metrics()` | Medium — use sklearn | Everything |
| `roc_curve_data()` | Easy — one sklearn call | Tab 2 plots |
| `pr_curve_data()` | Easy — one sklearn call | Tab 2 plots |
| `compute_calibration()` | Medium — bin probabilities | Tab 2 calibration |
| `compute_subgroup_metrics()` | Medium — calls `compute_metrics` per group | Tab 3 |
| `equity_gap()` | Easy — subtract reference value | Tab 3 |

Once `compute_metrics()` is working, run Model A in the notebook and confirm you get a dict with AUROC, sensitivity, etc. That is your signal that the pipeline is working.

**Person 2 — `models/model_b.py`** — read the design brief, choose an architecture, implement `fit()` and `predict_proba()`.

**Person 3 — `models/model_c.py`** — read the design brief, choose a missing-notes strategy, implement `fit()` and `predict_proba()`.

Once all three models are trained and saved, everyone converges on the evaluation app. The implementation phase is done.

### The Explainer — minutes 25–30
- [ ] Run Model A; generate predicted probabilities on the validation set
- [ ] Confirm AUROC > 0.85 (signals the pipeline is working correctly)
- [ ] Note which features Model A considers most important (`model_a.feature_importance()`)
- [ ] Start the calibration plot — is the model well-calibrated?

### The Failure Hunter — minutes 25–30
- [ ] Using Model A val predictions, compute sensitivity and specificity at threshold 0.5
- [ ] Run `compute_subgroup_metrics()` grouped by `age_band` — note any drop across age groups
- [ ] Flag the group with the largest sensitivity gap as your first investigation target

### The Gatekeeper — minutes 25–30
- [ ] Read the model design briefs (`models/model_b.py` or `models/model_c.py`) — decide which your team is implementing
- [ ] Review the staffing constraint: if nurses can handle 4 alerts per 12-hour shift per 50-patient pod, what does that imply about acceptable false positive rate?
- [ ] For Model A, plot predicted probabilities as a histogram to understand the score distribution

---

## 10. Key Clinical Facts

- **SOFA score** (Sequential Organ Failure Assessment) combines six organ system scores: respiratory, coagulation, liver, cardiovascular, renal, neurological. A SOFA of 0–5 is low severity; above 11 is associated with >50% mortality. It is calculated from labs, vital signs, and neurological assessment.

- **What a deteriorating ICU patient looks like:** Rising respiratory rate is often the earliest signal. Lactate rises as tissues stop receiving adequate oxygen. Blood pressure falls. Mental status changes. These signs often appear hours before a cardiac arrest — the window for intervention.

- **Why elderly patients present differently:** Elderly patients frequently take medications (beta-blockers, calcium channel blockers) that suppress the normal physiological stress response. Their heart rate may not rise even when circulation is failing. Fever may be absent despite severe infection. Normal-range vitals in an elderly patient can mask significant deterioration that would be obvious in a younger patient.

- **Why notes go missing:** Clinical notes are written by busy doctors and nurses during or after shifts. Notes are more likely to be absent during high-acuity periods (busy nights, short-staffed shifts), for patients considered "stable" by clinical intuition, and at the start of shifts before handover documentation is complete. Note absence is therefore not random — it is systematically correlated with shift pressure and perceived (not necessarily actual) patient stability.

---

## 11. Judging Criteria

| Criterion | Weight | Weak | Strong |
|---|---|---|---|
| **Evidence Quality** | 40% | Metric reported without confidence interval or sample size | Metric reported with subgroup n, confidence interval, and comparison to baseline |
| **Clarity** | 30% | Finding interpretable only by a data scientist | Finding interpretable by a clinician with no statistics training |
| **Deployability** | 30% | Recommendation is "improve the model" without specifics | Recommendation states exact threshold, patient scope, monitoring conditions, and escalation criteria |

**Top submissions will:**
- Identify at least one failure mode that is clinically meaningful (not just statistically significant)
- Provide a deployment recommendation that a real governance board could vote on
- Include at least one piece of evidence that would not be obvious from summary statistics alone (e.g. a subgroup finding, a calibration failure, a failure mode with a mechanistic explanation)

**The goal is not to find the "best" model. The goal is to tell the truth about all three.**

---

*Questions? Speak to a clinical mentor or a technical mentor. Each team has access to both throughout the event.*
