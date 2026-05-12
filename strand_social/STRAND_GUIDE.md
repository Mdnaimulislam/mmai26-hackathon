# MultimodalAI'26 Hackathon

## Housing Strand Guide — Is This Dataset Good Enough to Benchmark?

---

## 1. The scenario

Social landlords are rolling out smart metering, indoor environment sensors, and
resident surveys to understand energy vulnerability. A council has exported
**120 households** of readings—hourly smart‑meter kWh, temperatures, CO₂, noise,
and survey fields—plus property identifiers (`reference`, `Sub-building`,
`address`, `postcode`) and a layer of **daily environmental aggregates**
broadcast across hours.

That export is **not** audit-ready. Sensors drop out, timestamps drift, survey
response is sparse, references mix structured IDs with free text, sub-building
labels are missing, and **daily CO₂** has long outages—sometimes unevenly across
housing archetypes.

A **household-type mean** baseline forecast has already been run (`forecast_model`
in `housing_with_forecasts.csv`). It is good on average—and **systematically
wrong for some groups**. Before anyone publishes this package as a national
benchmark, your team answers one question:

**Is this dataset (and frozen baseline) fit to build a public benchmark on—or
only under clear conditions?**

---

## 2. Your role on the day

You are a **data governance bench** preparing a release decision—not a modelling
competition entry. Three tracks map to hackathon roles:

| Track | Role | Focus |
|---|---|---|
| **A — Sensor Inspector** | Data quality | Dropout, drift, metadata normalisation, CO₂ outage patterns |
| **B — Split Builder** | Benchmark design | Leakage-safe household splits; stratify by property type, postcode area, reference style |
| **C — Equity Analyst** | Fairness of the given baseline | Who is under/over-forecast; statistical tests; coverage equity |

Tracks A and B can run in parallel in Phase 2; Part 2 (notebook `02_equity_and_benchmark.ipynb`) is where
everyone aligns on the single **`benchmark_card.json`**.

---

## 3. What you must read first

1. This guide (you are here).
2. **[README.md](README.md)** — quick start, directory layout, deliverables.
3. **[data/README.md](data/README.md)** — column dictionary and known flaws.

---

## 4. What you implement

**Notebooks (primary path)**

- **`notebooks/01_explore_and_audit.ipynb`** — Phases 1–2: exploration, Track A profile (`compute_data_profile`), Track B split starter.
- **`notebooks/02_equity_and_benchmark.ipynb`** — Phase 3: MAE/RMSE/MBE, subgroup and coverage-equity analyses, benchmark card builder.

**Optional code**

- **`src/evaluate.py`** — Helpers for MAE/RMSE/MBE and missing rates; extend or ignore.
- **`src/report.py`** — Turn a completed card dict into a simple HTML report.
- **`app.py`** — Optional UI: baseline error table + JSON card preview.

There is **no** requirement to modify `app.py` or `src/*` to finish the challenge.

---

## 5. Deliverables (judges’ checklist)

Complete before demos. Details also on **[OMAIB_PATHWAY_PAGE.md](OMAIB_PATHWAY_PAGE.md)**.

| File | Purpose |
|---|---|
| `reference/data_profile.json` | Machine-readable quality audit |
| `reference/benchmark_card.json` | Verdict **READY / CONDITIONAL / NOT READY**, limitations, equity dimensions |
| `reference/equity_statement.md` | Plain language for non-technical stakeholders |

Optional: `saved_metrics/audit_metrics.csv`, `reference/Data_Quality_Report.html`.

---

## 6. Judging lens

- **Evidence:** numbers and examples—e.g. how many households exceed dropout thresholds, how long CO₂ gaps run, size of MBE gaps.
- **Clarity:** a policy officer should grasp who is harmed from your equity statement alone.
- **Integrity:** the card’s verdict must follow from the quantified limitations.

---

## 7. AI tools

Coding assistants and LLMs **are allowed**. Disclose tools and where you used
them on the submission form. Use them for drafting narrative—not for inventing
numbers you did not compute.

---

## 8. Licence and submission

Use a public GitHub repo, declare **CC BY 4.0** or **Apache 2.0**, and upload the
`reference/` artefacts plus the completed **[OMAIB_PATHWAY_PAGE.md](OMAIB_PATHWAY_PAGE.md)** checklist.

---

## 9. Support

**omaib-ukomain-group@sheffield.ac.uk**
