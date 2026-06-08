# Data Guide — Clinical Strand Demo

Three files, all synthetic. All patient identifiers and clinical values are generated — no real patient data. Do not use these files for your own submission.

---

## File overview

| File | Rows | Columns | Grain |
|---|---|---|---|
| `tabular.csv` | 500 | 37 | One row per patient |
| `notes.csv` | 344 | 2 | One row per patient who has a clinical note |
| `vitals_series.csv` | 12,000 | 8 | 24 hourly rows per patient |

All three share `patient_id` as the join key.

---

## `tabular.csv` — Patient feature matrix

The primary file used by the models. One row per patient; 37 columns.

### Identity

| Column | Type | Description |
|---|---|---|
| `patient_id` | string | Unique identifier (P0001–P0500) |

### Demographics

| Column | Type | Range / Values | Description |
|---|---|---|---|
| `age` | int | 25–92 | Age in years |
| `sex` | string | M, F | Biological sex |
| `sex_enc` | int | 0, 1 | Encoded sex (0 = M, 1 = F) |

### Surgery context

| Column | Type | Range / Values | Description |
|---|---|---|---|
| `surgery_type` | string | abdominal, orthopaedic, cardiac, vascular | Surgery category |
| `surgery_enc` | int | 0–3 | Integer-encoded surgery type |
| `admission_urgency` | string | elective, emergency | Admission type |
| `urgency_enc` | int | 0, 1 | 0 = elective, 1 = emergency |
| `asa_class` | int | 1–4 | ASA physical status class (higher = more severe systemic disease) |
| `op_duration_h` | float | 0.5–7.6 | Operation duration in hours |

### Intra-operative — blood loss (MNAR)

Blood loss is **Missing Not At Random**: records are absent for ~34% of patients, concentrated in cardiac (~51%) and vascular (~45%) cases where documentation burden is highest. True blood loss for missing records is systematically higher than the mean.

| Column | Type | Missing | Description |
|---|---|---|---|
| `blood_loss_ml` | float | 169 / 500 | Actual intra-operative blood loss (mL) — intentionally MNAR |
| `blood_loss_imputed` | float | 0 | Mean-imputed version; underestimates complex cases |
| `blood_loss_missing` | int | 0 | MNAR flag — 1 if `blood_loss_ml` was not recorded |
| `transfused` | int | 0 | Intra-operative transfusion given (0 / 1) |

### Comorbidities

| Column | Type | Description |
|---|---|---|
| `has_diabetes` | int | Documented diabetes (0 / 1) |
| `has_hypertension` | int | Documented hypertension (0 / 1) |

### Pre-operative laboratory values

| Column | Type | Range | Description |
|---|---|---|---|
| `preop_creatinine` | float | 0.43–2.51 | Serum creatinine (mg/dL) |
| `preop_wbc` | float | 2.0–13.0 | White blood cell count (×10⁹/L) |
| `preop_lactate` | float | 0.53–2.04 | Serum lactate (mmol/L) |

### ICU severity

| Column | Type | Range | Description |
|---|---|---|---|
| `sofa_score` | int | 0–19 | Sequential Organ Failure Assessment score |
| `icu_hours` | int | 4–66 | Total ICU stay duration (hours) |

### ICU vital signs — 24-hour aggregates

Summaries derived from the hourly `vitals_series.csv`.

| Column | Type | Range | Description |
|---|---|---|---|
| `hr_mean` | float | 43.8–123.0 | Mean heart rate (bpm) |
| `hr_std` | float | 3.2–11.5 | SD of heart rate |
| `rr_mean` | float | 8.5–25.4 | Mean respiratory rate (breaths/min) |
| `rr_std` | float | 1.0–2.9 | SD of respiratory rate |
| `spo2_mean` | float | 91.8–100.0 | Mean oxygen saturation (%) |
| `spo2_min` | float | 89.5–99.7 | Minimum SpO₂ over the 24-hour window |
| `sbp_mean` | float | 67.9–172.6 | Mean systolic blood pressure (mmHg) |
| `temp_mean` | float | 35.4–38.3 | Mean temperature (°C) |

> **Vascular haemodynamic masking:** vascular patients receive post-operative beta-blockade. Their mean HR (~70 bpm) and ICU lactate (~0.95 mmol/L) are the lowest of all surgery types, despite elevated complication risk. Models that weight vitals heavily will systematically under-flag this group.

### ICU laboratory values

| Column | Type | Range | Description |
|---|---|---|---|
| `icu_lactate` | float | 0.69–4.87 | ICU blood lactate (mmol/L) |
| `icu_creatinine` | float | 0.45–2.75 | ICU serum creatinine (mg/dL) |
| `icu_wbc` | float | 1.0–18.2 | ICU white blood cell count (×10⁹/L) |
| `icu_bilirubin` | float | 0.39–2.53 | ICU serum bilirubin (mg/dL) |

### Clinical notes — availability flag (MNAR)

Note absence is **Missing Not At Random**: notes are absent for ~31% of patients, concentrated in cardiac (~58%) and vascular (~42%) cases. Patients without notes have **double the complication rate** of those with notes — absence signals severity, not low documentation workload.

| Column | Type | Missing | Description |
|---|---|---|---|
| `has_notes` | int | 0 | 1 if a note was written; 0 otherwise |
| `note_risk_score` | float | 156 / 500 | NLP-derived risk score [0.02, 0.86]; NaN when no note exists |

### Outcomes

| Column | Type | Positive rate | Description |
|---|---|---|---|
| `deteriorated_24h` | int | 40.8% | Binary: clinical deterioration within 24 hours |
| `major_complication_30d` | int | 25.4% | Binary: major complication within 30 days — **primary model target** |

---

## `notes.csv` — Clinical notes text

One row per patient who has a clinical note. 344 of the 500 patients have a note. Join to `tabular.csv` on `patient_id`.

| Column | Type | Description |
|---|---|---|
| `patient_id` | string | Links to `tabular.csv` |
| `note_text` | string | Free-text ICU nursing / clinical note (50–200 words) |

**MNAR reminder:** the 156 patients absent from this file are not a random sample — they are disproportionately cardiac and vascular patients with higher complication rates. A model that treats zero-text as equivalent to a neutral note will systematically under-estimate risk for these patients.

---

## `vitals_series.csv` — Hourly vital signs time series

24 rows per patient (hours 0–23), 12,000 rows total. All values are complete — no missing data. Join to `tabular.csv` on `patient_id`.

| Column | Type | Range | Description |
|---|---|---|---|
| `patient_id` | string | — | Links to `tabular.csv` |
| `hour` | int | 0–23 | ICU observation hour |
| `hr` | float | 40.0–136.1 | Heart rate (bpm) |
| `rr` | float | 8.0–30.1 | Respiratory rate (breaths/min) |
| `spo2` | float | 89.5–100.0 | Oxygen saturation (%) |
| `sbp` | float | 60.0–200.0 | Systolic blood pressure (mmHg) |
| `temp` | float | 35.0–39.1 | Temperature (°C) |
| `lactate` | float | 0.30–6.36 | Blood lactate (mmol/L) |

The hourly series is used by **Model A** to compute temporal features: late-vs-early slope, variability (SD), and direction-of-change for each vital sign. The aggregated 24h summaries in `tabular.csv` (`hr_mean`, `hr_std`, etc.) are derived from this same series.
