# Demo Data Guide

This folder contains a lightweight subset of the housing strand dataset for fast, reproducible demo runs.

## Raw modality files

- `raw/properties.csv`:
  property-level metadata.
- `raw/indoor_environment_daily.csv`:
  temperature, humidity, and CO2 daily sensor values.
- `raw/energy_noise_daily.csv`:
  smart meter and ambient noise daily values.
- `raw/resident_feedback_daily.csv`:
  sparse resident comfort feedback (`survey_score`).

All rows are sampled from the full `data/raw/housing_properties_daily.csv` dataset in the repository root.

## Processed output

- `processed/` is used by notebooks and scripts for merged features and split artifacts.
