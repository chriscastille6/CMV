#!/usr/bin/env python3
"""
Generate extraction feedback report from correction log vs pipeline hints.

Compares logged corrections to enhanced_extraction_results.csv (pipeline pre-fill)
and current systematic_extraction_40_studies.csv values.

Outputs:
  review/EBSCO/extraction_feedback_report.md
  review/EBSCO/extraction_feedback_summary.csv

Run after batch coding sessions. Does NOT modify pipeline regex.

Usage:
  python3 review/EBSCO/extraction_feedback_report.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

EBSCO_DIR = Path(__file__).resolve().parent
CORRECTIONS_PATH = EBSCO_DIR / "extraction_corrections.csv"
EXTRACTION_PATH = EBSCO_DIR / "systematic_extraction_40_studies.csv"
PIPELINE_PATH = EBSCO_DIR / "enhanced_extraction_results.csv"
REPORT_PATH = EBSCO_DIR / "extraction_feedback_report.md"
SUMMARY_PATH = EBSCO_DIR / "extraction_feedback_summary.csv"

# Pipeline column -> extraction CSV column (when names differ)
PIPELINE_FIELD_MAP = {
    "order": "study_order",
}


def norm(value: object) -> str:
    if value is None:
        return "NA"
    s = str(value).strip()
    return s if s else "NA"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pipeline_row_by_order(rows: list[dict], study_order: str) -> dict | None:
    target = norm(study_order)
    for row in rows:
        order = norm(row.get("order", row.get("study_order", "")))
        if order == target:
            return row
    return None


def extraction_row_by_order(rows: list[dict], study_order: str) -> dict | None:
    target = norm(study_order)
    for row in rows:
        if norm(row.get("study_order", "")) == target:
            return row
    return None


def pipeline_hint(pipeline_row: dict | None, field_name: str) -> str:
    if not pipeline_row:
        return "NA"
    if field_name in pipeline_row:
        return norm(pipeline_row[field_name])
    return "NA"


def build_summary(corrections: list[dict], pipeline_rows: list[dict], extraction_rows: list[dict]) -> list[dict]:
    summary: list[dict] = []
    for corr in corrections:
        study_order = norm(corr.get("study_order", ""))
        field_name = norm(corr.get("field_name", ""))
        old_value = norm(corr.get("old_value", ""))
        new_value = norm(corr.get("new_value", ""))
        pipe_row = pipeline_row_by_order(pipeline_rows, study_order)
        ext_row = extraction_row_by_order(extraction_rows, study_order)
        hint = pipeline_hint(pipe_row, field_name)
        current = norm(ext_row.get(field_name, "")) if ext_row else "NA"

        if hint == "NA":
            pipeline_match = "no_pipeline_field"
        elif hint == old_value:
            pipeline_match = "matched_old"
        elif hint == new_value:
            pipeline_match = "matched_new"
        else:
            pipeline_match = "discordant"

        csv_matches_correction = current == new_value

        summary.append(
            {
                "correction_id": corr.get("correction_id", ""),
                "corrected_at": corr.get("corrected_at", ""),
                "study_order": study_order,
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value,
                "source": corr.get("source", ""),
                "pipeline_hint": hint,
                "pipeline_match": pipeline_match,
                "csv_current_value": current,
                "csv_matches_correction": str(csv_matches_correction),
            }
        )
    return summary


def write_summary_csv(rows: list[dict]) -> None:
    if not rows:
        columns = [
            "correction_id",
            "corrected_at",
            "study_order",
            "field_name",
            "old_value",
            "new_value",
            "source",
            "pipeline_hint",
            "pipeline_match",
            "csv_current_value",
            "csv_matches_correction",
        ]
    else:
        columns = list(rows[0].keys())
    with SUMMARY_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    corrections: list[dict],
    summary_rows: list[dict],
    field_counts: Counter,
    study_counts: Counter,
    top_fields: list[tuple[str, int]],
) -> None:
    lines = [
        "# Extraction Feedback Report",
        "",
        f"**Generated**: {date.today().isoformat()}",
        "",
        "Compares logged corrections against `enhanced_extraction_results.csv` pipeline hints "
        "and current `systematic_extraction_40_studies.csv` values.",
        "",
        "> **Note**: This report is read-only. Pipeline regex is not auto-updated from corrections.",
        "",
        "## Summary",
        "",
        f"- **Total corrections logged**: {len(corrections)}",
        f"- **Distinct fields corrected**: {len(field_counts)}",
        f"- **Studies with corrections**: {len(study_counts)}",
        "",
        "## Fields corrected most often",
        "",
        "| Rank | field_name | count |",
        "|------|------------|------:|",
    ]

    for i, (field, count) in enumerate(top_fields[:10], start=1):
        lines.append(f"| {i} | `{field}` | {count} |")

    if not top_fields:
        lines.append("| — | *(none yet)* | 0 |")

    lines.extend(
        [
            "",
            "## Top 5 fields — candidates for future regex updates",
            "",
        ]
    )
    for field, count in top_fields[:5]:
        lines.append(f"- `{field}` ({count} correction{'s' if count != 1 else ''})")
    if not top_fields:
        lines.append("- *(none yet)*")

    lines.extend(
        [
            "",
            "## Studies with most corrections",
            "",
            "| study_order | corrections |",
            "|-------------|------------:|",
        ]
    )
    for study_order, count in study_counts.most_common(15):
        lines.append(f"| {study_order} | {count} |")
    if not study_counts:
        lines.append("| — | 0 |")

    lines.extend(
        [
            "",
            "## Pipeline hint alignment",
            "",
            "| pipeline_match | count | meaning |",
            "|----------------|------:|---------|",
        ]
    )
    match_counts = Counter(r["pipeline_match"] for r in summary_rows)
    meanings = {
        "matched_old": "Pipeline pre-fill matched the value we replaced",
        "matched_new": "Pipeline already had the corrected value",
        "discordant": "Pipeline hint differs from both old and new",
        "no_pipeline_field": "Field not in pipeline output or no pipeline row",
    }
    for key in ["matched_old", "matched_new", "discordant", "no_pipeline_field"]:
        if match_counts.get(key, 0):
            lines.append(f"| {key} | {match_counts[key]} | {meanings[key]} |")

    lines.extend(
        [
            "",
            "## Correction detail",
            "",
            "| id | date | study | field | old → new | pipeline_hint | match |",
            "|----|------|-------|-------|-----------|---------------|-------|",
        ]
    )
    for row in summary_rows:
        lines.append(
            f"| {row['correction_id']} | {row['corrected_at']} | {row['study_order']} | "
            f"`{row['field_name']}` | {row['old_value']} → {row['new_value']} | "
            f"{row['pipeline_hint']} | {row['pipeline_match']} |"
        )

    lines.extend(
        [
            "",
            "## Workflow reminder",
            "",
            "1. Run `enhanced_extraction_pipeline.R` for pre-fill hints",
            "2. Human-code using `SYSTEMATIC_EXTRACTION_TEMPLATE.md`",
            "3. Log overrides: `log_extraction_correction.py`",
            "4. Re-run this report after batch sessions",
            "",
            f"Machine-readable detail: `{SUMMARY_PATH.name}`",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    corrections = read_csv(CORRECTIONS_PATH)
    pipeline_rows = read_csv(PIPELINE_PATH)
    extraction_rows = read_csv(EXTRACTION_PATH)

    summary_rows = build_summary(corrections, pipeline_rows, extraction_rows)
    write_summary_csv(summary_rows)

    field_counts = Counter(norm(c.get("field_name", "")) for c in corrections)
    study_counts = Counter(norm(c.get("study_order", "")) for c in corrections)
    top_fields = field_counts.most_common()

    write_report(corrections, summary_rows, field_counts, study_counts, top_fields)

    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Corrections: {len(corrections)} | Fields: {len(field_counts)} | Studies: {len(study_counts)}")
    if top_fields[:5]:
        print("Top fields:", ", ".join(f"{f}({n})" for f, n in top_fields[:5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
