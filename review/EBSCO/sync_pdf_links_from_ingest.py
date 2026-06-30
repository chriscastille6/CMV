#!/usr/bin/env python3
"""Reconcile articles_master PDF fields from INGEST_LOG and on-disk EBSCO_M*.pdf files.

After merge_sources.py rebuilds articles_master.csv, EBSCO ingest paths are not in merge
inputs; this script restores has_pdf / pdf_path / pdf_status from the ingest log and filename
fallback (latest matched row per master_id, then EBSCO_{M####}_*.pdf on disk).
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
DEFAULT_MASTER = ROOT / "review" / "master" / "articles_master.csv"
INGEST_LOG = EBSCO_DIR / "pdfs" / "INGEST_LOG.csv"
PDF_DIR = EBSCO_DIR / "pdfs"


def norm_doi(value: str) -> str:
    v = (value or "").strip().lower()
    if v.startswith("https://doi.org/"):
        v = v[18:]
    if v.startswith("doi:"):
        v = v[4:]
    return v.strip()


def build_pdf_map(
    *,
    root: Path = ROOT,
    ingest_log: Path = INGEST_LOG,
    pdf_dir: Path = PDF_DIR,
) -> dict[str, str]:
    """Map master article_id -> repo-relative pdf_path for files that exist."""
    by_mid: dict[str, tuple[str, str]] = {}
    if ingest_log.exists():
        with ingest_log.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("status") != "matched":
                    continue
                mid = (row.get("master_id") or "").strip()
                rel = (row.get("pdf_path") or "").strip()
                if not mid or not rel:
                    continue
                ts = row.get("processed_at") or ""
                prev = by_mid.get(mid)
                if prev is None or ts >= prev[0]:
                    by_mid[mid] = (ts, rel)

    pdf_map: dict[str, str] = {}
    for mid, (_, rel) in by_mid.items():
        if (root / rel).exists():
            pdf_map[mid] = rel

    if pdf_dir.is_dir():
        for path in pdf_dir.glob("EBSCO_M*.pdf"):
            match = re.match(r"EBSCO_(M\d+)_", path.name)
            if not match:
                continue
            mid = match.group(1)
            rel = f"review/EBSCO/pdfs/{path.name}"
            pdf_map.setdefault(mid, rel)

    return pdf_map


@contextmanager
def master_file_lock(master_path: Path):
    lock_path = master_path.with_suffix(".csv.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


@dataclass
class SyncResult:
    pdf_map_size: int
    restored: int
    alias: int
    missing_master: int

    def as_dict(self) -> dict[str, int]:
        return {
            "pdf_map": self.pdf_map_size,
            "restored": self.restored,
            "alias": self.alias,
            "missing_master": self.missing_master,
        }


def _row_has_pdf_link(row: dict[str, str], rel: str) -> bool:
    return (
        (row.get("has_pdf") or "").lower() == "true"
        and (row.get("pdf_path") or "").strip() == rel
        and (row.get("pdf_status") or "") == "available"
    )


def sync_pdf_links_from_ingest(
    master_path: Path | None = None,
    *,
    dry_run: bool = False,
    today: str | None = None,
) -> SyncResult:
    master = master_path or DEFAULT_MASTER
    if not master.exists():
        return SyncResult(0, 0, 0, 0)

    pdf_map = build_pdf_map()
    updated_at = today or date.today().isoformat()
    missing_master: list[str] = []

    with master_file_lock(master):
        with master.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
            rows = list(reader)

        by_id = {r.get("article_id", ""): r for r in rows}
        doi_index: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            doi = norm_doi(row.get("doi", ""))
            if doi:
                doi_index.setdefault(doi, []).append(row)

        restored = 0
        for mid, rel in pdf_map.items():
            if not (ROOT / rel).exists():
                continue
            row = by_id.get(mid)
            if not row:
                missing_master.append(mid)
                continue
            if _row_has_pdf_link(row, rel):
                continue
            if not dry_run:
                row["has_pdf"] = "True"
                row["pdf_path"] = rel
                row["pdf_status"] = "available"
                row["updated_at"] = updated_at
            restored += 1

        alias = 0
        for mid, rel in pdf_map.items():
            row = by_id.get(mid)
            if not row or not (ROOT / rel).exists():
                continue
            doi = norm_doi(row.get("doi", ""))
            if not doi:
                continue
            for other in doi_index.get(doi, []):
                if other.get("article_id") == mid:
                    continue
                if _row_has_pdf_link(other, rel):
                    continue
                if not dry_run:
                    other["has_pdf"] = "True"
                    other["pdf_path"] = rel
                    other["pdf_status"] = "available"
                    other["updated_at"] = updated_at
                alias += 1

        if not dry_run and (restored or alias):
            with master.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)

    return SyncResult(
        pdf_map_size=len(pdf_map),
        restored=restored,
        alias=alias,
        missing_master=len(missing_master),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync articles_master PDF fields from INGEST_LOG and EBSCO_M*.pdf files",
    )
    parser.add_argument(
        "--master",
        type=Path,
        default=DEFAULT_MASTER,
        help="Path to articles_master.csv",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without writing articles_master.csv",
    )
    args = parser.parse_args()

    result = sync_pdf_links_from_ingest(args.master, dry_run=args.dry_run)
    prefix = "Would restore" if args.dry_run else "Restored"
    print(f"pdf_map entries: {result.pdf_map_size}")
    print(f"{prefix} primary rows: {result.restored}")
    print(f"{prefix} DOI alias rows: {result.alias}")
    if result.missing_master:
        print(f"missing_master (PDF on disk, no master row): {result.missing_master}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
