#!/usr/bin/env python3
"""Merge legacy, EBSCO, extraction, and Zotero sources into articles_master.csv.

After merge, run export-only add scripts (they are not part of this merge):
  python3 review/EBSCO/add_export_only_master_rows.py
  python3 review/EBSCO/add_export_only_master_rows_151_200.py
Then `python3 review/master/progress_counter.py`.

Also run `python3 review/master/find_duplicates.py` to audit master-row duplicates.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MASTER_DIR = ROOT / "review" / "master"
EBSCO_DIR = ROOT / "review" / "EBSCO"
sys.path.insert(0, str(MASTER_DIR))
sys.path.insert(0, str(EBSCO_DIR))
from examination import (  # noqa: E402
    EXAMINATION_COLUMNS,
    enrich_master_records,
    merge_extraction_status,
)
from ebsco_search_order import (  # noqa: E402
    is_ebsco_pool_member,
    load_search_order_entries,
    search_order_row_to_patch,
)
from publisher_outlet import infer_publisher_outlet  # noqa: E402
from sync_pdf_links_from_ingest import sync_pdf_links_from_ingest  # noqa: E402

LEGACY_DIR = ROOT / "review" / "legacy"
IMPORTS_DIR = EBSCO_DIR / "imports"

TODAY = date.today().isoformat()

MASTER_COLUMNS = [
    "article_id",
    "title",
    "authors",
    "year",
    "journal",
    "volume",
    "issue",
    "doi",
    "publisher_outlet",
    "ebsco_an",
    "ebsco_search_position",
    "abstract",
    "ebsco_db",
    "ebsco_plink",
    "cover_date",
    "sources",
    "source_import_file",
    "ebsco_batch",
    "legacy_refid",
    "legacy_final_include",
    "legacy_text_snippet",
    "legacy_mv_pct",
    "legacy_match_method",
    "legacy_match_confidence",
    "screening_status",
    "screening_level1_include",
    "screening_notes",
    "extraction_status",
    "study_order",
    "extraction_file",
    "zotero_key",
    "pdf_path",
    "has_pdf",
    "examination_status",
    "pdf_status",
    "corpus_tier",
    "examination_source",
    "examination_updated_at",
    "notes",
    "created_at",
    "updated_at",
]

DEFAULT_EBSCO_BATCHES = [
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-2.csv",
        "source_tag": "ebsco_2026_06_batch1",
        "ebsco_batch": 1,
        "record_range": "1-50",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-3.csv",
        "source_tag": "ebsco_2026_06_batch2",
        "ebsco_batch": 2,
        "record_range": "51-100",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-4.csv",
        "source_tag": "ebsco_2026_06_batch3",
        "ebsco_batch": 3,
        "record_range": "101-150",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-5.csv",
        "source_tag": "ebsco_2026_06_batch4",
        "ebsco_batch": 4,
        "record_range": "151-200",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-6.csv",
        "source_tag": "ebsco_2026_06_batch5",
        "ebsco_batch": 5,
        "record_range": "201-250",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_25_2026-1.csv",
        "source_tag": "ebsco_2026_06_batch251_300",
        "ebsco_batch": 12,
        "record_range": "251-300",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-7.csv",
        "source_tag": "ebsco_2026_06_batch6",
        "ebsco_batch": 6,
        "record_range": "301-350",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-8.csv",
        "source_tag": "ebsco_2026_06_batch7",
        "ebsco_batch": 7,
        "record_range": "351-400",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-9.csv",
        "source_tag": "ebsco_2026_06_batch8",
        "ebsco_batch": 8,
        "record_range": "401-450",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-10.csv",
        "source_tag": "ebsco_2026_06_batch9",
        "ebsco_batch": 9,
        "record_range": "451-500",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-11.csv",
        "source_tag": "ebsco_2026_06_batch10",
        "ebsco_batch": 10,
        "record_range": "501-550",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_24_2026-12.csv",
        "source_tag": "ebsco_2026_06_batch11",
        "ebsco_batch": 11,
        "record_range": "551-570",
    },
]

EBSCO_FEB_PATH = EBSCO_DIR / "ebsco_export_50_records.csv"
LEGACY_PATH = LEGACY_DIR / "legacy_extracted_data.csv"
EXTRACTION_PATH = EBSCO_DIR / "systematic_extraction_40_studies.csv"
ZOTERO_PATH = LEGACY_DIR / "legacy_182_zotero_inventory.csv"
OVERLAP_PATH = LEGACY_DIR / "legacy_182_overlap_report.csv"
DUPLICATE_REPORT = MASTER_DIR / "duplicate_report.md"
DUPLICATES_FLAGGED = MASTER_DIR / "duplicates_flagged.csv"
TITLE_FUZZY_THRESHOLD = 0.92

DUPLICATE_COLUMNS = [
    "conflict_id",
    "scope",
    "match_key_type",
    "match_key_value",
    "title",
    "doi",
    "ebsco_an",
    "batch_files",
    "other_source",
    "other_ref",
    "action_recommended",
]


@dataclass
class EbscoHit:
    """One row from an EBSCO metadata export."""

    batch_file: str
    batch_label: str
    ebsco_an: str
    doi: str
    title: str
    year: str
    row_index: int


@dataclass
class DuplicateConflict:
    scope: str
    match_key_type: str
    match_key_value: str
    title: str
    doi: str
    ebsco_an: str
    batch_files: list[str] = field(default_factory=list)
    other_source: str = ""
    other_ref: str = ""

    def action_recommended(self) -> str:
        if self.scope == "within_batch":
            return "remove_duplicate_row"
        if self.scope == "cross_batch":
            return "skip_row_on_merge"
        return "review_linkage"


def norm_doi(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    if v in {"na", "n/a", "none", "null", "nan", "-"}:
        return ""
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if v.startswith(prefix):
            v = v[len(prefix) :]
    return v.strip()


def norm_title(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def parse_year(value: str | None) -> str:
    if not value:
        return ""
    s = str(value).strip()
    m = re.search(r"(19|20)\d{2}", s)
    return m.group(0) if m else ""


def parse_bool(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip().lower()
    if s in ("true", "yes", "1", "t"):
        return "True"
    if s in ("false", "no", "0", "f"):
        return "False"
    return ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fuzzy_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def batch_label_from_path(path: Path) -> str:
    """User-facing batch label from filename suffix (e.g. ...-3.csv -> batch 3)."""
    stem = path.stem
    if stem.rsplit("-", 1)[-1].isdigit():
        return f"batch {stem.rsplit('-', 1)[-1]}"
    return path.name


def ebsco_hit_from_row(row: dict[str, str], path: Path, row_index: int) -> EbscoHit:
    pub_date = row.get("publicationDate", "")
    year = parse_year(pub_date) or parse_year(row.get("coverDate", ""))
    return EbscoHit(
        batch_file=path.name,
        batch_label=batch_label_from_path(path),
        ebsco_an=(row.get("an") or "").strip(),
        doi=norm_doi(row.get("doi")),
        title=(row.get("title") or "").strip(),
        year=year,
        row_index=row_index,
    )


def load_ebsco_hits(path: Path) -> list[EbscoHit]:
    return [
        ebsco_hit_from_row(row, path, i + 2)
        for i, row in enumerate(read_csv(path))
    ]


def match_ebsco_pair(a: EbscoHit, b: EbscoHit) -> str | None:
    if a.ebsco_an and a.ebsco_an == b.ebsco_an:
        return "ebsco_an"
    if a.doi and a.doi == b.doi:
        return "doi"
    if (
        a.year
        and b.year
        and a.year == b.year
        and fuzzy_ratio(a.title, b.title) >= TITLE_FUZZY_THRESHOLD
    ):
        return "title_year_fuzzy"
    return None


def _conflict_key(c: DuplicateConflict) -> tuple[str, str, str, str]:
    return (c.scope, c.match_key_type, c.match_key_value, ";".join(sorted(c.batch_files)))


def _add_conflict(conflicts: list[DuplicateConflict], seen: set[tuple], c: DuplicateConflict) -> None:
    key = _conflict_key(c)
    if key not in seen:
        seen.add(key)
        conflicts.append(c)


def load_reference_pool(source: str, path: Path) -> list[dict[str, str]]:
    pool: list[dict[str, str]] = []
    if source == "legacy_182":
        for row in read_csv(ZOTERO_PATH):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            pool.append(
                {
                    "ref": f"refid:{row.get('refid', '')}",
                    "doi": norm_doi(row.get("doi")),
                    "title": title,
                    "year": parse_year(row.get("year", "")),
                }
            )
    elif source == "extraction_csv":
        for row in read_csv(EXTRACTION_PATH):
            pool.append(
                {
                    "ref": f"study_order:{row.get('study_order', '')}",
                    "doi": norm_doi(row.get("doi")),
                    "title": (row.get("study_title") or "").strip(),
                    "year": parse_year(row.get("year", "")),
                }
            )
    return pool


def match_hit_to_reference(hit: EbscoHit, ref: dict[str, str]) -> str | None:
    if hit.doi and ref["doi"] and hit.doi == ref["doi"]:
        return "doi"
    if (
        hit.year
        and ref["year"]
        and hit.year == ref["year"]
        and fuzzy_ratio(hit.title, ref["title"]) >= TITLE_FUZZY_THRESHOLD
    ):
        return "title_year_fuzzy"
    return None


def scan_ebsco_duplicates(batch_paths: list[Path]) -> list[DuplicateConflict]:
    """Scan EBSCO import files for within-batch and cross-batch duplicates."""
    conflicts: list[DuplicateConflict] = []
    seen: set[tuple] = set()
    by_file: dict[str, list[EbscoHit]] = {}

    for path in batch_paths:
        if not path.exists():
            continue
        hits = load_ebsco_hits(path)
        by_file[path.name] = hits

        for i, a in enumerate(hits):
            for b in hits[i + 1 :]:
                key_type = match_ebsco_pair(a, b)
                if not key_type:
                    continue
                value = a.ebsco_an if key_type == "ebsco_an" else a.doi if key_type == "doi" else f"{a.year}|{norm_title(a.title)}"
                _add_conflict(
                    conflicts,
                    seen,
                    DuplicateConflict(
                        scope="within_batch",
                        match_key_type=key_type,
                        match_key_value=value,
                        title=a.title,
                        doi=a.doi,
                        ebsco_an=a.ebsco_an,
                        batch_files=[a.batch_file],
                    ),
                )

    files = list(by_file.keys())
    for i, fa in enumerate(files):
        for fb in files[i + 1 :]:
            for a in by_file[fa]:
                for b in by_file[fb]:
                    key_type = match_ebsco_pair(a, b)
                    if not key_type:
                        continue
                    value = (
                        a.ebsco_an
                        if key_type == "ebsco_an"
                        else a.doi
                        if key_type == "doi"
                        else f"{a.year}|{norm_title(a.title)}"
                    )
                    _add_conflict(
                        conflicts,
                        seen,
                        DuplicateConflict(
                            scope="cross_batch",
                            match_key_type=key_type,
                            match_key_value=value,
                            title=a.title,
                            doi=a.doi,
                            ebsco_an=a.ebsco_an,
                            batch_files=sorted({a.batch_file, b.batch_file}),
                        ),
                    )
    return conflicts


def scan_reference_duplicates(
    batch_paths: list[Path], source: str, ref_path: Path
) -> list[DuplicateConflict]:
    conflicts: list[DuplicateConflict] = []
    seen: set[tuple] = set()
    pool = load_reference_pool(source, ref_path)

    for path in batch_paths:
        if not path.exists():
            continue
        for hit in load_ebsco_hits(path):
            for ref in pool:
                key_type = match_hit_to_reference(hit, ref)
                if not key_type:
                    continue
                value = (
                    hit.doi
                    if key_type == "doi"
                    else f"{hit.year}|{norm_title(hit.title)}"
                )
                _add_conflict(
                    conflicts,
                    seen,
                    DuplicateConflict(
                        scope=f"vs_{source}",
                        match_key_type=key_type,
                        match_key_value=value,
                        title=hit.title,
                        doi=hit.doi,
                        ebsco_an=hit.ebsco_an,
                        batch_files=[hit.batch_file],
                        other_source=source,
                        other_ref=ref["ref"],
                    ),
                )
    return conflicts


def check_duplicates(new_csv_path: Path) -> list[DuplicateConflict]:
    """Check a new EBSCO CSV against prior imports and reference sources."""
    new_path = Path(new_csv_path)
    if not new_path.exists():
        raise FileNotFoundError(new_path)

    existing = sorted(
        p
        for p in IMPORTS_DIR.glob("EBSCO-Metadata-*.csv")
        if p.resolve() != new_path.resolve()
    )
    conflicts = scan_ebsco_duplicates([new_path, *existing])
    conflicts.extend(scan_reference_duplicates([new_path], "legacy_182", ZOTERO_PATH))
    conflicts.extend(scan_reference_duplicates([new_path], "extraction_csv", EXTRACTION_PATH))
    return [c for c in conflicts if new_path.name in c.batch_files]


def collect_all_duplicate_conflicts(batch_paths: list[Path] | None = None) -> list[DuplicateConflict]:
    paths = batch_paths or [b["path"] for b in DEFAULT_EBSCO_BATCHES]
    paths = [Path(p) for p in paths]
    conflicts: list[DuplicateConflict] = []
    seen: set[tuple] = set()
    for group in (
        scan_ebsco_duplicates(paths),
        scan_reference_duplicates(paths, "legacy_182", ZOTERO_PATH),
        scan_reference_duplicates(paths, "extraction_csv", EXTRACTION_PATH),
    ):
        for c in group:
            _add_conflict(conflicts, seen, c)
    return conflicts


def format_batch_files(files: list[str]) -> str:
    labels = sorted({batch_label_from_path(Path(f)) for f in files})
    return "; ".join(labels)


def print_duplicate_warnings(conflicts: list[DuplicateConflict], header: str) -> None:
    if not conflicts:
        print(f"{header}: no duplicates detected.")
        return
    print(f"{header}: {len(conflicts)} conflict(s)")
    for c in conflicts:
        batches = format_batch_files(c.batch_files)
        if c.scope == "cross_batch":
            print(f"  DUPLICATE: [{c.title}] appears in {batches} ({c.match_key_type}={c.match_key_value})")
        elif c.scope == "within_batch":
            print(f"  WITHIN-BATCH DUPLICATE: [{c.title}] in {batches}")
        else:
            print(
                f"  {c.scope.upper()}: [{c.title}] in {batches} "
                f"matches {c.other_source} ({c.other_ref})"
            )


def write_duplicate_report(conflicts: list[DuplicateConflict], out_path: Path) -> None:
    within = [c for c in conflicts if c.scope == "within_batch"]
    cross = [c for c in conflicts if c.scope == "cross_batch"]
    legacy = [c for c in conflicts if c.scope == "vs_legacy_182"]
    extraction = [c for c in conflicts if c.scope == "vs_extraction_csv"]

    lines = [
        "# EBSCO Duplicate Report",
        "",
        f"**Generated**: {TODAY}",
        f"**Script**: `review/master/merge_sources.py`",
        "",
        "## Summary",
        "",
        f"| Scope | Count |",
        f"|-------|------:|",
        f"| Within-batch duplicates | {len(within)} |",
        f"| Cross-batch duplicates | {len(cross)} |",
        f"| vs legacy 182 (Zotero inventory) | {len(legacy)} |",
        f"| vs extraction CSV | {len(extraction)} |",
        "",
        "## Match keys used",
        "",
        "1. EBSCO accession number (`an` / `ebsco_an`) — exact",
        "2. Normalized DOI — exact",
        f"3. Title + year fuzzy match (ratio ≥ {TITLE_FUZZY_THRESHOLD})",
        "",
        "## Within-batch duplicates",
        "",
    ]
    if within:
        for c in within:
            lines.append(
                f"- **{c.title}** — {format_batch_files(c.batch_files)} "
                f"({c.match_key_type}: `{c.match_key_value}`)"
            )
    else:
        lines.append("- None (expected).")

    lines.extend(["", "## Cross-batch duplicates", ""])
    if cross:
        for c in cross:
            lines.append(
                f"- **DUPLICATE: {c.title}** — appears in {format_batch_files(c.batch_files)} "
                f"({c.match_key_type}: `{c.match_key_value}`, DOI: `{c.doi or 'n/a'}`)"
            )
    else:
        lines.append("- None across configured EBSCO batches.")

    lines.extend(["", "## Duplicates vs legacy 182", ""])
    if legacy:
        for c in legacy:
            lines.append(
                f"- **{c.title}** — {format_batch_files(c.batch_files)} ↔ {c.other_ref}"
            )
    else:
        lines.append("- None detected against `legacy_182_zotero_inventory.csv`.")

    lines.extend(["", "## Duplicates vs extraction CSV", ""])
    if extraction:
        for c in extraction:
            lines.append(
                f"- **{c.title}** — {format_batch_files(c.batch_files)} ↔ {c.other_ref}"
            )
    else:
        lines.append("- None detected against `systematic_extraction_40_studies.csv`.")

    lines.extend(
        [
            "",
            "## What to do",
            "",
            "- **Within-batch**: remove the extra row from the export before merge.",
            "- **Cross-batch**: keep one copy; merge script collapses on `ebsco_an`/DOI/title+year.",
            "- **vs legacy/extraction**: confirm linkage; set `legacy_refid` or `study_order` if correct.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_duplicates_flagged(conflicts: list[DuplicateConflict], out_path: Path) -> None:
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DUPLICATE_COLUMNS)
        writer.writeheader()
        for i, c in enumerate(conflicts, start=1):
            writer.writerow(
                {
                    "conflict_id": f"D{i:04d}",
                    "scope": c.scope,
                    "match_key_type": c.match_key_type,
                    "match_key_value": c.match_key_value,
                    "title": c.title,
                    "doi": c.doi,
                    "ebsco_an": c.ebsco_an,
                    "batch_files": ";".join(sorted(c.batch_files)),
                    "other_source": c.other_source,
                    "other_ref": c.other_ref,
                    "action_recommended": c.action_recommended(),
                }
            )


def merge_field(existing: str, incoming: str) -> str:
    if incoming and (not existing or len(incoming) > len(existing)):
        return incoming
    return existing


def add_source(sources: str, tag: str) -> str:
    parts = [p.strip() for p in sources.split(";") if p.strip()]
    if tag not in parts:
        parts.append(tag)
    return ";".join(parts)


def add_import_file(existing: str, filename: str) -> str:
    parts = [p.strip() for p in existing.split(";") if p.strip()]
    if filename not in parts:
        parts.append(filename)
    return ";".join(parts)


def empty_record() -> dict[str, str]:
    rec = {col: "" for col in MASTER_COLUMNS}
    rec["created_at"] = TODAY
    rec["updated_at"] = TODAY
    rec["screening_status"] = "pending"
    rec["extraction_status"] = "none"
    return rec


class Registry:
    def __init__(self) -> None:
        self.by_key: dict[str, dict[str, str]] = {}
        self.title_year_index: list[tuple[str, str, str]] = []
        self.stats: dict[str, int] = defaultdict(int)
        self.duplicate_ebsco: list[str] = []
        self.next_id = 1

    def _assign_id(self, rec: dict[str, str]) -> None:
        if not rec.get("article_id"):
            rec["article_id"] = f"M{self.next_id:04d}"
            self.next_id += 1

    def find_key(
        self,
        doi: str = "",
        ebsco_an: str = "",
        title: str = "",
        year: str = "",
        legacy_refid: str = "",
    ) -> str | None:
        if legacy_refid:
            for key, rec in self.by_key.items():
                if rec.get("legacy_refid", "") == legacy_refid:
                    return key
        doi_n = norm_doi(doi)
        if doi_n:
            for key, rec in self.by_key.items():
                if norm_doi(rec.get("doi", "")) == doi_n:
                    return key
        if ebsco_an:
            for key, rec in self.by_key.items():
                if rec.get("ebsco_an", "") == ebsco_an:
                    return key
        if title and year:
            for key, t, y in self.title_year_index:
                if y == year and fuzzy_ratio(title, t) >= 0.92:
                    return key
        return None

    def upsert(
        self,
        patch: dict[str, str],
        *,
        source_tag: str,
        import_file: str = "",
        match_hint: tuple[str, str, str, str] | None = None,
    ) -> str:
        doi = patch.get("doi", "")
        ebsco_an = patch.get("ebsco_an", "")
        title = patch.get("title", "")
        year = patch.get("year", "")
        legacy_refid = patch.get("legacy_refid", "")

        key = self.find_key(
            doi=doi,
            ebsco_an=ebsco_an,
            title=title,
            year=year,
            legacy_refid=legacy_refid,
        )
        if key is None:
            key = f"new:{self.next_id}"
            rec = empty_record()
            self.by_key[key] = rec
            if title and year:
                self.title_year_index.append((key, title, year))
        else:
            rec = self.by_key[key]
            self.stats["merged_records"] += 1

        for field, value in patch.items():
            if field in ("sources", "source_import_file"):
                continue
            if not value:
                continue
            if field == "extraction_status":
                rec[field] = merge_extraction_status(rec.get(field, ""), value)
            else:
                rec[field] = merge_field(rec.get(field, ""), value)

        rec["sources"] = add_source(rec.get("sources", ""), source_tag)
        if import_file:
            rec["source_import_file"] = add_import_file(
                rec.get("source_import_file", ""), import_file
            )
        rec["updated_at"] = TODAY
        self._assign_id(rec)

        if match_hint:
            refid, method, confidence, snippet = match_hint
            if not rec.get("legacy_refid"):
                rec["legacy_refid"] = refid
                rec["legacy_match_method"] = method
                rec["legacy_match_confidence"] = confidence
                if snippet:
                    rec["legacy_text_snippet"] = merge_field(
                        rec.get("legacy_text_snippet", ""), snippet
                    )

        return key


def ebsco_row_to_patch(row: dict[str, str], batch_meta: dict[str, Any]) -> dict[str, str]:
    pub_date = row.get("publicationDate", "")
    year = parse_year(pub_date) or parse_year(row.get("coverDate", ""))
    journal = (row.get("source") or "").strip()
    doi = norm_doi(row.get("doi"))
    outlet, _ = infer_publisher_outlet(doi, journal)
    return {
        "title": (row.get("title") or "").strip(),
        "authors": (row.get("contributors") or "").strip(),
        "year": year,
        "journal": journal,
        "volume": (row.get("volume") or "").strip(),
        "issue": (row.get("issue") or "").strip(),
        "doi": doi,
        "publisher_outlet": outlet,
        "ebsco_an": (row.get("an") or "").strip(),
        "abstract": (row.get("abstract") or "").strip(),
        "ebsco_db": (row.get("longDBName") or row.get("shortDBName") or "").strip(),
        "ebsco_plink": (row.get("plink") or "").strip(),
        "cover_date": (row.get("coverDate") or "").strip(),
        "ebsco_batch": str(batch_meta["ebsco_batch"]),
        "notes": f"ebsco_record_range={batch_meta['record_range']}",
    }


def load_legacy(registry: Registry) -> None:
    rows = read_csv(LEGACY_PATH)
    included = [r for r in rows if parse_bool(r.get("final_include")) == "True"]
    registry.stats["legacy_rows"] = len(rows)
    registry.stats["legacy_included"] = len(included)

    for row in included:
        refid = (row.get("Refid") or "").strip()
        mv = (row.get("method_variance_pct") or "").strip()
        snippet = (row.get("text_extraction") or "").strip()
        registry.upsert(
            {
                "legacy_refid": refid,
                "legacy_final_include": "True",
                "legacy_text_snippet": snippet[:500] if snippet else "",
                "legacy_mv_pct": mv,
                "legacy_match_method": "refid_direct",
                "legacy_match_confidence": "exact",
                "screening_level1_include": parse_bool(row.get("level1_include")),
                "screening_status": "included"
                if parse_bool(row.get("level1_include")) == "True"
                else "pending",
                "extraction_status": "legacy_only",
            },
            source_tag="legacy_182",
            import_file=LEGACY_PATH.name,
        )
        registry.stats["legacy_upserts"] += 1


def enrich_from_search_order_export(registry: Registry) -> dict[str, int]:
    """Enrich in-pool master rows from 06_26_2026 native search-order export; skip off-pool."""
    stats = {"enriched": 0, "skipped_off_pool": 0, "skipped_no_match": 0}
    for entry in load_search_order_entries():
        key = registry.find_key(
            doi=entry.get("doi", ""),
            ebsco_an=entry.get("ebsco_an", ""),
            title=entry.get("title", ""),
            year=entry.get("year", ""),
        )
        if key is None:
            stats["skipped_no_match"] += 1
            continue
        rec = registry.by_key[key]
        if not is_ebsco_pool_member(rec):
            stats["skipped_off_pool"] += 1
            continue
        registry.upsert(
            search_order_row_to_patch(entry),
            source_tag="ebsco_2026_search_order",
            import_file=entry.get("import_file", ""),
        )
        stats["enriched"] += 1
    return stats


def load_ebsco_batches(registry: Registry, batches: list[dict[str, Any]]) -> None:
    seen_an: dict[str, str] = {}
    for batch in batches:
        path: Path = batch["path"]
        if not path.exists():
            registry.stats["missing_ebsco_files"] += 1
            continue
        rows = read_csv(path)
        registry.stats[f"ebsco_batch{batch['ebsco_batch']}_rows"] = len(rows)
        for row in rows:
            an = (row.get("an") or "").strip()
            if an in seen_an:
                registry.duplicate_ebsco.append(
                    f"AN {an}: {seen_an[an]} vs {path.name}"
                )
            else:
                seen_an[an] = path.name
            registry.upsert(
                ebsco_row_to_patch(row, batch),
                source_tag=batch["source_tag"],
                import_file=path.name,
            )
            registry.stats["ebsco_upserts"] += 1


def load_ebsco_feb(registry: Registry) -> None:
    rows = read_csv(EBSCO_FEB_PATH)
    registry.stats["ebsco_feb_rows"] = len(rows)
    for row in rows:
        registry.upsert(
            {
                "title": (row.get("title") or "").strip(),
                "authors": (row.get("authors") or "").strip(),
                "year": parse_year(row.get("year", "")),
                "journal": (row.get("journal") or "").strip(),
                "volume": (row.get("volume") or "").strip(),
                "issue": (row.get("issue") or "").strip(),
                "doi": norm_doi(row.get("doi")),
                "ebsco_an": (row.get("an") or "").strip(),
                "ebsco_plink": (row.get("plink") or "").strip(),
                "cover_date": (row.get("cover_date") or "").strip(),
            },
            source_tag="ebsco_2026_02",
            import_file=EBSCO_FEB_PATH.name,
        )
        registry.stats["ebsco_feb_upserts"] += 1


def load_extraction(registry: Registry) -> None:
    rows = read_csv(EXTRACTION_PATH)
    registry.stats["extraction_rows"] = len(rows)
    for row in rows:
        study_order = (row.get("study_order") or "").strip()
        refid = ""
        if study_order.startswith("L") and study_order[1:].isdigit():
            refid = study_order[1:]
        patch = {
            "title": (row.get("study_title") or "").strip(),
            "authors": (row.get("authors") or "").strip(),
            "year": parse_year(row.get("year", "")),
            "journal": (row.get("journal") or "").strip(),
            "doi": norm_doi(row.get("doi")),
            "study_order": study_order,
            "extraction_file": "systematic_extraction_40_studies.csv",
            "extraction_status": "complete",
            "legacy_mv_pct": (row.get("method_variance_pct") or "").strip(),
        }
        if refid:
            patch["legacy_refid"] = refid
            patch["legacy_match_method"] = "refid_L_prefix"
            patch["legacy_match_confidence"] = "exact"
        registry.upsert(
            patch,
            source_tag="extraction_csv",
            import_file=EXTRACTION_PATH.name,
        )
        registry.stats["extraction_upserts"] += 1


def load_zotero(registry: Registry) -> None:
    rows = read_csv(ZOTERO_PATH)
    registry.stats["zotero_rows"] = len(rows)
    for row in rows:
        refid = (row.get("refid") or "").strip()
        if not refid:
            continue
        patch = {
            "legacy_refid": refid,
            "title": (row.get("title") or "").strip(),
            "year": parse_year(row.get("year", "")),
            "journal": (row.get("journal") or "").strip(),
            "doi": norm_doi(row.get("doi")),
            "zotero_key": (row.get("zotero_item_key") or "").strip(),
            "has_pdf": parse_bool(row.get("has_pdf")),
        }
        registry.upsert(
            patch,
            source_tag="zotero_inventory",
            import_file=ZOTERO_PATH.name,
        )
        registry.stats["zotero_upserts"] += 1


def apply_overlap_report(registry: Registry) -> None:
    rows = read_csv(OVERLAP_PATH)
    assigned_refids = {
        rec.get("legacy_refid")
        for rec in registry.by_key.values()
        if rec.get("legacy_refid")
    }

    for row in rows:
        refid = (row.get("refid") or "").strip()
        method = (row.get("match_method") or "").strip()
        confidence = (row.get("confidence") or "").strip()
        study_order = (row.get("matched_study_order") or "").strip()
        if not refid or refid in assigned_refids:
            continue
        for rec in registry.by_key.values():
            if rec.get("study_order") == study_order and study_order:
                if rec.get("legacy_refid") and rec.get("legacy_refid") != refid:
                    continue
                rec["legacy_refid"] = refid
                rec["legacy_match_method"] = method or "overlap_report"
                rec["legacy_match_confidence"] = confidence or "weak"
                assigned_refids.add(refid)
                break


def write_master(registry: Registry, out_path: Path) -> None:
    records = sorted(registry.by_key.values(), key=lambda r: r.get("article_id", ""))
    records = enrich_master_records(records)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MASTER_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def crosswalk_ebsco_batch(registry: Registry, batch_num: int, source_tag: str) -> dict[str, Any]:
    """Crosswalk one EBSCO rerun batch to legacy 182, hunt list, gaps, and extraction."""
    batch_str = str(batch_num)
    batch_records = [
        r
        for r in registry.by_key.values()
        if r.get("ebsco_batch") == batch_str or source_tag in r.get("sources", "")
    ]
    seen: set[str] = set()
    batch_unique: list[dict[str, str]] = []
    for r in batch_records:
        aid = r.get("article_id", "")
        if aid not in seen:
            seen.add(aid)
            batch_unique.append(r)

    legacy_refids = {
        r.get("legacy_refid")
        for r in registry.by_key.values()
        if parse_bool(r.get("legacy_final_include")) == "True" and r.get("legacy_refid")
    }
    hunt_refids = {"142", "147", "153", "160", "161", "163", "165", "166", "172", "191"}
    gaps_refids = {
        (row.get("refid") or "").strip()
        for row in read_csv(LEGACY_DIR / "legacy_182_gaps_only.csv")
        if (row.get("refid") or "").strip()
    }
    extraction_refids = set()
    for r in registry.by_key.values():
        so = r.get("study_order", "")
        if so.startswith("L") and so[1:].isdigit():
            extraction_refids.add(so[1:])

    matched_legacy: list[tuple[str, str]] = []
    matched_hunt: list[tuple[str, str]] = []
    matched_gaps: list[tuple[str, str]] = []
    matched_extraction: list[tuple[str, str]] = []
    for r in batch_unique:
        rid = r.get("legacy_refid", "")
        if rid and rid in legacy_refids:
            matched_legacy.append((rid, r.get("title", "")[:80]))
        if rid and rid in hunt_refids:
            matched_hunt.append((rid, r.get("title", "")[:80]))
        if rid and rid in gaps_refids:
            matched_gaps.append((rid, r.get("title", "")[:80]))
        if rid and rid in extraction_refids:
            matched_extraction.append((rid, r.get("title", "")[:80]))
        if not rid:
            doi = norm_doi(r.get("doi"))
            for other in registry.by_key.values():
                if (
                    other.get("legacy_refid")
                    and parse_bool(other.get("legacy_final_include")) == "True"
                    and norm_doi(other.get("doi")) == doi
                    and doi
                ):
                    matched_legacy.append((other["legacy_refid"], r.get("title", "")[:80]))
                    break

    return {
        "batch_num": batch_num,
        "batch_count": len(batch_unique),
        "matched_legacy_refid": matched_legacy,
        "matched_hunt_refid": matched_hunt,
        "matched_gaps_refid": matched_gaps,
        "matched_extraction_refid": matched_extraction,
    }


def _append_crosswalk_section(lines: list[str], crosswalk: dict[str, Any], heading: str) -> None:
    lines.extend(
        [
            "",
            f"## {heading}",
            "",
            f"- Records in master: **{crosswalk['batch_count']}**",
            f"- Matched legacy 182 refids: **{len(crosswalk['matched_legacy_refid'])}**",
            f"- Matched hunt-list refids (10-pilot): **{len(crosswalk['matched_hunt_refid'])}**",
            f"- Matched gaps-only list (`legacy_182_gaps_only.csv`): **{len(crosswalk['matched_gaps_refid'])}**",
            f"- Matched prior extraction (`L{{refid}}`): **{len(crosswalk['matched_extraction_refid'])}**",
            "",
        ]
    )
    for label, key in (
        ("Legacy 182 matches", "matched_legacy_refid"),
        ("Hunt-list matches", "matched_hunt_refid"),
        ("Gaps-only matches", "matched_gaps_refid"),
        ("Prior extraction matches", "matched_extraction_refid"),
    ):
        items = crosswalk[key]
        if items:
            lines.append(f"### {label}")
            for rid, title in items:
                lines.append(f"- Refid {rid}: {title}")
            lines.append("")


def write_report(
    registry: Registry,
    out_path: Path,
    crosswalks: list[dict[str, Any]],
    *,
    pdf_sync: Any | None = None,
) -> None:
    total = len(registry.by_key.values())
    ebsco_rerun_total = sum(
        registry.stats.get(f"ebsco_batch{b['ebsco_batch']}_rows", 0)
        for b in DEFAULT_EBSCO_BATCHES
    )
    legacy_linked = sum(1 for r in registry.by_key.values() if r.get("legacy_refid"))

    lines = [
        "# Merge Report",
        "",
        f"**Generated**: {TODAY}",
        "",
        "## Input counts",
        "",
        f"| Source | Rows loaded |",
        f"|--------|-------------|",
        f"| Legacy extracted (`final_include=TRUE`) | {registry.stats.get('legacy_included', 0)} |",
        f"| EBSCO batch 1 (`EBSCO-Metadata-06_24_2026-2.csv`, records 1–50) | {registry.stats.get('ebsco_batch1_rows', 0)} |",
        f"| EBSCO batch 2 (`EBSCO-Metadata-06_24_2026-3.csv`, records 51–100) | {registry.stats.get('ebsco_batch2_rows', 0)} |",
        f"| EBSCO batch 3 (`EBSCO-Metadata-06_24_2026-4.csv`, records 101–150) | {registry.stats.get('ebsco_batch3_rows', 0)} |",
        f"| EBSCO batch 4 (`EBSCO-Metadata-06_24_2026-5.csv`, records 151–200) | {registry.stats.get('ebsco_batch4_rows', 0)} |",
        f"| EBSCO batch 5 (`EBSCO-Metadata-06_24_2026-6.csv`, records 201–250) | {registry.stats.get('ebsco_batch5_rows', 0)} |",
        f"| EBSCO batch 6 (`EBSCO-Metadata-06_24_2026-7.csv`, records 301–350) | {registry.stats.get('ebsco_batch6_rows', 0)} |",
        f"| EBSCO batch 7 (`EBSCO-Metadata-06_24_2026-8.csv`, records 351–400) | {registry.stats.get('ebsco_batch7_rows', 0)} |",
        f"| EBSCO batch 8 (`EBSCO-Metadata-06_24_2026-9.csv`, records 401–450) | {registry.stats.get('ebsco_batch8_rows', 0)} |",
        f"| EBSCO batch 9 (`EBSCO-Metadata-06_24_2026-10.csv`, records 451–500) | {registry.stats.get('ebsco_batch9_rows', 0)} |",
        f"| EBSCO batch 10 (`EBSCO-Metadata-06_24_2026-11.csv`, records 501–550) | {registry.stats.get('ebsco_batch10_rows', 0)} |",
        f"| EBSCO batch 11 (`EBSCO-Metadata-06_24_2026-12.csv`, records 551–570) | {registry.stats.get('ebsco_batch11_rows', 0)} |",
        f"| EBSCO June 2026 rerun **total** | {ebsco_rerun_total} |",
        f"| EBSCO Feb export (`ebsco_export_50_records.csv`) | {registry.stats.get('ebsco_feb_rows', 0)} |",
        f"| Extraction CSV | {registry.stats.get('extraction_rows', 0)} |",
        f"| Zotero inventory | {registry.stats.get('zotero_rows', 0)} |",
        "",
        "## Output",
        "",
        f"- **Total master rows**: {total}",
        f"- **Records with legacy_refid**: {legacy_linked}",
        f"- **Cross-source merges** (duplicate keys collapsed): {registry.stats.get('merged_records', 0)}",
        f"- **PDF links restored from INGEST_LOG** (post-merge): {pdf_sync.restored if pdf_sync else 0} primary, {pdf_sync.alias if pdf_sync else 0} DOI alias",
        "",
        f"## EBSCO duplicate ANs (across batches 1–{len(DEFAULT_EBSCO_BATCHES)})",
        "",
    ]
    if registry.duplicate_ebsco:
        lines.extend(f"- {d}" for d in registry.duplicate_ebsco)
    else:
        lines.append("- None detected between configured EBSCO batches.")

    for crosswalk in crosswalks:
        batch_num = crosswalk["batch_num"]
        record_range = next(
            (b["record_range"] for b in DEFAULT_EBSCO_BATCHES if b["ebsco_batch"] == batch_num),
            "",
        )
        _append_crosswalk_section(
            lines,
            crosswalk,
            f"Batch {record_range} crosswalk (ebsco_batch={batch_num})",
        )

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge review sources into articles_master.csv")
    parser.add_argument(
        "--output",
        type=Path,
        default=MASTER_DIR / "articles_master.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=MASTER_DIR / "merge_report.md",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run duplicate detection only; do not merge into articles_master.csv",
    )
    parser.add_argument(
        "--new-csv",
        type=Path,
        metavar="PATH",
        help="Check one new EBSCO CSV against existing imports (implies --check-only)",
    )
    args = parser.parse_args()

    batch_paths = [b["path"] for b in DEFAULT_EBSCO_BATCHES]

    if args.new_csv:
        conflicts = check_duplicates(args.new_csv)
        print_duplicate_warnings(conflicts, f"Duplicate check for {args.new_csv.name}")
        write_duplicate_report(conflicts, DUPLICATE_REPORT)
        write_duplicates_flagged(conflicts, DUPLICATES_FLAGGED)
        print(f"Wrote {DUPLICATE_REPORT}")
        print(f"Wrote {DUPLICATES_FLAGGED}")
        return

    all_conflicts = collect_all_duplicate_conflicts(batch_paths)
    print_duplicate_warnings(all_conflicts, "EBSCO duplicate scan (all configured batches)")
    write_duplicate_report(all_conflicts, DUPLICATE_REPORT)
    write_duplicates_flagged(all_conflicts, DUPLICATES_FLAGGED)

    if args.check_only:
        print(f"Wrote {DUPLICATE_REPORT}")
        print(f"Wrote {DUPLICATES_FLAGGED}")
        return

    registry = Registry()
    load_legacy(registry)
    load_ebsco_batches(registry, DEFAULT_EBSCO_BATCHES)
    load_ebsco_feb(registry)
    load_extraction(registry)
    load_zotero(registry)
    apply_overlap_report(registry)
    search_order_stats = enrich_from_search_order_export(registry)
    registry.stats["search_order_enriched"] = search_order_stats["enriched"]
    registry.stats["search_order_skipped_off_pool"] = search_order_stats["skipped_off_pool"]
    registry.stats["search_order_skipped_no_match"] = search_order_stats["skipped_no_match"]

    crosswalks = [
        crosswalk_ebsco_batch(registry, b["ebsco_batch"], b["source_tag"])
        for b in DEFAULT_EBSCO_BATCHES
    ]
    write_master(registry, args.output)
    pdf_sync = sync_pdf_links_from_ingest(args.output)
    write_report(registry, args.report, crosswalks, pdf_sync=pdf_sync)

    print(
        f"Search-order enrich: {registry.stats.get('search_order_enriched', 0)} in-pool rows; "
        f"skipped off-pool {registry.stats.get('search_order_skipped_off_pool', 0)}; "
        f"no master match {registry.stats.get('search_order_skipped_no_match', 0)}"
    )
    print(f"Wrote {args.output} ({len(registry.by_key)} rows)")
    print(
        f"PDF links restored from INGEST_LOG: {pdf_sync.restored} primary, "
        f"{pdf_sync.alias} DOI alias (pdf_map={pdf_sync.pdf_map_size})"
    )
    print(f"Wrote {args.report}")
    print(f"Wrote {DUPLICATE_REPORT}")
    print(f"Wrote {DUPLICATES_FLAGGED}")


if __name__ == "__main__":
    main()
