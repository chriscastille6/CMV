#!/usr/bin/env python3
"""
Progress counter for the EBSCO PRISMA screening pool (570 articles).

Builds or refreshes the canonical pool file, prints status, and writes:
  - review/EBSCO/ebsco_screening_pool_570.csv
  - review/EBSCO/download_queue_ebsco_order.csv
  - review/EBSCO/missed_in_first_150.csv
  - review/EBSCO/MISSED_IN_FIRST_150.md
  - review/DOWNLOAD_EXAMINATION_PROGRESS.md
  - review/download_progress_summary.csv
  - review/progress_dashboard_data.json
  - review/ebsco_on_hand_cohort_data.json
  - review/ebsco_worklist_1_150_data.json
  - review/prisma_flow_data.json
  - review/progress_results_data.json
  - review/progress_summary_data.json
  - review/progress_extraction_summary_data.json
  - review/progress_ebsco_150_summary_data.json
  - review/PROGRESS_DASHBOARD.html

Examples:
  python3 review/master/progress_counter.py
  python3 review/master/progress_counter.py --build-only
  python3 review/master/progress_counter.py --no-write
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from build_results_tables import (
    EXTRACTION_SUMMARY_JSON,
    build_results_payload,
    build_summary_payload,
    summary_table,
    write_results_json,
    write_summary_json,
)
from examination import load_combined_extraction_rows

try:
    from journal_ulmc_table import build_journal_ulmc_payload, write_outputs as write_journal_ulmc_outputs
except ImportError:
    build_journal_ulmc_payload = None  # type: ignore[misc, assignment]
    write_journal_ulmc_outputs = None  # type: ignore[misc, assignment]

try:
    from audit_results import run_audit as run_results_audit
except ImportError:
    run_results_audit = None  # type: ignore[misc, assignment]

ROOT = Path(__file__).resolve().parents[2]

EBSCO_DIR = ROOT / "review" / "EBSCO"
if str(EBSCO_DIR) not in sys.path:
    sys.path.insert(0, str(EBSCO_DIR))

from publisher_outlet import infer_publisher_outlet  # noqa: E402
from build_ebsco_150_summary import (  # noqa: E402
    build_ebsco_150_summary_payload,
    write_ebsco_150_summary_json,
)
from ebsco_search_order import (  # noqa: E402
    FIRST_150_SIZE,
    QUEUE_FILENAME,
    build_position_lookups,
    load_worklist_1_150_from_master,
    lookup_search_position,
)

from dashboard_html import format_dashboard_html

AUDIT_REPORT = ROOT / "review" / "audit_results_report.md"
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
CROSSWALK_PATH = ROOT / "review" / "legacy" / "zotero_full_crosswalk.csv"
POOL_PATH = ROOT / "review" / "EBSCO" / "ebsco_screening_pool_570.csv"
QUEUE_PATH = ROOT / "review" / "EBSCO" / QUEUE_FILENAME
MISSED_CSV = ROOT / "review" / "EBSCO" / "missed_in_first_150.csv"
MISSED_MD = ROOT / "review" / "EBSCO" / "MISSED_IN_FIRST_150.md"
PROGRESS_MD = ROOT / "review" / "DOWNLOAD_EXAMINATION_PROGRESS.md"
SUMMARY_CSV = ROOT / "review" / "download_progress_summary.csv"
DASHBOARD_JSON = ROOT / "review" / "progress_dashboard_data.json"
PRISMA_FLOW_JSON = ROOT / "review" / "prisma_flow_data.json"
RESULTS_JSON = ROOT / "review" / "progress_results_data.json"
SUMMARY_JSON = ROOT / "review" / "progress_summary_data.json"
DASHBOARD_HTML = ROOT / "review" / "PROGRESS_DASHBOARD.html"
COHORT_ON_HAND_CSV = ROOT / "review" / "EBSCO" / "examination_cohort_on_hand.csv"
ON_HAND_COHORT_JSON = ROOT / "review" / "ebsco_on_hand_cohort_data.json"
WORKLIST_1150_JSON = ROOT / "review" / "ebsco_worklist_1_150_data.json"
EBSCO_150_SUMMARY_JSON = ROOT / "review" / "progress_ebsco_150_summary_data.json"
EVIDENCE_PATH = ROOT / "review" / "EBSCO" / "ebsco_150_screening_evidence.csv"
VERIFICATION_SAMPLE_PATH = ROOT / "review" / "EBSCO" / "VERIFICATION_SAMPLE.md"
VERIFICATION_MASTER_IDS = ("M0183", "M0244", "M0282")
LEGACY_INCLUDED_HOLDOUT = 182

PRISMA_IDENTIFIED = 1036  # legacy full-query total (570-pool strand)
PRISMA_INCLUDED_DEFAULT = 182  # legacy gold-standard holdout
EBSCO_EXPORT_1150 = 150
EBSCO_OFF_POOL_1150 = 0  # positions 21, 89, 148, 149, 150 now in master (2026-06-26)
EXTRACTION_PATH = ROOT / "review" / "EBSCO" / "systematic_extraction_40_studies.csv"

PRISMA_POOL_SIZE = 570
EXPORT_GAP_SIZE = 50  # EBSCO positions 251-300 not yet exported
KNOWN_IN_MASTER = 511  # documented unique EBSCO June 2026 imports in master

POOL_COLUMNS = [
    "pool_id",
    "title",
    "authors",
    "year",
    "journal",
    "publisher_outlet",
    "publisher_outlet_detail",
    "doi",
    "ebsco_an",
    "ebsco_search_position",
    "in_master",
    "master_article_id",
    "pool_status",
    "gap_reason",
    "pdf_status",
    "examination_status",
    "zotero_key",
    "pdf_path",
    "sort_rank",
    "notes",
]

SUMMARY_METRICS = [
    "screening_pool_total",
    "in_master_registry",
    "pool_gap_rows",
    "pdf_downloaded",
    "pdf_in_zotero",
    "pdf_missing",
    "exam_fully_coded",
    "exam_partially_coded",
    "exam_read_snippet_only",
    "exam_not_read",
    "exam_unknown",
    "remaining_to_download",
    "remaining_to_examine",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_year(value: str | None) -> int:
    if not value:
        return 0
    s = str(value).strip()
    if s.isdigit():
        return int(s)
    for part in s.split("-"):
        if part.isdigit() and len(part) == 4:
            return int(part)
    return 0


def is_ebsco_pool_member(rec: dict[str, str]) -> bool:
    sources = rec.get("sources", "") or ""
    if "ebsco_2026" in sources:
        return True
    return rec.get("corpus_tier", "") == "ebsco_screened"


def pool_pdf_status(rec: dict[str, str], zotero_has_pdf: bool) -> str:
    if rec.get("has_pdf", "").lower() == "true":
        return "downloaded"
    if (rec.get("pdf_path") or "").strip():
        return "downloaded"
    if rec.get("pdf_status", "") == "available":
        return "downloaded"
    if zotero_has_pdf:
        return "downloaded"
    if (rec.get("zotero_key") or "").strip():
        return "in_zotero"
    return "missing"


def load_zotero_pdf_keys(path: Path) -> set[str]:
    """Return zotero_keys that have an attached PDF in the crosswalk."""
    rows = load_csv(path)
    if not rows:
        return set()
    keys: set[str] = set()
    for row in rows:
        key = (row.get("zotero_key") or row.get("item_key") or "").strip()
        if not key:
            continue
        has_pdf = (
            (row.get("has_pdf") or row.get("has_attachment") or "").lower() in ("true", "yes", "1")
            or (row.get("pdf_path") or row.get("attachment_path") or "").strip()
        )
        if has_pdf:
            keys.add(key)
    return keys


def build_pool_rows(
    master: list[dict[str, str]],
    zotero_pdf_keys: set[str],
    *,
    by_doi: dict[str, int] | None = None,
    by_an: dict[str, int] | None = None,
) -> list[dict[str, str]]:
    if by_doi is None or by_an is None:
        by_doi, by_an, _ = build_position_lookups()

    members = [r for r in master if is_ebsco_pool_member(r)]
    members.sort(key=lambda r: (-parse_year(r.get("year")), (r.get("title") or "").lower()))

    rows: list[dict[str, str]] = []
    for idx, rec in enumerate(members, start=1):
        zkey = (rec.get("zotero_key") or "").strip()
        outlet, outlet_detail = infer_publisher_outlet(rec.get("doi"), rec.get("journal"))
        search_pos = (rec.get("ebsco_search_position") or "").strip()
        if not search_pos:
            pos = lookup_search_position(rec.get("doi"), rec.get("ebsco_an"), by_doi, by_an)
            search_pos = str(pos) if pos is not None else ""
        rows.append(
            {
                "pool_id": f"P{idx:04d}",
                "title": rec.get("title", ""),
                "authors": rec.get("authors", ""),
                "year": rec.get("year", ""),
                "journal": rec.get("journal", ""),
                "publisher_outlet": outlet,
                "publisher_outlet_detail": outlet_detail,
                "doi": rec.get("doi", ""),
                "ebsco_an": rec.get("ebsco_an", ""),
                "ebsco_search_position": search_pos,
                "in_master": "Y",
                "master_article_id": rec.get("article_id", ""),
                "pool_status": "in_pool",
                "gap_reason": "",
                "pdf_status": pool_pdf_status(rec, zkey in zotero_pdf_keys),
                "examination_status": rec.get("examination_status", ""),
                "zotero_key": zkey,
                "pdf_path": rec.get("pdf_path", ""),
                "sort_rank": str(idx),
                "notes": rec.get("notes", ""),
            }
        )

    gap_count = max(0, PRISMA_POOL_SIZE - len(rows))
    gap_start = len(rows) + 1
    for i in range(gap_count):
        pool_num = gap_start + i
        if i < EXPORT_GAP_SIZE:
            reason = "export_gap_251_300"
            note = "EBSCO export positions 251-300 not yet downloaded; merge after import"
        else:
            reason = "pool_reconcile"
            note = "In PRISMA 570 pool but not in master; reconcile with DistillerSR export"
        rows.append(
            {
                "pool_id": f"P{pool_num:04d}",
                "title": "",
                "authors": "",
                "year": "",
                "journal": "",
                "publisher_outlet": "NA",
                "publisher_outlet_detail": "",
                "doi": "",
                "ebsco_an": "",
                "ebsco_search_position": "",
                "in_master": "N",
                "master_article_id": "",
                "pool_status": "pool_gap",
                "gap_reason": reason,
                "pdf_status": "missing",
                "examination_status": "not_in_master",
                "zotero_key": "",
                "pdf_path": "",
                "sort_rank": str(pool_num),
                "notes": note,
            }
        )

    return rows


def compute_metrics(pool: list[dict[str, str]]) -> dict[str, int | dict[str, int]]:
    in_master = [r for r in pool if r.get("in_master") == "Y"]
    gaps = [r for r in pool if r.get("pool_status") == "pool_gap"]
    pdf = Counter(r.get("pdf_status", "") for r in in_master)
    exam = Counter(r.get("examination_status", "") for r in pool)

    downloaded = pdf.get("downloaded", 0)
    in_zotero = pdf.get("in_zotero", 0)
    missing_pdf = pdf.get("missing", 0)

    fully = exam.get("fully_coded", 0)
    partial = exam.get("partially_coded", 0)
    snippet = exam.get("read_snippet_only", 0)
    not_read = exam.get("not_read", 0)
    unknown_exam = exam.get("not_in_master", 0) + exam.get("unknown", 0)

    remaining_download = missing_pdf + len(gaps)
    remaining_examine = sum(
        1 for r in pool if r.get("examination_status", "") not in ("fully_coded",)
    )
    pool_total = len(pool)

    return {
        "screening_pool_total": pool_total,
        "in_master_registry": len(in_master),
        "pool_gap_rows": len(gaps),
        "pdf_downloaded": downloaded,
        "pdf_in_zotero": in_zotero,
        "pdf_missing": missing_pdf,
        "exam_fully_coded": fully,
        "exam_partially_coded": partial,
        "exam_read_snippet_only": snippet,
        "exam_not_read": not_read,
        "exam_unknown": unknown_exam,
        "remaining_to_download": remaining_download,
        "remaining_to_examine": remaining_examine,
        "pdf_status_counts": dict(sorted(pdf.items())),
        "examination_status_counts": dict(sorted(exam.items())),
        "download_pct": round(100 * downloaded / pool_total, 1) if pool_total else 0.0,
        "examination_pct": round(100 * fully / pool_total, 1) if pool_total else 0.0,
    }


def _search_position_sort_key(row: dict[str, str]) -> tuple[int, int, str]:
    """Primary: ebsco_search_position asc; fallback: year desc for unmapped rows."""
    raw = (row.get("ebsco_search_position") or "").strip()
    if raw.isdigit():
        return (0, int(raw), row.get("pool_id", ""))
    return (1, -parse_year(row.get("year")), row.get("pool_id", ""))


def build_download_queue(pool: list[dict[str, str]]) -> list[dict[str, str]]:
    missing = [
        r
        for r in pool
        if r.get("pool_status") == "in_pool" and r.get("pdf_status") == "missing"
    ]
    missing.sort(key=_search_position_sort_key)
    queue: list[dict[str, str]] = []
    for rank, row in enumerate(missing, start=1):
        queue.append(
            {
                "queue_rank": str(rank),
                "ebsco_search_position": row.get("ebsco_search_position", ""),
                "pool_id": row.get("pool_id", ""),
                "master_article_id": row.get("master_article_id", ""),
                "year": row.get("year", ""),
                "title": row.get("title", ""),
                "doi": row.get("doi", ""),
                "ebsco_an": row.get("ebsco_an", ""),
                "examination_status": row.get("examination_status", ""),
                "journal": row.get("journal", ""),
            }
        )
    return queue


def build_missed_in_first_150(pool: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Articles at EBSCO search positions 1–150 that still need a PDF."""
    in_scope = [
        r
        for r in pool
        if r.get("pool_status") == "in_pool"
        and (r.get("ebsco_search_position") or "").strip().isdigit()
        and int(r["ebsco_search_position"]) <= FIRST_150_SIZE
    ]
    in_scope.sort(key=_search_position_sort_key)
    have_pdf = [r for r in in_scope if r.get("pdf_status") == "downloaded"]
    missing = [r for r in in_scope if r.get("pdf_status") != "downloaded"]

    rows: list[dict[str, str]] = []
    for row in missing:
        rows.append(
            {
                "ebsco_search_position": row.get("ebsco_search_position", ""),
                "pool_id": row.get("pool_id", ""),
                "master_article_id": row.get("master_article_id", ""),
                "year": row.get("year", ""),
                "title": row.get("title", ""),
                "doi": row.get("doi", ""),
                "journal": row.get("journal", ""),
                "ebsco_an": row.get("ebsco_an", ""),
                "examination_status": row.get("examination_status", ""),
            }
        )

    metrics = {
        "in_scope": len(in_scope),
        "have_pdf": len(have_pdf),
        "missing_pdf": len(missing),
    }
    return rows, metrics


