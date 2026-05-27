#!/usr/bin/env python3
"""
validate_submission.py -- Pre-commit validator for housing strand submission files.

Validates:
  reference/omaib_pathway.json         -- schema, verdicts, non-zero metrics, overall_verdict
  reference/housing_benchmark_card.json -- schema, deployment questions, component verdicts

Exit 0 on success, exit 1 on any error (triggers pre-commit failure).
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ERRORS = []
WARNINGS = []

VALID_VERDICTS = {"READY", "CONDITIONAL", "NOT READY"}
VALID_OPTION_TYPES = {
    "coverage_report",
    "threshold_sensitivity_report",
    "fairness_disparity_summary",
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
            err(f"{label}.{key} is empty or a placeholder")
        else:
            warn(f"{label}.{key} is empty (recommended to fill)")


def validate_pathway(path):
    print(f"  Checking {path.name} ...")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} -- invalid JSON: {e}")
        return

    if data.get("schema_version") != "omaib-housing":
        err(f"schema_version must be 'omaib-housing', got '{data.get('schema_version')}'")
    if data.get("submission_type") != "housing_benchmark_card":
        err(
            f"submission_type must be 'housing_benchmark_card', "
            f"got '{data.get('submission_type')}'"
        )

    team = data.get("team", {})
    if is_placeholder(team.get("name", "")):
        err("team.name is empty -- fill in your team name before committing")
    if is_placeholder(team.get("members", "")):
        err("team.members is empty -- list all team member names")

    models = data.get("models", [])
    if len(models) < 2:
        err(
            f"models array has {len(models)} entr{'y' if len(models) == 1 else 'ies'}; "
            f"at least 2 required"
        )

    for i, m in enumerate(models):
        label = f"models[{i}] ({m.get('name', 'unnamed')})"

        verdict = m.get("verdict", "")
        if verdict not in VALID_VERDICTS:
            err(f"{label}.verdict '{verdict}' must be one of: {', '.join(sorted(VALID_VERDICTS))}")
        if verdict in ("CONDITIONAL", "NOT READY"):
            check_string(m, "conditions", label)

        check_string(m, "narrative", label)

        metrics = m.get("metrics", {})
        if metrics.get("auroc", 0.0) == 0.0:
            err(f"{label}.metrics.auroc is 0 -- populate real metric values")
        if metrics.get("n_properties", 0) == 0:
            err(f"{label}.metrics.n_properties is 0 -- fill in the test set property count")

    overall = data.get("overall_verdict", "")
    if overall not in VALID_VERDICTS:
        err(
            f"overall_verdict '{overall}' must be one of: {', '.join(sorted(VALID_VERDICTS))}"
        )

    check_string(data, "overall_notes", "top-level", required=False)


def validate_benchmark_card(path):
    print(f"  Checking {path.name} ...")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} -- invalid JSON: {e}")
        return

    if data.get("schema_version") != "omaib-housing-v0.1":
        err(f"schema_version must be 'omaib-housing-v0.1'")

    team = data.get("team", {})
    if is_placeholder(team.get("name", "")):
        err("team.name is empty")

    models = data.get("models", [])
    if len(models) < 2:
        err(
            f"models array has {len(models)} entr{'y' if len(models) == 1 else 'ies'}; "
            f"at least 2 required"
        )

    for i, m in enumerate(models):
        label = f"models[{i}] ({m.get('name', 'unnamed')})"

        verdict = m.get("verdict", "")
        if verdict not in VALID_VERDICTS:
            err(f"{label}.verdict '{verdict}' must be one of: {', '.join(sorted(VALID_VERDICTS))}")
        check_string(m, "narrative", label)

        metrics = m.get("metrics", {})
        if metrics.get("auroc", 0.0) == 0.0:
            err(f"{label}.metrics.auroc is 0")
        if metrics.get("n_properties", 0) == 0:
            err(f"{label}.metrics.n_properties is 0")

        # Deployment questions -- all eight required
        dq = m.get("deployment_questions", {})
        for q in ("q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8"):
            if is_placeholder(dq.get(q, "")):
                err(f"{label}.deployment_questions.{q} is empty")

    # Component verdicts -- all three required
    cv = data.get("component_verdicts", {})
    for component in ("data_quality", "split_integrity", "equity"):
        verdict = cv.get(component, "")
        if verdict not in VALID_VERDICTS:
            err(
                f"component_verdicts.{component} '{verdict}' must be one of: "
                f"{', '.join(sorted(VALID_VERDICTS))}"
            )

    # Overall verdict
    overall = data.get("overall_verdict", "")
    if overall not in VALID_VERDICTS:
        err(
            f"overall_verdict '{overall}' must be one of: {', '.join(sorted(VALID_VERDICTS))}"
        )

    # Option-specific
    opt = data.get("option_specific", {})
    opt_type = opt.get("type", "")
    if opt_type and opt_type not in VALID_OPTION_TYPES:
        warn(
            f"option_specific.type '{opt_type}' is not a recognised type "
            f"({', '.join(sorted(VALID_OPTION_TYPES))})"
        )
    if is_placeholder(opt.get("title", "")):
        warn("option_specific.title is empty")
    if not opt.get("content"):
        warn("option_specific.content is empty")


def main():
    pathway_path = ROOT / "reference" / "omaib_pathway.json"
    card_path = ROOT / "reference" / "housing_benchmark_card.json"

    print("\nHousing Strand Submission Validator")
    print("=" * 40)

    missing = [p for p in (pathway_path, card_path) if not p.exists()]
    for p in missing:
        err(f"{p.name} not found at expected path {p.relative_to(ROOT)}")

    if pathway_path.exists():
        validate_pathway(pathway_path)
    if card_path.exists():
        validate_benchmark_card(card_path)

    print()
    if WARNINGS:
        for w in WARNINGS:
            print(w)
    if ERRORS:
        print()
        for e in ERRORS:
            print(e)
        print(f"\n[FAIL] {len(ERRORS)} error(s) found. Fix before committing.\n")
        sys.exit(1)
    else:
        print("[PASS] All submission files validated successfully.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
