# Can we trust this data to choose which homes get a boiler upgrade?

**One-page summary for a housing officer or council committee — no technical background needed.**
**Team SCA-dream-soultion · Housing Strand**

---

## What we were asked

The council has two years of daily sensor readings (temperature, humidity, CO₂, energy, noise)
from **250 social-housing properties** and wants to decide which homes get a boiler upgrade this
winter. Our job was not to build the cleverest model — it was to answer one question honestly:
**is this data safe to use for that decision, and where is it not?**

## What we built

A single web tool — the **Cold-Home Triage & Dataset Trust Auditor** — that does three things and
is honest about its own limits:

1. **Ranks every property** by cold-risk for the winter upgrade budget.
2. **Audits the sensor data** behind that ranking and flags properties where the sensors have failed.
3. **Checks the ranking is fair** across different property types.

## The four things the data told us

| Finding | What it means for the upgrade decision |
|---|---|
| **CO₂ sensors have failed in 40 of 250 homes** (missing 70–95% of the time) | These homes have an *equipment* problem. Good news: we tested it and the CO₂ readings add almost nothing to predicting cold homes — so the broken sensors do **not** secretly bias the ranking. They should still be repaired so future audits are complete. |
| **"Yesterday's temperature" is a trap** | A model that uses yesterday's indoor temperature *looks* far more accurate (it jumps from 84% to 93%), but that is cheating — it is almost the answer in disguise. We removed it. Our reported accuracy is the **honest** number. |
| **Flats are harder to assess** | The model is much more reliable for houses than for flats. Flats are genuinely warmer (only ~10% of flat-days are cold, vs ~37% for houses) because they share walls and hold heat. **Recommendation: rank flats against flats, houses against houses — not all on one list.** |
| **The single ranked list naturally favours houses** | That is *correct*, not biased — houses really are colder. But if the council wants the coldest homes of *every* type reached, a "fair" within-type split adds **14 flats** the single list would skip. This is a policy choice for the council to make on purpose. |

## Our verdict: **CONDITIONAL — safe to use, with three conditions**

The data **can** support the winter upgrade ranking, provided:

1. **Use the sensor-robust model** (the honest one), not the version that leans on yesterday's
   temperature.
2. **Rank within property type** (flats vs flats), because the model is weaker for flats.
3. **Repair the 40 broken CO₂ sensors** as a maintenance task, and re-check the data after one
   heating season.

## Why this matters for residents

A missed cold home is not a rounding error — it is a household left below the WHO's 19 °C minimum
for another winter, which is a real health risk for elderly and vulnerable residents. Our tool is
built to be **honest about which homes it can and cannot confidently rank**, so the budget reaches
the people who need it most.

---
*Full evidence: `reference/housing_benchmark_card.json` · live tool: `streamlit run app.py`*
