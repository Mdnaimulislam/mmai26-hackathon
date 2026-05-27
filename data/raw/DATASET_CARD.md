# Dataset Card — ICU Multimodal Patient Dataset

## Identity

| Field | Value |
|---|---|
| **File** | `icu_patients.csv` |
| **Patients** | 5,000 synthetic post-surgical ICU patients |
| **Rows** | 5,000 (one per patient) |
| **Columns** | 182 |

---

## Outcomes

| Column | Type | Rate | Description |
|---|---|---|---|
| `deteriorated_24h` | int | **42.0 %** | Primary target — patient deteriorated within 24 h in ICU |
| `major_complication_30d` | int | **30.0 %** | Secondary target — major complication within 30 days post-surgery |

Both outcomes are present for every patient. The strand's primary target is **`deteriorated_24h`**.

---

## Column Groups

### 1. Demographics (cols 1–4)

| Column | Type | NaN | Description |
|---|---|---|---|
| `patient_id` | str | 0 | Unique ID (P0001–P5000) |
| `age` | int | 0 | Age in years (25–92, mean ≈ 63) |
| `sex` | str | 0 | `M` or `F` |
| `sex_enc` | int | 0 | 1 = female, 0 = male |

### 2. Surgical context (cols 5–10)

| Column | Type | NaN | Description |
|---|---|---|---|
| `surgery_type` | str | 0 | `cardiac` (1,033), `vascular` (1,007), `abdominal` (1,727), `orthopaedic` (1,233) |
| `surgery_enc` | int | 0 | Ordinal: cardiac=3, vascular=2, abdominal=1, orthopaedic=0 |
| `admission_urgency` | str | 0 | `elective` (3,835) or `emergency` (1,165) |
| `urgency_enc` | int | 0 | 1 = emergency, 0 = elective |
| `asa_class` | int | 0 | ASA physical status 1–4 (1=400, 2=2,561, 3=1,876, 4=163) |
| `op_duration_h` | float | 0 | Operation duration in hours |

### 3. Intra-operative (cols 11–14)

| Column | Type | NaN | Description |
|---|---|---|---|
| `blood_loss_ml` | float | **1,755 (35.1 %)** | Estimated blood loss (mL). **MNAR** — see below |
| `blood_loss_imputed` | float | 0 | `blood_loss_ml` with training-set mean filled where missing |
| `blood_loss_missing` | int | 0 | 1 = blood loss was not recorded |
| `transfused` | int | 0 | 1 = intra-operative blood transfusion |

### 4. Comorbidities (cols 15–16)

| Column | Type | NaN | Description |
|---|---|---|---|
| `has_diabetes` | int | 0 | 1 = diabetes |
| `has_hypertension` | int | 0 | 1 = hypertension |

### 5. Pre-operative laboratory results (cols 17–19)

| Column | Type | NaN | Description |
|---|---|---|---|
| `preop_creatinine` | float | 0 | Creatinine before surgery (mg/dL) |
| `preop_wbc` | float | 0 | White blood cell count (×10⁹/L) |
| `preop_lactate` | float | 0 | Serum lactate before surgery (mmol/L) |

### 6. ICU admission severity (col 20)

| Column | Type | NaN | Description |
|---|---|---|---|
| `sofa_score` | int | 0 | SOFA score at ICU admission (0–20; higher = more organ failure) |

### 7. Vital signs — 24-hour ICU aggregates (cols 21–28)

Derived from the hourly series (see Section 9). Present as summary statistics for models that do not use the full time series.

| Column | Type | NaN | Description |
|---|---|---|---|
| `hr_mean` | float | 0 | Heart rate 24 h mean (bpm) |
| `hr_std` | float | 0 | Heart rate 24 h standard deviation — instability marker |
| `rr_mean` | float | 0 | Respiratory rate 24 h mean (breaths/min) |
| `rr_std` | float | 0 | Respiratory rate standard deviation |
| `spo2_mean` | float | 0 | Oxygen saturation 24 h mean (%) |
| `spo2_min` | float | 0 | Minimum SpO₂ in the 24 h window — worst-case marker |
| `sbp_mean` | float | 0 | Systolic blood pressure 24 h mean (mmHg) |
| `temp_mean` | float | 0 | Temperature 24 h mean (°C) |

### 8. ICU laboratory results (cols 29–32)

| Column | Type | NaN | Description |
|---|---|---|---|
| `icu_lactate` | float | 0 | Serum lactate at ICU admission (mmol/L) — perfusion failure marker |
| `icu_creatinine` | float | 0 | Creatinine at ICU admission (mg/dL) — AKI marker |
| `icu_wbc` | float | 0 | White blood cell count at ICU admission (×10⁹/L) |
| `icu_bilirubin` | float | 0 | Total bilirubin (mg/dL) — liver function marker |

### 9. Clinical notes (cols 33–35)

| Column | Type | NaN | Description |
|---|---|---|---|
| `has_notes` | int | 0 | 1 = a clinical note exists for this patient |
| `note_risk_score` | float | **1,582 (31.6 %)** | Pre-extracted NLP risk score (0–1). **NaN when `has_notes == 0`** |
| `icu_hours` | int | 0 | Total hours in ICU before step-down or event |

