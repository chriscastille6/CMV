"""EBSCO native search-order worklist (06_26_2026 export, positions 1–200)."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
IMPORTS_DIR = Path(__file__).resolve().parent / "imports"

FIRST_150_SIZE = 150
FIRST_200_SIZE = 200

# Native EBSCO search order export (4 × 50 rows).
EBSCO_SEARCH_ORDER_IMPORTS: list[dict[str, Any]] = [
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_26_2026.csv",
        "position_start": 1,
        "record_range": "1-50",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_26_2026-2.csv",
        "position_start": 51,
        "record_range": "51-100",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_26_2026-3.csv",
        "position_start": 101,
        "record_range": "101-150",
    },
    {
        "path": IMPORTS_DIR / "EBSCO-Metadata-06_26_2026-4.csv",
        "position_start": 151,
        "record_range": "151-200",
    },
]

QUEUE_FILENAME = "download_queue_ebsco_order.csv"


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


def parse_year(value: str | None) -> str:
    if not value:
        return ""
    s = str(value).strip()
    m = re.search(r"(19|20)\d{2}", s)
    return m.group(0) if m else ""


def is_ebsco_pool_member(rec: dict[str, str]) -> bool:
    sources = rec.get("sources", "") or ""
    if "ebsco_2026" in sources:
        return True
    return rec.get("corpus_tier", "") == "ebsco_screened"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_search_order_entries() -> list[dict[str, str]]:
    """Load rows from the 06_26_2026 search-order export with assigned positions."""
    entries: list[dict[str, str]] = []
    for batch in EBSCO_SEARCH_ORDER_IMPORTS:
        path: Path = batch["path"]
        if not path.exists():
            continue
        start = int(batch["position_start"])
        for i, row in enumerate(read_csv(path)):
            position = start + i
            pub_date = row.get("publicationDate", "")
            year = parse_year(pub_date) or parse_year(row.get("coverDate", ""))
            entries.append(
                {
                    "ebsco_search_position": str(position),
                    "ebsco_an": (row.get("an") or "").strip(),
                    "doi": norm_doi(row.get("doi")),
                    "title": (row.get("title") or "").strip(),
                    "authors": (row.get("contributors") or "").strip(),
                    "year": year,
                    "journal": (row.get("source") or "").strip(),
                    "abstract": (row.get("abstract") or "").strip(),
                    "ebsco_db": (row.get("longDBName") or row.get("shortDBName") or "").strip(),
                    "ebsco_plink": (row.get("plink") or "").strip(),
                    "cover_date": (row.get("coverDate") or "").strip(),
                    "volume": (row.get("volume") or "").strip(),
                    "issue": (row.get("issue") or "").strip(),
                    "import_file": path.name,
                    "record_range": batch["record_range"],
                }
            )
    return entries


def build_position_lookups(
    entries: list[dict[str, str]] | None = None,
) -> tuple[dict[str, int], dict[str, int], dict[str, dict[str, str]]]:
    """Return (by_doi, by_an, by_position) lookups."""
    if entries is None:
        entries = load_search_order_entries()
    by_doi: dict[str, int] = {}
    by_an: dict[str, int] = {}
    by_position: dict[str, dict[str, str]] = {}
    for entry in entries:
        pos = int(entry["ebsco_search_position"])
        doi = entry.get("doi", "")
        an = entry.get("ebsco_an", "")
        if doi:
            by_doi[doi] = pos
        if an:
            by_an[an] = pos
        by_position[str(pos)] = entry
    return by_doi, by_an, by_position


def lookup_search_position(
    doi: str | None,
    ebsco_an: str | None,
    by_doi: dict[str, int],
    by_an: dict[str, int],
) -> int | None:
    doi_n = norm_doi(doi)
    if doi_n and doi_n in by_doi:
        return by_doi[doi_n]
    an = (ebsco_an or "").strip()
    if an and an in by_an:
        return by_an[an]
    return None


def find_master_for_entry(
    entry: dict[str, str],
    master: list[dict[str, str]],
) -> dict[str, str] | None:
    """Match a search-order export row to an articles_master record."""
    doi = entry.get("doi", "")
    an = entry.get("ebsco_an", "")
    for rec in master:
        if doi and norm_doi(rec.get("doi")) == doi:
            return rec
    if an:
        for rec in master:
            if rec.get("ebsco_an", "") == an:
                return rec
    return None


def load_worklist_1_150_from_master(
    master: list[dict[str, str]],
) -> list[dict[str, str]]:
    """
    One row per EBSCO native export position 1–150, merged with master when matched.

    Uses DOI / ebsco_an join (not master ebsco_search_position) so stale position
    fields on enriched rows do not drop export slots from the worklist.
    """
    rows: list[dict[str, str]] = []
    for entry in load_search_order_entries():
        pos = int(entry["ebsco_search_position"])
        if pos > FIRST_150_SIZE:
            continue
        rec = find_master_for_entry(entry, master)
        if rec:
            merged = {**rec}
            merged["ebsco_search_position"] = str(pos)
            if not merged.get("title"):
                merged["title"] = entry.get("title", "")
            if not merged.get("abstract"):
                merged["abstract"] = entry.get("abstract", "")
            rows.append(merged)
        else:
            rows.append(
                {
                    "article_id": "",
                    "ebsco_search_position": str(pos),
                    "title": entry.get("title", ""),
                    "authors": entry.get("authors", ""),
                    "year": entry.get("year", ""),
                    "journal": entry.get("journal", ""),
                    "doi": entry.get("doi", ""),
                    "abstract": entry.get("abstract", ""),
                    "ebsco_an": entry.get("ebsco_an", ""),
                    "screening_status": "pending",
                }
            )
    rows.sort(key=lambda r: int(r["ebsco_search_position"]))
    return rows


def search_order_row_to_patch(entry: dict[str, str]) -> dict[str, str]:
    return {
        "title": entry.get("title", ""),
        "authors": entry.get("authors", ""),
        "year": entry.get("year", ""),
        "journal": entry.get("journal", ""),
        "volume": entry.get("volume", ""),
        "issue": entry.get("issue", ""),
        "doi": entry.get("doi", ""),
        "ebsco_an": entry.get("ebsco_an", ""),
        "abstract": entry.get("abstract", ""),
        "ebsco_db": entry.get("ebsco_db", ""),
        "ebsco_plink": entry.get("ebsco_plink", ""),
        "cover_date": entry.get("cover_date", ""),
        "ebsco_search_position": entry.get("ebsco_search_position", ""),
        "notes": f"ebsco_search_position={entry.get('ebsco_search_position', '')};ebsco_record_range={entry.get('record_range', '')}",
    }
