#!/usr/bin/env python3
"""
Query examination status for AI agents and humans.

Examples:
  python3 review/master/check_examination_status.py --summary
  python3 review/master/check_examination_status.py --article-id M0001
  python3 review/master/check_examination_status.py --legacy-refid 142
  python3 review/master/check_examination_status.py --study-order L142
  python3 review/master/check_examination_status.py --doi 10.1111/joop.12503
  python3 review/master/check_examination_status.py --unexamined --limit 20
  python3 review/master/check_examination_status.py --tier legacy_gold --status read_snippet_only
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"


def norm_doi(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if v.startswith(prefix):
            v = v[len(prefix) :]
    return v.strip()


def load_master(path: Path = MASTER_PATH) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def record_summary(rec: dict[str, str]) -> dict[str, str]:
    return {
        "article_id": rec.get("article_id", ""),
        "title": (rec.get("title") or "")[:120],
        "legacy_refid": rec.get("legacy_refid", ""),
        "study_order": rec.get("study_order", ""),
        "doi": rec.get("doi", ""),
        "screening_status": rec.get("screening_status", ""),
        "extraction_status": rec.get("extraction_status", ""),
        "examination_status": rec.get("examination_status", ""),
        "pdf_status": rec.get("pdf_status", ""),
        "corpus_tier": rec.get("corpus_tier", ""),
        "examination_source": rec.get("examination_source", ""),
        "sources": rec.get("sources", ""),
        "has_pdf": rec.get("has_pdf", ""),
    }


def print_records(records: list[dict[str, str]], fmt: str) -> None:
    if not records:
        print("No matching records.")
        return
    if fmt == "json":
        print(json.dumps([record_summary(r) for r in records], indent=2))
        return
    for rec in records:
        s = record_summary(rec)
        print(
            f"{s['article_id']}\t{s['examination_status']}\t"
            f"refid={s['legacy_refid'] or '-'}\tstudy_order={s['study_order'] or '-'}\t"
            f"{s['title']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Query examination status from articles_master.csv")
    parser.add_argument("--article-id", help="Lookup by article_id (e.g. M0142)")
    parser.add_argument("--legacy-refid", help="Lookup by legacy Refid")
    parser.add_argument("--study-order", help="Lookup by study_order (e.g. L142 or 31)")
    parser.add_argument("--doi", help="Lookup by DOI")
    parser.add_argument("--ebsco-an", help="Lookup by EBSCO accession number")
    parser.add_argument("--status", choices=["not_read", "pdf_missing", "read_snippet_only", "partially_coded", "fully_coded"])
    parser.add_argument("--tier", choices=["legacy_gold", "extraction_coded", "ebsco_screened", "supplementary"])
    parser.add_argument("--unexamined", action="store_true", help="Shorthand for --status not_read")
    parser.add_argument("--included-only", action="store_true", help="Only screening_status=included")
    parser.add_argument("--summary", action="store_true", help="Print status histograms")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--master", type=Path, default=MASTER_PATH)
    args = parser.parse_args()

    rows = load_master(args.master)
    if not rows:
        print(f"No rows in {args.master}", file=sys.stderr)
        sys.exit(1)

    if args.summary:
        for col in ("examination_status", "pdf_status", "corpus_tier", "extraction_status", "screening_status"):
            counts = Counter(r.get(col, "") or "(empty)" for r in rows)
            print(f"## {col}")
            for key, count in counts.most_common():
                print(f"  {key}: {count}")
            print()
        return

    matches = rows
    if args.article_id:
        matches = [r for r in matches if r.get("article_id") == args.article_id]
    if args.legacy_refid:
        matches = [r for r in matches if r.get("legacy_refid") == str(args.legacy_refid)]
    if args.study_order:
        matches = [r for r in matches if r.get("study_order") == args.study_order]
    if args.doi:
        d = norm_doi(args.doi)
        matches = [r for r in matches if norm_doi(r.get("doi")) == d]
    if args.ebsco_an:
        matches = [r for r in matches if r.get("ebsco_an") == args.ebsco_an]
    if args.unexamined:
        matches = [r for r in matches if r.get("examination_status") == "not_read"]
    elif args.status:
        matches = [r for r in matches if r.get("examination_status") == args.status]
    if args.tier:
        matches = [r for r in matches if r.get("corpus_tier") == args.tier]
    if args.included_only:
        matches = [r for r in matches if r.get("screening_status") == "included"]

    print_records(matches[: args.limit], args.format)


if __name__ == "__main__":
    main()
