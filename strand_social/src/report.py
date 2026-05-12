"""Lightweight report helpers for the Housing Strand (dataset audit).

HTML reporting is produced mainly in the notebooks. This module offers a small
HTML preview you can call from code or extend for a custom report layout.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path


def benchmark_card_to_html(card: dict, title: str = "Housing benchmark card preview") -> str:
    """Render a minimal read-only HTML view of the benchmark card JSON."""
    pretty = json.dumps(card, indent=2, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>{escape(title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 1.5rem; }}
pre {{ background: #f4f4f4; padding: 1rem; overflow: auto; border-radius: 8px; }}
</style></head><body>
<h1>{escape(title)}</h1>
<p>Schema: <code>{escape(str(card.get("schema", "")))}</code></p>
<pre>{escape(pretty)}</pre>
</body></html>"""


def write_data_quality_report(
    card: dict,
    output_path: str | Path,
) -> None:
    """Write `Data_Quality_Report.html` next to your benchmark card evidence."""
    output_path = Path(output_path)
    output_path.write_text(
        benchmark_card_to_html(card, title="Housing Data Quality Report"),
        encoding="utf-8",
    )
