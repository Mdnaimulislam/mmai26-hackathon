"""Generate synthetic ICU patient dataset for the Clinical Strand.
Run once: python data/raw/generate_data.py
Produces: data/raw/icu_patients.csv  (500 patients, one row per patient)
"""
import numpy as np
import pandas as pd
from pathlib import Path


def generate(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.RandomState(seed)

    # ── Demographics ─────────────────────────────────────────────────────────
    age = rng.normal(65, 15, n).clip(18, 95).astype(int)
    sex = rng.choice(["M", "F"], n)
    admission_type = rng.choice(
        ["medical", "surgical", "trauma"], n, p=[0.60, 0.30, 0.10]
    )

    # ── Severity ──────────────────────────────────────────────────────────────
    sofa = rng.poisson(6, n).clip(0, 20).astype(int)

    # ── Vital signs (24-hour aggregates) ─────────────────────────────────────
    hr_mean  = rng.normal(90, 20, n).clip(40, 180).round(1)
    hr_std   = rng.exponential(10, n).clip(1, 50).round(1)
    rr_mean  = rng.normal(18, 5, n).clip(8, 40).round(1)
    rr_std   = rng.exponential(3, n).clip(0.5, 15).round(1)
    spo2_mean = rng.normal(96, 3, n).clip(70, 100).round(1)
    spo2_min  = (spo2_mean - rng.exponential(2, n)).clip(70, 100).round(1)
    sbp_mean = rng.normal(115, 20, n).clip(60, 200).round(1)
    temp_mean = rng.normal(37.2, 0.8, n).clip(35.0, 40.5).round(2)

    # ── Laboratory results ────────────────────────────────────────────────────
    lactate    = rng.exponential(1.5, n).clip(0.5, 15).round(2)
    creatinine = rng.exponential(1.2, n).clip(0.4, 15).round(2)
    wbc        = rng.normal(11, 5, n).clip(1, 30).round(1)
    bilirubin  = rng.exponential(1.0, n).clip(0.2, 20).round(2)

    # ── Clinical notes ────────────────────────────────────────────────────────
    # 30 % of patients have no notes (not random — surgical patients respond less)
    note_prob = np.where(admission_type == "surgical", 0.55, 0.75)
    has_notes = (rng.uniform(0, 1, n) < note_prob).astype(int)
    raw_note_risk = rng.uniform(0, 1, n)
    note_risk_score = np.where(has_notes, raw_note_risk, np.nan)

    # ── Ground truth: latent risk → deterioration label ──────────────────────
    risk = (
        (sofa / 20) * 0.30
        + ((100 - spo2_mean) / 30).clip(0, 1) * 0.20
        + (lactate.clip(0, 8) / 8) * 0.25
        + ((age - 18) / 77) * 0.10
        + rng.uniform(0, 1, n) * 0.15
    )
    # Notes contribute when available
    risk = np.where(has_notes, risk * 0.70 + raw_note_risk * 0.30, risk)
    risk = (risk - risk.min()) / (risk.max() - risk.min())

    # ~34 % deterioration rate (top tertile)
    deteriorated = (risk > np.percentile(risk, 66)).astype(int)

    df = pd.DataFrame(
        {
            "patient_id":       [f"P{i:04d}" for i in range(1, n + 1)],
            "age":              age,
            "sex":              sex,
            "admission_type":   admission_type,
            "sofa_score":       sofa,
            "hr_mean":          hr_mean,
            "hr_std":           hr_std,
            "rr_mean":          rr_mean,
            "rr_std":           rr_std,
            "spo2_mean":        spo2_mean,
            "spo2_min":         spo2_min,
            "sbp_mean":         sbp_mean,
            "temp_mean":        temp_mean,
            "lactate":          lactate,
            "creatinine":       creatinine,
            "wbc":              wbc,
            "bilirubin":        bilirubin,
            "has_notes":        has_notes,
            "note_risk_score":  note_risk_score,
            "deteriorated":     deteriorated,
        }
    )
    return df


if __name__ == "__main__":
    out = Path(__file__).parent
    df = generate()
    df.to_csv(out / "icu_patients.csv", index=False)
    print(f"Saved {len(df)} patients to icu_patients.csv")
    print(f"  Deterioration rate : {df['deteriorated'].mean():.1%}")
    print(f"  Notes available    : {df['has_notes'].mean():.1%}")
    print(f"  Age  mean / std    : {df['age'].mean():.1f} / {df['age'].std():.1f}")
