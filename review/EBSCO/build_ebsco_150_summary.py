"""Build EBSCO 1–150 scoped extraction summary JSON for the progress dashboard."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MASTER_DIR = ROOT / "review" / "master"
if str(MASTER_DIR) not in sys.path:
    sys.path.insert(0, str(MASTER_DIR))

from build_results_tables import (  # noqa: E402
    build_extraction_indexes,
    build_study_record,
    build_summary_payload,
    classify_cohort,
    lookup_extraction_row,
    normalize_tristate,
    parse_numeric,
)
from examination import (  # noqa: E402
    count_filled_fields,
    is_fully_coded_row,
    is_master_id_key,
    is_partially_coded_row,
)

EVIDENCE_PATH = ROOT / "review" / "EBSCO" / "ebsco_150_screening_evidence.csv"
SUMMARY_JSON = ROOT / "review" / "progress_ebsco_150_summary_data.json"

PREVALENCE_METRICS: tuple[tuple[str, str], ...] = (
    ("harman_deployed", "Harman deployed"),
    ("three_step_complete", "Three-step complete"),
    ("procedural_remedies_used", "Procedural remedies used"),
    ("richardson_2009_cited", "Richardson (2009) cited"),
    ("ulmc_in_final", "ULMC in final model"),
    ("empirical_ulmc", "Empirical ULMC"),
)

THREE_STEP_CHART_FIELDS: tuple[tuple[str, str], ...] = (
    ("step1_presence_delta_chisq_reported", "Step 1 χ²"),
    ("step2_method_r_bias_test_reported", "Step 2 method-R"),
    ("step3_contamination_reported", "Step 3 MV reported"),
    ("three_step_complete", "All steps complete"),
)

MV_HISTOGRAM_BINS: tuple[tuple[str, float, float | None], ...] = (
    ("0–5%", 0.0, 5.0),
    ("5–10%", 5.0, 10.0),
    ("10–20%", 10.0, 20.0),
    ("20–30%", 20.0, 30.0),
    ("30%+", 30.0, None),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_worklist_ids(evidence_path: Path = EVIDENCE_PATH) -> list[str]:
    rows = read_csv(evidence_path)
    return [
        (r.get("master_id") or "").strip()
        for r in rows
        if (r.get("master_id") or "").strip()
    ]


def load_included_ids(evidence_path: Path = EVIDENCE_PATH) -> set[str]:
    rows = read_csv(evidence_path)
    return {
        (r.get("master_id") or "").strip()
        for r in rows
        if (r.get("decision") or "").strip().lower() == "included"
        and (r.get("master_id") or "").strip()
    }


def subset_results_payload(
    results_payload: dict[str, Any],
    article_ids: set[str],
) -> dict[str, Any]:
    studies = [
        s
        for s in results_payload.get("studies") or []
        if (s.get("article_id") or s.get("master_id") or "") in article_ids
    ]
    legacy = [s for s in studies if s.get("cohort") == "legacy"]
    pool = [s for s in studies if s.get("cohort") == "ebsco_pool"]
    other = [s for s in studies if s.get("cohort") == "other"]
    return {
        **results_payload,
        "total_count": len(studies),
        "legacy_count": len(legacy),
        "ebsco_pool_count": len(pool),
        "other_count": len(other),
        "studies": studies,
        "legacy_studies": legacy,
        "ebsco_pool_studies": pool,
        "other_studies": other,
    }


def build_scoped_studies(
    master: list[dict[str, str]],
    extraction_rows: list[dict[str, str]],
    article_ids: set[str],
    *,
    min_fields: int,
) -> list[dict[str, str]]:
    master_by_id = {r.get("article_id", ""): r for r in master if r.get("article_id")}
    by_order, by_doi = build_extraction_indexes(extraction_rows)
    studies: list[dict[str, str]] = []

    for mid in sorted(article_ids):
        rec = master_by_id.get(mid)
        ext_row = lookup_extraction_row(rec, by_order, by_doi) if rec else None
        if not ext_row and is_master_id_key(mid):
            ext_row = by_order.get(mid)
        if not ext_row or count_filled_fields(ext_row) < min_fields:
            continue
        coded_via = "extraction:key_fields>=" + str(min_fields)
        if rec and rec.get("examination_status") == "fully_coded":
            coded_via = "master:fully_coded"
        elif is_fully_coded_row(ext_row):
            coded_via = "extraction:key_fields>=4"
        study = build_study_record(
            rec,
            ext_row,
            cohort=classify_cohort(rec),
            coded_via=coded_via,
        )
        studies.append(study)

    studies.sort(key=lambda s: (s.get("year") or "0", (s.get("title") or "").lower()), reverse=True)
    return studies


def merge_study_field(study: dict[str, str], ext_row: dict[str, str] | None, field: str) -> str:
    val = (study.get(field) or "").strip()
    if val and normalize_tristate(val) != "NA":
        return val
    if ext_row:
        return (ext_row.get(field) or "").strip()
    return val


def build_prevalence_charts(
    studies: list[dict[str, str]],
    extraction_rows: list[dict[str, str]],
    article_ids: set[str],
) -> list[dict[str, Any]]:
    by_order, _by_doi = build_extraction_indexes(extraction_rows)
    ext_by_mid: dict[str, dict[str, str]] = {}
    for row in extraction_rows:
        key = (row.get("study_order") or row.get("master_id") or "").strip()
        if key in article_ids:
            ext_by_mid[key] = row

    total = len(studies) or len(article_ids)
    if not total:
        return []

    bars: list[dict[str, Any]] = []
    for field, label in PREVALENCE_METRICS:
        true_count = 0
        for study in studies:
            mid = study.get("article_id") or study.get("master_id") or ""
            ext = ext_by_mid.get(mid)
            val = merge_study_field(study, ext, field)
            if normalize_tristate(val) == "TRUE":
                true_count += 1
        pct = round(100 * true_count / len(studies), 1) if studies else 0.0
        bars.append(
            {
                "metric_id": field,
                "label": label,
                "count": true_count,
                "total": len(studies),
                "pct": pct,
            }
        )
    return bars


def build_three_step_chart(
    studies: list[dict[str, str]],
    extraction_rows: list[dict[str, str]],
    article_ids: set[str],
) -> list[dict[str, Any]]:
    ext_by_mid: dict[str, dict[str, str]] = {}
    for row in extraction_rows:
        key = (row.get("study_order") or row.get("master_id") or "").strip()
        if key in article_ids:
            ext_by_mid[key] = row
    total = len(studies)
    if not total:
        return []
    bars: list[dict[str, Any]] = []
    for field, label in THREE_STEP_CHART_FIELDS:
        true_count = 0
        for study in studies:
            mid = study.get("article_id") or study.get("master_id") or ""
            ext = ext_by_mid.get(mid)
            val = merge_study_field(study, ext, field)
            if normalize_tristate(val) == "TRUE":
                true_count += 1
        bars.append(
            {
                "metric_id": field,
                "label": label,
                "count": true_count,
                "total": total,
                "pct": round(100 * true_count / total, 1) if total else 0.0,
            }
        )
    return bars


def build_mv_histogram(
    studies: list[dict[str, str]],
    extraction_rows: list[dict[str, str]],
    article_ids: set[str],
) -> dict[str, Any]:
    ext_by_mid: dict[str, dict[str, str]] = {}
    for row in extraction_rows:
        key = (row.get("study_order") or row.get("master_id") or "").strip()
        if key in article_ids:
            ext_by_mid[key] = row
    values: list[float] = []
    for study in studies:
        mid = study.get("article_id") or study.get("master_id") or ""
        ext = ext_by_mid.get(mid)
        raw = merge_study_field(study, ext, "method_variance_pct")
        v = parse_numeric(raw)
        if v is not None:
            values.append(v)
    bins: list[dict[str, Any]] = []
    for label, lo, hi in MV_HISTOGRAM_BINS:
        if hi is None:
            matched = [v for v in values if v >= lo]
        else:
            matched = [v for v in values if lo <= v < hi]
        bins.append({"label": label, "count": len(matched)})
    return {
        "n_numeric": len(values),
        "total": len(studies),
        "bins": bins,
    }


def build_temporal_trends(studies: list[dict[str, str]]) -> list[dict[str, Any]]:
    year_counts: dict[str, int] = {}
    for study in studies:
        year = (study.get("year") or "").strip()
        if not year or year.upper() == "NA":
            continue
        year_counts[year] = year_counts.get(year, 0) + 1
    return [
        {"year": year, "count": count}
        for year, count in sorted(year_counts.items())
    ]


def build_scope_visuals(
    studies: list[dict[str, str]],
    extraction_rows: list[dict[str, str]],
    article_ids: set[str],
) -> dict[str, Any]:
    return {
        "three_step_chart": build_three_step_chart(studies, extraction_rows, article_ids),
        "mv_histogram": build_mv_histogram(studies, extraction_rows, article_ids),
        "temporal_trends": build_temporal_trends(studies),
    }


def compute_coding_counts(
    master: list[dict[str, str]],
    extraction_rows: list[dict[str, str]],
    worklist_ids: list[str],
    included_ids: set[str],
) -> dict[str, int]:
    master_by_id = {r.get("article_id", ""): r for r in master if r.get("article_id")}
    by_order, by_doi = build_extraction_indexes(extraction_rows)

    fully_coded = 0
    partial_included = 0

    for mid in worklist_ids:
        rec = master_by_id.get(mid)
        ext_row = lookup_extraction_row(rec, by_order, by_doi) if rec else by_order.get(mid)
        is_full = bool(
            rec
            and rec.get("examination_status") == "fully_coded"
            or (ext_row and is_fully_coded_row(ext_row))
        )
        if is_full:
            fully_coded += 1
        elif mid in included_ids and ext_row and is_partially_coded_row(ext_row):
            partial_included += 1

    return {
        "screened": len(worklist_ids),
        "l1_included": len(included_ids),
        "fully_coded": fully_coded,
        "partial_coded": partial_included,
        "included_with_coding": sum(
            1
            for mid in included_ids
            if (
                (master_by_id.get(mid) and master_by_id[mid].get("examination_status") == "fully_coded")
                or (
                    (ext := lookup_extraction_row(master_by_id.get(mid), by_order, by_doi) or by_order.get(mid))
                    and is_partially_coded_row(ext)
                )
            )
        ),
    }


def build_l1_funnel(worklist_metrics: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not worklist_metrics:
        return []
    items = [
        ("Included", int(worklist_metrics.get("included", 0))),
        ("Excluded (eligibility)", int(worklist_metrics.get("excluded", 0))),
        ("Excluded (PLS-SEM)", int(worklist_metrics.get("excluded_pls", 0))),
    ]
    total = sum(n for _, n in items) or 1
    return [{"label": label, "count": count, "pct": round(100 * count / total, 1)} for label, count in items]


def build_ebsco_150_summary_payload(
    master: list[dict[str, str]],
    results_payload: dict[str, Any],
    extraction_rows: list[dict[str, str]],
    evidence_path: Path = EVIDENCE_PATH,
    worklist_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    worklist_ids = load_worklist_ids(evidence_path)
    worklist_set = set(worklist_ids)
    included_ids = load_included_ids(evidence_path)

    coding_counts = compute_coding_counts(master, extraction_rows, worklist_ids, included_ids)

    fully_coded_payload = subset_results_payload(results_payload, worklist_set)
    fully_coded_summary = build_summary_payload(fully_coded_payload, extraction_rows)

    included_studies = build_scoped_studies(
        master,
        extraction_rows,
        included_ids,
        min_fields=2,
    )
    included_payload = {
        **results_payload,
        "total_count": len(included_studies),
        "studies": included_studies,
        "legacy_studies": [s for s in included_studies if s.get("cohort") == "legacy"],
        "ebsco_pool_studies": [s for s in included_studies if s.get("cohort") == "ebsco_pool"],
        "other_studies": [s for s in included_studies if s.get("cohort") == "other"],
    }
    included_summary = build_summary_payload(included_payload, extraction_rows)

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "last_updated": now,
        "strand": "ebsco_worklist_positions_1_150_extraction",
        "evidence_csv_path": str(evidence_path.relative_to(ROOT)),
        "coding_counts": coding_counts,
        "l1_funnel": build_l1_funnel(worklist_metrics),
        "scopes": {
            "fully_coded_1_150": {
                "label": "Fully coded in EBSCO 1–150 worklist",
                "n": coding_counts["fully_coded"],
                "summary": fully_coded_summary,
                "prevalence_charts": build_prevalence_charts(
                    fully_coded_payload.get("studies") or [],
                    extraction_rows,
                    worklist_set,
                ),
                "visuals": build_scope_visuals(
                    fully_coded_payload.get("studies") or [],
                    extraction_rows,
                    worklist_set,
                ),
            },
            "l1_included_coded": {
                "label": "L1 included with extraction coding (partial or full)",
                "n": coding_counts["included_with_coding"],
                "summary": included_summary,
                "prevalence_charts": build_prevalence_charts(
                    included_studies,
                    extraction_rows,
                    included_ids,
                ),
                "visuals": build_scope_visuals(
                    included_studies,
                    extraction_rows,
                    included_ids,
                ),
            },
        },
    }


def write_ebsco_150_summary_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def main() -> None:
    from build_results_tables import MASTER_PATH, build_results_payload, read_csv as br_read_csv
    from examination import load_combined_extraction_rows

    master = br_read_csv(MASTER_PATH)
    extraction_rows = load_combined_extraction_rows()
    results_payload = build_results_payload(master, extraction_rows)
    payload = build_ebsco_150_summary_payload(master, results_payload, extraction_rows)
    write_ebsco_150_summary_json(SUMMARY_JSON, payload)
    cc = payload["coding_counts"]
    print(
        f"Wrote {SUMMARY_JSON.relative_to(ROOT)} — "
        f"screened={cc['screened']} included={cc['l1_included']} "
        f"fully_coded={cc['fully_coded']} partial={cc['partial_coded']}"
    )


if __name__ == "__main__":
    main()
