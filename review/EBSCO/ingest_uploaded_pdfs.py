#!/usr/bin/env python3
"""
Ingest EBSCO full-text PDFs from Downloads (or a single path) into the CMV review corpus.

Matches parsed bibliographic data to articles_master.csv, copies PDFs to
review/EBSCO/pdfs/, updates has_pdf / pdf_path / pdf_status, and appends INGEST_LOG.csv.

Usage:
  python3 review/EBSCO/ingest_uploaded_pdfs.py --scan-downloads
  python3 review/EBSCO/ingest_uploaded_pdfs.py --pdf ~/Downloads/EBSCO-FullText-06_24_2026-4.pdf
  python3 review/EBSCO/ingest_uploaded_pdfs.py --scan-downloads --dry-run

After a batch:
  python3 review/master/progress_counter.py

Concurrency: run one ingest process at a time. Parallel runs contend on
articles_master.csv; the script uses file locking but batch ingest is safest
via --scan-downloads (serial per file) rather than multiple --pdf agents.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import re
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
MASTER_LOCK_PATH = MASTER_PATH.with_suffix(".csv.lock")
PDF_DIR = EBSCO_DIR / "pdfs"
TEXT_DIR = EBSCO_DIR / "text"
IMPORTS_DIR = EBSCO_DIR / "imports"
INGEST_LOG = PDF_DIR / "INGEST_LOG.csv"
DOWNLOADS_DIR = Path.home() / "Downloads"

sys.path.insert(0, str(EBSCO_DIR))
from parse_ebsco_fulltext_pdf import (  # noqa: E402
    extract_text,
    first_author_last,
    match_ebsco_metadata,
    parse_fulltext_article,
    slug,
)

INGEST_COLUMNS = [
    "filename",
    "processed_at",
    "master_id",
    "refid",
    "match_type",
    "pdf_path",
    "status",
    "title",
    "notes",
]

TITLE_FUZZY_THRESHOLD = 0.92


def norm_doi(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    if v in {"na", "n/a", "none", "null", "nan", "-"}:
        return ""
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if v.startswith(prefix):
            v = v[len(prefix) :]
    return v.rstrip(".,;)")


def norm_title(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def fuzzy_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def extract_doi_from_text(text: str) -> str:
    first_page = text[:12000]
    for block in (first_page, text):
        for pat in (
            r"https?://doi\.org/(10\.1038/s41598-\S+)",
            r"(10\.1038/s41598-\d+-\d+)",
            r"https?://doi\.org/(10\.\S+)",
            r"doi\.org/(10\.\S+)",
            r"doi:\s*(10\.\S+)",
            r"(10\.1038/\S+)",
            r"(10\.3390/\S+)",
            r"(10\.1111/\S+)",
            r"(10\.5093/\S+)",
            r"(10\.1371/journal\.\S+)",
        ):
            m = re.search(pat, block, re.I)
            if m:
                return norm_doi(m.group(1))
    return ""


def _looks_like_author_line(line: str) -> bool:
    if re.search(r"@|\.edu|\.ac\.|ORCID|https?://", line, re.I):
        return True
    if re.search(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\d*(?:,\s*[A-Z][a-z]+)", line) and (
        re.search(r"\d", line) or " & " in line or " and " in line.lower()
    ):
        return True
    return False


def extract_title_from_text(text: str) -> str:
    """Recover article title when header parse leaves title blank (e.g. PLOS ONE)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""

    title_parts: list[str] = []
    for ln in lines[:20]:
        if re.search(
            r"^(Received|Accepted|Published|Keywords|Abstract|doi:|http|Copyright|OPEN ACCESS)\b",
            ln,
            re.I,
        ):
            break
        if _looks_like_author_line(ln):
            break
        if re.search(
            r"^(Background|Introduction|Objective|Methods|Results|Conclusion|ABSTRACT)\b",
            ln,
            re.I,
        ):
            break
        if len(ln) > 140 or (ln.endswith(".") and len(ln) > 60):
            break
        title_parts.append(ln)
        if len(title_parts) >= 8:
            break

    return re.sub(r"\s+", " ", " ".join(title_parts)).strip()


