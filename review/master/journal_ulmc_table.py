#!/usr/bin/env python3
"""
Aggregate ULMC-using studies by journal for the fully coded corpus and broader pools.

ULMC used (primary definition):
  - empirical_ulmc == TRUE, OR
  - statistical_methods_mv contains "ULMC" (case-insensitive)

Default includes PLS-SEM studies (no PLS exclusion). Set exclude_pls_only=True to
drop studies where pls_cbsem_category == "PLS-SEM" and empirical_ulmc is not TRUE.

Outputs:
  - review/ULMC_BY_JOURNAL.csv
  - review/ULMC_BY_JOURNAL.md

Examples:
  python3 review/master/journal_ulmc_table.py
  python3 review/master/progress_counter.py   # also regenerates journal table
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from build_results_tables import (
    EXTRACTION_PATH,
    MASTER_PATH,
    build_results_payload,
    classify_pls_cbsem,
    normalize_tristate,
    pct,
    read_csv,
    study_order_key,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = ROOT / "review" / "ULMC_BY_JOURNAL.csv"
OUTPUT_MD = ROOT / "review" / "ULMC_BY_JOURNAL.md"

ULMC_DEFINITION = (
    "empirical_ulmc=TRUE OR statistical_methods_mv contains 'ULMC' (case-insensitive); "
    "includes PLS-SEM studies by default"
)


def is_ulmc_used(
    study: dict[str, str],
    *,
    exclude_pls_only: bool = False,
) -> bool:
    """Return True when the study meets the ULMC-used definition."""
    empirical = normalize_tristate(study.get("empirical_ulmc"))
    methods = (study.get("statistical_methods_mv") or "").upper()
    via_empirical = empirical == "TRUE"
    via_methods = "ULMC" in methods
    if not (via_empirical or via_methods):
        return False
    if exclude_pls_only:
        cat = study.get("pls_cbsem_category") or classify_pls_cbsem(study)
        if cat == "PLS-SEM" and not via_empirical:
            return False
    return True


def normalize_journal(name: str | None) -> str:
    """Light normalization: trim, collapse whitespace, standardize '&' vs 'and'."""
    if not name:
        return "(unknown journal)"
    s = str(name).strip()
    if not s or s.upper() in ("NA", "N/A", "NAN", "NONE", "NULL", "-"):
        return "(unknown journal)"
    s = re.sub(r"\s+&\s+", " and ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def journal_group_key(name: str | None) -> str:
    return normalize_journal(name).casefold()


def pick_display_journal(names: list[str]) -> str:
    """Prefer the most frequent spelling; tie-break by shorter then alpha."""
    if not names:
        return "(unknown journal)"
    counts = Counter(names)
    best = sorted(counts.items(), key=lambda x: (-x[1], len(x[0]), x[0].lower()))[0][0]
    return best


def aggregate_by_journal(
    studies: list[dict[str, str]],
    *,
    exclude_pls_only: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    """Return (rows sorted by n desc, total_ulmc_n)."""
    ulmc_studies = [s for s in studies if is_ulmc_used(s, exclude_pls_only=exclude_pls_only)]
    total = len(ulmc_studies)

    by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    raw_names: dict[str, list[str]] = defaultdict(list)

    for study in ulmc_studies:
        raw = (study.get("journal") or "").strip() or "(unknown journal)"
        key = journal_group_key(raw)
        by_key[key].append(study)
        raw_names[key].append(normalize_journal(raw))

    rows: list[dict[str, Any]] = []
    for key, matched in by_key.items():
        journal = pick_display_journal(raw_names[key])
        orders = sorted(
            {study_order_key(s) for s in matched if study_order_key(s)},
            key=lambda x: (not x.startswith("L"), x.replace("L", "").zfill(6)),
        )
        n = len(matched)
        rows.append(
            {
                "journal": journal,
                "n_studies": n,
                "pct_of_ulmc_corpus": pct(n, total) if total else "0.0%",
                "study_orders": "; ".join(orders),
            }
        )

    rows.sort(key=lambda r: (-r["n_studies"], r["journal"].lower()))
    return rows, total


def build_journal_ulmc_payload(
    results_payload: dict[str, Any],
    extraction_rows: list[dict[str, str]] | None = None,
    *,
    exclude_pls_only: bool = False,
) -> dict[str, Any]:
    """Structured payload for progress_summary_data.json."""
    studies: list[dict[str, str]] = results_payload.get("studies") or []
    rows, ulmc_n = aggregate_by_journal(studies, exclude_pls_only=exclude_pls_only)

    payload: dict[str, Any] = {
        "corpus": "fully_coded",
        "corpus_label": "Fully coded corpus (same as Summary / Datasets tab)",
        "corpus_n": len(studies),
        "ulmc_n": ulmc_n,
        "definition": ULMC_DEFINITION,
        "exclude_pls_only": exclude_pls_only,
        "rows": rows,
    }

    if extraction_rows is not None:
        ext_studies = [
            {
                "journal": (r.get("journal") or "").strip(),
                "study_order": (r.get("study_order") or "").strip(),
                "empirical_ulmc": r.get("empirical_ulmc", ""),
                "statistical_methods_mv": r.get("statistical_methods_mv", ""),
                "pls_cbsem_category": classify_pls_cbsem(
                    {
                        "pls_sem_used": r.get("pls_sem_used", ""),
                        "not_pls": r.get("not_pls", ""),
                        "estimator": r.get("estimator", ""),
                    }
                ),
            }
            for r in extraction_rows
        ]
        broad_rows, broad_n = aggregate_by_journal(ext_studies, exclude_pls_only=exclude_pls_only)
        payload["broader"] = {
            "corpus": "extraction_csv",
            "corpus_label": (
                f"All rows in {EXTRACTION_PATH.relative_to(ROOT)} "
                f"({len(extraction_rows)} studies; not all fully coded)"
            ),
            "corpus_n": len(extraction_rows),
            "ulmc_n": broad_n,
            "legacy_overlap_note": (
                "Legacy 182 cohort (legacy_extracted_data.csv) has 216 empirical_ulmc=TRUE rows "
                "but no structured journal field; journal counts for legacy-only studies require "
                "articles_master.csv join (included in fully coded corpus above)."
            ),
            "rows": broad_rows,
        }

    return payload


def format_md_report(
    payload: dict[str, Any],
    *,
    top_n: int | None = None,
) -> str:
    today = date.today().isoformat()
    rows = payload["rows"]
    if top_n:
        display_rows = rows[:top_n]
    else:
        display_rows = rows

    lines = [
        "# ULMC studies by journal",
        "",
        f"**Generated**: {today}  ",
        f"**Corpus**: {payload['corpus_label']} (N={payload['corpus_n']})  ",
        f"**ULMC-used studies**: {payload['ulmc_n']}  ",
        "",
        "## Definition",
        "",
        f"- {payload['definition']}",
        f"- PLS exclusion: {'yes' if payload.get('exclude_pls_only') else 'no (default — all empirical ULMC)'}",
        "",
        "## Primary table (fully coded corpus)",
        "",
        "| Journal | n | % of ULMC corpus | Study orders |",
        "|---------|--:|-----------------:|--------------|",
    ]
    for row in display_rows:
        orders = row["study_orders"]
        if len(orders) > 80:
            orders = orders[:77] + "..."
        lines.append(
            f"| {row['journal']} | {row['n_studies']} | {row['pct_of_ulmc_corpus']} | {orders} |"
        )
    if top_n and len(rows) > top_n:
        lines.append(f"| … | ({len(rows) - top_n} more journals) | | |")

    broader = payload.get("broader")
    if broader:
        lines.extend(
            [
                "",
                "## Broader count (extraction CSV, not audit-primary)",
                "",
                f"**Source**: {broader['corpus_label']}  ",
                f"**ULMC-used**: {broader['ulmc_n']} of {broader['corpus_n']} rows  ",
                "",
                f"_{broader['legacy_overlap_note']}_",
                "",
                "| Journal | n | % of ULMC corpus |",
                "|---------|--:|-----------------:|",
            ]
        )
        for row in broader["rows"][:15]:
            lines.append(
                f"| {row['journal']} | {row['n_studies']} | {row['pct_of_ulmc_corpus']} |"
            )
        if len(broader["rows"]) > 15:
            lines.append(f"| … | ({len(broader['rows']) - 15} more journals) | |")

    lines.extend(
        [
            "",
            "## Refresh",
            "",
            "```bash",
            "python3 review/master/journal_ulmc_table.py",
            "# or",
            "python3 review/master/progress_counter.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["journal", "n_studies", "pct_of_ulmc_corpus", "study_orders"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(
    payload: dict[str, Any],
    *,
    csv_path: Path = OUTPUT_CSV,
    md_path: Path = OUTPUT_MD,
) -> None:
    write_csv(csv_path, payload["rows"])
    md_path.write_text(format_md_report(payload), encoding="utf-8")


def journal_ulmc_summary_table(payload: dict[str, Any]) -> dict[str, Any]:
    """Summary-tab table dict compatible with build_results_tables.summary_table."""
    rows = payload["rows"]
    note = (
        f"{payload['ulmc_n']} ULMC-used studies in {payload['corpus_label']} "
        f"(N={payload['corpus_n']}). {payload['definition']}."
    )
    broader = payload.get("broader")
    if broader:
        note += (
            f" Broader extraction CSV: {broader['ulmc_n']}/{broader['corpus_n']} ULMC-used "
            "(see ULMC_BY_JOURNAL.md)."
        )

    table_rows = [
        {
            "metric_id": f"journal_ulmc.{i}",
            "label": row["journal"],
            "value": row["n_studies"],
            "n": payload["ulmc_n"],
            "definition": f"ULMC-used studies in {row['journal']}.",
            "filter_rule": {
                "description": f"journal == {row['journal']!r} AND ULMC used",
                "filter": {"fn": "is_ulmc_used", "journal": row["journal"]},
            },
            "study_orders": row["study_orders"].split("; ") if row["study_orders"] else [],
            "cells": [row["journal"], str(row["n_studies"]), row["pct_of_ulmc_corpus"]],
        }
        for i, row in enumerate(rows)
    ]
    return {
        "id": "journal_ulmc",
        "title": "ULMC by journal",
        "columns": ["Journal", "Count", "% of ULMC corpus"],
        "rows": table_rows,
        "note": note,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ULMC-by-journal table from fully coded corpus")
    parser.add_argument("--master", type=Path, default=MASTER_PATH)
    parser.add_argument("--extraction", type=Path, default=EXTRACTION_PATH)
    parser.add_argument("--csv", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--md", type=Path, default=OUTPUT_MD)
    parser.add_argument(
        "--exclude-pls-only",
        action="store_true",
        help="Exclude PLS-SEM unless empirical_ulmc=TRUE",
    )
    parser.add_argument("--no-broader", action="store_true", help="Skip broader extraction CSV section")
    args = parser.parse_args()

    master = read_csv(args.master)
    extraction = read_csv(args.extraction)
    if not master and not extraction:
        print("No master or extraction data.", file=sys.stderr)
        sys.exit(1)

    results = build_results_payload(master, extraction)
    ext_for_broader = None if args.no_broader else extraction
    payload = build_journal_ulmc_payload(
        results,
        ext_for_broader,
        exclude_pls_only=args.exclude_pls_only,
    )
    payload["generated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    write_outputs(payload, csv_path=args.csv, md_path=args.md)

    print(f"Wrote {args.csv.relative_to(ROOT)} ({payload['ulmc_n']} ULMC studies, {len(payload['rows'])} journals)")
    print(f"Wrote {args.md.relative_to(ROOT)}")
    print("\nTop journals:")
    for row in payload["rows"][:10]:
        print(f"  {row['n_studies']:3d}  {row['journal']}")


if __name__ == "__main__":
    main()
