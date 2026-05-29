"""Streamlit app for Clinical strand demo solution."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import sys

sys.path.append(str(Path(__file__).resolve().parent))
from app import generate_demo_outputs


def read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    st.set_page_config(page_title="Clinical Strand Demo", layout="wide")
    st.title("Clinical Strand Demo Solution")
    st.caption("MultimodalAI'26 - starter kit runnable solution (Streamlit)")

    st.markdown(
        """
This app is a **starter-kit workbench**. It helps teams build evidence, but it does not complete hackathon
deliverables for participants.
"""
    )

    with st.expander("Clinical strand requirements (from STRAND_GUIDE)", expanded=False):
        st.markdown(
            """
### Five deliverables
1. **The solution** (runnable tool)
2. **`omaib_pathway.json`** (governance manifest)
3. **`model_safety_report.json`** (full safety report)
4. **Evidence Dashboard** (5 required views)
5. **Option-specific deliverable** in `option_specific`

### Three track roles
- **Builder**: solution and option-specific work
- **Evidence Analyst**: data quality, MNAR, equity, leakage evidence
- **Governance Lead**: manifest/safety report verdicts and narratives
"""
        )

    if "run_result" not in st.session_state:
        st.session_state.run_result = None

    if st.button("Run Demo Pipeline", type="primary"):
        with st.spinner("Training model and generating outputs..."):
            st.session_state.run_result = generate_demo_outputs()

    result = st.session_state.run_result
    if not result:
        st.info("Click **Run Demo Pipeline** to generate outputs.")
        return

    st.success("Demo pipeline finished.")
    c1, c2 = st.columns(2)
    c1.metric("Train rows", result["train_rows"])
    c2.metric("Test rows", result["test_rows"])

    metrics_dir = Path(result["metrics_dir"])
    evidence = read_json(Path(result["evidence_dashboard_path"]))
    if evidence:
        st.subheader("Evidence Dashboard (Required 5 Views)")
        st.json(evidence, expanded=False)

    st.subheader("Participant deliverable TODOs")
    st.warning(
        "This app does not generate final deliverables. Teams must fill `reference/omaib_pathway.json` and "
        "`reference/model_safety_report.json` with their own evidence-backed narratives, answers, and verdicts."
    )
    st.markdown(
        """
- [ ] Assign the 3 track roles across team members.
- [ ] Complete all 5 evidence dashboard views with your own analysis.
- [ ] Fill all required JSON fields in the `reference/` templates.
- [ ] Decide and complete one valid `option_specific` type payload.
- [ ] Run `python validate_submission.py` before commit/PR.
"""
    )

    st.subheader("Saved Metrics")
    eval_path = metrics_dir / "evaluation_metrics.csv"
    subgroup_path = metrics_dir / "subgroup_equity.csv"
    if eval_path.exists():
        st.markdown("`evaluation_metrics.csv`")
        st.dataframe(pd.read_csv(eval_path), use_container_width=True)
    if subgroup_path.exists():
        st.markdown("`subgroup_equity.csv`")
        st.dataframe(pd.read_csv(subgroup_path), use_container_width=True)


if __name__ == "__main__":
    main()