def extract_year_from_text(text: str) -> str:
    head = text[:4000]
    for pat in (
        r"Published[:\s]+(?:\w+\s+\d{1,2},?\s+)?(\d{4})",
        r"Received[:\s]+(?:\w+\s+\d{1,2},?\s+)?(\d{4})",
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        r"\((\d{4})\)",
    ):
        m = re.search(pat, head, re.I)
        if m:
            y = int(m.group(1))
            if 1990 <= y <= 2030:
                return str(y)
    return ""


def find_master_by_id(
    master_rows: list[dict[str, str]], article_id: str
) -> dict[str, str] | None:
    aid = article_id.strip().upper()
    for row in master_rows:
        if (row.get("article_id") or "").strip().upper() == aid:
            return row
    return None


def append_master_note(row: dict[str, str], note: str) -> None:
    existing = (row.get("notes") or "").strip()
    if note in existing:
        return
    row["notes"] = f"{existing}; {note}" if existing else note


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@contextmanager
def master_file_lock():
    """Exclusive lock for articles_master.csv and INGEST_LOG read-merge-write."""
    MASTER_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MASTER_LOCK_PATH, "w", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def verify_master_pdf_persisted(article_id: str, rel_pdf_path: str) -> None:
    row = find_master_by_id(load_csv(MASTER_PATH), article_id)
    if not row:
        raise RuntimeError(f"master verify failed: {article_id} not found after write")
    if row.get("has_pdf", "").lower() != "true":
        raise RuntimeError(f"master verify failed: {article_id} has_pdf not True after write")
    if (row.get("pdf_path") or "").strip() != rel_pdf_path:
        raise RuntimeError(
            f"master verify failed: {article_id} pdf_path "
            f"expected {rel_pdf_path!r}, got {(row.get('pdf_path') or '').strip()!r}"
        )


def commit_master_pdf_ingest(
    article_id: str,
    rel_pdf_path: str,
    notes_to_append: list[str] | None = None,
) -> tuple[list[dict[str, str]], list[str], int]:
    """Reload master under lock, apply PDF fields, write, and verify persistence."""
    with master_file_lock():
        master_rows = load_csv(MASTER_PATH)
        if not master_rows:
            raise RuntimeError(f"Master empty during commit: {MASTER_PATH}")
        fieldnames = list(master_rows[0].keys())
        primary = find_master_by_id(master_rows, article_id)
        if not primary:
            raise RuntimeError(f"master commit failed: {article_id} not found")
        for note in notes_to_append or []:
            append_master_note(primary, note)
        update_master(master_rows, article_id, rel_pdf_path, dry_run=False)
        aliases = sync_doi_aliases(master_rows, primary, rel_pdf_path, dry_run=False)
        write_master(master_rows, fieldnames)
        verify_master_pdf_persisted(article_id, rel_pdf_path)
        return master_rows, fieldnames, aliases


def locked_upsert_ingest_log(row: dict[str, str]) -> None:
    with master_file_lock():
        upsert_ingest_log(row)


def load_ingest_log() -> list[dict[str, str]]:
    return load_csv(INGEST_LOG)


def logged_filenames(log_rows: list[dict[str, str]]) -> set[str]:
    return {r.get("filename", "") for r in log_rows if r.get("filename")}


