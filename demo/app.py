"""Housing strand demo app.

Single-file entrypoint for both:
1) Streamlit UI: streamlit run app.py
2) CLI pipeline: python app.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

import joblib
import pandas as pd

# Repo root (parent of demo/) holds src/, data/, saved_models/, reference/.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.data_pipeline import FEATURES, load_and_merge  # FEATURES = deployable set (no leakage)
from src.evaluate import compute_metrics
from src.evidence import (
    aggregate_dataset_audit,
    compute_equity_view,
    compute_leakage_view,
    compute_mnar_view,
    compute_sensor_quality_view,
)

THRESHOLD = 0.5

_VERDICTS = ["CONDITIONAL", "PASS", "FAIL"]


def _load_reference(root: Path, filename: str) -> dict:
    p = root / "reference" / filename
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _save_reference(root: Path, filename: str, data: dict) -> None:
    p = root / "reference" / filename
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _validate_required_inputs(root: Path) -> tuple[Path, Path]:
    data_dir = root / "data" / "processed"
    train_path = data_dir / "train_features.csv"
    test_path = data_dir / "test_features.csv"
    model_path = root / "saved_models" / "model_a_logistic_baseline.joblib"

    missing = [str(p) for p in [train_path, test_path] if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required processed files. Run notebooks/data_exploration_training.ipynb "
            "from top to bottom to generate data/processed/train_features.csv and "
            "data/processed/test_features.csv. "
            f"Missing: {', '.join(missing)}"
        )
    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found at {model_path}. "
            "Run the Model Training section in notebooks/data_exploration_training.ipynb first."
        )

    return test_path, model_path


def generate_demo_outputs():
    """Load the notebook-trained model and evaluate it on the held-out test set."""
    root = _REPO_ROOT
    raw_dir = root / "data" / "raw"

    test_path, model_path = _validate_required_inputs(root)
    test_df = pd.read_csv(test_path)
    train_df = pd.read_csv(root / "data" / "processed" / "train_features.csv")

    # Load the model trained and saved by the notebook — do not re-train here.
    model = joblib.load(model_path)

    X_test = test_df[FEATURES]
    y_test = test_df["cold_risk"]
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = compute_metrics(y_test, y_prob, threshold=THRESHOLD, model_name="model_a")
    metrics["n_properties"] = int(test_df["reference"].nunique())

    # Evidence dashboard — computed in-memory, never saved to disk
    merged = load_and_merge(raw_dir)
    evidence_df = merged.copy()
    evidence_df["cold_risk"] = (evidence_df["avgTemperature"] < 19.0).astype(int)

    sensor_quality_view = compute_sensor_quality_view(evidence_df)
    mnar_view = compute_mnar_view(evidence_df)
    leakage_view = compute_leakage_view(train_df, test_df)

    # Equity view: compute subgroup AUROC per property_type
    from sklearn.metrics import roc_auc_score as _roc_auc

    equity_rows = []
    for group, grp_df in test_df.groupby("property_type"):
        grp_idx = grp_df.index
        grp_y = y_test.iloc[grp_idx] if hasattr(y_test, "iloc") else y_test[grp_idx]
        grp_prob = y_prob[grp_idx]
        if len(set(grp_y)) < 2:
            grp_auroc = 0.0
        else:
            grp_auroc = float(_roc_auc(grp_y, grp_prob))
        equity_rows.append(
            {
                "model": "model_a",
                "group": group,
                "auroc": grp_auroc,
                "gap_vs_terraced": 0.0,
            }
        )

    # Compute gap vs terraced
    terraced_auroc = next(
        (r["auroc"] for r in equity_rows if r["group"] == "terraced"), 0.0
    )
    for row in equity_rows:
        row["gap_vs_terraced"] = round(row["auroc"] - terraced_auroc, 4)

    equity_view = compute_equity_view(equity_rows)

    dataset_audit = aggregate_dataset_audit(
        sensor_quality_verdict=sensor_quality_view["verdict"],
        split_integrity_verdict=leakage_view["verdict"],
        equity_verdict=equity_view["verdict"],
    )
    evidence_dashboard = {
        "sensor_data_quality": sensor_quality_view,
        "mnar_analysis": mnar_view,
        "subgroup_equity": equity_view,
        "leakage_audit": leakage_view,
        "dataset_audit": {
            "data_quality": dataset_audit.data_quality,
            "split_integrity": dataset_audit.split_integrity,
            "equity": dataset_audit.equity,
            "overall_verdict": dataset_audit.overall,
        },
    }

    return {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "metrics": metrics,
        "evidence_dashboard": evidence_dashboard,
        "model_path": str(model_path),
    }


def run():
    try:
        result = generate_demo_outputs()
        m = result["metrics"]
        print("Demo pipeline complete.")
        print(f"Train rows: {result['train_rows']} | Test rows: {result['test_rows']}")
        print(
            f"AUROC: {m['auroc']}  AUPRC: {m['auprc']}  Brier: {m['brier_score']}  "
            f"Sensitivity: {m['sensitivity']}"
        )
        print(f"Model loaded from: {result['model_path']}")
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        print("Tip: Run notebooks/data_exploration_training.ipynb first.")
        raise


def run_streamlit():
    import streamlit as st

    st.set_page_config(page_title="Housing Strand Demo", layout="wide")
    st.title("Housing Strand Demo Solution")
    st.caption("MultimodalAI'26 - starter kit runnable solution (Streamlit)")

    st.markdown(
        """
