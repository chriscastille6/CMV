#!/usr/bin/env python3
"""
Build progress_results_data.json and progress_extraction_summary_data.json for the dashboard.

Joins articles_master.csv with systematic_extraction_40_studies.csv via study_order,
legacy_refid, or DOI. A study is fully coded when:
  - examination_status == fully_coded in master, OR
  - extraction row has >= 4 key MV fields populated (see examination.KEY_EXTRACTION_FIELDS).

Examples:
  python3 review/master/build_results_tables.py
  python3 review/master/progress_counter.py   # also writes results + summary JSON
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from examination import (
    EXTRACTION_PATH,
    KEY_EXTRACTION_FIELDS,
    is_fully_coded_row,
    load_combined_extraction_rows,
    read_csv,
)

ROOT = Path(__file__).resolve().parents[2]
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
RESULTS_JSON = ROOT / "review" / "progress_results_data.json"
SUMMARY_JSON = ROOT / "review" / "progress_summary_data.json"
EXTRACTION_SUMMARY_JSON = ROOT / "review" / "progress_extraction_summary_data.json"
EBSCO_DIR = ROOT / "review" / "EBSCO"

if str(EBSCO_DIR) not in sys.path:
    sys.path.insert(0, str(EBSCO_DIR))

from publisher_outlet import PUBLISHER_OUTLETS, infer_publisher_outlet  # noqa: E402

DISPLAY_FIELDS: tuple[str, ...] = (
    "study_order",
    "article_id",
    "master_id",
    "title",
    "authors",
    "year",
    "journal",
    "publisher_outlet",
    "doi",
    "management_domain",
    "empirical_ulmc",
    "pls_cbsem_category",
    "pls_sem_used",
    "estimator",
    "method_variance_pct",
    "harman_deployed",
    "harman_variance_pct",
    "statistical_methods_mv",
    "procedural_remedies_used",
    "ulmc_improves_fit",
    "ulmc_in_final",
    "author_conclusion_mv",
    "mv_inference_criteria_list",
    "mv_inferred_not_problem",
    "authors_business_school",
    "sample_n",
    "num_constructs",
    "num_indicators",
    "complexity_ratio",
    "underpowered_heuristic",
    "legacy_refid",
    "notes",
)

OPTIONAL_EXTRACTION_FIELDS = (
    "mv_inference_criteria_list",
    "mv_inferred_not_problem",
    "authors_business_school",
    "procedural_remedies_list",
    "details_in_supplement",
    "extraction_incomplete_main_text",
    "publisher_outlet_detail",
)

MASTER_TITLE_FIELDS = ("title", "authors", "year", "journal", "doi")
EXTRACTION_TITLE_FIELDS = ("study_title", "authors", "year", "journal", "doi")


def norm_doi(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if v.startswith(prefix):
            v = v[len(prefix) :]
    return v.strip()


def is_ebsco_pool_member(rec: dict[str, str]) -> bool:
    sources = rec.get("sources", "") or ""
    if "ebsco_2026" in sources:
        return True
    return rec.get("corpus_tier", "") == "ebsco_screened"


def is_legacy_cohort(rec: dict[str, str] | None) -> bool:
    if not rec:
        return False
    if rec.get("corpus_tier") == "legacy_gold":
        return True
    return "legacy_182" in (rec.get("sources", "") or "")


def build_extraction_indexes(
    rows: list[dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_order: dict[str, dict[str, str]] = {}
    by_doi: dict[str, dict[str, str]] = {}
    for row in rows:
        order = (row.get("study_order") or "").strip()
        if order:
            by_order[order] = row
            if order.isdigit():
                by_order[f"L{order}"] = row
        doi = norm_doi(row.get("doi"))
        if doi:
            by_doi[doi] = row
    return by_order, by_doi


def lookup_extraction_row(
    master_rec: dict[str, str] | None,
    by_order: dict[str, dict[str, str]],
    by_doi: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    if not master_rec:
        return None
    study_order = (master_rec.get("study_order") or "").strip()
    if study_order and study_order in by_order:
        return by_order[study_order]
    if study_order.startswith("L"):
        stripped = study_order[1:]
        if stripped in by_order:
            return by_order[stripped]
    legacy_refid = (master_rec.get("legacy_refid") or "").strip()
    if legacy_refid and legacy_refid in by_order:
        return by_order[legacy_refid]
    doi = norm_doi(master_rec.get("doi"))
    if doi and doi in by_doi:
        return by_doi[doi]
    return None


def pick(row: dict[str, str] | None, key: str, default: str = "") -> str:
    if not row:
        return default
    value = row.get(key, default)
    return (value or default).strip()


def build_study_record(
    master_rec: dict[str, str] | None,
    extraction_row: dict[str, str] | None,
    *,
    cohort: str,
    coded_via: str,
) -> dict[str, str]:
    out: dict[str, str] = {"cohort": cohort, "coded_via": coded_via}
    ext = extraction_row or {}
    mas = master_rec or {}

    out["study_order"] = pick(mas, "study_order") or pick(ext, "study_order")
    out["legacy_refid"] = pick(mas, "legacy_refid") or pick(ext, "legacy_refid") or "NA"
    out["article_id"] = pick(mas, "article_id") or "NA"
    out["master_id"] = out["article_id"]

    for master_key, ext_key in zip(MASTER_TITLE_FIELDS, EXTRACTION_TITLE_FIELDS, strict=True):
        out[master_key] = pick(mas, master_key) or pick(ext, ext_key)

    if not out.get("study_order"):
        out["study_order"] = "NA"
    if not out.get("doi"):
        out["doi"] = "NA"

    field_sources = {
        "management_domain": ext,
        "empirical_ulmc": ext,
        "not_pls": ext,
        "pls_sem_used": ext,
        "estimator": ext,
        "method_variance_pct": ext,
        "harman_deployed": ext,
        "harman_variance_pct": ext,
        "statistical_methods_mv": ext,
        "procedural_remedies_used": ext,
        "procedural_remedies_list": ext,
        "multisource_same_construct": ext,
        "different_sources_iv_dv": ext,
        "distinct_sources_other": ext,
        "three_step_complete": ext,
        "three_step_approach_used": ext,
        "step1_presence_delta_chisq_reported": ext,
        "step2_method_r_bias_test_reported": ext,
        "step3_contamination_reported": ext,
        "richardson_2009_cited": ext,
        "ulmc_improves_fit": ext,
        "ulmc_in_final": ext,
        "author_conclusion_mv": ext,
        "mv_inference_criteria_list": ext,
        "mv_inferred_not_problem": ext,
        "authors_business_school": ext,
        "sample_n": ext,
        "num_constructs": ext,
        "num_indicators": ext,
        "complexity_ratio": ext,
        "publisher_outlet": ext,
        "details_in_supplement": ext,
        "extraction_incomplete_main_text": ext,
    }
    for field, source in field_sources.items():
        out[field] = pick(source, field)

    outlet = out.get("publisher_outlet", "")
    if not outlet or outlet.upper() == "NA":
        inferred, _detail = infer_publisher_outlet(out.get("doi"), out.get("journal"))
        out["publisher_outlet"] = inferred

    out["underpowered_heuristic"] = compute_underpowered_heuristic(
        out.get("num_constructs"),
        out.get("num_indicators"),
        out.get("complexity_ratio"),
    )

    out["pls_cbsem_category"] = classify_pls_cbsem(out)
    pls_issues = pls_field_inconsistencies(out)
    extraction_notes = pick(ext, "notes")
    if pls_issues:
        flag_text = "; ".join(pls_issues)
        out["notes"] = f"{extraction_notes}; {flag_text}" if extraction_notes else flag_text
    else:
        out["notes"] = extraction_notes

    return out


def classify_cohort(master_rec: dict[str, str] | None) -> str:
    if master_rec and is_ebsco_pool_member(master_rec):
        return "ebsco_pool"
    if is_legacy_cohort(master_rec):
        return "legacy"
    return "other"


def build_results_payload(
    master: list[dict[str, str]],
    extraction_rows: list[dict[str, str]],
) -> dict[str, Any]:
    by_order, by_doi = build_extraction_indexes(extraction_rows)
    present_columns = set(extraction_rows[0].keys()) if extraction_rows else set()
    columns = [c for c in DISPLAY_FIELDS if c not in OPTIONAL_EXTRACTION_FIELDS or c in present_columns]

    seen_orders: set[str] = set()
    studies: list[dict[str, str]] = []

    for rec in master:
        if rec.get("examination_status") != "fully_coded":
            continue
        ext_row = lookup_extraction_row(rec, by_order, by_doi)
        study = build_study_record(
            rec,
            ext_row,
            cohort=classify_cohort(rec),
            coded_via="master:fully_coded",
        )
        key = study["study_order"] or study.get("article_id", "")
        if key and key in seen_orders:
            continue
        if key:
            seen_orders.add(key)
        studies.append(study)

    for ext_row in extraction_rows:
        if not is_fully_coded_row(ext_row):
            continue
        order = (ext_row.get("study_order") or "").strip()
        if not order or order in seen_orders or f"L{order}" in seen_orders:
            continue
        master_match = next(
            (
                r
                for r in master
                if lookup_extraction_row(r, by_order, by_doi) is ext_row
            ),
            None,
        )
        if master_match and master_match.get("examination_status") == "fully_coded":
            continue
        study = build_study_record(
            master_match,
            ext_row,
            cohort=classify_cohort(master_match),
            coded_via="extraction:key_fields>=4",
        )
        seen_orders.add(order)
        studies.append(study)

    studies.sort(key=lambda s: (s.get("year") or "0", (s.get("title") or "").lower()), reverse=True)

    legacy = [s for s in studies if s["cohort"] == "legacy"]
    ebsco_pool = [s for s in studies if s["cohort"] == "ebsco_pool"]
    other = [s for s in studies if s["cohort"] == "other"]

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "last_updated": now,
        "total_count": len(studies),
        "legacy_count": len(legacy),
        "ebsco_pool_count": len(ebsco_pool),
        "other_count": len(other),
        "columns": columns,
        "column_labels": {c: c.replace("_", " ") for c in columns},
        "studies": studies,
        "legacy_studies": legacy,
        "ebsco_pool_studies": ebsco_pool,
        "other_studies": other,
        "key_extraction_fields": list(KEY_EXTRACTION_FIELDS),
    }


def write_results_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def normalize_tristate(value: str | None) -> str:
    s = (value or "").strip()
    if not s or s.upper() in ("NA", "N/A", "NAN", "NONE", "NULL", "-"):
        return "NA"
    if s.upper() in ("TRUE", "T", "YES", "1"):
        return "TRUE"
    if s.upper() in ("FALSE", "F", "NO", "0"):
        return "FALSE"
    return s


PLS_CBSEM_CATEGORIES: tuple[str, ...] = ("PLS-SEM", "CB-SEM", "Other/Unknown", "NA")


def normalize_estimator(value: str | None) -> str:
    s = (value or "").strip().upper()
    if not s or s in ("NA", "N/A", "-"):
        return "NA"
    if s == "PLS-SEM" or s == "PLS":
        return "PLS-SEM"
    if s == "CB-SEM":
        return "CB-SEM"
    return s


def classify_pls_cbsem(study: dict[str, str]) -> str:
    """Mutually exclusive PLS vs CB-SEM category (one per study)."""
    pls_used = normalize_tristate(study.get("pls_sem_used"))
    not_pls = normalize_tristate(study.get("not_pls"))
    estimator = normalize_estimator(study.get("estimator"))

    if pls_used == "TRUE" or estimator == "PLS-SEM":
        return "PLS-SEM"
    if estimator == "CB-SEM" or not_pls == "TRUE":
        return "CB-SEM"

    has_signal = pls_used != "NA" or not_pls != "NA" or estimator != "NA"
    if not has_signal:
        return "NA"
    return "Other/Unknown"


def pls_field_inconsistencies(study: dict[str, str]) -> list[str]:
    """Flag contradictory PLS/CB-SEM extraction fields (VARIABLE_CODEBOOK rules)."""
    issues: list[str] = []
    pls_used = normalize_tristate(study.get("pls_sem_used"))
    not_pls = normalize_tristate(study.get("not_pls"))
    estimator = normalize_estimator(study.get("estimator"))

    if pls_used == "TRUE" and not_pls == "TRUE":
        issues.append("pls_sem_used=TRUE but not_pls=TRUE")
    if pls_used == "TRUE" and estimator == "CB-SEM":
        issues.append("pls_sem_used=TRUE but estimator=CB-SEM")
    if pls_used == "FALSE" and estimator == "PLS-SEM":
        issues.append("pls_sem_used=FALSE but estimator=PLS-SEM")
    if not_pls == "FALSE" and estimator == "CB-SEM":
        issues.append("not_pls=FALSE but estimator=CB-SEM")
    if pls_used == "FALSE" and not_pls == "FALSE":
        issues.append("pls_sem_used=FALSE and not_pls=FALSE")
    return issues


def parse_numeric(value: str | None) -> float | None:
    if not value:
        return None
    s = str(value).strip()
    if not s or s.upper() in ("NA", "N/A", "NAN", "NONE", "NULL", "-", "TRUE", "FALSE"):
        return None
    s = s.replace("%", "").replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", s)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def compute_underpowered_heuristic(
    num_constructs: str | None,
    num_indicators: str | None,
    complexity_ratio: str | None,
) -> str:
    """Coding-guidance flag: TRUE if any ULMC complexity risk factor is met."""
    nc = parse_numeric(num_constructs)
    ni = parse_numeric(num_indicators)
    cr = parse_numeric(complexity_ratio)
    if cr is None and nc and ni and nc > 0:
        cr = ni / nc

    criteria: list[bool] = []
    if ni is not None:
        criteria.append(ni < 15)
    if cr is not None:
        criteria.append(cr < 3)
    if nc is not None:
        criteria.append(nc > 10)

    if not criteria:
        return "NA"
    return "TRUE" if any(criteria) else "FALSE"


def pct(n: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{100 * n / total:.1f}%"


def split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    s = str(value).strip()
    if not s or s.upper() in ("NA", "N/A", "NONE", "NULL", "-"):
        return []
    parts = re.split(r"[;|,]+", s)
    return [p.strip() for p in parts if p.strip() and p.strip().upper() not in ("NA", "NONE")]


def study_order_key(study: dict[str, str]) -> str:
    return (study.get("study_order") or study.get("article_id") or "").strip()


def study_orders_for(studies: list[dict[str, str]]) -> list[str]:
    keys = [study_order_key(s) for s in studies]
    return sorted(k for k in keys if k)


def filter_rule_eq(field: str, value: str, description: str) -> dict[str, Any]:
    return {
        "description": description,
        "filter": {"field": field, "op": "eq", "value": value},
    }


def filter_rule_fn(description: str, fn_name: str) -> dict[str, Any]:
    return {
        "description": description,
        "filter": {"fn": fn_name},
    }


def spacer_row(columns: int = 3) -> dict[str, Any]:
    return {
        "metric_id": "",
        "label": "",
        "value": "",
        "n": 0,
        "definition": "",
        "filter_rule": {},
        "study_orders": [],
        "cells": [""] * columns,
    }


def metric_row(
    metric_id: str,
    label: str,
    value: int | float | str,
    n: int,
    definition: str,
    filter_rule: dict[str, Any],
    study_orders: list[str],
    cells: list[str],
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "label": label,
        "value": value,
        "n": n,
        "definition": definition,
        "filter_rule": filter_rule,
        "study_orders": study_orders,
        "cells": cells,
    }


def count_tristate_metrics(
    studies: list[dict[str, str]],
    field: str,
    *,
    table_id: str,
    total: int,
    field_label: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label in ("TRUE", "FALSE", "NA"):
        matched = [s for s in studies if normalize_tristate(s.get(field)) == label]
        n = len(matched)
        rows.append(
            metric_row(
                f"{table_id}.{label}",
                label,
                n,
                total,
                f"Studies where {field_label} is {label}.",
                filter_rule_eq(field, label, f"{field_label} == {label}"),
                study_orders_for(matched),
                [label, str(n), pct(n, total)],
            )
        )
    other_labels = {
        normalize_tristate(s.get(field))
        for s in studies
        if normalize_tristate(s.get(field)) not in ("TRUE", "FALSE", "NA")
    }
    for label in sorted(other_labels):
        matched = [s for s in studies if normalize_tristate(s.get(field)) == label]
        n = len(matched)
        rows.append(
            metric_row(
                f"{table_id}.{label}",
                label,
                n,
                total,
                f"Studies where {field_label} is {label} (non-standard tristate).",
                filter_rule_eq(field, label, f"{field_label} == {label}"),
                study_orders_for(matched),
                [label, str(n), pct(n, total)],
            )
        )
    return rows


def summary_table(
    table_id: str,
    title: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    *,
    note: str = "",
) -> dict[str, Any]:
    return {
        "id": table_id,
        "title": title,
        "columns": columns,
        "rows": rows,
        "note": note,
    }


def count_audit_metrics(summary_or_tables: dict[str, Any] | list[dict[str, Any]]) -> int:
    if isinstance(summary_or_tables, list):
        tables = summary_or_tables
    else:
        tables = summary_or_tables.get("tables") or []
    return sum(
        1
        for table in tables
        for row in table.get("rows") or []
        if isinstance(row, dict) and row.get("metric_id")
    )


def build_summary_payload(
    results_payload: dict[str, Any],
    extraction_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    studies: list[dict[str, str]] = results_payload.get("studies") or []
    total = len(studies)
    tables: list[dict[str, Any]] = []
    journal_ulmc_counts: dict[str, Any] | None = None

    legacy_studies = [s for s in studies if s.get("cohort") == "legacy"]
    pool_studies = [s for s in studies if s.get("cohort") == "ebsco_pool"]
    other_studies = [s for s in studies if s.get("cohort") == "other"]
    tables.append(
        summary_table(
            "corpus_counts",
            "Corpus counts (fully coded)",
            ["Cohort", "Count", "% of corpus"],
            [
                metric_row(
                    "corpus_counts.total",
                    "Fully coded (total)",
                    total,
                    total,
                    "All fully coded studies in the Datasets tab.",
                    filter_rule_fn("All studies in fully coded corpus", "all_studies"),
                    study_orders_for(studies),
                    ["Fully coded (total)", str(total), "100.0%"],
                ),
                metric_row(
                    "corpus_counts.legacy",
                    "Legacy 182",
                    len(legacy_studies),
                    total,
                    "Fully coded studies from the legacy 182 gold cohort.",
                    filter_rule_eq("cohort", "legacy", "cohort == legacy"),
                    study_orders_for(legacy_studies),
                    ["Legacy 182", str(len(legacy_studies)), pct(len(legacy_studies), total)],
                ),
                metric_row(
                    "corpus_counts.ebsco_pool",
                    "EBSCO 570-pool",
                    len(pool_studies),
                    total,
                    "Fully coded studies in the EBSCO 570 screening pool.",
                    filter_rule_eq("cohort", "ebsco_pool", "cohort == ebsco_pool"),
                    study_orders_for(pool_studies),
                    ["EBSCO 570-pool", str(len(pool_studies)), pct(len(pool_studies), total)],
                ),
                metric_row(
                    "corpus_counts.other",
                    "Other",
                    len(other_studies),
                    total,
                    "Fully coded studies outside legacy 182 and EBSCO pool.",
                    filter_rule_eq("cohort", "other", "cohort == other"),
                    study_orders_for(other_studies),
                    ["Other", str(len(other_studies)), pct(len(other_studies), total)],
                ),
            ],
        )
    )

    pls_by_cat: dict[str, list[dict[str, str]]] = {cat: [] for cat in PLS_CBSEM_CATEGORIES}
    for s in studies:
        cat = s.get("pls_cbsem_category") or classify_pls_cbsem(s)
        pls_by_cat.setdefault(cat, []).append(s)
    inconsistent = [s for s in studies if pls_field_inconsistencies(s)]
    pls_note = (
        "One category per study: PLS if pls_sem_used=TRUE or estimator=PLS-SEM; "
        "else CB-SEM if estimator=CB-SEM or not_pls=TRUE; else Other/Unknown or NA."
    )
    if inconsistent:
        pls_note += (
            f" {len(inconsistent)} stud{'y' if len(inconsistent) == 1 else 'ies'} "
            "with conflicting PLS/CB-SEM fields (see Datasets notes)."
        )
    pls_rows = [
        metric_row(
            f"pls_cbsem.{cat}",
            cat,
            len(pls_by_cat.get(cat, [])),
            total,
            f"Studies classified as {cat} (mutually exclusive PLS vs CB-SEM).",
            filter_rule_eq("pls_cbsem_category", cat, f"pls_cbsem_category == {cat}"),
            study_orders_for(pls_by_cat.get(cat, [])),
            [cat, str(len(pls_by_cat.get(cat, []))), pct(len(pls_by_cat.get(cat, [])), total)],
        )
        for cat in PLS_CBSEM_CATEGORIES
    ]
    tables.append(
        summary_table(
            "pls_usage",
            "PLS vs CB-SEM",
            ["Category", "Count", "% of corpus"],
            pls_rows,
            note=pls_note,
        )
    )

    harman_numeric: list[tuple[dict[str, str], float]] = []
    for s in studies:
        v = parse_numeric(s.get("harman_variance_pct"))
        if v is not None:
            harman_numeric.append((s, v))
    harman_values = [v for _, v in harman_numeric]
    harman_orders = study_orders_for([s for s, _ in harman_numeric])
    if harman_values:
        harman_mean = statistics.mean(harman_values)
        harman_rows: list[dict[str, Any]] = [
            metric_row(
                "harman.mean_pct",
                "Mean reported Harman variance %",
                round(harman_mean, 2),
                len(harman_values),
                "Arithmetic mean of numeric harman_variance_pct values.",
                filter_rule_fn(
                    "Studies with parseable numeric harman_variance_pct",
                    "parse_numeric(harman_variance_pct) is not None",
                ),
                harman_orders,
                ["Mean reported Harman variance %", f"{harman_mean:.2f}", f"n={len(harman_values)}"],
            ),
            metric_row(
                "harman.numeric_count",
                "Studies with numeric Harman variance %",
                len(harman_values),
                total,
                "Count of studies reporting a numeric Harman single-factor variance %.",
                filter_rule_fn(
                    "Studies with parseable numeric harman_variance_pct",
                    "parse_numeric(harman_variance_pct) is not None",
                ),
                harman_orders,
                ["Studies with numeric Harman variance %", str(len(harman_values)), pct(len(harman_values), total)],
            ),
        ]
        harman_note = (
            f"Mean of harman_variance_pct among {len(harman_values)} studies reporting a numeric value."
        )
    else:
        harman_rows = [
            metric_row(
                "harman.mean_pct",
                "Mean reported Harman variance %",
                "—",
                0,
                "Arithmetic mean of numeric harman_variance_pct values.",
                filter_rule_fn(
                    "Studies with parseable numeric harman_variance_pct",
                    "parse_numeric(harman_variance_pct) is not None",
                ),
                [],
                ["Mean reported Harman variance %", "—", "n=0"],
            ),
            metric_row(
                "harman.numeric_count",
                "Studies with numeric Harman variance %",
                0,
                total,
                "Count of studies reporting a numeric Harman single-factor variance %.",
                filter_rule_fn(
                    "Studies with parseable numeric harman_variance_pct",
                    "parse_numeric(harman_variance_pct) is not None",
                ),
                [],
                ["Studies with numeric Harman variance %", "0", pct(0, total)],
            ),
        ]
        harman_note = "No numeric harman_variance_pct values in fully coded corpus."

    harman_rows.append(spacer_row(3))
    harman_rows.append(
        metric_row(
            "harman_deployed.header",
            "Harman deployed (secondary)",
            "",
            total,
            "Section header for harman_deployed tristate counts.",
            {},
            [],
            ["Harman deployed (secondary)", "", ""],
        )
    )
    harman_rows.extend(
        count_tristate_metrics(
            studies,
            "harman_deployed",
            table_id="harman_deployed",
            total=total,
            field_label="harman_deployed",
        )
    )
    tables.append(
        summary_table(
            "harman_deployed",
            "Harman single-factor test",
            ["Statistic / deployment", "Value", "Count or %"],
            harman_rows,
            note=harman_note,
        )
    )

    ulmc_cross: dict[tuple[str, str], list[dict[str, str]]] = {}
    for s in studies:
        key = (
            normalize_tristate(s.get("ulmc_improves_fit")),
            normalize_tristate(s.get("ulmc_in_final")),
        )
        ulmc_cross.setdefault(key, []).append(s)
    ulmc_rows = [
        metric_row(
            f"ulmc_fit_cross.{a}_{b}",
            f"improves_fit={a}, in_final={b}",
            len(matched),
            total,
            f"Studies with ulmc_improves_fit={a} and ulmc_in_final={b}.",
            {
                "description": f"ulmc_improves_fit={a} AND ulmc_in_final={b}",
                "filter": {
                    "field": "ulmc_improves_fit",
                    "op": "eq",
                    "value": a,
                    "and": {"field": "ulmc_in_final", "op": "eq", "value": b},
                },
            },
            study_orders_for(matched),
            [f"improves_fit={a}, in_final={b}", str(len(matched)), pct(len(matched), total)],
        )
        for (a, b), matched in sorted(ulmc_cross.items(), key=lambda x: (-len(x[1]), x[0]))
    ]
    tables.append(
        summary_table(
            "ulmc_fit_cross",
            "ULMC fit and final model",
            ["ulmc_improves_fit × ulmc_in_final", "Count", "% of corpus"],
            ulmc_rows,
        )
    )

    remedies_used_studies = [
        s for s in studies if normalize_tristate(s.get("procedural_remedies_used")) == "TRUE"
    ]
    remedy_terms: dict[str, list[dict[str, str]]] = {}
    for s in studies:
        for term in split_terms(s.get("procedural_remedies_list")):
            remedy_terms.setdefault(term.lower(), []).append(s)
    remedy_rows: list[dict[str, Any]] = [
        metric_row(
            "procedural_remedies.any",
            "Any procedural remedy used",
            len(remedies_used_studies),
            total,
            "Studies where procedural_remedies_used is TRUE.",
            filter_rule_eq(
                "procedural_remedies_used",
                "TRUE",
                "procedural_remedies_used == TRUE",
            ),
            study_orders_for(remedies_used_studies),
            ["Any procedural remedy used", str(len(remedies_used_studies)), pct(len(remedies_used_studies), total)],
        ),
    ]
    source_remedy_fields: tuple[tuple[str, str], ...] = (
        ("multisource_same_construct", "Multisource — same construct (self + other)"),
        ("different_sources_iv_dv", "Different sources IV/DV (Podsakoff remedy)"),
        ("distinct_sources_other", "Distinct sources — other (archival, waves, levels)"),
    )
    for field, label in source_remedy_fields:
        matched = [s for s in studies if normalize_tristate(s.get(field)) == "TRUE"]
        remedy_rows.append(
            metric_row(
                f"procedural_remedies.{field}",
                label,
                len(matched),
                total,
                f"Studies where {field} is TRUE.",
                filter_rule_eq(field, "TRUE", f"{field} == TRUE"),
                study_orders_for(matched),
                [label, str(len(matched)), pct(len(matched), total)],
            )
        )
    for term, matched in sorted(remedy_terms.items(), key=lambda x: (-len(x[1]), x[0]))[:10]:
        remedy_rows.append(
            metric_row(
                f"procedural_remedies.{term.replace(' ', '_')}",
                term,
                len(matched),
                total,
                f"Studies listing '{term}' in procedural_remedies_list.",
                filter_rule_fn(
                    f"procedural_remedies_list contains '{term}'",
                    f"split_terms(procedural_remedies_list) includes {term!r}",
                ),
                study_orders_for(matched),
                [term, str(len(matched)), pct(len(matched), total)],
            )
        )
    if len(remedy_rows) == 1:
        remedy_rows.append(
            metric_row(
                "procedural_remedies.none_coded",
                "(no remedy terms coded)",
                0,
                total,
                "No procedural remedy terms found in procedural_remedies_list.",
                filter_rule_fn("No remedy terms in list", "procedural_remedies_list empty"),
                [],
                ["(no remedy terms coded)", "0", "0.0%"],
            )
        )
    tables.append(
        summary_table(
            "procedural_remedies",
            "Procedural remedies",
            ["Remedy / usage", "Count", "% of corpus"],
            remedy_rows,
        )
    )

    three_step_fields: tuple[tuple[str, str], ...] = (
        ("step1_presence_delta_chisq_reported", "Step 1 — presence/delta χ² reported"),
        ("step2_method_r_bias_test_reported", "Step 2 — trait/method-R bias test reported"),
        ("step3_contamination_reported", "Step 3 — indicator/construct MV reported"),
        ("three_step_complete", "Three-step procedure complete (Q2.29)"),
    )
    three_step_rows: list[dict[str, Any]] = []
    for field, label in three_step_fields:
        true_matched = [
            s for s in studies if normalize_tristate(s.get(field)) == "TRUE"
        ]
        three_step_rows.append(
            metric_row(
                f"three_step_procedure.{field}.TRUE",
                label,
                len(true_matched),
                total,
                f"Studies where {field} is TRUE.",
                filter_rule_eq(field, "TRUE", f"{field} == TRUE"),
                study_orders_for(true_matched),
                [label, str(len(true_matched)), pct(len(true_matched), total)],
            )
        )
    approach_used = [
        s for s in studies if normalize_tristate(s.get("three_step_approach_used")) == "TRUE"
    ]
    three_step_rows.append(
        metric_row(
            "three_step_procedure.three_step_approach_used.TRUE",
            "Three-step approach used (any step)",
            len(approach_used),
            total,
            "Studies where three_step_approach_used is TRUE.",
            filter_rule_eq(
                "three_step_approach_used",
                "TRUE",
                "three_step_approach_used == TRUE",
            ),
            study_orders_for(approach_used),
            [
                "Three-step approach used (any step)",
                str(len(approach_used)),
                pct(len(approach_used), total),
            ],
        )
    )
    tables.append(
        summary_table(
            "three_step_procedure",
            "Williams & McGonagle (2016) three-step ULMC procedure",
            ["Step / completion", "Count", "% of corpus"],
            three_step_rows,
            note="Step fields from extraction CSV (Q2.26–Q2.29). Blank cells count as not reported.",
        )
    )

    tables.append(
        summary_table(
            "richardson_2009_cited",
            "Richardson et al. (2009) citation",
            ["Value", "Count", "% of corpus"],
            count_tristate_metrics(
                studies,
                "richardson_2009_cited",
                table_id="richardson_2009_cited",
                total=total,
                field_label="richardson_2009_cited",
            ),
            note="Whether Richardson et al. (2009) is cited in methods or CMV discussion.",
        )
    )

    inference_rows = count_tristate_metrics(
        studies,
        "mv_inferred_not_problem",
        table_id="mv_inference",
        total=total,
        field_label="mv_inferred_not_problem",
    )
    criteria_terms: dict[str, list[dict[str, str]]] = {}
    for s in studies:
        for term in split_terms(s.get("mv_inference_criteria_list")):
            criteria_terms.setdefault(term.lower(), []).append(s)
    for term, matched in sorted(criteria_terms.items(), key=lambda x: (-len(x[1]), x[0]))[:10]:
        inference_rows.append(
            metric_row(
                f"mv_inference.criterion.{term.replace(' ', '_')}",
                f"criterion: {term}",
                len(matched),
                total,
                f"Studies listing '{term}' in mv_inference_criteria_list.",
                filter_rule_fn(
                    f"mv_inference_criteria_list contains '{term}'",
                    f"split_terms(mv_inference_criteria_list) includes {term!r}",
                ),
                study_orders_for(matched),
                [f"criterion: {term}", str(len(matched)), pct(len(matched), total)],
            )
        )
    tables.append(
        summary_table(
            "mv_inference",
            "MV inference (not a problem)",
            ["Category", "Count", "% of corpus"],
            inference_rows,
        )
    )

    tables.append(
        summary_table(
            "business_school_authors",
            "Authors at business school",
            ["Value", "Count", "% of corpus"],
            count_tristate_metrics(
                studies,
                "authors_business_school",
                table_id="business_school_authors",
                total=total,
                field_label="authors_business_school",
            ),
        )
    )

    outlet_priority = [o for o in PUBLISHER_OUTLETS if o != "NA"] + ["NA"]
    outlet_counts: Counter[str] = Counter()
    outlet_studies: dict[str, list[dict[str, str]]] = {o: [] for o in outlet_priority}
    for s in studies:
        outlet = (s.get("publisher_outlet") or "").strip()
        if not outlet or outlet.upper() == "NA":
            inferred, _ = infer_publisher_outlet(s.get("doi"), s.get("journal"))
            outlet = inferred
        outlet_counts[outlet] += 1
        outlet_studies.setdefault(outlet, []).append(s)

    non_mdpi_frontiers = sum(
        n for o, n in outlet_counts.items() if o not in ("MDPI", "Frontiers", "NA")
    )
    publisher_rows: list[dict[str, Any]] = []
    for outlet in outlet_priority:
        matched = outlet_studies.get(outlet, [])
        n = len(matched)
        if n == 0 and outlet not in ("MDPI", "Frontiers", "NA", "Other"):
            continue
        publisher_rows.append(
            metric_row(
                f"publisher_outlet.{outlet.replace(' ', '_').replace('/', '_')}",
                outlet,
                n,
                total,
                f"Studies with publisher_outlet = {outlet} (inferred from DOI/journal when CSV blank).",
                filter_rule_eq("publisher_outlet", outlet, f"publisher_outlet == {outlet}"),
                study_orders_for(matched),
                [outlet, str(n), pct(n, total)],
            )
        )
    if non_mdpi_frontiers:
        other_matched = [
            s
            for s in studies
            if (s.get("publisher_outlet") or infer_publisher_outlet(s.get("doi"), s.get("journal"))[0])
            not in ("MDPI", "Frontiers", "NA", "")
        ]
        publisher_rows.append(
            metric_row(
                "publisher_outlet.non_mdpi_frontiers",
                "Non-MDPI/Frontiers (combined)",
                non_mdpi_frontiers,
                total,
                "Sum of fully coded studies not published in MDPI or Frontiers outlets.",
                filter_rule_fn(
                    "publisher_outlet not in (MDPI, Frontiers, NA)",
                    "publisher_outlet not in ('MDPI', 'Frontiers', 'NA')",
                ),
                study_orders_for(other_matched),
                [
                    "Non-MDPI/Frontiers (combined)",
                    str(non_mdpi_frontiers),
                    pct(non_mdpi_frontiers, total),
                ],
            )
        )
    tables.append(
        summary_table(
            "publisher_outlet",
            "Publisher outlet (MDPI vs Frontiers vs other)",
            ["Outlet", "Count", "% of corpus"],
            publisher_rows,
            note="publisher_outlet from extraction CSV or inferred from DOI prefix / journal name.",
        )
    )

    tables.append(
        summary_table(
            "details_in_supplement",
            "Details in supplement (Q2.23)",
            ["Value", "Count", "% of corpus"],
            count_tristate_metrics(
                studies,
                "details_in_supplement",
                table_id="details_in_supplement",
                total=total,
                field_label="details_in_supplement",
            ),
            note="Authors refer to supplement/appendix for coding-relevant methods or results.",
        )
    )
    tables.append(
        summary_table(
            "extraction_incomplete_main_text",
            "Extraction incomplete in main text (Q2.24)",
            ["Value", "Count", "% of corpus"],
            count_tristate_metrics(
                studies,
                "extraction_incomplete_main_text",
                table_id="extraction_incomplete_main_text",
                total=total,
                field_label="extraction_incomplete_main_text",
            ),
            note="ULMC/MV/construct/Harman fields not fully in main PDF; coder must check supplement or cannot code.",
        )
    )

    mv_numeric: list[tuple[dict[str, str], float]] = []
    for s in studies:
        v = parse_numeric(s.get("method_variance_pct"))
        if v is not None:
            mv_numeric.append((s, v))
    mv_values = [v for _, v in mv_numeric]
    mv_orders = study_orders_for([s for s, _ in mv_numeric])
    if mv_values:
        mv_rows = [
            metric_row(
                "method_variance_pct.count",
                "n with numeric MV%",
                len(mv_values),
                total,
                "Studies with parseable numeric method_variance_pct.",
                filter_rule_fn(
                    "parse_numeric(method_variance_pct) is not None",
                    "parse_numeric(method_variance_pct) is not None",
                ),
                mv_orders,
                ["n with numeric MV%", str(len(mv_values)), pct(len(mv_values), total)],
            ),
            metric_row(
                "method_variance_pct.mean",
                "mean",
                round(statistics.mean(mv_values), 2),
                len(mv_values),
                "Mean of numeric method_variance_pct.",
                filter_rule_fn("mean of numeric method_variance_pct", "mean(method_variance_pct)"),
                mv_orders,
                ["mean", f"{statistics.mean(mv_values):.2f}", ""],
            ),
            metric_row(
                "method_variance_pct.median",
                "median",
                round(statistics.median(mv_values), 2),
                len(mv_values),
                "Median of numeric method_variance_pct.",
                filter_rule_fn("median of numeric method_variance_pct", "median(method_variance_pct)"),
                mv_orders,
                ["median", f"{statistics.median(mv_values):.2f}", ""],
            ),
            metric_row(
                "method_variance_pct.min",
                "min",
                round(min(mv_values), 2),
                len(mv_values),
                "Minimum numeric method_variance_pct.",
                filter_rule_fn("min of numeric method_variance_pct", "min(method_variance_pct)"),
                mv_orders,
                ["min", f"{min(mv_values):.2f}", ""],
            ),
            metric_row(
                "method_variance_pct.max",
                "max",
                round(max(mv_values), 2),
                len(mv_values),
                "Maximum numeric method_variance_pct.",
                filter_rule_fn("max of numeric method_variance_pct", "max(method_variance_pct)"),
                mv_orders,
                ["max", f"{max(mv_values):.2f}", ""],
            ),
        ]
        mv_note = f"Numeric values parsed from method_variance_pct ({len(mv_values)} of {total} studies)."
    else:
        mv_rows = [
            metric_row(
                "method_variance_pct.count",
                "n with numeric MV%",
                0,
                total,
                "Studies with parseable numeric method_variance_pct.",
                filter_rule_fn(
                    "parse_numeric(method_variance_pct) is not None",
                    "parse_numeric(method_variance_pct) is not None",
                ),
                [],
                ["n with numeric MV%", "0", "0.0%"],
            ),
        ]
        mv_note = "No numeric method_variance_pct values in fully coded corpus."
    tables.append(
        summary_table(
            "method_variance_pct",
            "Method variance %",
            ["Statistic", "Value", ""],
            mv_rows,
            note=mv_note,
        )
    )

    complexity_populated = [
        s for s in studies if parse_numeric(s.get("num_constructs")) is not None
    ]
    indicator_populated = [
        s for s in studies if parse_numeric(s.get("num_indicators")) is not None
    ]
    ratio_populated = [
        s for s in studies if parse_numeric(s.get("complexity_ratio")) is not None
    ]
    underpowered_true = [
        s for s in studies if normalize_tristate(s.get("underpowered_heuristic")) == "TRUE"
    ]
    underpowered_evaluable = [
        s
        for s in studies
        if normalize_tristate(s.get("underpowered_heuristic")) in ("TRUE", "FALSE")
    ]

    def mean_of(field: str, subset: list[dict[str, str]]) -> float | None:
        values = [parse_numeric(s.get(field)) for s in subset]
        nums = [v for v in values if v is not None]
        if not nums:
            return None
        return statistics.mean(nums)

    nc_mean = mean_of("num_constructs", complexity_populated)
    ni_mean = mean_of("num_indicators", indicator_populated)
    cr_mean = mean_of("complexity_ratio", ratio_populated)

    complexity_rows: list[dict[str, Any]] = [
        metric_row(
            "model_complexity.constructs_reported",
            "n with num_constructs",
            len(complexity_populated),
            total,
            "Studies with parseable num_constructs in extraction CSV.",
            filter_rule_fn(
                "parse_numeric(num_constructs) is not None",
                "parse_numeric(num_constructs) is not None",
            ),
            study_orders_for(complexity_populated),
            ["n with num_constructs", str(len(complexity_populated)), pct(len(complexity_populated), total)],
        ),
        metric_row(
            "model_complexity.indicators_reported",
            "n with num_indicators",
            len(indicator_populated),
            total,
            "Studies with parseable num_indicators in extraction CSV.",
            filter_rule_fn(
                "parse_numeric(num_indicators) is not None",
                "parse_numeric(num_indicators) is not None",
            ),
            study_orders_for(indicator_populated),
            ["n with num_indicators", str(len(indicator_populated)), pct(len(indicator_populated), total)],
        ),
    ]
    if nc_mean is not None:
        complexity_rows.append(
            metric_row(
                "model_complexity.mean_constructs",
                "mean constructs",
                round(nc_mean, 2),
                len(complexity_populated),
                "Mean num_constructs among studies with parseable value.",
                filter_rule_fn("mean(num_constructs)", "mean(num_constructs)"),
                study_orders_for(complexity_populated),
                ["mean constructs", f"{nc_mean:.2f}", ""],
            )
        )
    if ni_mean is not None:
        complexity_rows.append(
            metric_row(
                "model_complexity.mean_indicators",
                "mean indicators",
                round(ni_mean, 2),
                len(indicator_populated),
                "Mean num_indicators among studies with parseable value.",
                filter_rule_fn("mean(num_indicators)", "mean(num_indicators)"),
                study_orders_for(indicator_populated),
                ["mean indicators", f"{ni_mean:.2f}", ""],
            )
        )
    if cr_mean is not None:
        complexity_rows.append(
            metric_row(
                "model_complexity.mean_ratio",
                "mean complexity ratio",
                round(cr_mean, 2),
                len(ratio_populated),
                "Mean complexity_ratio (indicators per construct).",
                filter_rule_fn("mean(complexity_ratio)", "mean(complexity_ratio)"),
                study_orders_for(ratio_populated),
                ["mean complexity ratio", f"{cr_mean:.2f}", ""],
            )
        )
    complexity_rows.append(
        metric_row(
            "model_complexity.underpowered_heuristic",
            "underpowered heuristic TRUE",
            len(underpowered_true),
            len(underpowered_evaluable) or total,
            (
                "Coding-guidance flag TRUE when any of: num_indicators<15, "
                "complexity_ratio<3, num_constructs>10 (Richardson et al., 2009 / CFA practice)."
            ),
            filter_rule_fn(
                "underpowered_heuristic == TRUE",
                "underpowered_heuristic == TRUE",
            ),
            study_orders_for(underpowered_true),
            [
                "underpowered heuristic TRUE",
                str(len(underpowered_true)),
                pct(len(underpowered_true), len(underpowered_evaluable) or total),
            ],
        )
    )
    complexity_note = (
        "Model complexity fields from extraction CSV. underpowered_heuristic is derived "
        "(not a CSV column); see VARIABLE_CODEBOOK.md and AUDIT_RESULTS_METHODOLOGY.md §Model complexity."
    )
    tables.append(
        summary_table(
            "model_complexity",
            "Model complexity & ULMC power heuristic",
            ["Statistic", "Value", "Count or %"],
            complexity_rows,
            note=complexity_note,
        )
    )

    tables.append(
        summary_table(
            "management_domain",
            "Management domain",
            ["Value", "Count", "% of corpus"],
            count_tristate_metrics(
                studies,
                "management_domain",
                table_id="management_domain",
                total=total,
                field_label="management_domain",
            ),
        )
    )

    try:
        from journal_ulmc_table import (
            build_journal_ulmc_payload,
            journal_ulmc_summary_table,
        )

        journal_ulmc_counts = build_journal_ulmc_payload(
            results_payload,
            extraction_rows,
        )
        tables.append(journal_ulmc_summary_table(journal_ulmc_counts))
    except ImportError:
        pass

    now = results_payload.get("last_updated") or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()
    metric_count = count_audit_metrics(tables)
    out: dict[str, Any] = {
        "last_updated": now,
        "total_count": total,
        "table_count": len(tables),
        "metric_count": metric_count,
        "audit_version": 1,
        "tables": tables,
    }
    if journal_ulmc_counts is not None:
        out["journal_ulmc_counts"] = journal_ulmc_counts
    return out


def write_summary_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build progress_results_data.json for dashboard Results tab")
    parser.add_argument("--master", type=Path, default=MASTER_PATH)
    parser.add_argument("--extraction", type=Path, default=EXTRACTION_PATH)
    parser.add_argument("--output", type=Path, default=RESULTS_JSON)
    args = parser.parse_args()

    master = read_csv(args.master)
    extraction = load_combined_extraction_rows()
    if not master and not extraction:
        print("No master or extraction data found.", file=sys.stderr)
        sys.exit(1)

    payload = build_results_payload(master, extraction)
    write_results_json(args.output, payload)
    summary_payload = build_summary_payload(payload, extraction)
    write_summary_json(EXTRACTION_SUMMARY_JSON, summary_payload)
    print(
        f"Wrote {args.output.relative_to(ROOT)} — "
        f"{payload['total_count']} fully coded "
        f"(legacy={payload['legacy_count']}, ebsco_pool={payload['ebsco_pool_count']})"
    )
    print(
        f"Wrote {EXTRACTION_SUMMARY_JSON.relative_to(ROOT)} — "
        f"{summary_payload['table_count']} summary tables, "
        f"{summary_payload.get('metric_count', 0)} audit metrics"
    )


if __name__ == "__main__":
    main()
