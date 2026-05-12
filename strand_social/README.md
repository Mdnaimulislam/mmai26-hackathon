# Housing Strand — Is This Data Good Enough to Benchmark?

**MultimodalAI'26 Hackathon · 10 June 2026**

**Challenge:** A social-housing sensor export and a frozen baseline forecast are in
place. Your team decides whether this package is **READY / CONDITIONAL / NOT READY**
to publish as a public benchmark—after profiling data quality, designing safe splits,
and testing equity across households.

> Read **[STRAND_GUIDE.md](STRAND_GUIDE.md)** first if you are new to dataset
> readiness audits, social-housing data, or multi-person hackathon workflows.

---

## What this strand covers

Your task is to judge whether the **dataset (and the given baseline forecast) are
trustworthy enough** to benchmark against. Forecasts are **precomputed** in
`housing_with_forecasts.csv`. The `models/` folder documents scope—there is **no**
participant training loop in this repo.

---

## Quick start

```bash
pip install -r requirements.txt

# Step 1 — Phases 1–2 (tracks A, B, C starter + data profile)
jupyter notebook notebooks/01_explore_and_audit.ipynb
# If `jupyter` is not on PATH, use:  python -m notebook notebooks/01_explore_and_audit.ipynb

# Step 2 — Phase 3 (equity + Housing Benchmark Card)
jupyter notebook notebooks/02_equity_and_benchmark.ipynb

# Step 3 (optional) — launch the lightweight companion app
streamlit run app.py
# If `streamlit` is not on PATH:  python -m streamlit run app.py
```

**Headless check (runs both notebooks top-to-bottom, no browser):**

```bash
python scripts/validate_notebooks.py
```

Or manually:

```bash
python -m nbconvert --to notebook --execute notebooks/01_explore_and_audit.ipynb --inplace
python -m nbconvert --to notebook --execute notebooks/02_equity_and_benchmark.ipynb --inplace
```

(On Windows you may see a harmless `zmq` / event-loop `RuntimeWarning`; the run should still succeed.)

Works in **Google Colab** as well—upload `data/raw/*.csv` or mount the repo.

---

## What you build

| File / artefact | What you produce |
|---|---|
| `reference/data_profile.json` | Structured data quality profile (Track A) |
| `data/processed/*.csv` (optional) | Train/val/test splits without household leakage (Track B) |
| `reference/benchmark_card.json` | Housing Benchmark Card — JSON verdict (schema `omaib-housing-v0.1`) |
| `reference/equity_statement.md` | Three short paragraphs for policy readers |
| `saved_metrics/audit_metrics.csv` (optional) | Flat export of headline audit numbers |

Use **`src/evaluate.py`** helpers if you want the same error summaries as the
optional Streamlit app; extend with your own functions as needed.

---

## What is already provided

| File | Status |
|---|---|
| `data/raw/housing_synthetic_120hh.csv` | Main synthetic export (~90 days of hourly rows per household) |
| `data/raw/housing_with_forecasts.csv` | Same data + naive and baseline forecasts |
| `data/raw/data_profile_stub.json` | Starter schema for your profile |
| `data/raw/generate_data.py` | INTERNAL — confirms frozen files are present |
| `notebooks/01_explore_and_audit.ipynb` | Guided Phases 1–2 |
| `notebooks/02_equity_and_benchmark.ipynb` | Phase 3 equity + card builder |
| `app.py` | Optional Streamlit preview (forecast table + card viewer) |
| `src/report.py` | Optional HTML preview from a completed card |

---

## Final deliverables (`reference/`)

| File | What it is |
|---|---|
| `data_profile.json` | Machine-readable data quality audit |
| `benchmark_card.json` | OMAIB-style housing card — **judges check this first** |
| `equity_statement.md` | Plain-English equity narrative |

You may also export **`Data_Quality_Report.html`** via the notebook or
`src/report.write_data_quality_report()` for a simple HTML wrap of the card.

---

## Judging criteria

| Criterion | What judges look for |
|---|---|
| **Evidence quality** | Quantified gaps — dropout, drift, metadata, coverage equity—not vague claims |
| **Social clarity** | Could a housing policy officer act on your equity statement? |
| **Deployability** | Does the benchmark card match the evidence (verdict, limitations, `dimensions_tested`)? |

---

## Directory structure

```
housing_strand/
  data/
    raw/
      housing_synthetic_120hh.csv   main time series + metadata
      housing_with_forecasts.csv     + baseline forecasts (Phase 3)
      data_profile_stub.json         starter for Track A JSON
      generate_data.py               INTERNAL — not required for participants
    processed/                      Track B split CSVs (you create)
    README.md
  models/                           scope note — no trainable models in this strand
  notebooks/
    01_explore_and_audit.ipynb      Phases 1–2
    02_equity_and_benchmark.ipynb   Phase 3
  saved_models/                     unused placeholder
  saved_metrics/                    optional CSV exports
  src/
    evaluate.py                     audit / error helpers (provided, extensible)
    report.py                       optional HTML from benchmark JSON
  reference/                        FINAL OUTPUTS — judges look here
  scripts/
    validate_notebooks.py           schema check + optional --execute smoke test
  app.py                            optional Streamlit companion
  STRAND_GUIDE.md                   long-form participant guide
  OMAIB_PATHWAY_PAGE.md             one-page submission checklist
  requirements.txt
```

---

## Contact

**omaib-ukomain-group@sheffield.ac.uk**

Submission checklist and AI disclosure: **[OMAIB_PATHWAY_PAGE.md](OMAIB_PATHWAY_PAGE.md)**.
