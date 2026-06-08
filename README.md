# Clinical Strand — Can You Trust an AI in the ICU?

**MultimodalAI'26 Hackathon · 10 June 2026**

> **New to clinical AI? That's fine — that's the point.**
> Read **[STRAND_GUIDE.md](STRAND_GUIDE.md)** for the full task description, dataset overview, track roles, and judging criteria. If you are short on time, start with Section 10 (Your First 30 Minutes).

---

## What This Strand Is About

Each team builds a solution grounded in the ICU dataset and produces a structured set of evidence deliverables that a hospital safety committee could act on. The problem is defined, the dataset is provided, the output templates are given to you — **you fill them in based on what you find.**

---

## What Is in This Repository

```
clinical/
├── README.md               ← you are here
├── STRAND_GUIDE.md         ← full task description, dataset, roles, judging criteria
├── validate_submission.py  ← pre-commit validator for submission JSON files
├── .pre-commit-config.yaml ← pre-commit hook configuration
├── data/
│   └── raw/
│       ├── icu_patients.csv        — 5,000 patients, 182 columns (primary dataset)
│       └── DATASET_CARD.md         — full column reference and missingness guide
├── reference/
│   ├── omaib_pathway.json          — submission template: model evidence card (item B)
│   └── model_safety_report.json    — submission template: safety report (item C)
└── demo/                   ← reference implementation (optional walkthrough)
```

> The **demo/** folder is a guided reference walkthrough using a smaller synthetic dataset. It is not your submission — it shows one possible implementation. Your team builds from `data/raw/icu_patients.csv`.

---

## Quick Start

```bash
# Clone this branch only
git clone --branch clinical --single-branch https://github.com/omaib/mmai26-hackathon
cd mmai26-hackathon

# Create your team branch immediately — all your work goes here
git checkout -b your-team-name

# Install dependencies
pip install -r demo/requirements.txt

# Optional: explore the reference demo
cd demo
streamlit run app.py
```

> Use the demo to understand the expected workflow and evidence standards. When you are ready, work directly from `data/raw/icu_patients.csv` and fill in the templates in `reference/`.

---

## The Dataset

`data/raw/icu_patients.csv` — **5,000 synthetic post-surgical ICU patients, 182 columns.**

Primary outcome: `deteriorated_24h` (~42% positive). Secondary: `major_complication_30d` (~28%).

| Modality | Key columns | Notes |
|---|---|---|
| Demographics & surgical context | `age`, `sex`, `surgery_type`, `admission_urgency`, `asa_class` | |
| Intra-operative | `blood_loss_ml`, `transfused` | Blood loss MNAR (~36% missing) |
| ICU severity | `sofa_score` | 0–20 scale |
| Vital signs (24 h aggregates) | `hr_mean`, `rr_mean`, `spo2_mean`, `sbp_mean`, `temp_mean` | 8 summary features |
| ICU labs | `icu_lactate`, `icu_creatinine`, `icu_wbc`, `icu_bilirubin` | At admission |
| Clinical notes (NLP) | `has_notes`, `note_risk_score`, `note_text` | MNAR: ~32% of patients have no note |
| Hourly vitals | `hr_h00`–`hr_h23`, … `lactate_h00`–`lactate_h23` | 6 vitals × 24 hours = 144 columns |

Full column reference with missingness details: `data/raw/DATASET_CARD.md`.

```python
import pandas as pd
df = pd.read_csv('data/raw/icu_patients.csv')
print(df.shape)                              # expect (5000, 182)
print(df['deteriorated_24h'].mean())         # expect ~0.42
print(df['note_risk_score'].isna().mean())   # expect ~0.32 (MNAR)
print(df['blood_loss_missing'].mean())       # expect ~0.36 (MNAR)
```

---

## What You Submit

| Item | File | Description |
|---|---|---|
| **A** | *(your repo)* | Runnable solution — any tool, any stack |
| **B** | `reference/omaib_pathway.json` | Model evidence card — verdicts and metrics per model |
| **C** | `reference/model_safety_report.json` | Full safety report — narratives, subgroup analysis, deployment questions |
| **D** | *(your repo)* | Evidence Dashboard — five analytical views |
| **E** | *(embedded in C)* | Option-specific findings (`option_specific` section) |

Templates for B and C are provided in `reference/` — fill in the verdict, narrative, metrics, and deployment question fields based on your own evaluation. A pre-commit validator checks these files automatically.

---

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
# Hooks run automatically on every commit.
# To run manually before committing:
pre-commit run --all-files
```

The validator checks that `reference/omaib_pathway.json` and `reference/model_safety_report.json` have no empty required fields. Fix any errors before opening your PR.

---

## How to Submit

```bash
git add .
git commit -m "Team <your-team-name>: final clinical strand submission"
git push origin your-team-name
```

Then open a Pull Request on GitHub: `your-team-name → clinical`
Title: `"Team <your-team-name> — Clinical Strand Submission"`

**Final submission deadline: before 09:30 on 11 June.** Do not push directly to the `clinical` branch.

---

## Support

| Need | Who to ask |
|---|---|
| Clinical context or dataset questions | Problem holders (present throughout the day) |
| JSON templates or validator | Technical support desk |
| Scoping your challenge | Problem holders |

> **You are not expected to know everything going in. Ask early, ask often.**

