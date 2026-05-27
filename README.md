# Housing Strand — Can You Trust a Dataset Used for Housing Decisions?

**MultimodalAI'26 Hackathon · 10 June 2026**

---

## Read this first

Read **[STRAND_GUIDE.md](STRAND_GUIDE.md)** for the full challenge brief, track roles, design questions, and what your team must produce.

---

## What is provided

| Path | Contents |
|---|---|
| `data/raw/housing_properties_daily.csv` | Sensor readings and property metadata for 120 properties over 730 days |
| `reference/omaib_pathway.json` | Housing manifest template — fill in your team's models and verdicts |
| `reference/housing_benchmark_card.json` | Full Housing Benchmark Card template |
| `validate_submission.py` | Pre-submission validator — run before committing your JSON files |

---

## Create your team branch immediately after cloning

```bash
git checkout -b your-team-name
```

All your work goes on your team branch. **Do not commit directly to the housing branch.**

---

## Setup

Install the packages your team's models require. At minimum:

```bash
pip install pandas scikit-learn matplotlib seaborn
```

---

## Validate your submission before committing

```bash
python validate_submission.py
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