def append_ingest_log(row: dict[str, str]) -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    write_header = not INGEST_LOG.exists()
    with open(INGEST_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INGEST_COLUMNS, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerow(row)


def upsert_ingest_log(row: dict[str, str]) -> None:
    """Replace an existing INGEST_LOG row by filename, or append."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_ingest_log()
    filename = row.get("filename", "")
    replaced = False
    for i, existing in enumerate(rows):
        if existing.get("filename") == filename:
            rows[i] = {**existing, **row}
            replaced = True
            break
    if not replaced:
        rows.append(row)
    with open(INGEST_LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INGEST_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def parse_pdf(pdf_path: Path) -> dict:
    text, meta = extract_text(pdf_path)
    rec = parse_fulltext_article(text, meta)
    rec["source_pdf"] = pdf_path.name
    if not rec.get("doi"):
        rec["doi"] = extract_doi_from_text(text)
    if not rec.get("title"):
        rec["title"] = extract_title_from_text(text)
        if rec["title"]:
            rec["notes"] = (rec.get("notes") or "") + "; title from PDF text fallback"
    if not rec.get("year"):
        rec["year"] = extract_year_from_text(text)
    rec["_pdf_doi"] = norm_doi(rec.get("doi", ""))
    rec = match_ebsco_metadata(rec, EBSCO_DIR / "ebsco_export_50_records.csv")
    rec["_full_text"] = text
    return rec


def format_doi_ambiguity_note(doi: str, hits: list[dict[str, str]]) -> str:
    ids = ", ".join(
        f"{r.get('article_id', '?')}"
        f"(refid={r.get('legacy_refid') or '—'}, sources={r.get('sources', '')[:40]})"
        for r in hits
    )
    return (
        f"DOI {doi} matches {len(hits)} master rows: {ids}. "
        "Review probable_duplicates_review.csv; use --force-master-id to override."
    )


def match_to_master(
    rec: dict, master_rows: list[dict[str, str]]
) -> tuple[dict[str, str] | None, str, str]:
    """Return (master_row, match_type, ambiguity_note)."""
    doi = norm_doi(rec.get("doi", ""))
    year = str(rec.get("year", "") or "").strip()
    title = rec.get("title", "")

    if doi:
        hits = [r for r in master_rows if norm_doi(r.get("doi", "")) == doi]
        if len(hits) == 1:
            return hits[0], "doi", ""
        if len(hits) > 1:
            note = format_doi_ambiguity_note(doi, hits)
            ebsco_hits = [r for r in hits if "ebsco_2026" in (r.get("sources") or "")]
            if len(ebsco_hits) == 1:
                return ebsco_hits[0], "doi_ebsco_pool", note
            if ebsco_hits:
                return ebsco_hits[0], "doi_ambiguous_ebsco", note
            legacy_hits = [r for r in hits if (r.get("legacy_refid") or "").strip()]
            if legacy_hits:
                return legacy_hits[0], "doi_legacy", note
            return hits[0], "doi_ambiguous", note

    best: dict[str, str] | None = None
    best_score = 0.0
    for row in master_rows:
        row_year = str(row.get("year", "") or "").strip()
        if year and row_year and year != row_year:
            continue
        score = fuzzy_ratio(title, row.get("title", ""))
        if score > best_score:
            best_score = score
            best = row
    if best and best_score >= TITLE_FUZZY_THRESHOLD:
        return best, f"title_fuzzy_{best_score:.3f}", ""
    return None, "", ""


def sync_doi_aliases(
    master_rows: list[dict[str, str]],
    primary: dict[str, str],
    rel_pdf_path: str,
    dry_run: bool,
) -> int:
    """Copy pdf_path to other master rows sharing the same DOI."""
    doi = norm_doi(primary.get("doi", ""))
    if not doi:
        return 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    for row in master_rows:
        if row.get("article_id") == primary.get("article_id"):
            continue
        if norm_doi(row.get("doi", "")) != doi:
            continue
        if (row.get("pdf_path") or "").strip() == rel_pdf_path:
            continue
        if not dry_run:
            row["has_pdf"] = "True"
            row["pdf_path"] = rel_pdf_path
            row["pdf_status"] = "available"
            row["updated_at"] = today
        count += 1
    return count


def dest_basename(master_row: dict[str, str], rec: dict) -> str:
    master_id = master_row.get("article_id", "M0000")
    authors_raw = rec.get("authors", "") or master_row.get("authors", "")
    if "creativecommons" in authors_raw.lower() or "open access article" in authors_raw.lower():
        authors_raw = master_row.get("authors", "")
    author = slug(first_author_last(authors_raw), max_len=24)
    year = rec.get("year") or master_row.get("year") or "0000"
    title_raw = rec.get("title") or master_row.get("title", "article")
    if title_raw.strip().startswith("ISSN") or "creativecommons" in title_raw.lower()[:200]:
        title_raw = master_row.get("title", title_raw)
    title_slug = slug(title_raw)
    return f"EBSCO_{master_id}_{author}_{year}_{title_slug}"


def save_artifacts(pdf_path: Path, dest_pdf: Path, text: str, copy_import: bool = True) -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    if copy_import:
        IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
        dest_import = IMPORTS_DIR / pdf_path.name
        if pdf_path.resolve() != dest_import.resolve():
            shutil.copy2(pdf_path, dest_import)
    shutil.copy2(pdf_path, dest_pdf)
    text_dest = TEXT_DIR / f"{dest_pdf.stem}.txt"
    text_dest.write_text(text, encoding="utf-8")


def update_master(
    master_rows: list[dict[str, str]],
    article_id: str,
    rel_pdf_path: str,
    dry_run: bool,
) -> bool:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = False
    for row in master_rows:
        if row.get("article_id") != article_id:
            continue
        if (row.get("pdf_path") or "").strip() == rel_pdf_path and (
            row.get("has_pdf", "").lower() == "true"
        ):
            return False
        if not dry_run:
            row["has_pdf"] = "True"
            row["pdf_path"] = rel_pdf_path
            row["pdf_status"] = "available"
            row["updated_at"] = today
        updated = True
        break
    return updated


def write_master(master_rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with open(MASTER_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(master_rows)


def process_pdf(
    pdf_path: Path,
    master_rows: list[dict[str, str]],
    log_rows: list[dict[str, str]],
    dry_run: bool = False,
    force_master_id: str | None = None,
) -> dict:
    filename = pdf_path.name
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    prev_log = next((r for r in log_rows if r.get("filename") == filename), None)
    if prev_log and prev_log.get("status") in ("matched", "duplicate") and not force_master_id:
        return {"filename": filename, "status": "skipped", "notes": "already in INGEST_LOG"}

    rec = parse_pdf(pdf_path)

    if force_master_id:
        master_row = find_master_by_id(master_rows, force_master_id)
        match_type = "force_master_id" if master_row else ""
        ambiguity_note = ""
        if not master_row:
            return {
                "filename": filename,
                "processed_at": now,
                "title": rec.get("title", ""),
                "status": "unmatched",
                "notes": f"force_master_id {force_master_id} not found in master",
            }
    else:
        master_row, match_type, ambiguity_note = match_to_master(rec, master_rows)

    result: dict = {
        "filename": filename,
        "processed_at": now,
        "title": rec.get("title", ""),
        "master_id": "",
        "refid": "",
        "match_type": match_type,
        "pdf_path": "",
        "status": "unmatched",
        "notes": (rec.get("notes") or "").strip().lstrip(";").strip(),
    }

    if not master_row:
        result["notes"] = (result.get("notes") or "") + "; no master match"
        if not dry_run:
            locked_upsert_ingest_log(result)
        return result

    article_id = master_row.get("article_id", "")
    refid = master_row.get("legacy_refid", "") or ""
    result["master_id"] = article_id
    result["refid"] = refid

    master_notes: list[str] = []
    if ambiguity_note:
        result["notes"] = (result.get("notes") or "") + f"; {ambiguity_note}"
        master_notes.append(ambiguity_note)
        print(f"  WARNING: {ambiguity_note}", file=sys.stderr)

    pdf_doi = norm_doi(rec.get("_pdf_doi") or rec.get("doi", ""))
    master_doi = norm_doi(master_row.get("doi", ""))
    if pdf_doi and master_doi and pdf_doi != master_doi:
        doi_note = (
            f"PDF DOI {pdf_doi} differs from master DOI {master_doi} "
            "(PLOS ONE vs Scientific Reports — may be wrong version or preprint)"
        )
        result["notes"] = (result.get("notes") or "") + f"; {doi_note}"
        master_notes.append(doi_note)

    existing_path = (master_row.get("pdf_path") or "").strip()
    if existing_path and (master_row.get("has_pdf", "").lower() == "true") and not force_master_id:
        result["status"] = "duplicate"
        result["pdf_path"] = existing_path
        result["match_type"] = match_type
        result["notes"] = (result.get("notes") or "") + f"; master already has pdf: {existing_path}"
        if not dry_run:
            locked_upsert_ingest_log(result)
        return result

    base = dest_basename(master_row, rec)
    dest_pdf = PDF_DIR / f"{base}.pdf"
    rel_path = f"review/EBSCO/pdfs/{dest_pdf.name}"

    if dry_run:
        result["status"] = "matched"
        result["pdf_path"] = rel_path
        return result

    save_artifacts(pdf_path, dest_pdf, rec.get("_full_text", ""))
    master_rows, _, aliases = commit_master_pdf_ingest(article_id, rel_path, master_notes)
    if aliases:
        result["notes"] = (result.get("notes") or "") + f"; synced {aliases} doi alias row(s)"
    result["status"] = "matched"
    result["pdf_path"] = rel_path
    locked_upsert_ingest_log(result)
    return result


def discover_pdfs(scan_downloads: bool, pdf_path: Path | None) -> list[Path]:
    paths: list[Path] = []
    if pdf_path:
        paths.append(pdf_path.expanduser().resolve())
    if scan_downloads:
        paths.extend(sorted(DOWNLOADS_DIR.glob("EBSCO-FullText*.pdf")))
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen and rp.exists():
            seen.add(rp)
            unique.append(rp)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest EBSCO full-text PDFs into CMV review corpus")
    parser.add_argument("--scan-downloads", action="store_true", help="Process EBSCO-FullText*.pdf in ~/Downloads")
    parser.add_argument("--pdf", type=Path, help="Process a single PDF path")
    parser.add_argument("--dry-run", action="store_true", help="Match only; do not copy or update master")
    parser.add_argument(
        "--force-master-id",
        metavar="M####",
        help="Force link to this articles_master article_id (reprocesses logged PDFs)",
    )
    args = parser.parse_args()

    if not args.scan_downloads and not args.pdf:
        parser.print_help()
        return 1

    pdf_paths = discover_pdfs(args.scan_downloads, args.pdf)
    if not pdf_paths:
        print("No PDFs found.")
        return 0

    master_rows = load_csv(MASTER_PATH)
    if not master_rows:
        print(f"Master not found or empty: {MASTER_PATH}", file=sys.stderr)
        return 1
    log_rows = load_ingest_log()

    results: list[dict] = []
    for pdf_path in pdf_paths:
        print(f"\n--- {pdf_path.name} ---")
        result = process_pdf(
            pdf_path,
            master_rows,
            log_rows,
            dry_run=args.dry_run,
            force_master_id=args.force_master_id,
        )
        results.append(result)
        if result.get("status") != "skipped":
            log_rows.append(result)
            if result.get("status") == "matched" and result.get("master_id"):
                mid = result["master_id"]
                for row in master_rows:
                    if row.get("article_id") == mid:
                        row["has_pdf"] = "True"
                        row["pdf_path"] = result.get("pdf_path", "")
                        row["pdf_status"] = "available"
                        break
        print(
            f"  {result.get('status')}: {result.get('title', '')[:70]}"
            f" -> {result.get('master_id') or '—'} ({result.get('match_type') or '—'})"
        )

    matched = [r for r in results if r.get("status") == "matched"]
    unmatched = [r for r in results if r.get("status") == "unmatched"]
    dupes = [r for r in results if r.get("status") == "duplicate"]
    skipped = [r for r in results if r.get("status") == "skipped"]

    print(f"\n=== Summary: {len(matched)} matched, {len(unmatched)} unmatched, "
          f"{len(dupes)} duplicate, {len(skipped)} skipped ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
