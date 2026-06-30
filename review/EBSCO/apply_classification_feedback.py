#!/usr/bin/env python3
"""
Apply user classification feedback to articles_master.csv.

Reads review/EBSCO/classification_feedback.csv and updates screening_status,
screening_notes, and screening_level1_include. Triggers extraction for newly
included articles.

Usage:
  # Edit classification_feedback.csv (user_decision column), then:
  python3 review/EBSCO/apply_classification_feedback.py
  python3 review/EBSCO/apply_classification_feedback.py --dry-run

  # Quick chat feedback (same as filling one CSV row):
  python3 review/EBSCO/apply_classification_feedback.py --decision M0244 include --notes "management domain confirmed"

Valid user_decision values: include, exclude, exclude_pls, manual_review
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
FEEDBACK_CSV = EBSCO_DIR / "classification_feedback.csv"
COHORT_PATH = EBSCO_DIR / "examination_cohort_on_hand.csv"

sys.path.insert(0, str(EBSCO_DIR))
from screen_level1_batch import load_csv, master_file_lock, write_master  # noqa: E402

DECISION_MAP = {
    "include": ("included", "True"),
    "included": ("included", "True"),
    "exclude": ("level1_fail", "False"),
    "excluded": ("level1_fail", "False"),
    "exclude_pls": ("excluded_pls", "False"),
    "excluded_pls": ("excluded_pls", "False"),
    "manual_review": ("manual_review", ""),
    "pending": ("pending", ""),
}

FEEDBACK_COLUMNS = [
    "master_id",
    "ebsco_search_position",
    "title",
    "current_screening_status",
    "user_decision",
    "user_notes",
    "applied",
]


def normalize_decision(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(" ", "_")


def apply_row_to_master(
    master_row: dict[str, str],
    decision: str,
    notes: str,
    *,
    today: str,
) -> bool:
    key = normalize_decision(decision)
    if key not in DECISION_MAP:
        return False

    screening_status, level1_include = DECISION_MAP[key]
    master_row["screening_status"] = screening_status
    master_row["screening_level1_include"] = level1_include
    note = f"User feedback {today}: {decision}"
    if notes:
        note += f"; {notes}"
    existing = (master_row.get("screening_notes") or "").strip()
    master_row["screening_notes"] = f"{existing}; {note}".strip("; ") if existing else note
    master_row["updated_at"] = today

    if screening_status == "included":
        master_row["examination_status"] = master_row.get("examination_status") or "read_snippet_only"
    elif screening_status in ("level1_fail", "excluded_pls"):
        master_row["examination_status"] = "read_snippet_only"
    elif screening_status == "manual_review":
        master_row["examination_status"] = "not_read"

    return True


def sync_cohort_from_master(master_by_id: dict[str, dict[str, str]]) -> int:
    cohort_rows = load_csv(COHORT_PATH)
    if not cohort_rows:
        return 0
    fieldnames = list(cohort_rows[0].keys())
    updated = 0
    for row in cohort_rows:
        mid = row.get("article_id", "")
        master_row = master_by_id.get(mid)
        if not master_row:
            continue
        row["screening_status"] = master_row.get("screening_status", "")
        row["examination_status"] = master_row.get("examination_status", "")
        updated += 1
    with open(COHORT_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(cohort_rows)
    return updated


def trigger_extraction(master_ids: list[str], *, dry_run: bool) -> None:
    if not master_ids:
        return
    cmd = [
        sys.executable,
        str(EBSCO_DIR / "extract_ebsco_on_hand_batch.py"),
        "--limit",
        "0",
    ]
    for mid in master_ids:
        cmd.extend(["--master-id", mid])
    if dry_run:
        print(f"[dry-run] Would run: {' '.join(cmd)}")
        return
    print(f"Triggering extraction for {len(master_ids)} included article(s)...")
    subprocess.run(cmd, cwd=ROOT, check=False)


def apply_feedback(
    feedback_path: Path,
    *,
    dry_run: bool = False,
    inline_decisions: list[tuple[str, str, str]] | None = None,
) -> dict[str, int]:
    today = date.today().isoformat()
    feedback_rows = load_csv(feedback_path) if feedback_path.exists() else []
    feedback_by_id = {r["master_id"]: r for r in feedback_rows if r.get("master_id")}

    if inline_decisions:
        for mid, decision, notes in inline_decisions:
            row = feedback_by_id.get(mid, {
                "master_id": mid,
                "ebsco_search_position": "",
                "title": "",
                "current_screening_status": "",
                "user_decision": "",
                "user_notes": "",
                "applied": "N",
            })
            row["user_decision"] = decision
            if notes:
                row["user_notes"] = notes
            feedback_by_id[mid] = row

    to_apply = [
        r for r in feedback_by_id.values()
        if normalize_decision(r.get("user_decision", "")) in DECISION_MAP
        and (r.get("applied") or "N").upper() != "Y"
    ]

    stats = {"applied": 0, "skipped": 0, "included_for_extraction": 0}
    included_ids: list[str] = []

    with master_file_lock():
        master_rows = load_csv(MASTER_PATH)
        if not master_rows:
            raise RuntimeError("articles_master.csv empty")
        fieldnames = list(master_rows[0].keys())
        master_by_id = {r["article_id"]: r for r in master_rows}

        for fb in to_apply:
            mid = fb["master_id"]
            master_row = master_by_id.get(mid)
            if not master_row:
                stats["skipped"] += 1
                continue
            decision = fb["user_decision"]
            notes = fb.get("user_notes") or ""
            if not apply_row_to_master(master_row, decision, notes, today=today):
                stats["skipped"] += 1
                continue
            fb["applied"] = "Y"
            fb["current_screening_status"] = master_row["screening_status"]
            stats["applied"] += 1
            if normalize_decision(decision) in ("include", "included"):
                included_ids.append(mid)

        if dry_run:
            print(f"[dry-run] Would apply {stats['applied']} feedback row(s)")
            if included_ids:
                trigger_extraction(included_ids, dry_run=True)
            return stats

        write_master(master_rows, fieldnames)
        master_by_id = {r["article_id"]: r for r in master_rows}
        sync_cohort_from_master(master_by_id)

    # Write updated feedback CSV
    out_rows = list(feedback_by_id.values())
    out_rows.sort(key=lambda r: r.get("master_id", ""))
    with open(feedback_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FEEDBACK_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    trigger_extraction(included_ids, dry_run=False)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply classification feedback CSV")
    parser.add_argument("--feedback", type=Path, default=FEEDBACK_CSV)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--decision", nargs=2, metavar=("MASTER_ID", "DECISION"))
    parser.add_argument("--notes", default="", help="Notes for --decision")
    args = parser.parse_args()

    inline = None
    if args.decision:
        inline = [(args.decision[0].upper(), args.decision[1], args.notes)]

    stats = apply_feedback(args.feedback, dry_run=args.dry_run, inline_decisions=inline)
    print(f"Applied: {stats['applied']} | Skipped: {stats['skipped']}")
    if stats["applied"] and not args.dry_run:
        print("Re-run: python3 review/master/progress_counter.py")


if __name__ == "__main__":
    main()
