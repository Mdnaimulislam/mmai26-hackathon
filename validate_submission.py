#!/usr/bin/env python3
"""
validate_submission.py -- Pre-demo validator for the SONAIR robotics strand.

Validates:
  reference/federation.json     -- all 10 node fields, UK coordinates, no template defaults
  reference/theme.config.json   -- all 5 fields, valid hex colour, no template defaults

Also runs cross-file consistency checks (node.name, city, and colour must agree
across both files).

Exit 0 on success, exit 1 on any error (triggers pre-commit failure).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ERRORS = []
WARNINGS = []

HEX_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")

# Template sentinel values that must be replaced before submission
TEMPLATE_LAT = 99.9999
TEMPLATE_LON = -9.9999
SHEFFIELD_LAT = 53.3814
SHEFFIELD_LON = -1.4884

PLACEHOLDER_STRINGS = {
    "",
    "your-uni-id",
    "your university full name",
    "your city",
    "your lab node name",
    "your lab project title",
    "yourtag1",
    "#your_brand_hex",
    "https://your-uni.github.io/sonair-portal",
    "describe your real equipment and collaboration needs in 1-2 sentences.",
    "describe your real equipment and collaboration needs in 1-2 sentences. this is your governance statement.",
    "./assets/logo.png",
    "0",
    "0.0",
    "not provided",
    "tbd",
    "todo",
    "placeholder",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def err(msg: str) -> None:
    ERRORS.append(f"  ERROR  {msg}")


def warn(msg: str) -> None:
    WARNINGS.append(f"  WARN   {msg}")


def is_placeholder(val) -> bool:
    return str(val).strip().lower() in PLACEHOLDER_STRINGS


def check_string(obj: dict, key: str, label: str, required: bool = True) -> None:
    val = obj.get(key, "")
    if not isinstance(val, str) or is_placeholder(val):
        if required:
            err(f"{label}.{key} is empty or a placeholder — fill in a real value")
        else:
            warn(f"{label}.{key} is empty (recommended to fill in)")


def get_current_branch() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        return branch if branch and branch not in ("HEAD", "robotic") else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# reference/federation.json
# ---------------------------------------------------------------------------


def validate_federation(path: Path) -> dict | None:
    print(f"  Checking {path.relative_to(ROOT)} ...")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} -- invalid JSON: {e}")
        return None

    node = data.get("node")
    card = data.get("co_creation_card")

    if not isinstance(node, dict):
        err("federation.json: 'node' object is missing or malformed")
        return None
    if not isinstance(card, dict):
        err("federation.json: 'co_creation_card' object is missing or malformed")
        return None

    # node.id ----------------------------------------------------------------
    node_id = node.get("id", "")
    if is_placeholder(node_id) or not node_id:
        err(
            "federation.json: node.id is empty or a placeholder "
            "— use your institution's short ID (e.g. 'edinburgh')"
        )
    else:
        if node_id != node_id.lower():
            err(f"federation.json: node.id '{node_id}' must be lowercase")
        if " " in node_id:
            err(
                f"federation.json: node.id '{node_id}' must not contain spaces — use hyphens"
            )
        branch = get_current_branch()
        if branch and node_id != branch:
            err(
                f"federation.json: node.id '{node_id}' must match your git branch '{branch}' "
                f"— rename one to match the other"
            )

    # node.name, node.city ---------------------------------------------------
    check_string(node, "name", "federation.json: node")
    check_string(node, "city", "federation.json: node")

    # node.lat ---------------------------------------------------------------
    lat = node.get("lat")
    if lat is None:
        err("federation.json: node.lat is missing")
    elif not isinstance(lat, (int, float)):
        err(
            f"federation.json: node.lat must be a number, got {type(lat).__name__} "
            f"— do not quote it as a string"
        )
    elif lat == TEMPLATE_LAT:
        err(
            f"federation.json: node.lat is still the template placeholder ({TEMPLATE_LAT}) "
            f"— use your real latitude"
        )
    elif lat == SHEFFIELD_LAT:
        err(
            f"federation.json: node.lat is the Sheffield example value ({SHEFFIELD_LAT}) "
            f"— replace with your real latitude"
        )
    elif not (49.0 <= lat <= 61.0):
        warn(
            f"federation.json: node.lat={lat} is outside the UK range 49–61 "
            f"— verify this is intentional"
        )

    # node.lon ---------------------------------------------------------------
    lon = node.get("lon")
    if lon is None:
        err("federation.json: node.lon is missing")
    elif not isinstance(lon, (int, float)):
        err(
            f"federation.json: node.lon must be a number, got {type(lon).__name__} "
            f"— do not quote it as a string"
        )
    elif lon == TEMPLATE_LON:
        err(
            f"federation.json: node.lon is still the template placeholder ({TEMPLATE_LON}) "
            f"— use your real longitude"
        )
    elif lon == SHEFFIELD_LON:
        err(
            f"federation.json: node.lon is the Sheffield example value ({SHEFFIELD_LON}) "
            f"— replace with your real longitude"
        )
    elif not (-8.0 <= lon <= 2.0):
        warn(
            f"federation.json: node.lon={lon} is outside the UK range -8 to 2 "
            f"— verify this is intentional"
        )

    # node.color -------------------------------------------------------------
    color = node.get("color", "")
    if is_placeholder(color) or not color:
        err(
            "federation.json: node.color is empty or a placeholder "
            "— use your institution's hex brand colour (e.g. '#3D5A80')"
        )
    elif not HEX_RE.match(str(color)):
        err(
            f"federation.json: node.color '{color}' is not a valid hex colour "
            f"— use #RRGGBB or #RGB format"
        )

    # node.url ---------------------------------------------------------------
    url = node.get("url", "")
    if is_placeholder(url) or not url:
        err(
            "federation.json: node.url is empty or a placeholder "
            "— provide the HTTPS URL of your deployed sub-portal"
        )
    elif not str(url).startswith("https://"):
        err(f"federation.json: node.url must start with https:// (got: '{url}')")

    # co_creation_card.title -------------------------------------------------
    check_string(card, "title", "federation.json: co_creation_card")

    # co_creation_card.tags --------------------------------------------------
    tags = card.get("tags")
    if tags is None:
        err("federation.json: co_creation_card.tags is missing")
    elif not isinstance(tags, list):
        err(
            "federation.json: co_creation_card.tags must be a JSON array "
            "— not a comma-separated string"
        )
    else:
        if len(tags) < 2:
            err(
                f"federation.json: co_creation_card.tags has {len(tags)} item(s) "
                f"— at least 2 are required"
            )
        elif len(tags) > 5:
            warn(
                f"federation.json: co_creation_card.tags has {len(tags)} items "
                f"— 5 or fewer recommended"
            )
        for j, tag in enumerate(tags):
            if not isinstance(tag, str) or is_placeholder(tag):
                err(
                    f"federation.json: co_creation_card.tags[{j}] is empty or a placeholder "
                    f"— replace with a real keyword"
                )

    # co_creation_card.description -------------------------------------------
    desc = card.get("description", "")
    if is_placeholder(desc) or not str(desc).strip():
        err(
            "federation.json: co_creation_card.description is empty or a placeholder "
            "— write your governance statement (1–2 sentences about your equipment or datasets)"
        )
    elif len(str(desc).split()) < 8:
        warn(
            "federation.json: co_creation_card.description is very short "
            "— aim for 1–2 meaningful sentences describing your real equipment or datasets"
        )

    return data


# ---------------------------------------------------------------------------
# reference/theme.config.json
# ---------------------------------------------------------------------------


def validate_theme(path: Path) -> dict | None:
    print(f"  Checking {path.relative_to(ROOT)} ...")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} -- invalid JSON: {e}")
        return None

    for field in ("institution_name", "node_name", "city"):
        check_string(data, field, "theme.config.json")

    # primary_color ----------------------------------------------------------
    color = data.get("primary_color", "")
    if is_placeholder(color) or not color:
        err(
            "theme.config.json: primary_color is empty or a placeholder "
            "— use your institution's hex brand colour (e.g. '#3D5A80')"
        )
    elif not HEX_RE.match(str(color)):
        err(
            f"theme.config.json: primary_color '{color}' is not a valid hex colour "
            f"— use #RRGGBB or #RGB format"
        )

    # logo_url ---------------------------------------------------------------
    logo = data.get("logo_url", "")
    if is_placeholder(logo) or not logo:
        err(
            "theme.config.json: logo_url is empty or a placeholder "
            "— provide a path (e.g. './assets/logo.png') or HTTPS URL to your logo"
        )

    return data


# ---------------------------------------------------------------------------
# Cross-file consistency
# ---------------------------------------------------------------------------


def cross_validate(fed_data: dict | None, theme_data: dict | None) -> None:
    if fed_data is None or theme_data is None:
        return

    node = fed_data.get("node", {})
    fed_name = node.get("name", "")
    fed_city = node.get("city", "")
    fed_color = node.get("color", "")
    theme_name = theme_data.get("institution_name", "")
    theme_city = theme_data.get("city", "")
    theme_color = theme_data.get("primary_color", "")

    if (
        fed_name
        and theme_name
        and not is_placeholder(fed_name)
        and not is_placeholder(theme_name)
        and fed_name != theme_name
    ):
        warn(
            f"node.name ('{fed_name}') does not match "
            f"theme.config.json institution_name ('{theme_name}') — align them"
        )

    if (
        fed_city
        and theme_city
        and not is_placeholder(fed_city)
        and not is_placeholder(theme_city)
        and fed_city != theme_city
    ):
        warn(
            f"federation.json node.city ('{fed_city}') does not match "
            f"theme.config.json city ('{theme_city}') — they should be the same location"
        )

    if (
        fed_color
        and theme_color
        and not is_placeholder(fed_color)
        and not is_placeholder(theme_color)
        and fed_color.upper() != theme_color.upper()
    ):
        warn(
            f"federation.json node.color ('{fed_color}') does not match "
            f"theme.config.json primary_color ('{theme_color}') "
            f"— consider using the same brand colour in both files"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    fed_path = ROOT / "reference" / "federation.json"
    theme_path = ROOT / "reference" / "theme.config.json"

    print("\nSONAIR Robotics Strand — Submission Validator")
    print("=" * 50)

    for p in (fed_path, theme_path):
        if not p.exists():
            err(f"{p.name} not found at expected path reference/{p.name}")

    fed_data = validate_federation(fed_path) if fed_path.exists() else None
    theme_data = validate_theme(theme_path) if theme_path.exists() else None

    cross_validate(fed_data, theme_data)

    print()
    if WARNINGS:
        for w in WARNINGS:
            print(w)
    if ERRORS:
        if WARNINGS:
            print()
        for e in ERRORS:
            print(e)
        print(f"\n[FAIL] {len(ERRORS)} error(s) found. Fix before your demo.\n")
        sys.exit(1)
    else:
        print(
            "[PASS] reference/federation.json and reference/theme.config.json validated successfully."
        )
        if WARNINGS:
            print(f"       {len(WARNINGS)} warning(s) above — review before the demo.")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
