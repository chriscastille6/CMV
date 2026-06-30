#!/usr/bin/env python3
"""Define the EBSCO on-hand PDF examination cohort (excludes legacy 182 holdout).

Writes:
  - review/EBSCO/examination_cohort_on_hand.csv
  - review/EBSCO/EXAMINATION_COHORT_ON_HAND.md
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
POOL_PATH = EBSCO_DIR / "ebsco_screening_pool_570.csv"
COHORT_CSV = EBSCO_DIR / "examination_cohort_on_hand.csv"
COHORT_MD = EBSCO_DIR / "EXAMINATION_COHORT_ON_HAND.md"


def load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_bool(v: str | None) -> bool:
    return str(v or "").strip().lower() in ("true", "1", "yes", "y")


def has_pdf(row: dict[str, str]) -> bool:
    if parse_bool(row.get("has_pdf")):
        return True
    return bool((row.get("pdf_path") or "").strip())


def pdf_exists(row: dict[str, str]) -> bool:
    rel = (row.get("pdf_path") or "").strip()
    if rel and (ROOT / rel).exists():
        return True
    mid = row.get("article_id", "")
    if mid:
        matches = list((EBSCO_DIR / "pdfs").glob(f"EBSCO_{mid}_*.pdf"))
        return bool(matches)
    return False


def is_ebsco_pool_member(row: dict[str, str], pool_ids: set[str]) -> bool:
    mid = row.get("article_id", "")
    if mid in pool_ids:
        return True
    sources = (row.get("sources") or "").lower()
    return "ebsco_2026" in sources or "ebsco" in sources


def is_legacy_holdout(row: dict[str, str]) -> bool:
    """Original systematic review (182) — replication holdout; exclude from live cohort."""
    if parse_bool(row.get("legacy_final_include")):
        return True
    if (row.get("legacy_refid") or "").strip():
        return True
    tier = (row.get("corpus_tier") or "").lower()
    if tier == "legacy_gold":
        return True
    sources = (row.get("sources") or "").lower()
    if "legacy_182" in sources and "ebsco" not in sources:
        return True
    if row.get("examination_status") == "fully_coded":
        src = (row.get("examination_source") or "").lower()
        if "legacy" in src or tier == "legacy_gold":
            return True
    return False


def build_cohort() -> tuple[list[dict[str, str]], dict]:
    master = load_csv(MASTER_PATH)
    pool = load_csv(POOL_PATH)
    pool_ids = {r["master_article_id"] for r in pool if r.get("master_article_id")}

    cohort: list[dict[str, str]] = []
    excluded: list[tuple[str, str]] = []

    for row in master:
        mid = row.get("article_id", "")
        if not is_ebsco_pool_member(row, pool_ids):
            continue
        if is_legacy_holdout(row):
            excluded.append((mid, "legacy holdout (182 replication)"))
            continue
        if not has_pdf(row) or not pdf_exists(row):
            continue
        cohort.append(row)

    cohort.sort(key=lambda r: r.get("article_id", ""))

    stats = {
        "cohort_n": len(cohort),
        "excluded_legacy": sum(1 for _, r in excluded if "legacy" in r),
        "screening": Counter(r.get("screening_status", "") for r in cohort),
        "examination": Counter(r.get("examination_status", "") for r in cohort),
    }
    return cohort, stats


def write_cohort_csv(cohort: list[dict[str, str]]) -> None:
    cols = [
        "article_id",
        "title",
        "authors",
        "year",
        "journal",
        "doi",
        "pdf_path",
        "screening_status",
        "examination_status",
        "study_order",
    ]
    with open(COHORT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in cohort:
            w.writerow({c: row.get(c, "") for c in cols})


def write_cohort_md(cohort: list[dict[str, str]], stats: dict) -> None:
    today = date.today().isoformat()
    ids = [r["article_id"] for r in cohort]
    screening = stats["screening"]
    examination = stats["examination"]

    lines = [
        "# EBSCO On-Hand PDF Examination Cohort",
        "",
        f"**Generated**: {today}",
        f"**Cohort size**: {stats['cohort_n']} articles",
        "",
        "## Purpose",
        "",
        "Live examination cohort for the EBSCO June 2026 search strand. The original",
        "systematic review (**legacy 182**) is held out for replication and must **not**",
        "be merged into this cohort or `systematic_extraction_ebsco_on_hand.csv`.",
        "",
        "## Inclusion rules",
        "",
        "1. Row in `review/master/articles_master.csv` with `has_pdf=True` (or non-empty `pdf_path`)",
        "2. PDF file exists on disk under `review/EBSCO/pdfs/`",
        "3. EBSCO 570 pool membership (`ebsco_screening_pool_570.csv`) **or** `ebsco_2026` / `ebsco` in `sources`",
        "",
        "## Exclusion rules",
        "",
        "1. `legacy_final_include=TRUE`",
        "2. Non-empty `legacy_refid` (original 182 studies)",
        "3. `corpus_tier=legacy_gold` or legacy-only `fully_coded` from prior extraction",
        "",
        "## Current status snapshot",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| Cohort N | {stats['cohort_n']} |",
    ]
    for k, v in sorted(screening.items()):
        lines.append(f"| screening_status={k or '(empty)'} | {v} |")
    for k, v in sorted(examination.items()):
        lines.append(f"| examination_status={k or '(empty)'} | {v} |")

    lines.extend([
        "",
        "## Output files",
        "",
        "- `review/EBSCO/examination_cohort_on_hand.csv` — machine-readable cohort list",
        "- `review/EBSCO/systematic_extraction_ebsco_on_hand.csv` — new extractions (separate from legacy)",
        "",
        "## master_id list",
        "",
        f"Total: **{len(ids)}**",
        "",
        "```",
        ", ".join(ids),
        "```",
        "",
    ])
    COHORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    cohort, stats = build_cohort()
    write_cohort_csv(cohort)
    write_cohort_md(cohort, stats)
    print(f"Cohort: {stats['cohort_n']} articles")
    print(f"Wrote {COHORT_CSV}")
    print(f"Wrote {COHORT_MD}")


if __name__ == "__main__":
    main()
