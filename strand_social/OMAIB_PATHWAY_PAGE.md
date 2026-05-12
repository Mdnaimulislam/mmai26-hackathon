# Submission Form — Housing Strand

Use **[STRAND_GUIDE.md](STRAND_GUIDE.md)** for the full scenario, track roles, and
workflow. This page is the **one-page submission checklist** for judging.

Fill this in before the judging session. One page maximum.

---

**Team name:**

**Which tracks did you build?**
- [ ] Track A — The Sensor Inspector (dropout and alignment profiler)
- [ ] Track B — The Split Builder (benchmark train/val/test splits)
- [ ] Track C — The Equity Analyst (forecasting fairness by household type)

---

## About your Housing Benchmark Card

| Question | Your answer |
|---|---|
| **Track A — Data quality** | How many households had significant sensor dropout (>20%)? How many had timestamp drift? How many properties have non-conforming `reference` values, blank `Sub-building`, or `avgCo2` outages of 7+ continuous days? |
| **Track B — Benchmark splits** | What split strategy did you use? How did you ensure no household appears in both train and test? How did you stratify across property type, postcode area, and reference type? |
| **Track C — Equity findings** | Which property type does the model under-forecast most? By how much? Is the gap statistically significant? What did the postcode-area and reference-type slices show? Any coverage-equity concern in `avgCo2`? |
| **Benchmark verdict** | Is this dataset fit for purpose as a public benchmark? READY / CONDITIONAL / NOT READY |
| **Most important data problem** | What is the single biggest data quality issue a researcher using this dataset must know about? |
| **Who is most affected?** | If a model trained on this data were deployed, which residents would be most likely to be underserved? |

If CONDITIONAL, list the conditions: (e.g. "Only usable after correcting timestamp drift in 36 households")

---

## AI tools used

AI coding assistants are allowed. Disclose what you used so judges can ask the right questions.

- [ ] GitHub Copilot or Codex
- [ ] Claude or others for code help. If others, provide details: _________
- [ ] LLM API called inside the tool itself (e.g. for generating the equity statement)
- [ ] None

Which parts were AI-assisted? _______

---

## Submission checklist

- [ ] `reference/data_profile.json` — your completed data quality profile (sensor dropout, drift, metadata audits, `avgCo2` outage flags)
- [ ] `reference/benchmark_card.json` — your completed Housing Benchmark Card (`schema`: `omaib-housing-v0.1`), with `dimensions_tested` and `coverage_equity` populated
- [ ] `reference/equity_statement.md` — your plain-English equity statement
- [ ] Notebooks `01_explore_and_audit.ipynb` and `02_equity_and_benchmark.ipynb` run end-to-end without errors on the starter data
- [ ] This form is filled in
- [ ] Code is in a public GitHub repo
- [ ] A licence is declared: CC BY 4.0 or Apache 2.0