This app is a **starter-kit workbench**. It helps teams build evidence, but it does not complete hackathon
deliverables for participants.
"""
    )

    with st.expander("Housing strand requirements (from STRAND_GUIDE)", expanded=False):
        st.markdown(
            """
### Five deliverables
1. **The solution** (runnable tool)
2. **`omaib_pathway.json`** (governance manifest)
3. **`housing_benchmark_card.json`** (full benchmark card)
4. **Evidence Dashboard** (5 required views)

### Three track roles
- **Builder**: solution and option-specific work
- **Evidence Analyst**: data quality, MNAR, equity, leakage evidence
- **Governance Lead**: manifest/card verdicts and narratives
"""
        )

    if "run_result" not in st.session_state:
        st.session_state.run_result = None

    if st.button("Run Demo Pipeline", type="primary"):
        try:
            with st.spinner("Evaluating model on test set..."):
                st.session_state.run_result = generate_demo_outputs()
        except FileNotFoundError as exc:
            st.session_state.run_result = None
            st.error(str(exc))
            st.info(
                "Next step: open notebooks/data_exploration_training.ipynb and run it top to bottom, "
                "then click 'Run Demo Pipeline' again."
            )
            return

    result = st.session_state.run_result
    if not result:
        st.info("Click **Run Demo Pipeline** to generate outputs.")
        return

    st.success("Demo pipeline finished.")
    c1, c2 = st.columns(2)
    c1.metric("Train rows", result["train_rows"])
    c2.metric("Test rows", result["test_rows"])

    m = result["metrics"]
    display_keys = (
        "auroc",
        "auprc",
        "brier_score",
        "sensitivity",
        "threshold",
        "n_total",
        "n_positive",
        "n_properties",
    )
    st.subheader("Model Metrics")
    st.dataframe(
        pd.DataFrame([{k: m[k] for k in display_keys if k in m}]),
        use_container_width=True,
    )

    # ── Submission form ────────────────────────────────────────────────────────
    root = _REPO_ROOT
    ref_pathway = _load_reference(root, "omaib_pathway.json")
    ref_card = _load_reference(root, "housing_benchmark_card.json")

    mp = next((x for x in ref_pathway.get("models", []) if x["name"] == "model_a"), {})
    mc = next((x for x in ref_card.get("models", []) if x["name"] == "model_a"), {})
    dq = mc.get("deployment_questions", {})

    cur_verdict = mp.get("verdict", "CONDITIONAL")
    verdict_idx = _VERDICTS.index(cur_verdict) if cur_verdict in _VERDICTS else 0

    st.subheader("Submission Form")
    st.caption(
        "Auto-generated metrics above are locked. Fill the fields below and click **Save** "
        "to write your entries into `reference/omaib_pathway.json` and "
        "`reference/housing_benchmark_card.json`, preserving their exact structure."
    )

    with st.form("submission_form"):
        st.markdown("#### Team")
        f_name = st.text_input(
            "Team name", value=ref_pathway.get("team", {}).get("name", "")
        )
        f_members = st.text_input(
            "Team members (comma-separated)",
            value=ref_pathway.get("team", {}).get("members", ""),
        )

        st.markdown("#### Model A — Governance")
        f_verdict = st.selectbox("Verdict", _VERDICTS, index=verdict_idx)
        f_conditions = st.text_area(
            "Conditions", value=mp.get("conditions", ""), height=80
        )
        f_narrative = st.text_area(
            "Narrative", value=mp.get("narrative", ""), height=120
        )

        st.markdown("#### Deployment Questions")
        f_q1 = st.text_area("Q1 — Intended use", value=dq.get("q1", ""), height=80)
        f_q2 = st.text_area(
            "Q2 — Known failure modes", value=dq.get("q2", ""), height=80
        )
        f_q3 = st.text_area("Q3 — Monitoring plan", value=dq.get("q3", ""), height=80)
        f_q4 = st.text_area("Q4 — Override protocol", value=dq.get("q4", ""), height=80)
        f_q5 = st.text_area(
            "Q5 — Retraining triggers", value=dq.get("q5", ""), height=80
        )

        st.markdown("#### Notes")
        f_notes = st.text_area(
            "Overall notes", value=ref_pathway.get("overall_notes", ""), height=100
        )

        saved = st.form_submit_button("Save to reference files", type="primary")

    if saved:
        today = str(date.today())
        live_metrics = {
            k: m[k]
            for k in (
                "auroc",
                "auprc",
                "brier_score",
                "sensitivity",
                "threshold",
                "n_properties",
            )
            if k in m
        }

        # omaib_pathway.json
        ref_pathway["team"]["name"] = f_name
        ref_pathway["team"]["members"] = f_members
        ref_pathway["submitted"] = today
        ref_pathway["overall_notes"] = f_notes
        for model in ref_pathway.get("models", []):
            if model["name"] == "model_a":
                model["verdict"] = f_verdict
                model["conditions"] = f_conditions
                model["narrative"] = f_narrative
                model["metrics"].update(live_metrics)

        # housing_benchmark_card.json
        ref_card["team"]["name"] = f_name
        ref_card["team"]["members"] = f_members
        ref_card["evaluation_date"] = today
        ref_card["overall_notes"] = f_notes
        for model in ref_card.get("models", []):
            if model["name"] == "model_a":
                model["verdict"] = f_verdict
                model["conditions"] = f_conditions
                model["narrative"] = f_narrative
                model["metrics"].update(live_metrics)
                model["deployment_questions"]["q1"] = f_q1
                model["deployment_questions"]["q2"] = f_q2
                model["deployment_questions"]["q3"] = f_q3
                model["deployment_questions"]["q4"] = f_q4
                model["deployment_questions"]["q5"] = f_q5

        _save_reference(root, "omaib_pathway.json", ref_pathway)
        _save_reference(root, "housing_benchmark_card.json", ref_card)
        st.success(
            "Reference files saved — `reference/omaib_pathway.json` and "
            "`reference/housing_benchmark_card.json` updated."
        )


def _is_streamlit_runtime() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return any(key.startswith("STREAMLIT_") for key in os.environ)


if __name__ == "__main__":
    if _is_streamlit_runtime():
        run_streamlit()
    else:
        run()
