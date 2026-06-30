"""Examination-status computation for articles_master.csv."""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXTRACTION_LEGACY_PATH = ROOT / "review" / "EBSCO" / "systematic_extraction_40_studies.csv"
EXTRACTION_ON_HAND_PATH = ROOT / "review" / "EBSCO" / "systematic_extraction_ebsco_on_hand.csv"
EXTRACTION_PATH = EXTRACTION_LEGACY_PATH  # backward compat for legacy-only callers

EXTRACTION_STATUS_RANK: dict[str, int] = {
    "none": 0,
    "legacy_only": 1,
    "partial": 2,
    "complete": 3,
}

EXAMINATION_STATUSES = (
    "not_read",
    "pdf_missing",
    "read_snippet_only",
    "partially_coded",
    "fully_coded",
)

PDF_STATUSES = ("unknown", "missing", "available")

CORPUS_TIERS = (
    "legacy_gold",
    "extraction_coded",
    "ebsco_screened",
    "supplementary",
)

KEY_EXTRACTION_FIELDS = (
    "management_domain",
    "empirical_ulmc",
    "statistical_methods_mv",
    "method_variance_pct",
    "procedural_remedies_list",
)

EXAMINATION_COLUMNS = (
    "examination_status",
    "pdf_status",
    "corpus_tier",
    "examination_source",
    "examination_updated_at",
)


def parse_bool(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "yes", "1", "t")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def merge_extraction_status(existing: str, incoming: str) -> str:
    """Prefer higher-rank extraction status (fixes legacy_only beating complete)."""
    er = EXTRACTION_STATUS_RANK.get(existing or "none", 0)
    ir = EXTRACTION_STATUS_RANK.get(incoming or "none", 0)
    if ir >= er:
        return incoming or existing
    return existing


def field_filled(value: str | None) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    return s not in ("", "NA", "N/A", "nan", "none", "null", "-")


def count_filled_fields(row: dict[str, str], fields: tuple[str, ...] = KEY_EXTRACTION_FIELDS) -> int:
    return sum(1 for f in fields if field_filled(row.get(f)))


def is_fully_coded_row(row: dict[str, str]) -> bool:
    """Row has enough structured MV fields for synthesis reuse."""
    return count_filled_fields(row) >= 4


def is_partially_coded_row(row: dict[str, str]) -> bool:
    return count_filled_fields(row) >= 2


def is_master_id_key(key: str) -> bool:
    """On-hand EBSCO rows keyed by M#### article_id / master_id."""
    return bool(re.fullmatch(r"M\d{4}", key.strip()))


def _row_study_order(row: dict[str, str]) -> str:
    return (row.get("study_order") or row.get("master_id") or "").strip()


def load_extraction_index(
    legacy_path: Path = EXTRACTION_LEGACY_PATH,
    on_hand_path: Path = EXTRACTION_ON_HAND_PATH,
) -> dict[str, dict[str, str]]:
    """Merge legacy L{refid} rows with on-hand M#### rows (on-hand wins for M#### keys)."""
    index: dict[str, dict[str, str]] = {}
    for row in read_csv(legacy_path):
        key = _row_study_order(row)
        if key:
            index[key] = row
    for row in read_csv(on_hand_path):
        key = _row_study_order(row)
        if key and is_master_id_key(key):
            index[key] = row
    return index


def load_combined_extraction_rows(
    legacy_path: Path = EXTRACTION_LEGACY_PATH,
    on_hand_path: Path = EXTRACTION_ON_HAND_PATH,
) -> list[dict[str, str]]:
    """All extraction rows for dashboard joins (deduped; on-hand wins for M#### keys)."""
    return list(load_extraction_index(legacy_path, on_hand_path).values())


def compute_pdf_status(rec: dict[str, str]) -> str:
    has_pdf = rec.get("has_pdf", "")
    if has_pdf == "True":
        return "available"
    if has_pdf == "False":
        return "missing"
    return "unknown"


