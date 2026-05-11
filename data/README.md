# Data — Clinical Strand

## Overview

| | |
|---|---|
| **File** | `raw/icu_patients.csv` |
| **Patients** | 500 (synthetic ICU patients) |
| **Schema** | One row per patient, 20 columns |
| **Outcome** | `deteriorated` — binary, 1 = deteriorated within 24 h |
| **Deterioration rate** | ≈ 34% |

> `raw/generate_data.py` is **internal** and not part of the participant workflow.
> The dataset is provided ready-to-use.

---

## Column dictionary

### Demographics

| Column | Type | Description |
|---|---|---|
| `patient_id` | str | Unique patient identifier |
| `age` | int | Age in years (18–95) |
| `sex` | str | `M` or `F` |
| `admission_type` | str | `medical`, `surgical`, or `trauma` |

### Clinical severity

| Column | Type | Description |
|---|---|---|
| `sofa_score` | int | Sequential Organ Failure Assessment score (0–20) |

### Vital signs (24-hour aggregates)

| Column | Type | Description |
|---|---|---|
| `hr_mean` | float | Mean heart rate (bpm) |
| `hr_std` | float | Std dev of heart rate — a measure of instability |
| `rr_mean` | float | Mean respiratory rate (breaths/min) |
| `rr_std` | float | Std dev of respiratory rate |
| `spo2_mean` | float | Mean peripheral oxygen saturation (%) |
| `spo2_min` | float | Minimum SpO2 in the 24-hour window |
| `sbp_mean` | float | Mean systolic blood pressure (mmHg) |
| `temp_mean` | float | Mean temperature (°C) |

### Laboratory results

| Column | Type | Description |
|---|---|---|
| `lactate` | float | Serum lactate (mmol/L) — elevated in sepsis and shock |
| `creatinine` | float | Serum creatinine (mg/dL) — kidney function marker |
| `wbc` | float | White blood cell count (×10⁹/L) — infection marker |
| `bilirubin` | float | Total bilirubin (mg/dL) — liver function marker |

### Clinical notes

| Column | Type | Description |
|---|---|---|
| `has_notes` | int | 1 = a clinical note exists for this patient, 0 = absent |
| `note_risk_score` | float | Risk signal extracted from the note (0–1); **`NaN` when `has_notes = 0`** |

### Outcome

| Column | Type | Description |
|---|---|---|
| `deteriorated` | int | **The prediction target.** 1 = patient deteriorated within 24 h |

---

## Processed splits

The notebook (`notebooks/01_explore_and_train.ipynb`) creates these from `raw/icu_patients.csv`:

| File | Approx. rows | Purpose |
|---|---|---|
| `processed/train.csv` | 350 | Model training |
| `processed/val.csv` | 75 | Tuning / early stopping |
| `processed/test.csv` | 75 | Final evaluation — **never use for training** |

Splits are stratified on `deteriorated` to preserve class balance. You can adjust the
ratios in the notebook (Step 3).

---

## Key data characteristics to investigate

### 1 — Missing data is not random (MNAR)

`note_risk_score` is `NaN` for ≈ 30% of patients, but the **missingness is not random**:
surgical patients are more likely to have no notes than medical patients, and their
deterioration pattern differs. This is the core challenge for **Model C**.

Questions to answer during evaluation:
- Does missingness rate differ by `admission_type`?
- Does deterioration rate differ between patients with and without notes?
- Does your model handle this gap systematically, or does it silently ignore it?

### 2 — Age distribution

Mean age ≈ 65 years with standard deviation ≈ 15 years. About 15–20% of patients are
aged 75 or above. Subgroup analysis by age band (`under_65`, `65_to_74`, `75_plus`)
may reveal differential model performance.

### 3 — Deterioration prevalence

≈ 34% of patients deteriorate. This means:
- A model that flags **everyone** achieves 100% sensitivity but 0% specificity
- A model that flags **no one** has 0% sensitivity — an equally useless baseline
- Any useful model must substantially outperform random chance (AUROC >> 0.5)
- The AUPRC baseline is approximately 0.34 (random classifier at this prevalence)
