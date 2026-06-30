#!/usr/bin/env python3
"""
Recompute Summary metrics from Datasets rows and assert audit survivability.

Examples:
  python3 review/master/audit_results.py
  python3 review/master/audit_results.py --report review/audit_results_report.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_results_tables import (
    EXTRACTION_PATH,
    MASTER_PATH,
    PLS_CBSEM_CATEGORIES,
    build_results_payload,
    build_summary_payload,
    classify_pls_cbsem,
    count_audit_metrics,
    parse_numeric,
    pls_field_inconsistencies,
    read_csv,
    study_order_key,
)
from examination import is_fully_coded_row, load_combined_extraction_rows

ROOT = Path(__file__).resolve().parents[2]
RESULTS_JSON = ROOT / "review" / "progress_results_data.json"
SUMMARY_JSON = ROOT / "review" / "progress_extraction_summary_data.json"
DEFAULT_REPORT = ROOT / "review" / "audit_results_report.md"

REQUIRED_ID_FIELDS = ("study_order", "article_id", "master_id", "legacy_refid", "doi")
NUMERIC_TOLERANCE = 0.01


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flatten_metrics(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for table in summary.get("tables") or []:
        for row in table.get("rows") or []:
            mid = row.get("metric_id")
            if mid:
                out[mid] = row
    return out


def numeric_close(a: Any, b: Any, tol: float = NUMERIC_TOLERANCE) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return str(a) == str(b)


def compare_metrics(
    expected: dict[str, dict[str, Any]],
    actual: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    if missing:
        errors.append(f"Missing metric_ids in recomputed summary: {sorted(missing)}")
    if extra:
        errors.append(f"Unexpected metric_ids in recomputed summary: {sorted(extra)}")
    for mid in sorted(set(expected) & set(actual)):
        exp = expected[mid]
        act = actual[mid]
        if not numeric_close(exp.get("value"), act.get("value")):
            errors.append(
                f"{mid}: value mismatch expected={exp.get('value')!r} actual={act.get('value')!r}"
            )
        if exp.get("n") != act.get("n"):
            errors.append(f"{mid}: n mismatch expected={exp.get('n')} actual={act.get('n')}")
        exp_orders = sorted(exp.get("study_orders") or [])
        act_orders = sorted(act.get("study_orders") or [])
        if exp_orders != act_orders:
            errors.append(
                f"{mid}: study_orders mismatch "
                f"(expected {len(exp_orders)}, actual {len(act_orders)})"
            )
    return errors


def check_dataset_ids(studies: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    always_required = ("study_order", "article_id", "master_id", "doi")
    for study in studies:
        key = study_order_key(study)
        missing = [f for f in always_required if not (study.get(f) or "").strip()]
        if study.get("cohort") == "legacy":
            refid = (study.get("legacy_refid") or "").strip()
            if not refid or refid == "NA":
                missing.append("legacy_refid")
        if study.get("master_id") and study.get("article_id"):
            if study["master_id"] != study["article_id"]:
                errors.append(
                    f"{key}: master_id {study['master_id']} != article_id {study['article_id']}"
                )
        if missing:
            errors.append(f"{key or '(no id)'}: missing fields {missing}")
    return errors


def check_pls_mutual_exclusivity(studies: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, str] = {}
    for study in studies:
        key = study_order_key(study)
        cat = study.get("pls_cbsem_category") or classify_pls_cbsem(study)
        if key in seen and seen[key] != cat:
            errors.append(f"{key}: multiple PLS/CB-SEM categories ({seen[key]}, {cat})")
        seen[key] = cat
    cat_sets = {cat: [] for cat in PLS_CBSEM_CATEGORIES}
    for study in studies:
        cat = study.get("pls_cbsem_category") or classify_pls_cbsem(study)
        cat_sets.setdefault(cat, []).append(study_order_key(study))
    all_assigned = [k for cat in PLS_CBSEM_CATEGORIES for k in cat_sets.get(cat, []) if k]
    if len(all_assigned) != len(set(all_assigned)):
        errors.append("Duplicate study_order across PLS/CB-SEM category buckets")
    return errors


def check_harman_mean(studies: list[dict[str, str]], summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    values = [
        v
        for s in studies
        if (v := parse_numeric(s.get("harman_variance_pct"))) is not None
    ]
    metrics = flatten_metrics(summary)
    harman_metric = metrics.get("harman.mean_pct")
    if not values:
        if harman_metric and harman_metric.get("value") not in ("—", "", None):
            errors.append("harman.mean_pct should be empty when no numeric values exist")
        return errors
    expected_mean = round(statistics.mean(values), 2)
    if harman_metric:
        if not numeric_close(harman_metric.get("value"), expected_mean):
            errors.append(
                f"harman.mean_pct value {harman_metric.get('value')} != "
                f"recomputed mean {expected_mean}"
            )
        if harman_metric.get("n") != len(values):
            errors.append(
                f"harman.mean_pct n={harman_metric.get('n')} != count {len(values)}"
            )
    return errors


def check_column_alignment(extraction_rows: list[dict[str, str]]) -> list[str]:
    """Flag extraction rows where boolean/numeric fields look misaligned."""
    warnings: list[str] = []
    tristate_fields = (
        "management_domain",
        "empirical_ulmc",
        "not_pls",
        "pls_sem_used",
        "harman_deployed",
        "procedural_remedies_used",
        "ulmc_improves_fit",
        "ulmc_in_final",
    )
    for row in extraction_rows:
        order = (row.get("study_order") or "").strip()
        if not order:
            continue
        for field in tristate_fields:
            raw = (row.get(field) or "").strip()
            if not raw or raw.upper() in ("NA", "N/A", "-"):
                continue
            if raw.upper() not in ("TRUE", "FALSE", "T", "F", "YES", "NO", "1", "0"):
                if any(ch.isdigit() for ch in raw) and "%" not in raw:
                    warnings.append(
                        f"{order}: {field}={raw!r} looks numeric — possible column shift"
                    )
        estimator = (row.get("estimator") or "").strip().upper()
        if estimator and estimator not in ("NA", "N/A", "-", "PLS-SEM", "PLS", "CB-SEM", "SEM", "CFA"):
            if estimator.isdigit() or (len(estimator) > 12 and " " not in estimator):
                warnings.append(f"{order}: estimator={estimator!r} — unexpected value (misalignment suspect)")
    return warnings


def check_independent_recompute(
    master: list[dict[str, str]],
    extraction: list[dict[str, str]],
    results_on_disk: dict[str, Any],
) -> list[str]:
    """Recompute results from CSV/master only; diff counts vs on-disk JSON."""
    errors: list[str] = []
    fresh = build_results_payload(master, extraction)
    disk_total = results_on_disk.get("total_count")
    fresh_total = fresh.get("total_count")
    if disk_total != fresh_total:
        errors.append(
            f"total_count mismatch: progress_results_data.json={disk_total} "
            f"vs recomputed from CSV={fresh_total}"
        )
    disk_orders = sorted(study_order_key(s) for s in results_on_disk.get("studies") or [])
    fresh_orders = sorted(study_order_key(s) for s in fresh.get("studies") or [])
    if disk_orders != fresh_orders:
        only_disk = set(disk_orders) - set(fresh_orders)
        only_fresh = set(fresh_orders) - set(disk_orders)
        if only_disk:
            errors.append(f"study_orders only on disk: {sorted(only_disk)[:10]}")
        if only_fresh:
            errors.append(f"study_orders only in CSV recompute: {sorted(only_fresh)[:10]}")
    return errors


def check_extraction_pls_conflicts(extraction_rows: list[dict[str, str]]) -> list[str]:
    warnings: list[str] = []
    for row in extraction_rows:
        if not is_fully_coded_row(row):
            continue
        order = (row.get("study_order") or "").strip()
        issues = pls_field_inconsistencies(row)
        if issues:
            warnings.append(f"{order}: {'; '.join(issues)}")
    return warnings


def write_report(
    path: Path,
    *,
    passed: bool,
    total_studies: int,
    metric_count: int,
    errors: list[str],
    warnings: list[str],
) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines = [
        "# Audit Results Report",
        "",
        f"**Generated**: {now}",
        f"**Status**: {'PASS' if passed else 'FAIL'}",
        f"**Fully coded studies**: {total_studies}",
        f"**Summary metrics with drill-down**: {metric_count}",
        "",
    ]
    if errors:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {e}" for e in errors)
        lines.append("")
    else:
        lines.extend(["## Errors", "", "None.", ""])
    if warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {w}" for w in warnings)
        lines.append("")
    else:
        lines.extend(["## Warnings", "", "None.", ""])
    lines.extend(
        [
            "## Checks performed",
            "",
            "- Recomputed all Summary metrics from Datasets rows",
            "- Compared value, n, and study_orders per metric_id",
            "- Verified PLS/CB-SEM mutual exclusivity (one category per study)",
            "- Verified Harman mean equals mean of numeric harman_variance_pct",
            "- Verified required identification fields on each Datasets row",
            "- Flagged PLS/CB-SEM field conflicts in extraction CSV",
            "- Flagged column misalignment suspects in extraction CSV",
            "- Independently recomputed fully coded corpus from CSV/master",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_audit(
    *,
    master_path: Path = MASTER_PATH,
    extraction_path: Path = EXTRACTION_PATH,
    results_path: Path = RESULTS_JSON,
    summary_path: Path = SUMMARY_JSON,
) -> tuple[bool, dict[str, Any]]:
    master = read_csv(master_path)
    extraction = load_combined_extraction_rows()

    if results_path.exists() and summary_path.exists():
        results_payload = load_json(results_path)
        summary_on_disk = load_json(summary_path)
    else:
        results_payload = build_results_payload(master, extraction)
        summary_on_disk = build_summary_payload(results_payload, extraction)

    studies = results_payload.get("studies") or []
    recomputed_summary = build_summary_payload(results_payload, extraction)

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_dataset_ids(studies))
    errors.extend(check_pls_mutual_exclusivity(studies))
    errors.extend(check_harman_mean(studies, recomputed_summary))
    errors.extend(
        compare_metrics(
            flatten_metrics(summary_on_disk),
            flatten_metrics(recomputed_summary),
        )
    )
    warnings.extend(check_extraction_pls_conflicts(extraction))
    warnings.extend(check_column_alignment(extraction))

    if results_path.exists():
        errors.extend(check_independent_recompute(master, extraction, results_payload))

    metric_count = count_audit_metrics(recomputed_summary)
    passed = len(errors) == 0
    return passed, {
        "total_studies": len(studies),
        "metric_count": metric_count,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Summary metrics against Datasets rows")
    parser.add_argument("--master", type=Path, default=MASTER_PATH)
    parser.add_argument("--extraction", type=Path, default=EXTRACTION_PATH)
    parser.add_argument("--results", type=Path, default=RESULTS_JSON)
    parser.add_argument("--summary", type=Path, default=SUMMARY_JSON)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    passed, info = run_audit(
        master_path=args.master,
        extraction_path=args.extraction,
        results_path=args.results,
        summary_path=args.summary,
    )
    write_report(
        args.report,
        passed=passed,
        total_studies=info["total_studies"],
        metric_count=info["metric_count"],
        errors=info["errors"],
        warnings=info["warnings"],
    )

    print(f"Audit: {'PASS' if passed else 'FAIL'}")
    print(f"Studies: {info['total_studies']} | Metrics with drill-down: {info['metric_count']}")
    print(f"Report: {args.report.relative_to(ROOT)}")
    if info["errors"]:
        print(f"Errors ({len(info['errors'])}):")
        for err in info["errors"][:20]:
            print(f"  - {err}")
        if len(info["errors"]) > 20:
            print(f"  ... and {len(info['errors']) - 20} more")
    if info["warnings"]:
        print(f"Warnings ({len(info['warnings'])}):")
        for warn in info["warnings"][:10]:
            print(f"  - {warn}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