def compute_corpus_tier(rec: dict[str, str]) -> str:
    sources = rec.get("sources", "")
    if parse_bool(rec.get("legacy_final_include")):
        return "legacy_gold"
    if "extraction_csv" in sources:
        return "extraction_coded"
    if any(tag.startswith("ebsco_") for tag in sources.split(";") if tag.strip()):
        return "ebsco_screened"
    return "supplementary"


def compute_examination_status(
    rec: dict[str, str],
    extraction_by_order: dict[str, dict[str, str]] | None = None,
) -> tuple[str, str]:
    """
    Return (examination_status, examination_source).

    examination_source is a semicolon-separated audit trail for agents.
    """
    if extraction_by_order is None:
        extraction_by_order = load_extraction_index()

    sources = rec.get("sources", "")
    study_order = (rec.get("study_order") or "").strip()
    snippet = (rec.get("legacy_text_snippet") or "").strip()
    screening = (rec.get("screening_status") or "").strip()
    extraction_status = (rec.get("extraction_status") or "none").strip()
    included = screening == "included" or parse_bool(rec.get("legacy_final_include"))
    has_extraction_source = "extraction_csv" in sources
    has_legacy_source = "legacy_182" in sources
    pdf_status = compute_pdf_status(rec)

    extraction_row = extraction_by_order.get(study_order) if study_order else None

    if extraction_status == "complete" or (extraction_row and is_fully_coded_row(extraction_row)):
        if extraction_row and (extraction_row.get("coding_mode") or "").strip() == "ai_autonomous":
            return "fully_coded", "ai_autonomous;key_fields>=4"
        if has_extraction_source:
            return "fully_coded", "extraction_csv;key_fields>=4"
        return "fully_coded", "on_hand_extraction;key_fields>=4"

    if has_extraction_source or study_order or extraction_row:
        if extraction_row and is_partially_coded_row(extraction_row):
            return "partially_coded", "extraction_csv;key_fields>=2"
        if has_extraction_source:
            return "partially_coded", "extraction_csv;source_tag"

    if has_legacy_source and snippet:
        if included and pdf_status == "missing":
            return "read_snippet_only", "legacy_182;snippet;pdf_missing"
        return "read_snippet_only", "legacy_182;snippet"

    if included and pdf_status in ("missing", "unknown") and not snippet:
        return "pdf_missing", "included;no_pdf;no_snippet"

    if included and pdf_status == "missing":
        return "pdf_missing", "included;pdf_missing"

    return "not_read", "default"


def enrich_record(
    rec: dict[str, str],
    extraction_by_order: dict[str, dict[str, str]] | None = None,
    *,
    today: str | None = None,
) -> dict[str, str]:
    """Add examination columns and fix extraction_status rank on an in-memory record."""
    existing_ext = rec.get("extraction_status", "none")
    # Re-derive extraction_status from sources when extraction row exists
    study_order = (rec.get("study_order") or "").strip()
    if extraction_by_order is None:
        extraction_by_order = load_extraction_index()
    extraction_row = extraction_by_order.get(study_order) if study_order else None
    if extraction_row:
        if is_fully_coded_row(extraction_row):
            existing_ext = merge_extraction_status(existing_ext, "complete")
        elif is_partially_coded_row(extraction_row):
            existing_ext = merge_extraction_status(existing_ext, "partial")
    elif "extraction_csv" in rec.get("sources", ""):
        existing_ext = merge_extraction_status(existing_ext, "partial")
    rec["extraction_status"] = existing_ext

    status, source = compute_examination_status(rec, extraction_by_order)
    rec["examination_status"] = status
    rec["pdf_status"] = compute_pdf_status(rec)
    rec["corpus_tier"] = compute_corpus_tier(rec)
    rec["examination_source"] = source
    rec["examination_updated_at"] = today or date.today().isoformat()
    return rec


def enrich_master_records(
    records: list[dict[str, str]],
    extraction_by_order: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    if extraction_by_order is None:
        extraction_by_order = load_extraction_index()
    today = date.today().isoformat()
    return [enrich_record(dict(rec), extraction_by_order, today=today) for rec in records]
