# Data Guide — Housing Strand

## File: `raw/housing_properties_daily.csv`

**Shape:** 250 properties × 731 days = 182,750 rows, 15 columns (daily averages, 1 Jan 2023 – 31 Dec 2024; 2024 is a leap year)

| Column | What it is | Missing? |
|---|---|---|
| `reference` | Property identifier — structured (`U` + 6–9 digits) or free-text address shorthand | Never |
| `Sub-building` | Flat label (e.g. `Flat 1A`) — blank string for non-flat properties | Never |
| `address` | Street address in varied formats | Never |
| `postcode` | `ZZ`-prefix fictional postcode — does not exist in Royal Mail's database | Never |
| `property_type` | `flat`, `terraced`, `semi-detached`, or `detached` | Never |
| `is_flat` | 1 if `property_type` is `flat`, else 0 | Never |
| `year` | Year (2023 or 2024) | Never |
| `month` | Month 1–12 | Never |
| `day` | Day of month | Never |
| `avgTemperature` | Mean indoor temperature that day (°C) | ~3% |
| `avgHumidity` | Mean indoor humidity that day (%) | ~5% |
| `avgCo2` | Mean indoor CO₂ concentration that day (ppm) | ~38% (MNAR) |
| `smart_meter_kwh` | Daily energy consumption (kWh) | ~2.6% |
| `noise_db` | Mean ambient sound level that day (dB) | ~8% |
| `survey_score` | Resident thermal comfort score (1.0–5.0 in 0.5 steps) | ~96–98% (MNAR — cold and higher-deprivation properties respond less often) |

**Postcodes and addresses are fictional.** `ZZ`-prefix area codes do not exist in the Royal Mail database. Street names are invented. These cannot be resolved to any real UK address.
