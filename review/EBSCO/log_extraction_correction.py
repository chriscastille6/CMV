#!/usr/bin/env python3
"""
Log a manual or agent correction to extraction_corrections.csv.

Optionally apply the correction to systematic_extraction_40_studies.csv with --apply.

Usage:
  python3 review/EBSCO/log_extraction_correction.py \\
    --study-order 3 --field pls_sem_used --old TRUE --new FALSE --note "CB-SEM study"

  python3 review/EBSCO/log_extraction_correction.py \\
    --study-order 3 --field harman_deployed --old NA --new TRUE --apply
"""

from __future__ import annotations

import argparse
import csv
import uuid
from datetime import date
from pathlib import Path

EBSCO_DIR = Path(__file__).resolve().parent
CORRECTIONS_PATH = EBSCO_DIR / "extraction_corrections.csv"
EXTRACTION_PATH = EBSCO_DIR / "systematic_extraction_40_studies.csv"

CORRECTION_COLUMNS = [
    "correction_id",
    "corrected_at",
    "study_order",
    "field_name",
    "old_value",
    "new_value",
    "source",
    "rationale",
    "pdf_path",
]


def next_correction_id(existing_rows: list[dict]) -> str:
    """Short sequential id: c001, c002, ..."""
    max_num = 0
    for row in existing_rows:
        cid = (row.get("correction_id") or "").strip()
        if cid.startswith("c") and cid[1:].isdigit():
            max_num = max(max_num, int(cid[1:]))
    return f"c{max_num + 1:03d}"


def read_corrections() -> list[dict]:
    if not CORRECTIONS_PATH.exists():
        return []
    with CORRECTIONS_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_corrections(rows: list[dict]) -> None:
    with CORRECTIONS_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CORRECTION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def study_order_key(value: str) -> str:
    return str(value).strip()


def apply_to_extraction(study_order: str, field_name: str, new_value: str) -> None:
    if not EXTRACTION_PATH.exists():
        raise FileNotFoundError(f"Extraction CSV not found: {EXTRACTION_PATH}")

    with EXTRACTION_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if field_name not in fieldnames:
        raise ValueError(f"Unknown field '{field_name}' in {EXTRACTION_PATH.name}")

    target = study_order_key(study_order)
    matched = [r for r in rows if study_order_key(r.get("study_order", "")) == target]
    if not matched:
        raise ValueError(f"No row with study_order={study_order!r} in {EXTRACTION_PATH.name}")

    for row in rows:
        if study_order_key(row.get("study_order", "")) == target:
            row[field_name] = new_value

    with EXTRACTION_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Log an extraction field correction.")
    parser.add_argument("--study-order", required=True, help="study_order (or master_id) in extraction CSV")
    parser.add_argument("--field", required=True, help="Column name to correct")
    parser.add_argument("--old", required=True, help="Previous value (use NA for missing)")
    parser.add_argument("--new", required=True, help="Corrected value")
    parser.add_argument(
        "--source",
        default="manual",
        choices=["manual", "agent", "pipeline"],
        help="Who made the correction (default: manual)",
    )
    parser.add_argument("--note", default="", help="Optional rationale or quote")
    parser.add_argument("--pdf-path", default="", help="Optional PDF path for traceability")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Also update systematic_extraction_40_studies.csv",
    )
    parser.add_argument(
        "--id",
        dest="correction_id",
        default="",
        help="Override correction_id (default: auto cNNN)",
    )
    args = parser.parse_args()

    rows = read_corrections()
    correction_id = args.correction_id.strip() or next_correction_id(rows)

    entry = {
        "correction_id": correction_id,
        "corrected_at": date.today().isoformat(),
        "study_order": study_order_key(args.study_order),
        "field_name": args.field.strip(),
        "old_value": args.old,
        "new_value": args.new,
        "source": args.source,
        "rationale": args.note,
        "pdf_path": args.pdf_path,
    }
    rows.append(entry)
    write_corrections(rows)

    print(f"Logged {correction_id}: study_order={entry['study_order']} "
          f"{entry['field_name']} {entry['old_value']} -> {entry['new_value']}")

    if args.apply:
        apply_to_extraction(entry["study_order"], entry["field_name"], entry["new_value"])
        print(f"Applied to {EXTRACTION_PATH.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
