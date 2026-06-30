#!/usr/bin/env python3
"""Backfill zotero_key and has_pdf on articles_master.csv from full crosswalk."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
from pathlib import Path

MASTER_DIR = Path(__file__).resolve().parent
LEGACY_DIR = MASTER_DIR.parent / "legacy"
DEFAULT_MASTER = MASTER_DIR / "articles_master.csv"
DEFAULT_CROSSWALK = LEGACY_DIR / "zotero_full_crosswalk.csv"

HIGH_CONFIDENCE_MATCH_TYPES = {"exact_doi", "exact_title", "zotero_key", "legacy_tag"}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def is_valid_zotero_key(key: str) -> bool:
    k = (key or "").strip()
    return bool(k) and k.lower() not in ("unknown", "none", "n/a")


def load_backfill_map(crosswalk_path: Path) -> dict[str, dict[str, str]]:
    """article_id -> {zotero_key, has_pdf, match_type}."""
    out: dict[str, dict[str, str]] = {}
    _, rows = read_csv(crosswalk_path)
    for row in rows:
        if row.get("status") not in ("linked", "already_in_master"):
            continue
        if row.get("match_type") not in HIGH_CONFIDENCE_MATCH_TYPES:
            continue
        aid = (row.get("master_article_id") or "").strip()
        zkey = (row.get("zotero_key") or "").strip()
        if not aid or not is_valid_zotero_key(zkey):
            continue
        has_pdf = (row.get("has_pdf") or "").strip().upper() == "Y"
        prev = out.get(aid)
        if prev:
            rank = {"exact_doi": 4, "zotero_key": 3, "exact_title": 2, "legacy_tag": 1}
            if rank.get(row["match_type"], 0) <= rank.get(prev["match_type"], 0):
                continue
        out[aid] = {
            "zotero_key": zkey,
            "has_pdf": "True" if has_pdf else "",
            "match_type": row["match_type"],
        }
    return out


def apply_backfill(
    master_rows: list[dict[str, str]],
    backfill_map: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], Counter]:
    today = date.today().isoformat()
    changes: Counter = Counter()

    for row in master_rows:
        aid = row.get("article_id", "")
        patch = backfill_map.get(aid)
        if not patch:
            continue

        new_key = patch["zotero_key"]
        existing_key = (row.get("zotero_key") or "").strip()

        if existing_key and existing_key != new_key:
            if existing_key.lower() not in ("unknown", "none", "n/a"):
                changes["skipped_key_conflict"] += 1
                continue

        if not existing_key or existing_key.lower() in ("unknown", "none", "n/a"):
            if row.get("zotero_key") != new_key:
                row["zotero_key"] = new_key
                changes["zotero_key_set"] += 1

        if patch["has_pdf"] == "True":
            current = (row.get("has_pdf") or "").strip()
            if current not in ("True", "true"):
                row["has_pdf"] = "True"
                changes["has_pdf_set"] += 1

        row["updated_at"] = today

    return master_rows, changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill zotero_key/has_pdf from crosswalk")
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.crosswalk.exists():
        raise SystemExit(f"Crosswalk not found: {args.crosswalk}. Run zotero_full_crosswalk.py first.")

    fieldnames, rows = read_csv(args.master)
    backfill_map = load_backfill_map(args.crosswalk)
    updated, changes = apply_backfill(rows, backfill_map)

    print(f"Backfill candidates: {len(backfill_map)}")
    for key, count in changes.most_common():
        print(f"  {key}: {count}")

    if args.dry_run:
        print("Dry run — master not written.")
        return

    write_csv(args.master, fieldnames, updated)
    print(f"Wrote {args.master}")


if __name__ == "__main__":
    main()
