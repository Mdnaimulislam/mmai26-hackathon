# Housing Strand Demo — Starter Walkthrough

This demo is a practical starter flow for the housing strand.
Use it to train a baseline model, then launch the Streamlit app to evaluate the model and fill your submission.

## Goal of this demo

- Train a baseline model in the notebook and save it to disk.
- Launch the Streamlit app to evaluate the saved model on the test set.
- Inspect evidence dashboard views (sensor quality, MNAR, equity, leakage, dataset audit).
- Fill the submission form to write governance answers into `reference/` JSONs.

## Prerequisites

- Python 3.10+
- A virtual environment (recommended)
- Jupyter support (VS Code, JupyterLab, or similar)

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows bash
pip install -r requirements.txt
```

## Run order

### 1) Run the notebook

Open and run all cells in:

- `notebooks/data_exploration_training.ipynb`

This notebook covers:

- Modality loading and data-quality snapshot
- Feature engineering and property-level split
- Baseline model training and saving to `saved_models/`

### 2) Launch the demo app

```bash
streamlit run app.py
```

The app loads the saved model, evaluates it on the test set, displays model metrics and the evidence dashboard, and provides a submission form for governance fields.

### 3) Optional CLI pipeline run

```bash
python app.py
```

Prints model metrics to console without Streamlit UI.

## What artifacts should exist after a successful run

- `saved_models/model_a_logistic_baseline.joblib`
- `data/processed/train_features.csv`
- `data/processed/test_features.csv`

## What this demo does not do for teams

The demo does not auto-fill final submission judgments.
Teams must complete their own evidence-backed final documents via the submission form or by editing:

- `reference/omaib_pathway.json`
- `reference/housing_benchmark_card.json`

## Troubleshooting

- If the app reports a missing model, rerun the notebook from top to bottom.
- If Streamlit command is unavailable, reactivate your virtual environment.
- If dependency issues occur, reinstall from `requirements.txt` in a clean environment.
