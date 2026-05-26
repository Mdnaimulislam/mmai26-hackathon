# Data — Clinical Strand

## Overview

| | |
|---|---|
| **Patients** | 2,000 synthetic post-surgical ICU patients |
| **Primary file** | `raw/icu_patients.csv` — 2,000 rows × 182 columns |
| **Primary outcome** | `deteriorated_24h` — 1 = ICU deterioration within 24 h (42.3 %) |
| **Secondary outcome** | `major_complication_30d` — 1 = major complication within 30 days (28.2 %) |
| **Modalities** | Tabular (37 cols) + free-text clinical notes + 24-hour hourly vitals series |
| **Full column reference** | `raw/DATASET_CARD.md` |

---

## File structure

```
data/
└── raw/
    ├── icu_patients.csv   ← PRIMARY FILE (2,000 × 182, use this)
    └── DATASET_CARD.md               ← full column dictionary + verification code
```
---

## Quick-start

```python
import pandas as pd

df = pd.read_csv('data/raw/icu_patients.csv')

# Verify load
assert df.shape == (2000, 182)
print(df['deteriorated_24h'].mean())      # 0.423
print(df['has_notes'].mean())             # 0.684
print(df['blood_loss_missing'].mean())    # 0.357

# Tabular features (first 37 columns, no time series)
tabular = df.iloc[:, :37]

# Hourly vitals as 3-D array: shape (2000, 24, 6)
import numpy as np
vitals_order = ['hr', 'rr', 'spo2', 'sbp', 'temp', 'lactate']
vitals_wide  = df[[f'{v}_h{h:02d}' for v in vitals_order for h in range(24)]]
vitals_3d    = vitals_wide.values.reshape(2000, 6, 24).transpose(0, 2, 1)
```

---

## Column groups at a glance

| Group | Columns | Key notes |
|---|---|---|
| Demographics | `patient_id`, `age`, `sex`, `sex_enc` | Age 25–92, mean 63 |
| Surgical context | `surgery_type`, `surgery_enc`, `admission_urgency`, `urgency_enc`, `asa_class`, `op_duration_h` | 4 surgery types; 22.8 % emergency |
| Intra-operative | `blood_loss_ml`, `blood_loss_imputed`, `blood_loss_missing`, `transfused` | **MNAR 35.7 %** |
| Comorbidities | `has_diabetes`, `has_hypertension` | — |
| Pre-op labs | `preop_creatinine`, `preop_wbc`, `preop_lactate` | — |
| ICU severity | `sofa_score` | 0–20 |
| Vitals aggregates | `hr_mean`, `hr_std`, `rr_mean`, `rr_std`, `spo2_mean`, `spo2_min`, `sbp_mean`, `temp_mean` | Derived from hourly series |
| ICU labs | `icu_lactate`, `icu_creatinine`, `icu_wbc`, `icu_bilirubin` | Admission values |
| Clinical notes | `has_notes`, `note_risk_score`, `icu_hours` | **`note_risk_score` MNAR 31.6 %** |
| Outcomes | `deteriorated_24h`, `major_complication_30d` | Dual targets |
| Note text | `note_text` | NaN when `has_notes == 0` |
| Hourly vitals | `hr_h00`–`lactate_h23` | 24 h × 6 vitals = 144 columns, no NaN |

See `raw/DATASET_CARD.md` for the full column dictionary with types, NaN counts, and units.

---

## Key data characteristics to investigate

### 1 — Blood loss is Missing Not At Random (MNAR)

`blood_loss_ml` is `NaN` for **35.7 %** of patients. Missingness correlates with surgical risk, not recording convenience:

| Surgery type | Missing rate |
|---|---|
| Cardiac | 57.8 % |
| Vascular | 46.2 % |
| Abdominal | 25.4 % |
| Orthopaedic | 22.9 % |

Investigate how the missingness pattern relates to patient risk and whether your imputation strategy affects model performance for these subgroups.

### 2 — Clinical notes are Missing Not At Random (MNAR)

`note_risk_score` and `note_text` are `NaN` for **31.6 %** of patients. Note absence is driven by workload and case complexity, not by patient stability:

| Surgery type | Notes absent |
|---|---|
| Cardiac | 60.8 % |
| Vascular | 48.4 % |
| Abdominal | 17.6 % |
| Orthopaedic | 12.6 % |

Investigate how the absence pattern relates to patient acuity and whether your handling of missing `note_risk_score` values affects model performance in the `has_notes == 0` subgroup.

### 3 — Vascular patients: vital sign profile

Vascular surgery patients tend to receive tight post-operative haemodynamic management. Their ICU vital signs cluster differently from other surgery types:

| | Vascular | All others |
|---|---|---|
| `hr_mean` | 70.0 bpm | 80.5 bpm |
| `sbp_mean` | 130.1 mmHg | 122.1 mmHg |
| `icu_lactate` | 0.94 mmol/L | 2.48 mmol/L |

Examine whether this vital sign profile affects model performance for vascular patients relative to other surgery types.

### 4 — Temporal trends in hourly vitals

The hourly lactate trajectory (columns `lactate_h00`–`lactate_h23`) may carry different predictive signal than the 24-hour aggregate alone. If your team uses the hourly series, consider what temporal features best capture deterioration patterns.

### 5 — Age and silent deterioration

Mean age ≈ 62.6 years (SD 13.7). About **19.3 %** of patients are aged 75+.

| Age band | n | Deterioration rate |
|---|---|---|
| Under 65 | 1,147 | 35.8 % |
| 65–74 | 511 | 47.6 % |
| 75+ | 342 | 56.1 % |

Elderly patients deteriorate without alarming vital signs (blunted tachycardia in patients on beta-blockers). Subgroup analysis by age band is a required deliverable for the Evidence Dashboard.

### 6 — Deterioration prevalence by subgroup

Overall deterioration rate is **42.3 %**.

| Subgroup | Deterioration rate |
|---|---|
| Cardiac surgery | 74.8 % |
| Emergency admissions | 69.1 % |
| Vascular surgery | 42.4 % |
| Abdominal surgery | 36.6 % |
| Elective admissions | 34.4 % |
| Orthopaedic surgery | 23.3 % |

These gaps suggest that aggregate performance metrics alone may not capture how the model performs across different patient groups.