def format_missed_md(
    missed: list[dict[str, str]],
    metrics: dict[str, int],
    pool_metrics: dict[str, int | dict[str, int]],
) -> str:
    today = date.today().isoformat()
    lines = [
        "# Missed PDFs in EBSCO search positions 1–150",
        "",
        f"Generated: {today}",
        "",
        "## Top line",
        "",
        f"**{metrics['have_pdf']} of {metrics['in_scope']}** in-pool articles mapped to EBSCO positions 1–150 "
        f"already have a PDF. **{metrics['missing_pdf']}** still need a download.",
        "",
        f"Registry snapshot: pool **{pool_metrics['screening_pool_total']}**, "
        f"master-linked **{pool_metrics['in_master_registry']}**, "
        f"EBSCO PDFs downloaded **{pool_metrics['pdf_downloaded']}**.",
        "",
        "## How “first 150” is defined",
        "",
        "**Primary worklist:** native EBSCO search order from "
        "`review/EBSCO/imports/EBSCO-Metadata-06_26_2026*.csv` (positions **1–150**).",
        "",
        "Download queue (`download_queue_ebsco_order.csv`) sorts missing PDFs by "
        "`ebsco_search_position` ascending—not recent-first year sort.",
        "",
        "`pool_id` P0001–P0150 remains year-desc for the full 570 registry; "
        "use `ebsco_search_position` for examination/download priority.",
        "",
        "PDF present = `has_pdf` is true or `pdf_path` is non-empty in `articles_master.csv`.",
        "",
        "## Counts",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Screening pool | {pool_metrics['screening_pool_total']} |",
        f"| In master registry | {pool_metrics['in_master_registry']} |",
        f"| EBSCO positions 1–150 mapped in pool | {metrics['in_scope']} |",
        f"| Positions 1–150 — have PDF | {metrics['have_pdf']} |",
        f"| **Positions 1–150 — missing PDF** | **{metrics['missing_pdf']}** |",
        "",
    ]
    if missed:
        lines.extend(
            [
                "## Still to download (EBSCO positions 1–150 only)",
                "",
                "| EBSCO pos | master_id | pool_id | Year | DOI | Title (short) |",
                "|----------:|-----------|---------|-----:|-----|-----------------|",
            ]
        )
        for row in missed:
            title = row.get("title", "")
            if len(title) > 72:
                title = title[:69] + "…"
            lines.append(
                f"| {row.get('ebsco_search_position', '')} | {row.get('master_article_id', '')} | "
                f"{row.get('pool_id', '')} | {row.get('year', '')} | {row.get('doi', '')} | {title} |"
            )
        lines.append("")
    else:
        lines.extend(["## Still to download", "", "None — all mapped positions 1–150 have PDFs.", ""])

    lines.extend(
        [
            "## Files",
            "",
            f"- CSV: `{MISSED_CSV.relative_to(ROOT)}` ({len(missed)} rows)",
            f"- Worklist rule: `{ROOT.joinpath('review/EBSCO/EBSCO_PRIMARY_WORKLIST.md').relative_to(ROOT)}`",
            "- Regenerate: `python3 review/master/progress_counter.py`",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def format_progress_md(metrics: dict[str, int | dict[str, int]], pool_path: Path, queue_path: Path) -> str:
    today = date.today().isoformat()
    return f"""# Download & Examination Progress — EBSCO Screening Pool

**Updated**: {today}  
**Canonical pool**: `{pool_path.relative_to(ROOT)}`  
**Download queue (EBSCO search order)**: `{queue_path.relative_to(ROOT)}`

Regenerate after each download batch:

```bash
python3 review/master/progress_counter.py
```

---

## Screening pool (PRISMA EBSCO strand)

| Metric | Count |
|--------|------:|
| Screening pool (target) | **{metrics['screening_pool_total']}** |
| In master registry | **{metrics['in_master_registry']}** |
| Pool gap (not yet in master) | **{metrics['pool_gap_rows']}** |

## PDF status (master-linked rows only)

| Status | Count |
|--------|------:|
| Downloaded (`has_pdf`, `pdf_path`, or Zotero PDF) | **{metrics['pdf_downloaded']}** |
| In Zotero (metadata, no PDF yet) | **{metrics['pdf_in_zotero']}** |
| Missing | **{metrics['pdf_missing']}** |
| **Remaining to download** | **{metrics['remaining_to_download']}** |

## Examination status (full 570 pool)

| Status | Count |
|--------|------:|
| fully_coded | **{metrics['exam_fully_coded']}** |
| partially_coded | **{metrics['exam_partially_coded']}** |
| read_snippet_only | **{metrics['exam_read_snippet_only']}** |
| not_read | **{metrics['exam_not_read']}** |
| not_in_master (pool gaps) | **{metrics['exam_unknown']}** |
| **Remaining to examine** (not fully_coded) | **{metrics['remaining_to_examine']}** |

---

## Gap notes

- **570** is the user-confirmed PRISMA deduplicated screening pool (`review/EBSCO/PRISMA_06_24_2026_UPDATE.md`).
- **{metrics['in_master_registry']}** unique EBSCO June 2026 rows are in `articles_master.csv` (expected ~{KNOWN_IN_MASTER}).
- **{EXPORT_GAP_SIZE}** gap rows = EBSCO export positions **251–300** (not yet imported).
- **{max(0, metrics['pool_gap_rows'] - EXPORT_GAP_SIZE)}** additional gap rows = reconcile with DistillerSR / remaining PRISMA pool.

## After downloading a PDF

1. Save the PDF under `review/pdfs/` (or your hunt folder).
2. Update the master row in `articles_master.csv`:
   - `has_pdf` = `True`
   - `pdf_path` = relative path to the file
   - `pdf_status` = `available` (optional; backfill script sets this)
   - `zotero_key` if added to Zotero
3. Re-run `python3 review/master/progress_counter.py` to refresh counts and the download queue.

Optional: run `python3 review/master/backfill_examination_status.py` after bulk master edits.
"""


def build_prisma_flow_payload(
    worklist_metrics: dict[str, int | dict[str, int] | str],
    *,
    export_positions: int = EBSCO_EXPORT_1150,
    off_pool_removed: int = EBSCO_OFF_POOL_1150,
) -> dict:
    """PRISMA 2020 flow for EBSCO search positions 1–150 (live L1 screening to date)."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    in_pool = int(worklist_metrics.get("worklist_n", 0))
    pdfs = int(worklist_metrics.get("pdf_count", in_pool))
    assessed = int(worklist_metrics.get("scanned", 0))
    included = int(worklist_metrics.get("included", 0))
    excluded = int(worklist_metrics.get("excluded", 0))
    excluded_pls = int(worklist_metrics.get("excluded_pls", 0))
    manual = int(worklist_metrics.get("manual_review", 0))
    pending = int(worklist_metrics.get("pending", 0))
    excluded_total = excluded + excluded_pls
    return {
        "last_updated": now,
        "strand": "ebsco_worklist_positions_1_150",
        "identified": export_positions,
        "off_pool_removed": off_pool_removed,
        "in_pool": in_pool,
        "pdfs_retrieved": pdfs,
        "full_text_assessed": assessed,
        "l1_included": included,
        "l1_excluded": excluded,
        "l1_excluded_pls": excluded_pls,
        "l1_excluded_total": excluded_total,
        "l1_manual_review": manual,
        "l1_pending": pending,
        "included_note": (
            f"EBSCO positions 1–150 to date: {included} included, "
            f"{excluded_total} excluded ({excluded} eligibility + {excluded_pls} PLS), "
            f"{manual} manual review pending."
        ),
        "source_doc": "review/EBSCO/EBSCO_PRIMARY_WORKLIST.md",
        "legacy_strand_note": (
            f"Full 570-pool PRISMA ({PRISMA_IDENTIFIED} identified → {PRISMA_INCLUDED_DEFAULT} "
            "legacy included) deferred until batch screening continues past position 150."
        ),
    }


def build_ebsco_1150_l1_summary_table(
    worklist_metrics: dict[str, int | dict[str, int] | str],
) -> dict:
    """Summary table: EBSCO 1–150 Level 1 screening counts (primary reporting unit)."""
    assessed = int(worklist_metrics.get("scanned", 0)) or int(worklist_metrics.get("worklist_n", 0))
    rows_spec = [
        ("Export positions 1–150", EBSCO_EXPORT_1150, EBSCO_EXPORT_1150),
        ("In master (positions 1–150)", int(worklist_metrics.get("worklist_n", 0)), EBSCO_EXPORT_1150),
        ("With PDF on disk", int(worklist_metrics.get("pdf_count", 0)), EBSCO_EXPORT_1150),
        ("L1 assessed (with evidence)", assessed, assessed or 1),
        ("Included", int(worklist_metrics.get("included", 0)), assessed or 1),
        ("Excluded (eligibility)", int(worklist_metrics.get("excluded", 0)), assessed or 1),
        ("Excluded (PLS-SEM)", int(worklist_metrics.get("excluded_pls", 0)), assessed or 1),
        ("Manual review", int(worklist_metrics.get("manual_review", 0)), assessed or 1),
        ("Pending", int(worklist_metrics.get("pending", 0)), assessed or 1),
    ]
    rows = []
    for label, count, denom in rows_spec:
        pct = round(100 * count / denom, 1) if denom else 0.0
        rows.append({"Decision": label, "Count": count, "% of assessed": f"{pct}%" if denom == assessed and assessed else "—"})
    return summary_table(
        "ebsco_1150_l1_screening",
        "EBSCO 1–150 Level 1 screening (to date)",
        ["Decision", "Count", "% of assessed"],
        rows,
        note=(
            "Primary reporting strand for live screening. Positions 21, 89, 148–150 added to master 2026-06-26."
        ),
    )


def build_dashboard_summary_payload(
    worklist_metrics: dict[str, int | dict[str, int] | str],
) -> dict:
    """Audit JSON (progress_summary_data.json): EBSCO 1–150 L1 counts; not a dashboard tab."""
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    l1_table = build_ebsco_1150_l1_summary_table(worklist_metrics)
    return {
        "last_updated": now,
        "strand": "ebsco_worklist_positions_1_150",
        "table_count": 1,
        "tables": [l1_table],
    }


def build_dashboard_payload(metrics: dict[str, int | dict[str, int]]) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "last_updated": now,
        "pool_size": metrics["screening_pool_total"],
        "in_master_registry": metrics["in_master_registry"],
        "pool_gap_rows": metrics["pool_gap_rows"],
        "pdf_downloaded": metrics["pdf_downloaded"],
        "pdf_in_zotero": metrics["pdf_in_zotero"],
        "pdf_missing": metrics["pdf_missing"],
        "remaining_to_download": metrics["remaining_to_download"],
        "exam_fully_coded": metrics["exam_fully_coded"],
        "remaining_to_examine": metrics["remaining_to_examine"],
        "download_pct": metrics["download_pct"],
        "examination_pct": metrics["examination_pct"],
        "pdf_status_counts": metrics["pdf_status_counts"],
        "examination_status_counts": metrics["examination_status_counts"],
    }




def compute_on_hand_cohort_metrics(
    master: list[dict[str, str]],
    cohort_path: Path,
) -> dict[str, int | dict[str, int] | list[str] | str]:
    """Metrics for the on-hand PDF examination cohort (145 articles)."""
    master_by_id = {r.get("article_id", ""): r for r in master if r.get("article_id")}
    cohort_rows = load_csv(cohort_path)
    cohort_ids = [r.get("article_id", "").strip() for r in cohort_rows if r.get("article_id", "").strip()]

    screening: Counter[str] = Counter()
    examination: Counter[str] = Counter()
    pdf_count = 0

    for mid in cohort_ids:
        rec = master_by_id.get(mid)
        if not rec:
            screening["not_in_master"] += 1
            examination["not_in_master"] += 1
            continue

        ss = (rec.get("screening_status") or "").strip() or "pending"
        if ss == "level1_fail":
            screening["excluded"] += 1
        elif ss == "manual_review":
            screening["manual_review"] += 1
        else:
            screening[ss] += 1

        es = (rec.get("examination_status") or "").strip() or "unknown"
        examination[es] += 1

        has_pdf = (rec.get("has_pdf") or "").strip().lower() in ("true", "1", "yes")
        if has_pdf or (rec.get("pdf_path") or "").strip():
            pdf_count += 1

    l1_pending = screening.get("pending", 0)
    l1_manual = screening.get("manual_review", 0)
    cohort_n = len(cohort_ids)

    return {
        "cohort_n": cohort_n,
        "pdf_count": pdf_count,
        "l1_screened": cohort_n - l1_pending,
        "l1_included": screening.get("included", 0),
        "l1_excluded": screening.get("excluded", 0),
        "l1_excluded_pls": screening.get("excluded_pls", 0),
        "l1_manual_review": l1_manual,
        "l1_pending": l1_pending,
        "partially_coded": examination.get("partially_coded", 0),
        "fully_coded": examination.get("fully_coded", 0),
        "screening_status_counts": dict(sorted(screening.items())),
        "examination_status_counts": dict(sorted(examination.items())),
        "master_ids": cohort_ids,
        "cohort_source": str(cohort_path.relative_to(ROOT)),
    }


def build_on_hand_cohort_payload(metrics: dict[str, int | dict[str, int] | list[str] | str]) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "last_updated": now,
        "strand": "ebsco_on_hand_examination_cohort",
        "legacy_holdout_n": LEGACY_INCLUDED_HOLDOUT,
        "legacy_holdout_note": (
            "Legacy 182 included studies are held out for replication; "
            "not part of this on-hand cohort."
        ),
        "doc_path": "review/EBSCO/EXAMINATION_COHORT_ON_HAND.md",
        "extraction_csv_path": "review/EBSCO/systematic_extraction_ebsco_on_hand.csv",
        **{k: v for k, v in metrics.items() if k != "master_ids"},
    }


def _evidence_snippet(row: dict[str, str]) -> str:
    return (row.get("evidence_snippet") or row.get("pdf_evidence_snippet") or "").strip()


def _evidence_decision(row: dict[str, str]) -> str:
    decision = (row.get("decision") or row.get("screening_status") or "").strip()
    if decision == "level1_fail":
        return "excluded"
    return decision


def load_screening_evidence(path: Path) -> list[dict[str, str]]:
    rows = load_csv(path)
    normalized: list[dict[str, str]] = []
    for row in rows:
        normalized.append(
            {
                "master_id": row.get("master_id", ""),
                "ebsco_search_position": row.get("ebsco_search_position", ""),
                "title": row.get("title", ""),
                "q1_1_pass": row.get("q1_1_pass") or row.get("Q1_1_management_domain", ""),
                "q1_2_pass": row.get("q1_2_pass") or row.get("Q1_2_empirical_ulmc", ""),
                "q1_3_pass": row.get("q1_3_pass") or row.get("Q1_3_not_pls", ""),
                "decision": _evidence_decision(row),
                "confidence": row.get("confidence", ""),
                "evidence_snippet": _evidence_snippet(row),
                "evidence_type": row.get("evidence_type", ""),
                "rationale": row.get("rationale", ""),
                "q1_1_reason_code": row.get("q1_1_reason_code", ""),
                "q1_2_reason_code": row.get("q1_2_reason_code", ""),
                "q1_3_reason_code": row.get("q1_3_reason_code", ""),
                "decision_reason_code": row.get("decision_reason_code", ""),
                "decision_reason_text": row.get("decision_reason_text", ""),
            }
        )
    return normalized


def summarize_screening_evidence(evidence: list[dict[str, str]]) -> dict[str, int | float]:
    decisions = Counter(_evidence_decision(r) for r in evidence if r.get("master_id"))
    scanned = sum(
        1
        for r in evidence
        if _evidence_decision(r) not in ("", "pending")
    )
    total = len(evidence)
    pending = decisions.get("pending", 0)
    return {
        "worklist_n": total,
        "scanned": scanned,
        "scanned_pct": round(100 * scanned / total, 1) if total else 0.0,
        "included": decisions.get("included", 0),
        "excluded": decisions.get("excluded", 0),
        "excluded_pls": decisions.get("excluded_pls", 0),
        "manual_review": decisions.get("manual_review", 0),
        "pending": pending,
        "screening_status_counts": dict(sorted(decisions.items())),
    }


def build_verification_sample(evidence: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {r["master_id"]: r for r in evidence if r.get("master_id")}
    sample: list[dict[str, str]] = []
    for mid in VERIFICATION_MASTER_IDS:
        row = by_id.get(mid)
        if not row:
            continue
        sample.append(
            {
                "master_id": mid,
                "ebsco_search_position": row.get("ebsco_search_position", ""),
                "title": row.get("title", ""),
                "decision": row.get("decision", ""),
                "confidence": row.get("confidence", ""),
                "decision_reason_code": row.get("decision_reason_code", ""),
                "decision_reason_text": row.get("decision_reason_text", ""),
                "q1_1_reason_code": row.get("q1_1_reason_code", ""),
                "q1_2_reason_code": row.get("q1_2_reason_code", ""),
                "q1_3_reason_code": row.get("q1_3_reason_code", ""),
                "evidence_snippet": row.get("evidence_snippet", ""),
                "verification_role": (
                    "high_confidence_include"
                    if mid == "M0183"
                    else "low_confidence_manual_review"
                ),
                "doc_path": str(VERIFICATION_SAMPLE_PATH.relative_to(ROOT)),
            }
        )
    return sample


def merge_master_screening_into_evidence(
    evidence_rows: list[dict[str, str]],
    master_by_id: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    """Master `screening_status` wins after human feedback (e.g. classification_feedback)."""
    merged: list[dict[str, str]] = []
    for row in evidence_rows:
        mid = row.get("master_id", "")
        rec = master_by_id.get(mid)
        if not rec:
            merged.append(row)
            continue
        ss = (rec.get("screening_status") or "").strip()
        if ss == "level1_fail":
            decision = "excluded"
        elif ss:
            decision = ss
        else:
            decision = row.get("decision", "")
        notes = (rec.get("screening_notes") or "").strip()
        out = {**row, "decision": decision}
        if notes and "User feedback" in notes and decision == "excluded":
            out["decision_reason_code"] = "EXCLUDE_Q1_1_DOMAIN_USER"
            out["decision_reason_text"] = (
                f"{row.get('decision_reason_text', '')} "
                f"User override: {notes.split('User feedback', 1)[-1].strip()}"
            ).strip()
        merged.append(out)
    return merged


def worklist_1_150_master_rows(master: list[dict[str, str]]) -> list[dict[str, str]]:
    """Export positions 1–150 joined to master (DOI/AN match)."""
    return load_worklist_1_150_from_master(master)


def compute_worklist_1_150_metrics(
    master: list[dict[str, str]],
    cohort_path: Path,
    evidence_path: Path | None = None,
) -> dict[str, int | dict[str, int] | list[dict[str, str]] | str]:
    """
    EBSCO positions 1–150 primary worklist (all master rows at export positions 1–150).

    Scanned = L1 decision + evidence snippet captured (from evidence CSV when present).
    """
    master_by_id = {r.get("article_id", ""): r for r in master if r.get("article_id")}
    worklist_rows = worklist_1_150_master_rows(master)
    worklist_ids = [r.get("article_id", "").strip() for r in worklist_rows if r.get("article_id", "").strip()]

    screening: Counter[str] = Counter()
    pdf_count = 0

    for mid in worklist_ids:
        rec = master_by_id.get(mid)
        if not rec:
            screening["not_in_master"] += 1
            continue

        ss = (rec.get("screening_status") or "").strip() or "pending"
        if ss == "level1_fail":
            screening["excluded"] += 1
        elif ss == "manual_review":
            screening["manual_review"] += 1
        else:
            screening[ss] += 1

        has_pdf = (rec.get("has_pdf") or "").strip().lower() in ("true", "1", "yes")
        if has_pdf or (rec.get("pdf_path") or "").strip():
            pdf_count += 1

    total = len(worklist_ids)
    pending = screening.get("pending", 0)
    scanned = total - pending

    evidence_rows: list[dict[str, str]] = []
    verification_sample: list[dict[str, str]] = []
    if evidence_path and evidence_path.exists():
        evidence_rows = load_screening_evidence(evidence_path)
        if evidence_rows:
            evidence_rows = merge_master_screening_into_evidence(evidence_rows, master_by_id)
            ev_summary = summarize_screening_evidence(evidence_rows)
            scanned = int(ev_summary["scanned"])
            pending = int(ev_summary["pending"])
            screening = Counter(ev_summary["screening_status_counts"])  # type: ignore[assignment]
            verification_sample = build_verification_sample(evidence_rows)

    return {
        "worklist_n": total,
        "pdf_count": pdf_count,
        "scanned": scanned,
        "scanned_pct": round(100 * scanned / total, 1) if total else 0.0,
        "included": screening.get("included", 0),
        "excluded": screening.get("excluded", 0),
        "excluded_pls": screening.get("excluded_pls", 0),
        "manual_review": screening.get("manual_review", 0),
        "pending": pending,
        "screening_status_counts": dict(sorted(screening.items())),
        "cohort_source": str(cohort_path.relative_to(ROOT)),
        "evidence_csv_path": str(evidence_path.relative_to(ROOT)) if evidence_path and evidence_path.exists() else "",
        "verification_doc_path": str(VERIFICATION_SAMPLE_PATH.relative_to(ROOT)),
        "screening_evidence_rows": evidence_rows,
        "verification_sample": verification_sample,
        "doc_path": "review/EBSCO/EBSCO_PRIMARY_WORKLIST.md",
        "review_doc_path": "review/EBSCO/CLASSIFICATION_REVIEW.md",
    }


def build_worklist_1_150_payload(metrics: dict[str, int | dict[str, int] | list[dict[str, str]] | str]) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    evidence_rows = metrics.get("screening_evidence_rows") or []
    verification = metrics.get("verification_sample") or []
    l1_summary_table = build_ebsco_1150_l1_summary_table(metrics)
    base = {k: v for k, v in metrics.items() if k not in ("screening_evidence_rows",)}
    return {
        "last_updated": now,
        "strand": "ebsco_worklist_positions_1_150",
        "definition": (
            "Primary worklist: all 150 EBSCO native export positions 1–150 in articles_master.csv. "
            "Scanned = Level 1 decision applied with PDF or metadata evidence snippet captured."
        ),
        **base,
        "summary_table_count": 1,
        "summary_tables": [l1_summary_table],
        "verification_sample": verification,
        "screening_summary_table": {
            "title": "EBSCO 1–150 Level 1 screening",
            "columns": [
                "master_id",
                "ebsco_search_position",
                "decision",
                "confidence",
                "decision_reason_code",
                "decision_reason_text",
                "evidence_snippet",
            ],
            "row_count": len(evidence_rows),
            "rows": evidence_rows[:50],
            "note": (
                f"Showing first 50 of {len(evidence_rows)} rows. "
                f"Full file: {metrics.get('evidence_csv_path', '')}"
            ),
        },
    }


def write_dashboard_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")



def print_summary(metrics: dict[str, int | dict[str, int]]) -> None:
    print(f"Screening pool: {metrics['screening_pool_total']}")
    print(f"In master registry: {metrics['in_master_registry']}")
    print(
        f"PDF downloaded: {metrics['pdf_downloaded']} | "
        f"in_zotero: {metrics['pdf_in_zotero']} | "
        f"missing: {metrics['pdf_missing']}"
    )
    print(
        f"Examination: fully_coded {metrics['exam_fully_coded']} | "
        f"partially_coded {metrics['exam_partially_coded']} | "
        f"snippet_only {metrics['exam_read_snippet_only']} | "
        f"not_read {metrics['exam_not_read']}"
    )
    print(f"Remaining to download: {metrics['remaining_to_download']}")
    print(f"Remaining to examine (not fully_coded): {metrics['remaining_to_examine']}")
    print(f"Pool gap rows: {metrics['pool_gap_rows']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="EBSCO 570-pool download/examination progress counter")
    parser.add_argument("--master", type=Path, default=MASTER_PATH)
    parser.add_argument("--crosswalk", type=Path, default=CROSSWALK_PATH)
    parser.add_argument("--no-write", action="store_true", help="Print only; do not write output files")
    parser.add_argument("--build-only", action="store_true", help="Write pool/queue files only")
    parser.add_argument(
        "--included",
        type=int,
        default=PRISMA_INCLUDED_DEFAULT,
        help="Legacy included studies count for PRISMA flow (default: 182)",
    )
    parser.add_argument(
        "--identified",
        type=int,
        default=PRISMA_IDENTIFIED,
        help="Records identified count for PRISMA flow (default: 1036)",
    )
    args = parser.parse_args()

    master = load_csv(args.master)
    if not master:
        print(f"No rows in {args.master}", file=sys.stderr)
        sys.exit(1)

    zotero_pdf_keys = load_zotero_pdf_keys(args.crosswalk)
    pool = build_pool_rows(master, zotero_pdf_keys)
    metrics = compute_metrics(pool)
    queue = build_download_queue(pool)
    missed, missed_metrics = build_missed_in_first_150(pool)

    print_summary(metrics)
    print(
        f"EBSCO positions 1-150: mapped={missed_metrics['in_scope']} "
        f"have_pdf={missed_metrics['have_pdf']} missing_pdf={missed_metrics['missing_pdf']}"
    )

    if args.no_write:
        return

    write_csv(POOL_PATH, pool, POOL_COLUMNS)
    write_csv(
        QUEUE_PATH,
        queue,
        [
            "queue_rank",
            "ebsco_search_position",
            "pool_id",
            "master_article_id",
            "year",
            "title",
            "doi",
            "ebsco_an",
            "examination_status",
            "journal",
        ],
    )
    write_csv(
        MISSED_CSV,
        missed,
        [
            "ebsco_search_position",
            "pool_id",
            "master_article_id",
            "year",
            "title",
            "doi",
            "journal",
            "ebsco_an",
            "examination_status",
        ],
    )

    if args.build_only:
        print(f"Wrote {POOL_PATH.relative_to(ROOT)} ({len(pool)} rows)")
        print(f"Wrote {QUEUE_PATH.relative_to(ROOT)} ({len(queue)} rows)")
        print(f"Wrote {MISSED_CSV.relative_to(ROOT)} ({len(missed)} rows)")
        return

    PROGRESS_MD.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_MD.write_text(format_progress_md(metrics, POOL_PATH, QUEUE_PATH), encoding="utf-8")
    MISSED_MD.write_text(format_missed_md(missed, missed_metrics, metrics), encoding="utf-8")

    summary_rows = [{"metric": k, "count": str(metrics[k])} for k in SUMMARY_METRICS]
    write_csv(SUMMARY_CSV, summary_rows, ["metric", "count"])

    on_hand_metrics = compute_on_hand_cohort_metrics(master, COHORT_ON_HAND_CSV)
    on_hand_payload = build_on_hand_cohort_payload(on_hand_metrics)
    worklist_metrics = compute_worklist_1_150_metrics(master, COHORT_ON_HAND_CSV, EVIDENCE_PATH)
    worklist_payload = build_worklist_1_150_payload(worklist_metrics)

    dashboard_payload = build_dashboard_payload(metrics)
    write_dashboard_json(DASHBOARD_JSON, dashboard_payload)
    write_dashboard_json(ON_HAND_COHORT_JSON, on_hand_payload)
    write_dashboard_json(WORKLIST_1150_JSON, worklist_payload)

    prisma_payload = build_prisma_flow_payload(worklist_metrics)
    write_dashboard_json(PRISMA_FLOW_JSON, prisma_payload)

    extraction_rows = load_combined_extraction_rows()
    results_payload = build_results_payload(master, extraction_rows)
    write_results_json(RESULTS_JSON, results_payload)
    extraction_summary_payload = build_summary_payload(results_payload, extraction_rows)
    write_summary_json(EXTRACTION_SUMMARY_JSON, extraction_summary_payload)

    summary_payload = build_dashboard_summary_payload(worklist_metrics)
    write_summary_json(SUMMARY_JSON, summary_payload)

    ebsco_150_summary_payload = build_ebsco_150_summary_payload(
        master,
        results_payload,
        extraction_rows,
        EVIDENCE_PATH,
        worklist_metrics,
    )
    write_ebsco_150_summary_json(EBSCO_150_SUMMARY_JSON, ebsco_150_summary_payload)

    if build_journal_ulmc_payload is not None and write_journal_ulmc_outputs is not None:
        journal_payload = build_journal_ulmc_payload(results_payload, extraction_rows)
        write_journal_ulmc_outputs(journal_payload)

    DASHBOARD_HTML.write_text(
        format_dashboard_html(
            dashboard_payload,
            results_payload,
            prisma_payload,
            on_hand_payload,
            worklist_payload,
            ebsco_150_summary_payload,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {POOL_PATH.relative_to(ROOT)}")
    print(f"Wrote {QUEUE_PATH.relative_to(ROOT)} ({len(queue)} articles missing PDF)")
    print(f"Wrote {MISSED_CSV.relative_to(ROOT)} ({len(missed)} missing in EBSCO 1-150)")
    print(f"Wrote {MISSED_MD.relative_to(ROOT)}")
    print(f"Wrote {PROGRESS_MD.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_CSV.relative_to(ROOT)}")
    print(f"Wrote {DASHBOARD_JSON.relative_to(ROOT)}")
    print(f"Wrote {ON_HAND_COHORT_JSON.relative_to(ROOT)} (cohort N={on_hand_metrics['cohort_n']})")
    print(
        f"Wrote {WORKLIST_1150_JSON.relative_to(ROOT)} "
        f"(scanned={worklist_metrics['scanned']}/{worklist_metrics['worklist_n']})"
    )
    print(f"Wrote {PRISMA_FLOW_JSON.relative_to(ROOT)}")
    print(f"Wrote {RESULTS_JSON.relative_to(ROOT)} ({results_payload['total_count']} fully coded)")
    print(
        f"Wrote {SUMMARY_JSON.relative_to(ROOT)} "
        f"({summary_payload['table_count']} audit summary table)"
    )
    print(
        f"Wrote {EXTRACTION_SUMMARY_JSON.relative_to(ROOT)} "
        f"({extraction_summary_payload['table_count']} extraction summary tables)"
    )
    cc = ebsco_150_summary_payload["coding_counts"]
    print(
        f"Wrote {EBSCO_150_SUMMARY_JSON.relative_to(ROOT)} "
        f"(screened={cc['screened']} included={cc['l1_included']} "
        f"fully_coded={cc['fully_coded']} partial={cc['partial_coded']})"
    )
    print(f"Wrote {DASHBOARD_HTML.relative_to(ROOT)}")

    if write_journal_ulmc_outputs is not None:
        print(f"Wrote {ROOT.joinpath('review/ULMC_BY_JOURNAL.csv').relative_to(ROOT)}")
        print(f"Wrote {ROOT.joinpath('review/ULMC_BY_JOURNAL.md').relative_to(ROOT)}")

    if run_results_audit is not None:
        passed, audit_info = run_results_audit(
            master_path=args.master,
            extraction_path=EXTRACTION_PATH,
            results_path=RESULTS_JSON,
            summary_path=EXTRACTION_SUMMARY_JSON,
        )
        from audit_results import write_report as write_audit_report

        write_audit_report(
            AUDIT_REPORT,
            passed=passed,
            total_studies=audit_info["total_studies"],
            metric_count=audit_info["metric_count"],
            errors=audit_info["errors"],
            warnings=audit_info["warnings"],
        )
        if passed:
            warn_n = len(audit_info.get("warnings") or [])
            suffix = f" ({warn_n} warning{'s' if warn_n != 1 else ''})" if warn_n else ""
            print(f"Audit: PASS{suffix} → {AUDIT_REPORT.relative_to(ROOT)}")
        else:
            print(
                f"WARNING: Audit FAIL — {len(audit_info['errors'])} error(s). "
                f"See {AUDIT_REPORT.relative_to(ROOT)}",
                file=sys.stderr,
            )
    else:
        print(
            "Audit skipped (import failed). Run: python3 review/master/audit_results.py",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
