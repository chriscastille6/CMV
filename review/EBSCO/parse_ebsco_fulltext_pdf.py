#!/usr/bin/env python3
"""
Parse EBSCO full-text export PDF(s) into per-article artifacts.

Unlike metadata exports (parse_ebsco_export_pdf.py), full-text exports are usually
one published article per PDF — not a TOC + metadata bundle.

Outputs (per input PDF):
  - ebsco_fulltext_export_<date>.csv  (append or create)
  - ebsco_fulltext_<date>/<stem>/     (optional split dir; single file = copy only)
  - review/EBSCO/text/EBSCO_<record>_<author>_<year>_*.txt
  - review/EBSCO/pdfs/EBSCO_<record>_<author>_<year>_*.pdf  (when --save-pdf)

Usage:
  python parse_ebsco_fulltext_pdf.py /path/to/EBSCO-FullText-06_24_2026.pdf
  python parse_ebsco_fulltext_pdf.py --imports-dir review/EBSCO/imports/*.pdf

Requires: pymupdf (pip install pymupdf)
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
IMPORTS_DIR = ROOT / "imports"
TEXT_DIR = ROOT / "text"
PDF_DIR = ROOT / "pdfs"


def extract_text(pdf_path: Path) -> str:
    try:
        import fitz
    except ImportError:
        sys.exit("Install pymupdf: pip install pymupdf")
    doc = fitz.open(str(pdf_path))
    text = "\n".join(page.get_text() or "" for page in doc)
    meta = doc.metadata or {}
    doc.close()
    return text, meta


def parse_fulltext_article(text: str, pdf_meta: dict | None = None) -> dict:
    """Heuristic bibliographic parse from first page of a journal article PDF."""
    pdf_meta = pdf_meta or {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    head = "\n".join(lines[:40])

    # Journal (Year), vol, pages — e.g. JOOP: Journal ... (2020), 93, 578–604
    # JWOP/COP Madrid: Journal ... (2019) 35(1) 9-15
    journal_year = ""
    year = ""
    volume = ""
    issue = ""
    page_range = ""
    journal = ""
    m = re.search(
        r"^(.+?)\s*\((\d{4})\)\s*,\s*(\d+)\s*,\s*(\d+[–\-]\d+)",
        head,
        re.MULTILINE,
    )
    if m:
        journal_year = m.group(0)
        year = m.group(2)
        volume = m.group(3)
        page_range = m.group(4)
        journal = re.sub(r"\s+", " ", m.group(1)).strip()
    else:
        m2 = re.search(
            r"^(.+?)\s*\((\d{4})\)\s+(\d+)\((\d+)\)\s+(\d+[–\-]\d+)",
            head,
            re.MULTILINE,
        )
        if m2:
            journal_year = m2.group(0)
            year = m2.group(2)
            volume = m2.group(3)
            issue = m2.group(4)
            page_range = m2.group(5)
            journal = re.sub(r"\s+", " ", m2.group(1)).strip()

    # Title / authors from EBSCO "Cite this article as:" block when present
    title = (pdf_meta.get("title") or "").strip()
    authors = ""
    cite_m = re.search(
        r"Cite this article as:\s*(.+?)\s*\((\d{4})\)\.\s*(.+?)\.\s*(.+?),\s*(\d+)",
        head,
        re.I | re.S,
    )
    if cite_m:
        if not authors:
            authors = cite_m.group(1).strip().rstrip(".")
        if not year:
            year = cite_m.group(2)
        if not title:
            title = re.sub(r"\s+", " ", cite_m.group(3)).strip()
        if not journal:
            journal = re.sub(r"\s+", " ", cite_m.group(4)).strip()
        if not volume:
            volume = cite_m.group(5)

    # Nature / Scientific Reports: title on first lines, journal footer later
    if not title and lines:
        title_parts: list[str] = []
        for ln in lines[:10]:
            if re.search(
                r"^(OPEN|Keywords|Abbreviations|Abstract|Received)\b|"
                r"Department of|University|School of|Faculty of",
                ln,
                re.I,
            ):
                break
            if re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+", ln) and re.search(r"\d", ln) and (
                "&" in ln or re.search(r"\d+\*?$", ln)
            ):
                break
            if re.match(r"^[A-Za-z]", ln) and len(ln) > 3:
                title_parts.append(ln)
            elif title_parts:
                break
        if title_parts and len(" ".join(title_parts)) >= 20:
            title = re.sub(r"\s+", " ", " ".join(title_parts)).strip()

    sr_m = re.search(
        r"Scientific Reports\s*\|\s*\((\d{4})\)\s+(\d+):(\d+)",
        text[:12000],
        re.I,
    )
    if sr_m:
        year = year or sr_m.group(1)
        volume = volume or sr_m.group(2)
        issue = issue or sr_m.group(3)
        journal = journal or "Scientific Reports"

    # Title: often the longest title-case block after journal header
    if not title:
        for i, ln in enumerate(lines[:15]):
            if re.search(r"\(\d{4}\)", ln):
                parts = []
                for j in range(i + 1, min(i + 6, len(lines))):
                    if re.match(r"^[\w\s,'\-–—:;()?]+$", lines[j]) and not re.search(
                        r"\d{1,2}\*", lines[j]
                    ):
                        parts.append(lines[j])
                    else:
                        break
                if parts:
                    title = re.sub(r"\s+", " ", " ".join(parts)).strip()
                break

    # Authors: superscript line (JOOP) or comma-separated names (JWOP)
    title_norm = re.sub(r"\s+", " ", title).strip().lower()
    if not authors:
        for i, ln in enumerate(lines[:25]):
            ln_norm = re.sub(r"\s+", " ", ln).strip().lower()
            if title_norm and (ln_norm == title_norm or title_norm.startswith(ln_norm[:30])):
                continue
            if re.search(r"Department|University|School|Faculty|Eidgen|Northern Illinois|San Diego", ln):
                if authors:
                    break
                continue
            if re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+", ln) and re.search(r"\d", ln):
                cleaned = re.sub(r"\d+\*?", "", ln)
                cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,")
                if cleaned and cleaned.lower() not in title_norm:
                    authors = cleaned
                    break
            if re.search(r"[A-Z][a-z]+,\s+[A-Z]", ln) and " and " in ln:
                authors = ln.strip()
                break

    # DOI: prefer article DOI on first page (Nature, JOOP, JWOP, generic)
    doi = ""
    first_page = text[:12000]
    received_block = text[text.find("Received"): text.find("Received") + 500] if "Received" in text else ""
    for block in (first_page, received_block, head):
        for pat in [
            r"https?://doi\.org/(10\.1038/s41598-\S+)",
            r"(10\.1038/s41598-\d+-\d+)",
            r"(10\.1111/joop\.\d+)",
            r"(10\.5093/jwop\d+a\d+)",
            r"https?://doi\.org/(10\.\S+)",
            r"doi:\s*(10\.\S+)",
        ]:
            dm = re.search(pat, block, re.I)
            if dm:
                doi = dm.group(1).rstrip(".,;)")
                break
        if doi:
            break

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "volume": volume,
        "issue": issue,
        "doi": doi,
        "page_range": page_range,
        "pages": str(text.count("\f") + text.count("\n\n")),  # placeholder
        "source_pdf": "",
        "filename": "",
        "ebsco_record_num": "",
        "notes": "",
    }


def slug(s: str, max_len: int = 48) -> str:
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:max_len].rstrip("_")


def first_author_last(authors: str) -> str:
    if not authors:
        return "Unknown"
    first = authors.split(";")[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    parts = first.split()
    return parts[-1] if parts else "Unknown"


def match_ebsco_metadata(rec: dict, export_csv: Path) -> dict:
    """Crosswalk to ebsco_export_50_records.csv by DOI or title prefix."""
    if not export_csv.exists():
        return rec
    with open(export_csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    doi = rec.get("doi", "")
    title = rec.get("title", "").lower()[:60]
    for row in rows:
        if doi and row.get("doi") == doi:
            rec["ebsco_record_num"] = row.get("record_num", "")
            rec["authors"] = row.get("authors", "") or rec.get("authors", "")
            rec["notes"] = "matched ebsco_export_50_records.csv by DOI"
            return rec
        rt = (row.get("title") or "").lower()[:60]
        if title and rt and (title in rt or rt in title):
            rec["ebsco_record_num"] = row.get("record_num", "")
            rec["doi"] = row.get("doi", "") or rec.get("doi", "")
            if not _authors_look_valid(rec.get("authors", "")):
                rec["authors"] = row.get("authors", "")
            rec["journal"] = rec.get("journal") or row.get("journal", "")
            rec["volume"] = rec.get("volume") or row.get("volume", "")
            rec["issue"] = rec.get("issue") or row.get("issue", "")
            rec["notes"] = "matched ebsco_export_50_records.csv by title"
            return rec
    return rec


def _authors_look_valid(authors: str) -> bool:
    if not authors:
        return False
    if "Journal of" in authors or "Psychology ()" in authors:
        return False
    return bool(re.search(r"[A-Z][a-z]+,\s*[A-Z]", authors) or ";" in authors)


def process_pdf(
    pdf_path: Path,
    out_csv: Path,
    save_pdf: bool = True,
    copy_import: bool = True,
) -> dict:
    text, meta = extract_text(pdf_path)
    rec = parse_fulltext_article(text, meta)
    rec["source_pdf"] = str(pdf_path)
    rec = match_ebsco_metadata(rec, ROOT / "ebsco_export_50_records.csv")

    record = rec.get("ebsco_record_num") or "000"
    author = first_author_last(rec.get("authors", ""))
    year = rec.get("year") or "0000"
    title_slug = slug(rec.get("title", "article"))
    base = f"EBSCO_{record.zfill(3)}_{author}_et_al_{year}_{title_slug}"

    if copy_import:
        IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
        dest_import = IMPORTS_DIR / pdf_path.name
        if pdf_path.resolve() != dest_import.resolve():
            shutil.copy2(pdf_path, dest_import)

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    text_path = TEXT_DIR / f"{base}.txt"
    text_path.write_text(text, encoding="utf-8")
    rec["filename"] = text_path.name

    if save_pdf:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        pdf_dest = PDF_DIR / f"{base}.pdf"
        shutil.copy2(pdf_path, pdf_dest)
        rec["filename"] = pdf_dest.name

    # append CSV
    fieldnames = [
        "record_num",
        "title",
        "authors",
        "year",
        "journal",
        "volume",
        "issue",
        "doi",
        "page_range",
        "filename",
        "source_pdf",
        "ebsco_record_num",
        "notes",
    ]
    next_num = 1
    if out_csv.exists():
        with open(out_csv, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            if rows:
                next_num = max(int(r.get("record_num", 0) or 0) for r in rows) + 1
    row = {
        "record_num": next_num,
        "title": rec["title"],
        "authors": rec["authors"],
        "year": rec["year"],
        "journal": rec["journal"],
        "volume": rec.get("volume", ""),
        "issue": rec.get("issue", ""),
        "doi": rec["doi"],
        "page_range": rec.get("page_range", ""),
        "filename": rec["filename"],
        "source_pdf": pdf_path.name,
        "ebsco_record_num": rec.get("ebsco_record_num", ""),
        "notes": rec.get("notes", ""),
    }
    write_header = not out_csv.exists()
    with open(out_csv, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerow(row)
    return rec


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    date_tag = datetime.now().strftime("%m_%d_%Y")
    out_csv = ROOT / f"ebsco_fulltext_export_{date_tag}.csv"

    paths = [Path(p) for p in sys.argv[1:] if not p.startswith("--")]
    for p in paths:
        if not p.exists():
            print(f"Skip (not found): {p}", file=sys.stderr)
            continue
        rec = process_pdf(p, out_csv)
        print(f"Parsed: {rec.get('title', '')[:60]}...")
        print(f"  DOI: {rec.get('doi')}")
        print(f"  Saved: {rec.get('filename')}")
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
