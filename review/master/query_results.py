#!/usr/bin/env python3
"""
Reproducible queries over fully coded results with source citations.

Computes from articles_master.csv + systematic_extraction_40_studies.csv via
build_results_tables (same logic as progress_summary_data.json).

Examples:
  python3 review/master/query_results.py --stat pls_count
  python3 review/master/query_results.py --stat harman_mean
  python3 review/master/query_results.py --study-order 3
  python3 review/master/query_results.py --master-id M0210
  python3 review/master/query_results.py --list-fully-coded
  python3 review/master/query_results.py --metric-id pls_cbsem.PLS-SEM
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build_results_tables import (
    EXTRACTION_PATH,
    MASTER_PATH,
    build_results_payload,
    build_summary_payload,
    read_csv,
    study_order_key,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS_JSON = ROOT / "review" / "progress_results_data.json"
SUMMARY_JSON = ROOT / "review" / "progress_summary_data.json"

STAT_METRIC_IDS: dict[str, str] = {
    "pls_count": "pls_cbsem.PLS-SEM",
    "cbsem_count": "pls_cbsem.CB-SEM",
    "fully_coded_total": "corpus_counts.total",
    "legacy_count": "corpus_counts.legacy",
    "ebsco_pool_count": "corpus_counts.ebsco_pool",
    "harman_mean": "harman.mean_pct",
    "harman_numeric_count": "harman.numeric_count",
    "harman_deployed_true": "harman_deployed.TRUE",
    "mv_pct_mean": "method_variance_pct.mean",
    "mv_pct_numeric_count": "method_variance_pct.count",
    "procedural_remedies_any": "procedural_remedies.any",
    "management_domain_true": "management_domain.TRUE",
}


def csv_row_ref(path: Path, row_index: int) -> str:
    """1-based file row (row 1 = header)."""
    return f"{path.relative_to(ROOT)}:row {row_index + 2}"


def find_csv_row_by_study_order(rows: list[dict[str, str]], order: str) -> tuple[int | None, dict[str, str] | None]:
    key = order.strip()
    for idx, row in enumerate(rows):
        so = (row.get("study_order") or "").strip()
        if so == key:
            return idx, row
        if key.isdigit() and so == f"L{key}":
            return idx, row
    return None, None


def find_master_row(rows: list[dict[str, str]], *, master_id: str | None, study_order: str | None) -> tuple[int | None, dict[str, str] | None]:
    if master_id:
        mid = master_id.strip().upper()
        for idx, row in enumerate(rows):
            aid = (row.get("article_id") or "").strip().upper()
            if aid == mid:
                return idx, row
    if study_order:
        _, ext = find_csv_row_by_study_order(rows, study_order)
        if ext:
            return None, ext
        key = study_order.strip()
        for idx, row in enumerate(rows):
            so = (row.get("study_order") or "").strip()
            if so == key or (key.isdigit() and so == f"L{key}"):
                return idx, row
    return None, None


def load_payloads(
    master_path: Path,
    extraction_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, str]], list[dict[str, str]]]:
    master = read_csv(master_path)
    extraction = read_csv(extraction_path)
    results = build_results_payload(master, extraction)
    summary = build_summary_payload(results, extraction)
    return results, summary, master, extraction


def flatten_metrics(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for table in summary.get("tables") or []:
        for row in table.get("rows") or []:
            if isinstance(row, dict) and row.get("metric_id"):
                out[row["metric_id"]] = {
                    "table_id": table.get("id"),
                    "table_title": table.get("title"),
                    **row,
                }
    return out


def print_metric(metric: dict[str, Any], *, sources: list[str]) -> None:
    print(f"value: {metric.get('value')}")
    print(f"n: {metric.get('n')}")
    fr = metric.get("filter_rule") or {}
    print(f"rule: {fr.get('description') or metric.get('definition', '')}")
    if fr.get("filter"):
        print(f"filter: {json.dumps(fr['filter'])}")
    print("source:")
    for src in sources:
        print(f"  {src}")
    orders = metric.get("study_orders") or []
    print(f"study_orders ({len(orders)}):")
    for order in orders:
        print(f"  {order}")


def print_study_detail(
    study: dict[str, str],
    *,
    master: list[dict[str, str]],
    extraction: list[dict[str, str]],
) -> None:
    order = study_order_key(study)
    ext_idx, ext_row = find_csv_row_by_study_order(extraction, order)
    master_idx = None
    mid = (study.get("master_id") or study.get("article_id") or "").strip()
    for idx, row in enumerate(master):
        if (row.get("article_id") or "").strip() == mid:
            master_idx = idx
            break

    print(f"study_order: {study.get('study_order', '')}")
    print(f"master_id: {study.get('master_id', '')}")
    print(f"legacy_refid: {study.get('legacy_refid', '')}")
    print(f"title: {study.get('title', '')}")
    print(f"cohort: {study.get('cohort', '')}")
    print(f"coded_via: {study.get('coded_via', '')}")
    print(f"pls_cbsem_category: {study.get('pls_cbsem_category', '')}")
    print("source:")
    if master_idx is not None:
        print(f"  {csv_row_ref(MASTER_PATH, master_idx)} (articles_master.csv)")
    if ext_idx is not None:
        print(f"  {csv_row_ref(EXTRACTION_PATH, ext_idx)} (systematic_extraction_40_studies.csv)")
    print(f"  {RESULTS_JSON.relative_to(ROOT)} (progress_results_data.json)")
    print("---")
    for key in sorted(study):
        if key in ("study_order", "master_id", "legacy_refid", "title", "cohort", "coded_via", "pls_cbsem_category"):
            continue
        print(f"{key}: {study[key]}")


def list_fully_coded(results: dict[str, Any], extraction: list[dict[str, str]]) -> None:
    studies = results.get("studies") or []
    print(f"value: {len(studies)}")
    print(f"n: {len(studies)}")
    print(
        "rule: examination_status==fully_coded in master OR extraction row has >=4 key MV fields "
        f"({', '.join(['management_domain', 'empirical_ulmc', 'statistical_methods_mv', 'method_variance_pct', 'procedural_remedies_list'])})"
    )
    print("source:")
    print(f"  {MASTER_PATH.relative_to(ROOT)}")
    print(f"  {EXTRACTION_PATH.relative_to(ROOT)}")
    print(f"  review/master/build_results_tables.py")
    print("study_orders:")
    for study in studies:
        order = study_order_key(study)
        ext_idx, _ = find_csv_row_by_study_order(extraction, order)
        ext_ref = f", {csv_row_ref(EXTRACTION_PATH, ext_idx)}" if ext_idx is not None else ""
        print(f"  {order} ({study.get('cohort', '')}, {study.get('coded_via', '')}{ext_ref})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query audit-ready results with citations")
    parser.add_argument("--master", type=Path, default=MASTER_PATH)
    parser.add_argument("--extraction", type=Path, default=EXTRACTION_PATH)
    parser.add_argument("--stat", help=f"Named stat ({', '.join(sorted(STAT_METRIC_IDS))})")
    parser.add_argument("--metric-id", help="Full metric_id from progress_summary_data.json")
    parser.add_argument("--study-order", help="Lookup study by study_order (e.g. 3 or L142)")
    parser.add_argument("--master-id", help="Lookup study by article_id (e.g. M0210)")
    parser.add_argument("--list-fully-coded", action="store_true", help="List all fully coded study_orders")
    parser.add_argument("--list-stats", action="store_true", help="List available --stat names")
    args = parser.parse_args()

    if args.list_stats:
        for name, mid in sorted(STAT_METRIC_IDS.items()):
            print(f"{name}\t→\t{mid}")
        return

    results, summary, master, extraction = load_payloads(args.master, args.extraction)
    sources = [
        f"{args.master.relative_to(ROOT)} + {args.extraction.relative_to(ROOT)}",
        "review/master/build_results_tables.py → progress_summary_data.json",
    ]

    if args.list_fully_coded:
        list_fully_coded(results, extraction)
        return

    if args.study_order or args.master_id:
        studies = results.get("studies") or []
        study = None
        if args.study_order:
            key = args.study_order.strip()
            for s in studies:
                so = (s.get("study_order") or "").strip()
                if so == key or (key.isdigit() and so == f"L{key}"):
                    study = s
                    break
        if not study and args.master_id:
            mid = args.master_id.strip().upper()
            for s in studies:
                if (s.get("master_id") or s.get("article_id") or "").strip().upper() == mid:
                    study = s
                    break
        if not study and args.master_id:
            mid = args.master_id.strip().upper()
            for idx, row in enumerate(master):
                if (row.get("article_id") or "").strip().upper() == mid:
                    print(f"master_id: {mid}")
                    print(f"title: {row.get('title', '')}")
                    print(f"examination_status: {row.get('examination_status', '')}")
                    print(f"study_order: {row.get('study_order', '')}")
                    print(f"has_pdf: {row.get('has_pdf', '')}")
                    print(f"pdf_path: {row.get('pdf_path', '')}")
                    print(f"source: {csv_row_ref(args.master, idx)}")
                    print("note: not in fully coded corpus (Datasets/Summary)")
                    sys.exit(0)
        if not study:
            print("Study not found in fully coded corpus.", file=sys.stderr)
            sys.exit(1)
        print_study_detail(study, master=master, extraction=extraction)
        return

    metric_id = None
    if args.stat:
        metric_id = STAT_METRIC_IDS.get(args.stat)
        if not metric_id:
            print(f"Unknown --stat {args.stat!r}. Use --list-stats.", file=sys.stderr)
            sys.exit(1)
    elif args.metric_id:
        metric_id = args.metric_id
    else:
        parser.print_help()
        sys.exit(1)

    metrics = flatten_metrics(summary)
    metric = metrics.get(metric_id or "")
    if not metric:
        print(f"Metric not found: {metric_id}", file=sys.stderr)
        sys.exit(1)
    print(f"metric_id: {metric_id}")
    print_metric(metric, sources=sources)


if __name__ == "__main__":
    main()
