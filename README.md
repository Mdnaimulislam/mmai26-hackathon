# Housing Strand — Quick Start

**MultimodalAI'26 Hackathon · Can you trust a dataset used for housing decisions?**

---

## Setup

```bash
pip install -r requirements.txt
```

> **Do not use Google Colab.** The Streamlit app reads saved models and processed data from your local `saved_models/` and `data/processed/` directories. Run everything locally in VS Code with the Jupyter extension or JupyterLab.

---

## Create your team branch immediately after cloning

```bash
git checkout -b your-team-name
```

All your work goes on your team branch. **Do not commit directly to the housing branch.**

---

## Three phases — all tracks active from minute zero

| | Phase 1 — Build (60 min) | Phase 2 — Train (45 min) | Phase 3 — Evaluate & Report (90 min) |
|---|---|---|---|
| **Sensor Inspector** | `00_sensor_audit.ipynb` | Verify Tab 1 | Tab 5 — Benchmark Card |
| **Split Builder** | `01_split_and_features.ipynb` | **Run `02_train_models.ipynb`** (train all 3 models) | Tabs 1–2 + Tab 5 |
| **Equity Analyst** | Implement `model_b.py` + `model_c.py` + `evaluate.py` | Review training outputs | Tabs 3–4 + Tab 5 |

**Phase 1 is fully parallel** — all three tracks start immediately and have no dependencies on each other.
**Phase 2 is the handoff** — Equity Analyst's model implementations + Split Builder's splits → training runs.
**Phase 3 is the app** — all three tracks converge at Tab 5 to produce the Housing Benchmark Card.

Read `STRAND_GUIDE.md` for the full task description, design briefs, and track roles.

---

## What you implement

| File | Task | Phase | Track |
|---|---|---|---|
| `models/model_b.py` | Seasonal Logistic Regression — encoding and feature choices | 1 | Equity Analyst |
| `models/model_c.py` | CO₂-dependent LR — MNAR strategy choice | 1 | Equity Analyst |
| `src/evaluate.py` | Classification metrics, subgroup analysis, equity gap | 1 | Equity Analyst |

`models/model_a.py` is provided complete. Do not modify it.

---

## Launch the evaluation app

After running both notebooks:

```bash
streamlit run app.py
```

---

## Submit

```bash
git add .
git commit -m "Team <your-team-name>: Housing Strand final submission"
git push origin your-team-name
```

Then open a Pull Request: `your-team-name` → `housing`

**Submission window: 18:00–23:59 on 10 June.**
