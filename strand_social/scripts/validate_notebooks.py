#!/usr/bin/env python3
"""Validate and optionally execute Housing Strand notebooks (CI / smoke test).

From the `strand_housing` directory:

    python scripts/validate_notebooks.py
    python scripts/validate_notebooks.py --execute

Requires: nbformat, nbconvert, ipykernel (see requirements.txt).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = [
    ROOT / "notebooks" / "01_explore_and_audit.ipynb",
    ROOT / "notebooks" / "02_equity_and_benchmark.ipynb",
]


def validate_schema() -> None:
    import nbformat
    from nbformat.validator import validate

    for path in NOTEBOOKS:
        nb = nbformat.read(path, as_version=4)
        validate(nb)
        print(f"OK  {path.relative_to(ROOT)} (schema)")


def execute_all() -> None:
    out_dir = ROOT / "notebooks"
    for path in NOTEBOOKS:
        out = f"_validate_{path.stem}.ipynb"
        cmd = [
            sys.executable,
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            str(path),
            "--output-dir",
            str(out_dir),
            "--output",
            out,
            "--ExecutePreprocessor.timeout=600",
        ]
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, cwd=ROOT, check=True)
        tmp = out_dir / out
        if tmp.exists():
            tmp.unlink()
            print(f"OK  executed {path.name} (temp output removed)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--execute",
        action="store_true",
        help="Run each notebook with nbconvert (in addition to schema check).",
    )
    args = p.parse_args()

    validate_schema()
    if args.execute:
        execute_all()
    print("All checks passed.")


if __name__ == "__main__":
    main()