### 10. Outcomes (cols 36–37)

See [Outcomes](#outcomes) above.

### 11. Free-text clinical note (col 38)

| Column | Type | NaN | Description |
|---|---|---|---|
| `note_text` | str | **1,582 (31.6 %)** | Synthetic clinician narrative (100–200 words). NaN when `has_notes == 0` |

Source: `notes.csv`, left-joined on `patient_id`.

### 12. Hourly ICU vitals — pivoted wide (cols 39–182, 144 columns)

Six vitals × 24 hours = 144 columns. Column naming: `{vital}_h{HH}` where HH is zero-padded hour (00–23).

| Vital | Columns | Unit | Description |
|---|---|---|---|
| Heart rate | `hr_h00` – `hr_h23` | bpm | Hourly heart rate |
| Respiratory rate | `rr_h00` – `rr_h23` | breaths/min | Hourly respiratory rate |
| SpO₂ | `spo2_h00` – `spo2_h23` | % | Hourly oxygen saturation |
| Systolic BP | `sbp_h00` – `sbp_h23` | mmHg | Hourly systolic blood pressure |
| Temperature | `temp_h00` – `temp_h23` | °C | Hourly body temperature |
| Lactate | `lactate_h00` – `lactate_h23` | mmol/L | Hourly serum lactate |

No NaN values in any hourly column (all 5,000 patients have complete 24-hour vitals).

Source: `vitals_series.csv` (120,000 rows), pivoted with `pandas.pivot()`.

---

## Missing Data — MNAR Patterns

Two variables have significant non-random missingness. The patterns and rates below are as observed in the data.

### Blood loss MNAR (35.1 % missing)

`blood_loss_ml` is absent when documentation was not completed. Missingness is driven by case complexity:

- Cardiac surgery: highest missing rate (~58 %)
- Vascular surgery: elevated missing rate (~45 %)
- Emergency admissions: elevated relative to elective

A `blood_loss_missing` indicator column (0/1) is provided alongside `blood_loss_imputed` (training-set mean fill).

### Notes MNAR (31.6 % missing)

`note_text` and `note_risk_score` are absent when no clinical note was written. Absence correlates with care-team workload:

- Cardiac emergency cases: most likely to have no notes
- A `has_notes` flag (0/1) is provided; `note_risk_score` is always NaN when `has_notes == 0`

---

## Dataset Verification

```python
import pandas as pd

df = pd.read_csv('data/raw/icu_patients.csv')

assert df.shape == (5000, 182),          f"Expected (5000, 182), got {df.shape}"
assert df['patient_id'].nunique() == 5000
assert abs(df['deteriorated_24h'].mean() - 0.42) < 0.05,  "Deterioration rate out of range"
assert abs(df['major_complication_30d'].mean() - 0.28) < 0.05
assert df['blood_loss_missing'].mean() > 0.30,             "Blood loss MNAR rate too low"
assert df['has_notes'].mean() > 0.60,                      "Notes availability too low"
assert df[['hr_h00','lactate_h23']].isna().sum().sum() == 0, "Hourly vitals have unexpected NaN"
assert df['note_text'].isna().sum() == (df['has_notes'] == 0).sum(), "note_text / has_notes mismatch"

print("Verification passed")
print(f"  Shape           : {df.shape}")
print(f"  deteriorated_24h: {df['deteriorated_24h'].mean():.1%}")
print(f"  complication_30d: {df['major_complication_30d'].mean():.1%}")
print(f"  notes present   : {df['has_notes'].mean():.1%}")
print(f"  blood loss MNAR : {df['blood_loss_missing'].mean():.1%}")
```

---

## Column Index (quick reference)

```
[0]   patient_id
[1]   age
[2]   sex
[3]   sex_enc
[4]   surgery_type
[5]   surgery_enc
[6]   admission_urgency
[7]   urgency_enc
[8]   asa_class
[9]   op_duration_h
[10]  blood_loss_ml          ← MNAR (35.7 % NaN)
[11]  blood_loss_imputed
[12]  blood_loss_missing
[13]  transfused
[14]  has_diabetes
[15]  has_hypertension
[16]  preop_creatinine
[17]  preop_wbc
[18]  preop_lactate
[19]  sofa_score
[20]  hr_mean
[21]  hr_std
[22]  rr_mean
[23]  rr_std
[24]  spo2_mean
[25]  spo2_min
[26]  sbp_mean
[27]  temp_mean
[28]  icu_lactate
[29]  icu_creatinine
[30]  icu_wbc
[31]  icu_bilirubin
[32]  has_notes
[33]  note_risk_score        ← MNAR (31.6 % NaN, always NaN when has_notes == 0)
[34]  icu_hours
[35]  deteriorated_24h       ← PRIMARY TARGET (42.3 %)
[36]  major_complication_30d ← SECONDARY TARGET (28.2 %)
[37]  note_text              ← free text, NaN when has_notes == 0
[38–61]   hr_h00 – hr_h23
[62–85]   rr_h00 – rr_h23
[86–109]  spo2_h00 – spo2_h23
[110–133] sbp_h00 – sbp_h23
[134–157] temp_h00 – temp_h23
[158–181] lactate_h00 – lactate_h23
```
