# Data Guide — Housing Strand

Two starter CSV files live in **`data/raw/`**. Here is what each file is and why it exists.

---

## The scenario

A local housing council has deployed smart sensors across 120 social housing properties to monitor energy use, indoor conditions, and resident comfort. The goal is to build an AI forecasting model that helps identify households at risk of fuel poverty.

But the data is messy — as real sensor deployments always are. Some households have unreliable sensors. Some timestamps are wrong. Some residents never completed the comfort survey. Property records mix structured system IDs with free-text addresses. Before this data can be used to train a model, someone needs to profile it, flag the problems, and decide whether it is trustworthy enough to benchmark against.

---

## File 1 — `data/raw/housing_synthetic_120hh.csv`
**~259,200 rows — one row per household per hour (120 households × ~2,160 hours)**

### Property identity and address

| Column | What it is | Missing? |
|---|---|---|
| `household_id` | Internal household identifier, `HH-0001` to `HH-0120` | Never |
| `reference` | Property reference as held by the housing system — mix of structured system IDs (e.g. `U217012`), free-text address entries (e.g. `3 doveberry place`), and a small number of malformed / missing values | Rarely blank |
| `Sub-building` | Sub-building / flat identifier (e.g. `Flat A`, `Unit 12B`) | Sometimes blank |
| `address` | Property address — free-text, formatting varies | Never |
| `postcode` | UK-style postcode | Never |
| `property_type` | `flat`, `terraced`, or `semi-detached` | Never |
| `bedrooms` | Number of bedrooms (1–4) | Never |
| `n_residents` | Number of residents (1–4) | Never |

### Timing

| Column | What it is | Missing? |
|---|---|---|
| `timestamp_recorded` | Timestamp as recorded by the sensor system | Never |
| `timestamp_actual` | True timestamp (ground truth) | Never |
| `has_timestamp_drift` | 1 if recorded and actual timestamps disagree | Never |
| `year`, `month`, `day` | Calendar date split out from `timestamp_actual` | Never |

### Hourly sensor readings

| Column | What it is | Missing? |
|---|---|---|
| `smart_meter_kwh` | Energy consumption (kWh) — small random dropout | ~2.6% |
| `indoor_temp_c` | Indoor temperature (°C) — more unreliable per household | ~6.5% |
| `co2_ppm` | CO₂ concentration (ppm) — variable dropout | ~9% |
| `noise_db` | Acoustic noise level (dB) — privacy-preserving summary | ~14% |
| `outdoor_temp_c` | Outdoor temperature from weather station | Never |
| `survey_thermal_comfort` | Resident comfort score 1–5 — only 2 per household, 25% non-response | ~98% |

### Daily-averaged environmental readings

These are aggregated to the day, then attached to every hourly row of that day (same value repeats across the 24 hours).

| Column | What it is | Missing? |
|---|---|---|
| `avgTemperature` | Daily mean indoor temperature (°C) | Low |
| `avgHumidity` | Daily mean indoor relative humidity (%) | Low |
| `avgCo2` | Daily mean CO₂ (ppm) — sensor outages produce whole-day gaps | ~24% |

### Deliberate flaws built into this dataset

- Sensor dropout rates vary per household — some are far worse than average
- Timestamp drift affects ~30% of households — recorded time differs from actual time
- Survey non-response is not random — certain property types respond less
- Some households have long continuous gaps in `avgCo2` (sensor offline for days)
- `reference` is inconsistent — some properties carry a structured ID, others a free-text address; normalisation is required before joining external records
- `Sub-building` is missing for a meaningful fraction of properties
- `address` formatting is inconsistent — leading/trailing whitespace, mixed case, comma or no comma, occasional missing city

**17% of England's social housing residents live in flats.** Flats tend to be in higher-deprivation areas. If the forecasting model performs worse for flats, the residents most likely to be in fuel poverty are also the least well served.

---

## File 2 — `data/raw/housing_with_forecasts.csv`
**Subset of the main dataset with two forecasting models already run**

Same columns as above, plus:

| Column | What it is |
|---|---|
| `hour_of_day` | Hour extracted from timestamp (0–23) |
| `forecast_naive_24h` | Naive baseline: today's kWh = yesterday's kWh at the same hour |
| `naive_error` | Actual minus naive forecast |
| `forecast_model` | Household-type mean model forecast |
| `model_error` | Actual minus model forecast |

**The model's known flaw:** it was trained predominantly on terraced and semi-detached houses. Flats have a systematically different energy usage pattern — the model under-forecasts their demand by approximately 28%.

This is the equity problem your team needs to quantify and report.

---

## Want to go further after the hackathon?

| Dataset | Access | Notes |
|---|---|---|
| Smart Home with Weather (Kaggle) | Open | Similar sensor modalities, good for prototyping |
| IDEAL UK Household Energy Dataset | Free after registration (DOI: 10.1038/s41597-021-00921-y) | 255 UK homes, real data, peer-reviewed |
| UK Data Archive (UK National Smart Meter data) | Registered | Requires GDPR data processing agreement |
