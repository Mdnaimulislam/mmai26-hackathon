# Data Guide — Housing Strand

## File: `raw/housing_properties_daily.csv`

**Shape:** 250 properties × 730 days ≈ 182,750 rows (daily averages, 1 Jan 2023 – 31 Dec 2024)

| Column | What it is | Missing? |
|---|---|---|
| `reference` | Property identifier — structured (`U` + 6–9 digits) or free-text address shorthand | Never |
| `Sub-building` | Flat label (e.g. `Flat 1A`) — blank for houses | Never (blank for houses) |
| `address` | Street address in varied formats | Never |
| `postcode` | `ZZ`-prefix fictional postcode — does not exist in Royal Mail's database | Never |
| `year` | Year (2023 or 2024) | Never |
| `month` | Month 1–12 | Never |
| `day` | Day of month | Never |
| `avgTemperature` | Mean indoor temperature that day (°C) | ~3% |
| `avgHumidity` | Mean indoor humidity that day (%) | ~5% |
| `avgCo2` | Mean indoor CO₂ concentration that day (ppm) | ~38% |

**Postcodes and addresses are fictional.** `ZZ`-prefix area codes do not exist in the Royal Mail database. Street names are invented. These cannot be resolved to any real UK address.

