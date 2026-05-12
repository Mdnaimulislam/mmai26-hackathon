"""INTERNAL — housing synthetic CSV regeneration hook.

The hackathon ships frozen starter files:

  housing_synthetic_120hh.csv
  housing_with_forecasts.csv

These are the source of truth for participants. This repository does not
require running this script to complete the challenge.

If organisers need to rebuild data, replace this stub with a generator that
writes the two CSVs above and keep random seeds documented for reproducibility.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    main_csv = ROOT / "housing_synthetic_120hh.csv"
    fc_csv = ROOT / "housing_with_forecasts.csv"
    if not main_csv.exists() or not fc_csv.exists():
        raise FileNotFoundError(
            "Starter CSVs are missing. Restore from the repository or contact organisers."
        )
    print("Frozen starter data present — no regeneration in this strand build.")
    print(f"  {main_csv.name}")
    print(f"  {fc_csv.name}")


if __name__ == "__main__":
    main()
