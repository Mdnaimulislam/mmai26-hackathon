#!/usr/bin/env python3
"""
validate_submission.py -- Pre-commit validator for clinical strand submission files.

Advisory validator: flags missing or placeholder content as warnings so participants
can improve their work before submission. Only genuine file-format problems (invalid
JSON, missing files, wrong schema_version or submission_type) cause exit 1 and block
the commit.

Validates:
  reference/omaib_pathway.json        -- schema, verdicts, metrics, team fields
  reference/model_safety_report.json  -- schema, narratives, deployment Qs, failure catalogue

Exit 0 when structurally valid (warnings allowed); exit 1 only on format/schema errors.
"""


import json
import sys
from pathlib import Path


ROOT = Path(__file__).parent
ERRORS = []
WARNINGS = []


VALID_VERDICTS = {"APPROVE", "CONDITIONAL", "NOT APPROVED"}
VALID_OPTION_TYPES = {
    "scoring_rubric",
    "alert_burden_analysis",
    "threshold_sensitivity_report",
}
PLACEHOLDER_VALUES = {"", "0", "0.0", "not provided", "tbd", "todo", "placeholder"}




def err(msg):
    ERRORS.append(f"  ERROR  {msg}")




def warn(msg):
    WARNINGS.append(f"  WARN   {msg}")




def is_placeholder(val):
    return str(val).strip().lower() in PLACEHOLDER_VALUES




def check_string(obj, key, label, required=True):
    val = obj.get(key, "")
    if not isinstance(val, str) or is_placeholder(val):
        if required:
            warn(f"{label}.{key} is empty or a placeholder")
        else:
            warn(f"{label}.{key} is empty — recommended to fill")




def warn_failure_catalogue_size(label, fc):
    n = len(fc)
    if n == 0:
        warn(f"{label}.failure_catalogue — at least one failure mode is recommended")
    elif n <= 2:
        warn(f"{label}.failure_catalogue — 3+ entries recommended for a thorough catalogue")




def validate_pathway(path):
    print(f"  Checking {path.name} ...")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} — invalid JSON: {e}")
        return


    if data.get("schema_version") != "omaib-clinical":
        err(f"schema_version must be 'omaib-clinical', got '{data.get('schema_version')}'")
    if data.get("submission_type") != "model_safety_report":
        err(f"submission_type must be 'model_safety_report', got '{data.get('submission_type')}'")


    team = data.get("team", {})
    if is_placeholder(team.get("name", "")):
        warn("team.name is empty — fill in your team name before committing")
    if is_placeholder(team.get("members", "")):
        warn("team.members is empty — list all team member names")


    models = data.get("models", [])
    if len(models) < 2:
        warn(f"models array has {len(models)} entr{'y' if len(models) == 1 else 'ies'}; at least 2 required")


    for i, m in enumerate(models):
        label = f"models[{i}] ({m.get('name', 'unnamed')})"


        verdict = m.get("verdict", "")
        if verdict not in VALID_VERDICTS:
            warn(f"{label}.verdict '{verdict}' must be one of: {', '.join(sorted(VALID_VERDICTS))}")
        if verdict in ("CONDITIONAL", "NOT APPROVED"):
            check_string(m, "conditions", label)


        check_string(m, "narrative", label)


        metrics = m.get("metrics", {})
        if metrics.get("auroc", 0.0) == 0.0:
            warn(f"{label}.metrics.auroc is 0 — populate real metric values")
        if metrics.get("n_total", 0) == 0:
            warn(f"{label}.metrics.n_total is 0 — fill in the test set size")
        if metrics.get("n_positive", 0) == 0:
            warn(f"{label}.metrics.n_positive is 0 — fill in the number of positive cases")


    check_string(data, "overall_notes", "top-level", required=False)




