#!/usr/bin/env python3
"""
Apply Level 1 batch screening CSV to articles_master.csv and examination cohort.

Reads screening_batch_*.csv decisions and syncs screening_status, notes, and
examination_status from examination_cohort_on_hand.csv where available.

Usage:
  python3 review/EBSCO/apply_l1_batch_results.py
  python3 review/EBSCO/apply_l1_batch_results.py --batch review/EBSCO/screening_batch_cohort_on_hand_2026_06_25.csv
  python3 review/EBSCO/apply_l1_batch_results.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
COHORT_PATH = EBSCO_DIR / "examination_cohort_on_hand.csv"
DEFAULT_BATCH = EBSCO_DIR / "screening_batch_cohort_on_hand_2026_06_25.csv"

sys.path.insert(0, str(EBSCO_DIR))
from screen_level1_batch import (  # noqa: E402
    apply_results_to_master,
    load_csv,
    master_file_lock,
    write_master,
)


def decision_to_result(row: dict[str, str], cohort_row: dict[str, str] | None) -> dict:
    decision = (row.get("decision") or "").strip()
    mid = row["master_id"]
    title = row.get("title") or ""

    if decision == "included":
        screening_status = "included"
        level1_include = "True"
    elif decision == "excluded_pls":
        screening_status = "excluded_pls"
        level1_include = "False"
    elif decision == "excluded":
        screening_status = "level1_fail"
        level1_include = "False"
    elif decision == "manual_review":
        screening_status = "manual_review"
        level1_include = ""
    else:
        screening_status = "pending"
        level1_include = ""

    if cohort_row and cohort_row.get("screening_status"):
        cohort_ss = (cohort_row["screening_status"] or "").strip()
        if cohort_ss and cohort_ss != "pending":
            screening_status = cohort_ss
        elif cohort_ss == "pending" and decision == "manual_review":
            screening_status = "manual_review"

    if cohort_row and cohort_row.get("examination_status"):
        examination_status = cohort_row["examination_status"]
    elif screening_status == "manual_review":
        examination_status = "not_read"
    elif screening_status != "pending":
        examination_status = "read_snippet_only"
    else:
        examination_status = "not_read"

    note_parts = [
        f"L1 batch {date.today().isoformat()}",
        f"decision={decision}",
        (row.get("rationale") or "")[:120],
    ]
    if row.get("confidence"):
        note_parts.append(f"confidence={row['confidence']}")

    return {
        "master_id": mid,
        "title": title,
        "screening_status": screening_status,
        "screening_level1_include": level1_include,
        "screening_notes": "; ".join(p for p in note_parts if p),
        "examination_status": examination_status,
    }


def apply_batch(batch_path: Path, *, dry_run: bool = False) -> int:
    batch_rows = load_csv(batch_path)
    if not batch_rows:
        raise RuntimeError(f"No rows in {batch_path}")

    cohort_by_id = {r["article_id"]: r for r in load_csv(COHORT_PATH) if r.get("article_id")}
    results = [
        decision_to_result(row, cohort_by_id.get(row["master_id"]))
        for row in batch_rows
        if row.get("master_id")
    ]

    if dry_run:
        from collections import Counter

        counts = Counter(r["screening_status"] for r in results)
        print(f"[dry-run] Would update {len(results)} rows from {batch_path.name}")
        for status, n in sorted(counts.items()):
            print(f"  {status}: {n}")
        return len(results)

    apply_results_to_master(results, dry_run=False)

    # Keep cohort CSV aligned with master screening_status
    with master_file_lock():
        master_by_id = {r["article_id"]: r for r in load_csv(MASTER_PATH) if r.get("article_id")}
        cohort_rows = load_csv(COHORT_PATH)
        if cohort_rows:
            fieldnames = list(cohort_rows[0].keys())
            for row in cohort_rows:
                mid = row.get("article_id", "")
                master_row = master_by_id.get(mid)
                if not master_row:
                    continue
                row["screening_status"] = master_row.get("screening_status", "")
                row["examination_status"] = master_row.get("examination_status", "")
            with open(COHORT_PATH, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                w.writeheader()
                w.writerows(cohort_rows)

    return len(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply L1 batch CSV to articles_master")
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    n = apply_batch(args.batch, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"Synced {n} cohort rows; re-run progress_counter.py for dashboard refresh.")


if __name__ == "__main__":
    main()
