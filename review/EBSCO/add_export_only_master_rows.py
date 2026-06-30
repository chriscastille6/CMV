#!/usr/bin/env python3
"""Add EBSCO search-order export rows (positions 21, 89, 148, 149, 150) to articles_master.csv.

These five rows appear in the 06_26_2026 native export but were previously off-pool
(no master row). Applies user Level 1 screening decisions and links PDFs in pdfs/imports/.

Usage:
  python3 review/EBSCO/add_export_only_master_rows.py
  python3 review/EBSCO/add_export_only_master_rows.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_DIR = ROOT / "review" / "master"
MASTER_PATH = MASTER_DIR / "articles_master.csv"

sys.path.insert(0, str(MASTER_DIR))
sys.path.insert(0, str(EBSCO_DIR))

from ebsco_search_order import load_search_order_entries, search_order_row_to_patch  # noqa: E402
from examination import enrich_master_records  # noqa: E402
from merge_sources import MASTER_COLUMNS  # noqa: E402
from publisher_outlet import infer_publisher_outlet  # noqa: E402
from screen_level1_batch import load_csv, master_file_lock, write_master  # noqa: E402

TODAY = date.today().isoformat()

EXPORT_ONLY_POSITIONS = (21, 89, 148, 149, 150)

PDF_BY_POSITION: dict[int, str] = {
    21: "review/EBSCO/pdfs/imports/Mollet_2026_jonm_2207579.pdf",
    149: "review/EBSCO/pdfs/imports/Lin_2025_s40359-025-03570-7.pdf",
}

# User L1 decisions (2026-06-26)
L1_BY_POSITION: dict[int, dict[str, str]] = {
    21: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "User decision 2026-06-26: include; borderline OB/nursing management "
            "(organizational dehumanization → perceived stress → depersonalization)."
        ),
        "examination_status": "read_snippet_only",
    },
    89: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "User decision 2026-06-26: exclude; Q1.1 domain out of scope — "
            "K-12 chemistry education (teacher–student relationship → chemistry achievement)."
        ),
        "examination_status": "read_snippet_only",
    },
    148: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "User decision 2026-06-26: exclude; Q1.1 domain out of scope — "
            "adaptive sports/disability participation (not management or OB)."
        ),
        "examination_status": "read_snippet_only",
    },
    149: {
        "screening_status": "excluded_pls",
        "screening_level1_include": "False",
        "screening_notes": (
            "User decision 2026-06-26: exclude_pls; PLS-SEM substantive focus "
            "(gig/algorithmic control → work engagement); routine CMV checks only."
        ),
        "examination_status": "read_snippet_only",
    },
    150: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "User decision 2026-06-26: exclude; Q1.1 domain out of scope — "
            "student financial literacy (Tanzania accounting & finance)."
        ),
        "examination_status": "read_snippet_only",
    },
}


def next_master_id(rows: list[dict[str, str]]) -> str:
    max_num = 0
    for row in rows:
        m = re.match(r"M(\d+)", row.get("article_id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"M{max_num + 1:04d}"


def empty_record() -> dict[str, str]:
    rec = {col: "" for col in MASTER_COLUMNS}
    rec["created_at"] = TODAY
    rec["updated_at"] = TODAY
    rec["screening_status"] = "pending"
    rec["extraction_status"] = "none"
    return rec


def build_row(entry: dict[str, str], article_id: str) -> dict[str, str]:
    pos = int(entry["ebsco_search_position"])
    patch = search_order_row_to_patch(entry)
    outlet, _ = infer_publisher_outlet(patch.get("doi", ""), patch.get("journal", ""))

    rec = empty_record()
    rec.update(patch)
    rec["article_id"] = article_id
    rec["publisher_outlet"] = outlet
    rec["sources"] = "ebsco_2026_search_order"
    rec["source_import_file"] = entry.get("import_file", "")
    rec["corpus_tier"] = "ebsco_screened"
    rec["notes"] = (
        f"ebsco_search_position={pos};ebsco_record_range={entry.get('record_range', '')};"
        "export_only_added=2026-06-26"
    )

    pdf_rel = PDF_BY_POSITION.get(pos, "")
    if pdf_rel and (ROOT / pdf_rel).exists():
        rec["pdf_path"] = pdf_rel
        rec["has_pdf"] = "True"
        rec["pdf_status"] = "available"
    else:
        rec["has_pdf"] = "False"
        rec["pdf_status"] = "missing"

    l1 = L1_BY_POSITION[pos]
    rec["screening_status"] = l1["screening_status"]
    rec["screening_level1_include"] = l1["screening_level1_include"]
    rec["screening_notes"] = l1["screening_notes"]
    rec["examination_status"] = l1["examination_status"]
    rec["updated_at"] = TODAY
    return rec


def add_export_only_rows(*, dry_run: bool = False) -> list[tuple[str, int]]:
    master = load_csv(MASTER_PATH)
    by_pos = {int(e["ebsco_search_position"]): e for e in load_search_order_entries()}
    added: list[tuple[str, int]] = []

    for pos in EXPORT_ONLY_POSITIONS:
        entry = by_pos.get(pos)
        if not entry:
            raise SystemExit(f"Missing search-order entry for position {pos}")

        doi = entry.get("doi", "")
        for row in master:
            if doi and row.get("doi", "").lower() == doi.lower():
                raise SystemExit(
                    f"Position {pos} DOI {doi} already in master as {row.get('article_id')}"
                )
            if entry.get("ebsco_an") and row.get("ebsco_an") == entry["ebsco_an"]:
                raise SystemExit(
                    f"Position {pos} AN {entry['ebsco_an']} already in master as {row.get('article_id')}"
                )

        article_id = next_master_id(master)
        rec = build_row(entry, article_id)
        master.append(rec)
        added.append((article_id, pos))
        print(f"  + {article_id}  EBSCO #{pos}  {rec['screening_status']}  {rec['title'][:60]}…")

    if dry_run:
        print(f"[dry-run] Would add {len(added)} row(s); master would be {len(master)} rows")
        return added

    master = enrich_master_records(master)
    master.sort(key=lambda r: r.get("article_id", ""))
    with master_file_lock():
        write_master(master, MASTER_COLUMNS)
    print(f"Wrote {MASTER_PATH} ({len(master)} rows)")
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description="Add export-only EBSCO rows to articles_master.csv")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    added = add_export_only_rows(dry_run=args.dry_run)
    if added:
        ids = ", ".join(f"{mid} (#{pos})" for mid, pos in added)
        print(f"Added: {ids}")


if __name__ == "__main__":
    main()
