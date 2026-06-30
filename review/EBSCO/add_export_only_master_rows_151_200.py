#!/usr/bin/env python3
"""Add EBSCO search-order export rows (positions 151–200, off-pool) to articles_master.csv.

Thirty-two rows appear in batch 4 (EBSCO-Metadata-06_26_2026-4.csv) but had no master row.
Applies Level 1 screening decisions from metadata/domain rules and links PDFs when on disk.

Usage:
  python3 review/EBSCO/add_export_only_master_rows_151_200.py
  python3 review/EBSCO/add_export_only_master_rows_151_200.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_DIR = ROOT / "review" / "master"
MASTER_PATH = MASTER_DIR / "articles_master.csv"
PDF_DIR = EBSCO_DIR / "pdfs"

sys.path.insert(0, str(MASTER_DIR))
sys.path.insert(0, str(EBSCO_DIR))

from ebsco_search_order import load_search_order_entries, norm_doi, search_order_row_to_patch  # noqa: E402
from examination import enrich_master_records  # noqa: E402
from merge_sources import MASTER_COLUMNS  # noqa: E402
from publisher_outlet import infer_publisher_outlet  # noqa: E402
from screen_level1_batch import load_csv, master_file_lock, write_master  # noqa: E402

TODAY = date.today().isoformat()
POSITION_RANGE = range(151, 201)

# Positions with no master row as of 2026-06-26 (batch 4 canonical export).
EXPORT_ONLY_POSITIONS = (
    151, 152, 153, 154, 155, 160, 162, 163, 165, 167, 168, 169, 170, 171, 172, 173, 174,
    176, 178, 182, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 199,
)

L1_BY_POSITION: dict[int, dict[str, str]] = {
    151: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "User decision 2026-06-26: exclude; Q1.1 domain out of scope — "
            "public health (herpes zoster vaccination intention, Chongqing)."
        ),
    },
    152: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "higher-education teaching effectiveness (young lecturers, private universities)."
        ),
    },
    153: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; employee narcissism → creative self-efficacy → "
            "creativity; organizational behavior (Frontiers in Psychology)."
        ),
    },
    154: {
        "screening_status": "excluded_pls",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude_pls; PLS-SEM substantive focus "
            "(CSR, compliance programs, reputational risk); routine CMV checks only."
        ),
    },
    155: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "LLM impact on academic success (higher-education student sample)."
        ),
    },
    160: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; air-traffic-controller job satisfaction "
            "(occupational/work context, mixed-method SEM)."
        ),
    },
    162: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; resilient workforce during organisational change "
            "(IHRM, employee resilience)."
        ),
    },
    163: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; stretch-goal double-edged-sword effect "
            "(Asia Pacific Journal of Management)."
        ),
    },
    165: {
        "screening_status": "excluded_pls",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude_pls; PLS-SEM substantive focus "
            "(consumer trust/decision-making, marketing communications); routine CMV only."
        ),
    },
    167: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; moral licensing of work engagement "
            "(business ethics / OB)."
        ),
    },
    168: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; supplier orientation and SME performance "
            "(management/accounting)."
        ),
    },
    169: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; lean startup strategy and sustainable "
            "entrepreneurial performance."
        ),
    },
    170: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; configurational analysis of team effectiveness "
            "(Human Performance)."
        ),
    },
    171: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "clinical/psychiatric adolescent sample (BMC Psychiatry)."
        ),
    },
    172: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; leader humility → employee proactivity "
            "(affective mediation, OB)."
        ),
    },
    173: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "clinical depressive profiles among overweight/obese adults."
        ),
    },
    174: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "K-12 kindergarten teachers (compassion fatigue; not organizational management)."
        ),
    },
    176: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; e-skill self-efficacy and remote-work performance."
        ),
    },
    178: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; political climate and workplace cyberbullying "
            "perpetration (OB)."
        ),
    },
    182: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; role stress → work engagement dual-path model."
        ),
    },
    186: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; psychological contract breach and LMX "
            "(employee outcomes)."
        ),
    },
    187: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; borderline OB/nursing management "
            "(nurse presenteeism, head-nurse cognitive preferences; Journal of Nursing Management)."
        ),
    },
    188: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; team personality composition and innovation "
            "implementation (Applied Psychology)."
        ),
    },
    189: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; workplace mistreatment (insider vs outsider) "
            "among nursing staff (Journal of Advanced Nursing)."
        ),
    },
    190: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "residents' waste-separation behavior (consumer/environmental, not OB)."
        ),
    },
    191: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; abusive supervision serial/moderated mediation."
        ),
    },
    192: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; perceived overqualification and knowledge-sharing "
            "intention (IHRM)."
        ),
    },
    193: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; leader empowering and upper-echelons "
            "decision-making (Public Administration)."
        ),
    },
    194: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; mindfulness reducing workplace unethical behavior "
            "(Journal of Business Ethics)."
        ),
    },
    195: {
        "screening_status": "included",
        "screening_level1_include": "True",
        "screening_notes": (
            "Auto L1 2026-06-26: include; HPWS and employee performance "
            "(HRD International)."
        ),
    },
    196: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "clinical bariatric-surgery patient sample (Frontiers in Psychiatry)."
        ),
    },
    199: {
        "screening_status": "level1_fail",
        "screening_level1_include": "False",
        "screening_notes": (
            "Auto L1 2026-06-26: exclude; Q1.1 domain out of scope — "
            "marketing analytics / item-level CMV correction (not management OB)."
        ),
    },
}


def next_master_id(rows: list[dict[str, str]]) -> str:
    max_num = 0
    for row in rows:
        m = re.match(r"M(\d+)", row.get("article_id", ""))
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"M{max_num + 1:04d}"


def empty_record() -> dict[str, str]:
    rec = {col: "" for col in MASTER_COLUMNS}
    rec["created_at"] = TODAY
    rec["updated_at"] = TODAY
    rec["screening_status"] = "pending"
    rec["extraction_status"] = "none"
    return rec


def find_pdf_for_row(article_id: str, doi: str) -> str:
    """Return relative pdf_path if a matching PDF exists under review/EBSCO/pdfs/."""
    if article_id:
        matches = list(PDF_DIR.glob(f"EBSCO_{article_id}_*.pdf"))
        if matches:
            return str(matches[0].relative_to(ROOT))
    if doi:
        doi_tail = doi.split("/")[-1].replace(".", "")
        for pdf in PDF_DIR.rglob("*.pdf"):
            if doi_tail and doi_tail in pdf.name.replace(".", "").replace("-", ""):
                return str(pdf.relative_to(ROOT))
            if doi.replace("/", "-") in pdf.name:
                return str(pdf.relative_to(ROOT))
    return ""


def build_row(entry: dict[str, str], article_id: str) -> dict[str, str]:
    pos = int(entry["ebsco_search_position"])
    patch = search_order_row_to_patch(entry)
    outlet, _ = infer_publisher_outlet(patch.get("doi", ""), patch.get("journal", ""))

    rec = empty_record()
    rec.update(patch)
    rec["article_id"] = article_id
    rec["publisher_outlet"] = outlet
    rec["sources"] = "ebsco_2026_search_order"
    rec["source_import_file"] = entry.get("import_file", "")
    rec["corpus_tier"] = "ebsco_screened"
    rec["notes"] = (
        f"ebsco_search_position={pos};ebsco_record_range={entry.get('record_range', '')};"
        "export_only_added=2026-06-26"
    )

    pdf_rel = find_pdf_for_row(article_id, entry.get("doi", ""))
    if pdf_rel:
        rec["pdf_path"] = pdf_rel
        rec["has_pdf"] = "True"
        rec["pdf_status"] = "available"
    else:
        rec["has_pdf"] = "False"
        rec["pdf_status"] = "missing"

    l1 = L1_BY_POSITION[pos]
    rec["screening_status"] = l1["screening_status"]
    rec["screening_level1_include"] = l1["screening_level1_include"]
    rec["screening_notes"] = l1["screening_notes"]
    rec["examination_status"] = "read_snippet_only"
    rec["updated_at"] = TODAY
    return rec


def add_export_only_rows(*, dry_run: bool = False) -> list[tuple[str, int, str]]:
    master = load_csv(MASTER_PATH)
    by_pos = {int(e["ebsco_search_position"]): e for e in load_search_order_entries()}
    added: list[tuple[str, int, str]] = []

    for pos in EXPORT_ONLY_POSITIONS:
        if pos not in POSITION_RANGE:
            raise SystemExit(f"Position {pos} outside 151–200 range")
        entry = by_pos.get(pos)
        if not entry:
            raise SystemExit(f"Missing search-order entry for position {pos}")
        if pos not in L1_BY_POSITION:
            raise SystemExit(f"Missing L1 decision for position {pos}")

        doi = entry.get("doi", "")
        for row in master:
            if doi and norm_doi(row.get("doi", "")) == norm_doi(doi):
                raise SystemExit(
                    f"Position {pos} DOI {doi} already in master as {row.get('article_id')}"
                )
            if entry.get("ebsco_an") and row.get("ebsco_an") == entry["ebsco_an"]:
                raise SystemExit(
                    f"Position {pos} AN {entry['ebsco_an']} already in master as {row.get('article_id')}"
                )

        article_id = next_master_id(master)
        rec = build_row(entry, article_id)
        master.append(rec)
        added.append((article_id, pos, rec["screening_status"]))
        title_preview = rec["title"][:55] + "…" if len(rec["title"]) > 55 else rec["title"]
        print(f"  + {article_id}  EBSCO #{pos}  {rec['screening_status']}  {title_preview}")

    if dry_run:
        print(f"[dry-run] Would add {len(added)} row(s); master would be {len(master)} rows")
        return added

    master = enrich_master_records(master)
    master.sort(key=lambda r: r.get("article_id", ""))
    with master_file_lock():
        write_master(master, MASTER_COLUMNS)
    print(f"Wrote {MASTER_PATH} ({len(master)} rows)")
    return added


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add export-only EBSCO rows (151–200) to articles_master.csv"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    added = add_export_only_rows(dry_run=args.dry_run)
    if added:
        from collections import Counter

        counts = Counter(status for _, _, status in added)
        print(f"L1 breakdown: {dict(counts)}")
        ids = ", ".join(f"{mid} (#{pos})" for mid, pos, _ in added)
        print(f"Added: {ids}")


if __name__ == "__main__":
    main()
