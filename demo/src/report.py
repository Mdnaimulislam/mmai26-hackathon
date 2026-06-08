"""Report generation for the Clinical Strand.

Generates omaib_pathway.json (item B) and model_safety_report.json (item C)
conforming to the hackathon submission schema.
"""

from __future__ import annotations

from datetime import date


SCHEMA_VERSION_PATHWAY = "omaib-clinical"
SCHEMA_VERSION_REPORT = "omaib-clinical-v0.3"


def generate_json_pathway(
    metrics_by_model: dict,
    verdicts: dict,
    conditions: dict,
    narratives: dict,
    team_name: str,
    team_members: str,
    overall_notes: str,
) -> dict:
    """Generate the omaib_pathway.json structure (item B)."""
    models_out = []
    for key in metrics_by_model:
        m = metrics_by_model[key]
        models_out.append(
            {
                "name": key,
                "verdict": verdicts.get(key, "CONDITIONAL"),
                "conditions": conditions.get(key, ""),
                "narrative": narratives.get(key, ""),
                "metrics": {
                    "auroc": m.get("auroc"),
                    "auprc": m.get("auprc"),
                    "brier_score": m.get("brier_score"),
                    "sensitivity": m.get("sensitivity"),
                    "threshold": m.get("threshold"),
                    "n_total": m.get("n_total"),
                    "n_positive": m.get("n_positive"),
                },
            }
        )

    return {
        "schema_version": SCHEMA_VERSION_PATHWAY,
        "submission_type": "model_safety_report",
        "strand": "clinical",
        "hackathon": "MultimodalAI26",
        "submitted": str(date.today()),
        "team": {
            "name": team_name or "your-team-name",
            "members": team_members or "",
        },
        "models": models_out,
        "overall_notes": overall_notes or "",
    }


def generate_json_safety_report(
    metrics_by_model: dict,
    verdicts: dict,
    conditions: dict,
    narratives: dict,
    deployment_qs: dict,
    team_name: str,
    team_members: str,
    overall_notes: str,
) -> dict:
    """Generate the model_safety_report.json structure (item C)."""
    models_out = []
    for key in metrics_by_model:
        m = metrics_by_model[key]
        dq = deployment_qs.get(key, {})
        models_out.append(
            {
                "name": key,
                "verdict": verdicts.get(key, "CONDITIONAL"),
                "conditions": conditions.get(key, ""),
                "narrative": narratives.get(key, ""),
                "metrics": {
                    "auroc": m.get("auroc"),
                    "auprc": m.get("auprc"),
                    "brier_score": m.get("brier_score"),
                    "sensitivity": m.get("sensitivity"),
                    "threshold": m.get("threshold"),
                    "n_total": m.get("n_total"),
                    "n_positive": m.get("n_positive"),
                },
                "deployment_questions": {
                    "q1": dq.get("q1", "Not provided"),
                    "q2": dq.get("q2", "Not provided"),
                    "q3": dq.get("q3", "Not provided"),
                    "q4": dq.get("q4", "Not provided"),
                    "q5": dq.get("q5", "Not provided"),
                },
            }
        )

    return {
        "schema_version": SCHEMA_VERSION_REPORT,
        "report_type": "model_safety_report",
        "strand": "clinical",
        "hackathon": "MultimodalAI26",
        "team": {
            "name": team_name or "your-team-name",
            "members": team_members or "",
        },
        "evaluation_date": str(date.today()),
        "models": models_out,
        "overall_notes": overall_notes or "",
    }
