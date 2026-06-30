#!/usr/bin/env python3
"""Add/update publisher_outlet on articles_master.csv from DOI + journal (lightweight screening column)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from publisher_outlet import infer_publisher_outlet

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
COLUMN = "publisher_outlet"


def main() -> int:
    with MASTER_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    if COLUMN not in fieldnames:
        insert_at = fieldnames.index("doi") + 1 if "doi" in fieldnames else len(fieldnames)
        fieldnames.insert(insert_at, COLUMN)

    counts: dict[str, int] = {}
    for row in rows:
        existing = (row.get(COLUMN) or "").strip()
        if existing and existing.upper() != "NA":
            outlet = existing
        else:
            outlet, _ = infer_publisher_outlet(row.get("doi"), row.get("journal"))
            row[COLUMN] = outlet
        counts[outlet] = counts.get(outlet, 0) + 1

    with MASTER_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    mdpi = counts.get("MDPI", 0)
    frontiers = counts.get("Frontiers", 0)
    print(f"articles_master rows: {len(rows)}")
    print(f"MDPI: {mdpi}, Frontiers: {frontiers}")
    print(f"All outlets: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
