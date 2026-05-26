# Clinical Strand Demo — Running the Reference App

This is a reference implementation of one possible solution to the clinical strand challenge. It shows what a completed solution can look like — not a template you must follow.

---

## How to run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Prepare data and train models (run the notebooks in order, or run each script directly)
#    00_data_explore.ipynb   — inspect the dataset
#    01_preprocess_and_split.ipynb — split into train / val / test
#    02_train_models.ipynb   — train models and save artefacts to saved_models/

# 3. Launch the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## What to expect

- A patient selector showing individual risk scores from each model
- A monitoring protocol generated from the patient's predicted risk
- Evidence views: model performance, subgroup breakdowns, feature importance, and failure modes
- A pre-populated safety report section reflecting the demo model evaluations

Model artefacts are saved to `saved_models/` after running the training notebook. The reference JSON files in `reference/` show a completed submission.

---

## Data

The demo uses its own synthetic dataset (`data/raw/post_surgical_patients.csv`) — separate from the main strand dataset. Do not use this data for your own submission.
