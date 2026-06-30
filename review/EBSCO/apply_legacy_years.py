#!/usr/bin/env python3
"""
Apply legacy study years (and optional title/author) from the year entry template
to the main extraction CSV. Run after filling in legacy_studies_year_entry_template.csv.

Usage:
  python apply_legacy_years.py

Reads:  legacy_studies_year_entry_template.csv (year, title, first_author)
Updates: systematic_extraction_40_studies.csv (year, study_title, authors)
"""

import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "legacy_studies_year_entry_template.csv"
EXTRACTION_PATH = SCRIPT_DIR / "systematic_extraction_40_studies.csv"


def main():
    # Load template: only rows with non-empty year (or title/first_author) to apply
    updates = {}
    with open(TEMPLATE_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            so = row.get("study_order", "").strip()
            year = (row.get("year") or "").strip()
            title = (row.get("title") or "").strip()
            first_author = (row.get("first_author") or "").strip()
            if not so or so.startswith("#"):
                continue
            if year or title or first_author:
                updates[so] = {
                    "year": year,
                    "title": title,
                    "first_author": first_author,
                }

    if not updates:
        print("No legacy years/titles/authors to apply in the template.")
        return

    # Read main extraction CSV
    with open(EXTRACTION_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Normalize: legacy rows (study_order starting with L) with year "NA" -> ""
    for row in rows:
        if (row.get("study_order") or "").startswith("L") and (row.get("year") or "").strip().upper() == "NA":
            row["year"] = ""

    # Apply updates (match by study_order; only legacy rows like L2, L4, ...)
    applied = 0
    for row in rows:
        so = row.get("study_order", "")
        if so not in updates:
            continue
        u = updates[so]
        if u.get("year"):
            row["year"] = u["year"]
        if u.get("title"):
            row["study_title"] = u["title"]
        if u.get("first_author"):
            a = u["first_author"]
            if a and " et al" not in a.lower() and a.count(" ") < 2:
                row["authors"] = f"{a} et al." if " " not in a.strip() else a
            else:
                row["authors"] = a
        applied += 1

    # Write back
    with open(EXTRACTION_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Applied updates for {applied} legacy row(s). Study_orders: {', '.join(sorted(updates.keys()))}")
    print("Updated study_orders:", ", ".join(sorted(updates.keys())))


if __name__ == "__main__":
    main()
