"""Housing Strand — lightweight Streamlit companion.

Run from the repo root:
    streamlit run app.py

This app previews the frozen forecast file, summarises baseline errors by property type,
and displays `reference/benchmark_card.json` when present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.evaluate import summarise_forecast_errors
from src.report import benchmark_card_to_html

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
REF = ROOT / "reference"


def main() -> None:
    st.set_page_config(page_title="Housing Strand — Audit companion", layout="wide")
    st.title("Housing Strand — Audit companion")
    st.caption(
        "Dataset readiness & baseline forecast audit. "
        "Primary work happens in the notebooks; this app is optional."
    )

    fc_path = RAW / "housing_with_forecasts.csv"
    card_path = REF / "benchmark_card.json"

    tab1, tab2, tab3 = st.tabs(["Overview", "Forecast errors", "Benchmark card"])

    with tab1:
        st.markdown(
            """
There are **no models to train** here—forecasts are frozen in the CSV.
Teams profile sensors and metadata, build leakage-safe splits, and complete the
**Housing Benchmark Card** (`reference/benchmark_card.json`).

Quick start:
```bash
pip install -r requirements.txt
jupyter notebook notebooks/01_explore_and_audit.ipynb
```
"""
        )
        if fc_path.exists():
            st.success(f"Found forecasts file: `{fc_path.relative_to(ROOT)}`")
        else:
            st.error("Missing `data/raw/housing_with_forecasts.csv` — restore from the repository.")

    with tab2:
        if not fc_path.exists():
            st.warning("Load the starter CSV into `data/raw/` first.")
        else:
            df = pd.read_csv(fc_path)
            by_type = summarise_forecast_errors(df)
            st.subheader("Baseline forecast vs actual (by property type)")
            st.dataframe(by_type, use_container_width=True)

    with tab3:
        if card_path.exists():
            with card_path.open(encoding="utf-8") as f:
                card = json.load(f)
            components.html(
                benchmark_card_to_html(card, title="Housing Benchmark Card"),
                height=600,
                scrolling=True,
            )
            st.download_button(
                "Download benchmark_card.json",
                json.dumps(card, indent=2),
                file_name="benchmark_card.json",
                mime="application/json",
            )
        else:
            st.info(
                "Complete Part 2 of the hackathon and save "
                "`reference/benchmark_card.json` to preview it here."
            )


if __name__ == "__main__":
    main()
