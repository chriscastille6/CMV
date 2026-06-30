#!/usr/bin/env python3
"""
Parse EBSCO metadata export PDF into a CSV for matching with systematic extraction.
Output: ebsco_export_50_records.csv

Usage:
  python parse_ebsco_export_pdf.py [path_to_ebsco_export.pdf]
  Default path: ~/Downloads/EBSCO-Metadata-02_23_2026.pdf

Requires: pypdf  (pip install pypdf)
"""

import csv
import re
import sys
from pathlib import Path


def extract_text_from_pdf(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Install pypdf: pip install pypdf")
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_ebsco_export(text: str) -> list[dict]:
    """Split full text into record blocks and parse key fields."""
    records = []
    # Records start with "N. Title" (number, dot, space, title). Split by this pattern.
    # Pattern: newline followed by digits, dot, space, then capture rest of line(s) until LongDbName
    block_pattern = re.compile(
        r"\n(\d+)\.\s+(.+?)(?=\n(?:LongDbName|$))",
        re.DOTALL,
    )
    blocks = list(block_pattern.finditer(text))
    if not blocks:
        # Fallback: split by "LongDbName:" and infer record number from previous line
        parts = re.split(r"\nLongDbName:", text)
        for i, part in enumerate(parts[1:], start=1):  # skip TOC
            block_text = "LongDbName:" + part
            rec = _parse_one_block(block_text, record_num=i, title="")
            if rec.get("year") or rec.get("journal"):
                records.append(rec)
        return records
    for m in blocks:
        num, title_part = m.group(1), m.group(2)
        # Title may be multiline; take up to next field (LongDbName)
        title = re.sub(r"\s+", " ", title_part).strip()
        # Get the full block including LongDbName... until next "N. " or end
        start = m.start()
        next_m = block_pattern.search(text, m.end())
        end = next_m.start() if next_m else len(text)
        block_text = text[start:end]
        rec = _parse_one_block(block_text, record_num=int(num), title=title)
        records.append(rec)
    return records


def _parse_one_block(block: str, record_num: int, title: str) -> dict:
    def field(pattern: str, group: int = 1) -> str:
        m = re.search(pattern, block)
        return (m.group(group).strip() if m else "") or ""

    # PublicationDate: 20170901 -> year
    pub = field(r"PublicationDate:\s*(\d{8})")
    year = pub[:4] if len(pub) == 8 else ""

    # Contributors: often "Last, First; Last, First"
    contributors = field(r"Contributors:\s*([^\n]+?)(?=\n[A-Za-z]|\n\n|$)")
    contributors = re.sub(r"\s+", " ", contributors).strip()

    # Source: journal name
    source = field(r"Source:\s*([^\n]+)")

    # DOI: may appear as "DOI: 10.xxx" or "DOI: externalurl10.xxx" or in DOIDS
    doi = field(r"DOI:\s*(?:externalurl)?(10\.\S+?)(?:\s|https?://|$)")
    if not doi and "10." in block:
        doi = field(r"(10\.\d{4,}/[^\s\]\)\"']+)")

    # AN
    an = field(r"AN:\s*(\d+)")

    # Volume, Issue
    volume = field(r"Volume:\s*(\d+)")
    issue = field(r"Issue:\s*(\d+)")

    # CoverDate: Sep2017
    cover_date = field(r"CoverDate:\s*([^\n]+)")

    # plink
    plink = field(r"plink:\s*(https?://[^\s]+)")

    # If title not passed, try to get from "N. Title" in block
    if not title:
        t = re.search(r"^\d+\.\s+(.+?)(?=\nLongDbName)", block, re.DOTALL)
        if t:
            title = re.sub(r"\s+", " ", t.group(1)).strip()

    return {
        "record_num": record_num,
        "title": title,
        "authors": contributors,
        "year": year,
        "journal": source,
        "volume": volume,
        "issue": issue,
        "doi": doi,
        "an": an,
        "cover_date": cover_date,
        "plink": plink,
    }


def main():
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdf_path = Path.home() / "Downloads" / "EBSCO-Metadata-02_23_2026.pdf"
    if not pdf_path.exists():
        print(f"Not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    out_path = Path(__file__).resolve().parent / "ebsco_export_50_records.csv"
    print(f"Reading {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(text)} chars.")
    records = parse_ebsco_export(text)
    print(f"Parsed {len(records)} records.")
    fieldnames = [
        "record_num", "title", "authors", "year", "journal",
        "volume", "issue", "doi", "an", "cover_date", "plink",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    print(f"Wrote {out_path}")


def _parse_fallback(text: str) -> list[dict]:
    """Fallback: split by LongDbName: and parse each block."""
    records = []
    parts = re.split(r"\nLongDbName:", text)
    for i, part in enumerate(parts):
        if "PublicationDate:" not in part:
            continue
        block_text = "LongDbName:" + part
        # Try to get record number from preceding "N. Title" (in previous part)
        prev = parts[i - 1] if i > 0 else ""
        num_m = re.search(r"(\d+)\.\s+([^\n]+?)(?:\s*\.\s*)?\s*$", prev)
        num = int(num_m.group(1)) if num_m else i
        title = (num_m.group(2).strip() if num_m else "").strip(".")
        rec = _parse_one_block(block_text, record_num=num, title=title)
        if rec.get("year") or rec.get("journal"):
            records.append(rec)
    records.sort(key=lambda r: (r.get("record_num", 0), r.get("year", "")))
    return records


if __name__ == "__main__":
    main()
