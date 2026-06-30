#!/usr/bin/env python3
"""Backfill examination_* columns on articles_master.csv."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from examination import (
    EXAMINATION_COLUMNS,
    enrich_master_records,
)

MASTER_DIR = Path(__file__).resolve().parent
DEFAULT_MASTER = MASTER_DIR / "articles_master.csv"


def read_master(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def write_master(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ensure_columns(fieldnames: list[str]) -> list[str]:
    out = list(fieldnames)
    for col in EXAMINATION_COLUMNS:
        if col not in out:
            out.append(col)
    return out


def print_summary(rows: list[dict[str, str]]) -> None:
    print(f"Total rows: {len(rows)}")
    for col in ("examination_status", "pdf_status", "corpus_tier", "extraction_status"):
        counts = Counter(r.get(col, "") or "(empty)" for r in rows)
        print(f"\n{col}:")
        for key, count in counts.most_common():
            print(f"  {key}: {count}")

    overlap = [
        r
        for r in rows
        if "legacy_182" in r.get("sources", "")
        and "extraction_csv" in r.get("sources", "")
    ]
    print(f"\nlegacy_182 + extraction_csv overlap: {len(overlap)}")
    ext_fix = Counter(r.get("extraction_status") for r in overlap)
    print(f"  extraction_status after fix: {dict(ext_fix)}")
    exam_overlap = Counter(r.get("examination_status") for r in overlap)
    print(f"  examination_status: {dict(exam_overlap)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill examination status on master CSV")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_MASTER,
        help="Input articles_master.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: overwrite input)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print summary only")
    args = parser.parse_args()

    fieldnames, rows = read_master(args.input)
    enriched = enrich_master_records(rows)
    fieldnames = ensure_columns(fieldnames)

    if args.dry_run:
        print_summary(enriched)
        return

    out = args.output or args.input
    write_master(out, fieldnames, enriched)
    print(f"Wrote {out}")
    print_summary(enriched)


if __name__ == "__main__":
    main()
