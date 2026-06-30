#!/usr/bin/env python3
"""Backfill publisher_outlet columns in systematic_extraction_40_studies.csv from DOI/journal."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from publisher_outlet import infer_publisher_outlet

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "review" / "EBSCO" / "systematic_extraction_40_studies.csv"

NEW_COLUMNS = (
    "publisher_outlet",
    "publisher_outlet_detail",
    "details_in_supplement",
    "extraction_incomplete_main_text",
    "supplement_notes",
)


def main() -> int:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    for col in NEW_COLUMNS:
        if col not in fieldnames:
            if col == "publisher_outlet":
                insert_at = fieldnames.index("doi") + 1 if "doi" in fieldnames else len(fieldnames)
                fieldnames.insert(insert_at, col)
                insert_at += 1
                for rest in NEW_COLUMNS[1:]:
                    if rest not in fieldnames:
                        fieldnames.insert(insert_at, rest)
                        insert_at += 1
            else:
                fieldnames.append(col)

    mdpi = frontiers = 0
    for row in rows:
        for col in NEW_COLUMNS:
            row.setdefault(col, "NA" if col != "supplement_notes" else "")

        existing = (row.get("publisher_outlet") or "").strip()
        if existing and existing.upper() != "NA":
            continue

        outlet, detail = infer_publisher_outlet(row.get("doi"), row.get("journal"))
        if outlet != "NA":
            row["publisher_outlet"] = outlet
            if detail and not (row.get("publisher_outlet_detail") or "").strip():
                row["publisher_outlet_detail"] = detail
            if outlet == "MDPI":
                mdpi += 1
            elif outlet == "Frontiers":
                frontiers += 1

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Backfilled MDPI: {mdpi}, Frontiers: {frontiers} (total rows: {len(rows)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