def validate_safety_report(path):
    print(f"  Checking {path.name} ...")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} — invalid JSON: {e}")
        return


    if data.get("schema_version") != "omaib-clinical":
        err(f"schema_version must be 'omaib-clinical'")


    team = data.get("team", {})
    if is_placeholder(team.get("name", "")):
        warn("team.name is empty")
    if is_placeholder(team.get("members", "")):
        warn("team.members is empty")


    models = data.get("models", [])
    if len(models) < 2:
        warn(f"models array has {len(models)} entr{'y' if len(models) == 1 else 'ies'}; at least 2 required")


    for i, m in enumerate(models):
        label = f"models[{i}] ({m.get('name', 'unnamed')})"


        verdict = m.get("verdict", "")
        if verdict not in VALID_VERDICTS:
            warn(f"{label}.verdict '{verdict}' must be one of: {', '.join(sorted(VALID_VERDICTS))}")
        if verdict in ("CONDITIONAL", "NOT APPROVED"):
            check_string(m, "conditions", label)
        check_string(m, "narrative", label)


        metrics = m.get("metrics", {})
        if metrics.get("auroc", 0.0) == 0.0:
            warn(f"{label}.metrics.auroc is 0")
        if metrics.get("n_total", 0) == 0:
            warn(f"{label}.metrics.n_total is 0")


        # Deployment questions — all five recommended
        dq = m.get("deployment_questions", {})
        for q in ("q1_miss_rate", "q2_alert_precision", "q3_clearance_safety",
                  "q4_discrimination", "q5_calibration"):
            if is_placeholder(dq.get(q, "")):
                warn(f"{label}.deployment_questions.{q} is empty")


        # Failure analysis — all four recommended
        fa = m.get("failure_analysis", {})
        for field in ("who_is_missed", "false_alarm_profile",
                      "feature_importance_interpretation", "model_disagreement"):
            if is_placeholder(fa.get(field, "")):
                warn(f"{label}.failure_analysis.{field} is empty")


        # Failure catalogue — tiered recommendations
        fc = m.get("failure_catalogue", [])
        warn_failure_catalogue_size(label, fc)
        for j, entry in enumerate(fc):
            if is_placeholder(entry.get("mode", "")):
                warn(f"{label}.failure_catalogue[{j}].mode is empty")
            if is_placeholder(entry.get("example", "")):
                warn(f"{label}.failure_catalogue[{j}].example is empty (recommended)")


        # Explainability
        exp = m.get("explainability", {})
        if is_placeholder(exp.get("output_type", "")):
            warn(f"{label}.explainability.output_type is empty")
        if is_placeholder(exp.get("description", "")):
            warn(f"{label}.explainability.description is empty (recommended)")


        # Option-specific
        opt = m.get("option_specific", {})
        opt_type = opt.get("type", "")
        if opt_type and opt_type not in VALID_OPTION_TYPES:
            warn(f"{label}.option_specific.type '{opt_type}' is not a recognised type "
                 f"({', '.join(sorted(VALID_OPTION_TYPES))})")
        if is_placeholder(opt.get("title", "")):
            warn(f"{label}.option_specific.title is empty")




def main():
    pathway_path = ROOT / "reference" / "omaib_pathway.json"
    report_path = ROOT / "reference" / "model_safety_report.json"


    print("\nClinical Strand Submission Validator")
    print("=" * 40)


    missing = [p for p in (pathway_path, report_path) if not p.exists()]
    for p in missing:
        err(f"{p.name} not found at expected path {p.relative_to(ROOT)}")


    if pathway_path.exists():
        validate_pathway(pathway_path)
    if report_path.exists():
        validate_safety_report(report_path)


    print()
    if WARNINGS:
        for w in WARNINGS:
            print(w)
    if ERRORS:
        if WARNINGS:
            print()
        for e in ERRORS:
            print(e)
        print(f"\n[FAIL] {len(ERRORS)} error(s) found. Fix before committing.\n")
        sys.exit(1)
    if WARNINGS:
        print(
            f"\n[PASS WITH WARNINGS] {len(WARNINGS)} issue(s) above — review before "
            "submission, but the file is structurally valid and will not block "
            "your commit.\n"
        )
        sys.exit(0)
    print("[PASS] All submission files validated successfully.\n")
    sys.exit(0)




if __name__ == "__main__":
    main()