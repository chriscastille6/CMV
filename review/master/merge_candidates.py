#!/usr/bin/env python3
"""Read-only preview of merge candidates from probable_duplicates_review.csv.

Does NOT modify articles_master.csv. Use after human review of duplicate pairs.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_DIR = ROOT / "review" / "master"
MASTER_PATH = MASTER_DIR / "articles_master.csv"
REVIEW_CSV = MASTER_DIR / "probable_duplicates_review.csv"

MERGE_RECOMMENDATIONS = frozenset({"merge", "link"})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def pick_survivor(a: dict[str, str], b: dict[str, str]) -> tuple[str, str]:
    """Return (keep_id, drop_id) using simple heuristics."""
    score = lambda r: (  # noqa: E731
        (10 if r.get("legacy_refid") else 0)
        + (8 if "legacy_182" in (r.get("sources") or "") else 0)
        + (6 if (r.get("extraction_status") or "") not in ("", "none") else 0)
        + (4 if (r.get("has_pdf") or "").lower() == "true" else 0)
        + (2 if (r.get("study_order") or "").strip() else 0)
        + (1 if (r.get("zotero_key") or "").strip() else 0)
    )
    aid_a = a.get("article_id", "")
    aid_b = b.get("article_id", "")
    if score(a) > score(b):
        return aid_a, aid_b
    if score(b) > score(a):
        return aid_b, aid_a
    return (aid_a, aid_b) if aid_a < aid_b else (aid_b, aid_a)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview merge candidates (read-only)")
    parser.add_argument(
        "--recommendation",
        choices=["merge", "link", "all"],
        default="merge",
        help="Filter by recommendation (default: merge only)",
    )
    parser.add_argument("--group", metavar="G####", help="Show one group_id only")
    args = parser.parse_args()

    if not REVIEW_CSV.exists():
        print(f"Run find_duplicates.py first: {REVIEW_CSV} not found")
        return 1

    master = {r["article_id"]: r for r in read_csv(MASTER_PATH)}
    pairs = read_csv(REVIEW_CSV)

    filtered = [
        p
        for p in pairs
        if args.recommendation == "all" or p.get("recommendation") == args.recommendation
    ]
    if args.group:
        filtered = [p for p in filtered if p.get("group_id") == args.group]

    if not filtered:
        print("No matching pairs.")
        return 0

    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for p in filtered:
        gid = p.get("group_id") or "ungrouped"
        by_group[gid].append(p)

    print(f"Merge candidate preview ({len(filtered)} pairs, {len(by_group)} groups)\n")
    print("READ-ONLY — no files modified.\n")

    for gid in sorted(by_group):
        print(f"=== {gid} ===")
        for p in by_group[gid]:
            aid_a = p.get("article_id_a", "")
            aid_b = p.get("article_id_b", "")
            ra = master.get(aid_a, {})
            rb = master.get(aid_b, {})
            keep, drop = pick_survivor(ra, rb)
            print(
                f"  {aid_a} <-> {aid_b} | {p.get('match_type')} | "
                f"rec={p.get('recommendation')} | suggest keep {keep}, retire {drop}"
            )
            if p.get("doi"):
                print(f"    DOI: {p['doi']}")
            if p.get("legacy_refid"):
                print(f"    legacy_refid: {p['legacy_refid']}")
        print()

    print("After adjudication: manually merge rows or add cross-reference notes.")
    print("Re-run find_duplicates.py to verify cluster counts drop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
