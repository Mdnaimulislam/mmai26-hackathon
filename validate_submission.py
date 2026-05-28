#!/usr/bin/env python3
"""
validate_submission.py -- Pre-commit validator for housing strand submission files.

Validates:
  reference/omaib_pathway.json         -- schema, verdicts, non-zero metrics, overall_verdict
  reference/housing_benchmark_card.json -- schema, deployment questions, component verdicts

Exit 0 on success, exit 1 on any error (triggers pre-commit failure).
"""

import json
import subprocess
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
OPTION_REQUIRED_KEYS = {
    "coverage_report": {
        "property_type_distribution",
        "top_ranked_count",
        "over_represented_types",
        "under_represented_types",
        "reranking_under_fair_weighting",
    },
    "threshold_sensitivity_report": {
        "thresholds_tested",
        "flagged_count_at_each_threshold",
        "recommended_threshold",
        "sensitivity_fatigue_tradeoff",
    },
    "fairness_disparity_summary": {
        "disparity_findings",
        "most_affected_group",
        "recommended_mitigation",
    },
}


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


def get_current_branch():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        return branch if branch else None
    except Exception:
        return None


def check_exact_string(obj, key, expected, label):
    val = obj.get(key, "")
    if val != expected:
        err(f"{label}.{key} must be '{expected}', got '{val}'")


def validate_pathway(path):
    print(f"  Checking {path.name} ...")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} -- invalid JSON: {e}")
        return

    check_exact_string(data, "schema_version", "omaib-housing", "top-level")
    check_exact_string(data, "submission_type", "housing_benchmark_card", "top-level")
    check_exact_string(data, "strand", "housing", "top-level")
    check_exact_string(data, "hackathon", "MultimodalAI26", "top-level")
    check_string(data, "submitted", "top-level")

    team = data.get("team", {})
    if is_placeholder(team.get("name", "")):
        err("team.name is empty -- fill in your team name before committing")
    if is_placeholder(team.get("members", "")):
        err("team.members is empty -- list all team member names")
    branch = get_current_branch()
    if branch and team.get("name", "") != branch:
        err(f"team.name '{team.get('name', '')}' must match current git branch '{branch}'")

    models = data.get("models", [])
    if len(models) < 3:
        err(
            f"models array has {len(models)} entr{'y' if len(models) == 1 else 'ies'}; "
            f"at least 3 required"
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

    check_exact_string(data, "schema_version", "omaib-housing-v0.1", "top-level")
    check_exact_string(data, "report_type", "housing_benchmark_card", "top-level")
    check_exact_string(data, "strand", "housing", "top-level")
    check_exact_string(data, "hackathon", "MultimodalAI26", "top-level")
    check_string(data, "evaluation_date", "top-level")

    team = data.get("team", {})
    if is_placeholder(team.get("name", "")):
        err("team.name is empty")
    if is_placeholder(team.get("members", "")):
        err("team.members is empty")
    branch = get_current_branch()
    if branch and team.get("name", "") != branch:
        err(f"team.name '{team.get('name', '')}' must match current git branch '{branch}'")

    models = data.get("models", [])
    if len(models) < 3:
        err(
            f"models array has {len(models)} entr{'y' if len(models) == 1 else 'ies'}; "
            f"at least 3 required"
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
    if opt_type not in VALID_OPTION_TYPES:
        err(
            f"option_specific.type '{opt_type}' is not a recognised type "
            f"({', '.join(sorted(VALID_OPTION_TYPES))})"
        )
    if is_placeholder(opt.get("title", "")):
        err("option_specific.title is empty")
    content = opt.get("content")
    if not isinstance(content, dict) or not content:
        err("option_specific.content is empty")
        return

    required_keys = OPTION_REQUIRED_KEYS.get(opt_type, set())
    missing_keys = sorted([k for k in required_keys if k not in content])
    for key in missing_keys:
        err(f"option_specific.content.{key} is required for type '{opt_type}'")


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
