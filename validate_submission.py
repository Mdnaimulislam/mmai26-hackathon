#!/usr/bin/env python3
"""
validate_submission.py -- Pre-demo validator for the robotics strand.

Validates:
  federation.json     -- all 10 required fields, UK lat/lon range, no template defaults
  theme.config.json   -- all 5 required fields, no template defaults

Exit 0 on success, exit 1 on any error.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ERRORS = []
WARNINGS = []

TEMPLATE_DEFAULTS = {
    "your-uni-id",
    "Your University Full Name",
    "Your City",
    "Your Lab Node Name",
    "Your Lab Project Title",
    "YourTag1",
    "#YOUR_BRAND_HEX",
    "https://your-uni.github.io/sonair-portal",
    "Describe your real equipment and collaboration needs in 1-2 sentences. This is your governance statement.",
    "./assets/logo.png",
}

# Sheffield template defaults that must not appear in submissions
TEMPLATE_LAT = 53.3814
TEMPLATE_LON = -1.4884


def err(msg):
    ERRORS.append(f"  ERROR  {msg}")


def warn(msg):
    WARNINGS.append(f"  WARN   {msg}")


def is_template(val):
    return str(val).strip() in TEMPLATE_DEFAULTS


def load_json(path):
    if not path.exists():
        err(f"{path.name} not found at {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{path.name} is not valid JSON: {e}")
        return None


# ---------------------------------------------------------------------------
# federation.json
# ---------------------------------------------------------------------------

def validate_federation(data):
    if data is None:
        return

    node = data.get("node", {})
    card = data.get("co_creation_card", {})

    # Required node fields
    for field in ("id", "name", "city", "lat", "lon", "color", "url"):
        val = node.get(field)
        if val is None:
            err(f"federation.json: node.{field} is missing")
        elif is_template(val):
            err(f"federation.json: node.{field} still contains the template default — replace it")

    # Required co_creation_card fields
    for field in ("title", "tags", "description"):
        val = card.get(field)
        if val is None:
            err(f"federation.json: co_creation_card.{field} is missing")
        elif is_template(val):
            err(f"federation.json: co_creation_card.{field} still contains the template default — replace it")

    # UK lat/lon range
    lat = node.get("lat")
    lon = node.get("lon")
    if isinstance(lat, (int, float)):
        if lat == TEMPLATE_LAT:
            err(f"federation.json: node.lat is still the Sheffield template default ({TEMPLATE_LAT}) — use your real latitude")
        elif not (49 <= lat <= 61):
            warn(f"federation.json: node.lat={lat} is outside the UK range 49–61 — is this correct?")
    if isinstance(lon, (int, float)):
        if lon == TEMPLATE_LON:
            err(f"federation.json: node.lon is still the Sheffield template default ({TEMPLATE_LON}) — use your real longitude")
        elif not (-8 <= lon <= 2):
            warn(f"federation.json: node.lon={lon} is outside the UK range -8 to 2 — is this correct?")

    # tags must be a list
    tags = card.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            err("federation.json: co_creation_card.tags must be a JSON array, not a string")
        elif len(tags) < 2:
            warn("federation.json: co_creation_card.tags should contain at least 2 entries")
        elif len(tags) > 5:
            warn("federation.json: co_creation_card.tags should contain 5 entries or fewer")

    # url must start with https://
    url = node.get("url", "")
    if url and not str(url).startswith("https://"):
        err(f"federation.json: node.url must start with https:// (got: {url!r})")


# ---------------------------------------------------------------------------
# theme.config.json
# ---------------------------------------------------------------------------

def validate_theme(data):
    if data is None:
        return

    for field in ("institution_name", "node_name", "city", "primary_color", "logo_url"):
        val = data.get(field)
        if val is None:
            err(f"theme.config.json: {field} is missing")
        elif is_template(val):
            err(f"theme.config.json: {field} still contains the template default — replace it")

    color = data.get("primary_color", "")
    if color and not str(color).startswith("#"):
        warn(f"theme.config.json: primary_color should be a hex colour starting with # (got: {color!r})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("SONAIR Robotics Strand — submission validator")
    print("=" * 50)

    fed_path   = ROOT / "federation.json"
    theme_path = ROOT / "theme.config.json"

    print(f"\nChecking {fed_path.name} ...")
    validate_federation(load_json(fed_path))

    print(f"Checking {theme_path.name} ...")
    validate_theme(load_json(theme_path))

    print()
    if WARNINGS:
        for w in WARNINGS:
            print(w)
        print()

    if ERRORS:
        for e in ERRORS:
            print(e)
        print()
        print(f"FAILED — {len(ERRORS)} error(s) found. Fix the errors above before your demo.")
        sys.exit(1)
    else:
        print("PASSED — federation.json and theme.config.json look valid.")
        if WARNINGS:
            print(f"         {len(WARNINGS)} warning(s) above — review before submitting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
