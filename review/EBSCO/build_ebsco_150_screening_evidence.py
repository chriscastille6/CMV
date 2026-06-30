#!/usr/bin/env python3
"""
Build ebsco_150_screening_evidence.csv for the EBSCO 1–150 on-hand cohort.

Re-reads PDF text, applies Level 1 rules, captures quoted evidence snippets,
and writes structured decision_reason_code / decision_reason_text for verification.

Usage:
  python3 review/EBSCO/build_ebsco_150_screening_evidence.py
  python3 review/EBSCO/build_ebsco_150_screening_evidence.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
COHORT_PATH = EBSCO_DIR / "examination_cohort_on_hand.csv"
TEXT_DIR = EBSCO_DIR / "text"
OUTPUT_PATH = EBSCO_DIR / "ebsco_150_screening_evidence.csv"

sys.path.insert(0, str(EBSCO_DIR))
from ebsco_search_order import load_worklist_1_150_from_master  # noqa: E402
from parse_ebsco_fulltext_pdf import extract_text  # noqa: E402
from screen_level1_batch import (  # noqa: E402
    EMPIRICAL_PATTERNS,
    EXCLUDE_DOMAIN_KW,
    HARMAN_ONLY_PATTERNS,
    INCLUDE_DOMAIN_KW,
    MANAGEMENT_JOURNAL_HINTS,
    MARKER_ONLY_PATTERNS,
    PLS_PATTERNS,
    ULMC_PATTERNS,
    check_empirical_ulmc,
    check_management_domain,
    check_not_pls,
    derive_decision_reasons,
    load_csv,
    resolve_pdf_path,
)

OUTPUT_COLUMNS = [
    "master_id",
    "ebsco_search_position",
    "title",
    "screening_status",
    "Q1_1_management_domain",
    "Q1_2_empirical_ulmc",
    "Q1_3_not_pls",
    "decision",
    "confidence",
    "rationale",
    "q1_1_reason_code",
    "q1_1_reason_text",
    "q1_2_reason_code",
    "q1_2_reason_text",
    "q1_3_reason_code",
    "q1_3_reason_text",
    "decision_reason_code",
    "decision_reason_text",
    "evidence_type",
    "pdf_evidence_snippet",
    "text_file",
]


def _clean_snippet(text: str, max_len: int = 280) -> str:
    s = " ".join(text.replace("\n", " ").split())
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _context_snippet(full_text: str, match: re.Match[str], pad: int = 60) -> str:
    start = max(0, match.start() - pad)
    end = min(len(full_text), match.end() + pad)
    return _clean_snippet(full_text[start:end])


def _first_pattern_snippet(full_text: str, patterns: list[str]) -> tuple[str, re.Match[str] | None]:
    for pattern in patterns:
        m = re.search(pattern, full_text, re.I)
        if m:
            return _context_snippet(full_text, m), m
    return "", None


def infer_evidence_type(full_text: str, *, decision: str, pls_used: bool) -> str:
    if decision == "excluded_pls" or pls_used:
        return "pls"
    _, ulmc_m = _first_pattern_snippet(full_text, ULMC_PATTERNS)
    if ulmc_m:
        return "ulmc"
    _, harman_m = _first_pattern_snippet(full_text, HARMAN_ONLY_PATTERNS)
    if harman_m:
        return "harman"
    _, marker_m = _first_pattern_snippet(full_text, MARKER_ONLY_PATTERNS)
    if marker_m:
        return "marker"
    return "ulmc" if decision in ("included", "manual_review") else ""


def extract_pdf_evidence_snippet(
    full_text: str,
    *,
    q11: bool,
    q12: bool | None,
    q13: bool,
    pls_used: bool,
    decision: str,
) -> str:
    """Return raw PDF quote supporting the primary screening criterion."""
    if not full_text.strip():
        return ""

    if decision == "excluded_pls" or pls_used:
        snip, _ = _first_pattern_snippet(full_text, PLS_PATTERNS)
        if snip:
            return snip

    if not q11:
        hay = full_text.lower()[:8000]
        for kw in EXCLUDE_DOMAIN_KW + INCLUDE_DOMAIN_KW:
            idx = hay.find(kw.lower())
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(full_text), idx + len(kw) + 80)
                return _clean_snippet(full_text[start:end])
        return ""

    if q12 is False:
        for patterns in (HARMAN_ONLY_PATTERNS, MARKER_ONLY_PATTERNS, ULMC_PATTERNS):
            snip, _ = _first_pattern_snippet(full_text, patterns)
            if snip:
                return snip
        return ""

    snip, _ = _first_pattern_snippet(full_text, ULMC_PATTERNS)
    if snip:
        return snip
    snip, _ = _first_pattern_snippet(full_text, EMPIRICAL_PATTERNS)
    if snip:
        return snip

    if not q13:
        snip, _ = _first_pattern_snippet(full_text, PLS_PATTERNS)
        if snip:
            return snip

    return ""


def _text_file_for_pdf(pdf_path: Path | None, mid: str) -> str:
    if not pdf_path:
        return ""
    matches = list(TEXT_DIR.glob(f"EBSCO_{mid}_*.txt"))
    if matches:
        return matches[0].name
    stem = pdf_path.stem
    candidate = TEXT_DIR / f"{stem}.txt"
    return candidate.name if candidate.exists() else ""


def _screening_status(decision: str) -> str:
    if decision == "excluded":
        return "level1_fail"
    return decision


def _build_rationale(decision: str, q11: bool, q12: bool | None, q13: bool, q12_r: str, q13_r: str, q11_r: str) -> str:
    if q12 is None:
        return f"Q1.2 ambiguous: {q12_r}"
    if decision == "included":
        return "Q1.1–Q1.3 all pass"
    if decision == "manual_review" and q11 and q12 and q13:
        return "Low confidence include — verify manually. Q1.1–Q1.3 all pass"
    if decision == "excluded_pls":
        return f"PLS-SEM excluded (Q1.3): {q13_r}; domain={q11}; ulmc={q12}"
    fails = []
    if not q11:
        fails.append(f"Q1.1: {q11_r}")
    if q12 is False:
        fails.append(f"Q1.2: {q12_r}")
    if not q13:
        fails.append(f"Q1.3: {q13_r}")
    return "; ".join(fails) if fails else "Level 1 fail"


def screen_with_evidence(row: dict[str, str]) -> dict[str, str]:
    mid = row.get("article_id") or row.get("master_id", "")
    title = row.get("title") or ""
    abstract = row.get("abstract") or ""
    journal = row.get("journal") or ""
    ebsco_pos = (row.get("ebsco_search_position") or row.get("study_order") or "").strip()

    base = {
        "master_id": mid,
        "ebsco_search_position": ebsco_pos,
        "title": title,
        "screening_status": "pending",
        "Q1_1_management_domain": "",
        "Q1_2_empirical_ulmc": "",
        "Q1_3_not_pls": "",
        "decision": "pending",
        "confidence": "n/a",
        "rationale": "",
        "q1_1_reason_code": "",
        "q1_1_reason_text": "",
        "q1_2_reason_code": "",
        "q1_2_reason_text": "",
        "q1_3_reason_code": "",
        "q1_3_reason_text": "",
        "decision_reason_code": "PENDING",
        "decision_reason_text": "",
        "evidence_type": "",
        "pdf_evidence_snippet": "",
        "text_file": "",
    }

    pdf_path = resolve_pdf_path(row)
    if not pdf_path:
        ss = (row.get("screening_status") or "").strip()
        notes = (row.get("screening_notes") or "").strip()
        if ss and ss not in ("", "pending"):
            decision = "excluded" if ss == "level1_fail" else ss
            abstract_snip = _clean_snippet(abstract, 280) if abstract else "Metadata-only L1 decision"
            if "exclude_pls" in notes.lower() or ss == "excluded_pls":
                decision = "excluded_pls"
                code = "EXCLUDE_Q1_3_PLS"
            elif decision == "excluded":
                code = "EXCLUDE_Q1_1_DOMAIN_USER"
            elif decision == "included":
                code = "INCLUDE_ALL_CRITERIA_PASS"
            else:
                code = decision.upper()
            base.update(
                {
                    "screening_status": _screening_status(decision),
                    "decision": decision,
                    "confidence": "high",
                    "rationale": notes.split("User decision", 1)[-1].strip() if "User decision" in notes else notes,
                    "decision_reason_code": code,
                    "decision_reason_text": (
                        f"{notes} Decision: {decision} — metadata/user L1 (no PDF on disk)."
                    ),
                    "pdf_evidence_snippet": abstract_snip,
                    "evidence_type": "metadata",
                }
            )
            return base
        base["pdf_evidence_snippet"] = "PDF missing"
        base["decision_reason_text"] = "Decision: pending — PDF missing."
        return base

    try:
        full_text, _meta = extract_text(pdf_path)
    except Exception as exc:
        base["pdf_evidence_snippet"] = f"PDF extraction failed: {exc}"
        base["decision_reason_text"] = f"Decision: pending — PDF extraction failed: {exc}"
        return base

    if len(full_text.strip()) < 200:
        base["pdf_evidence_snippet"] = "Insufficient extracted text (<200 chars)"
        base["decision_reason_text"] = "Decision: pending — insufficient extracted text."
        return base

    q11, q11_r, q11_c = check_management_domain(title, abstract, journal, full_text)
    q12, q12_r, q12_c = check_empirical_ulmc(title, abstract, full_text)
    q13, pls_used, q13_r, q13_c = check_not_pls(title, abstract, full_text)

    confidences = [q11_c, q12_c, q13_c]
    overall_conf = "low" if "low" in confidences else ("medium" if "medium" in confidences else "high")

    if q12 is None:
        decision = "manual_review"
    elif q11 and q12 and q13:
        decision = "included"
    elif pls_used:
        decision = "excluded_pls"
    else:
        decision = "excluded"

    if overall_conf == "low" and decision == "included":
        decision = "manual_review"

    reasons = derive_decision_reasons(
        title=title,
        abstract=abstract,
        journal=journal,
        full_text=full_text,
        q11=q11,
        q11_r=q11_r,
        q11_c=q11_c,
        q12=q12,
        q12_r=q12_r,
        q12_c=q12_c,
        q13=q13,
        pls_used=pls_used,
        q13_r=q13_r,
        q13_c=q13_c,
        decision=decision,
        overall_conf=overall_conf,
    )

    evidence_type = infer_evidence_type(full_text, decision=decision, pls_used=pls_used)
    pdf_snippet = extract_pdf_evidence_snippet(
        full_text,
        q11=q11,
        q12=q12,
        q13=q13,
        pls_used=pls_used,
        decision=decision,
    )

    base.update(
        {
            "screening_status": _screening_status(decision),
            "Q1_1_management_domain": str(q11),
            "Q1_2_empirical_ulmc": str(q12) if q12 is not None else "",
            "Q1_3_not_pls": str(q13),
            "decision": decision,
            "confidence": overall_conf,
            "rationale": _build_rationale(decision, q11, q12, q13, q12_r, q13_r, q11_r),
            "evidence_type": evidence_type,
            "pdf_evidence_snippet": pdf_snippet,
            "text_file": _text_file_for_pdf(pdf_path, mid),
            **reasons,
        }
    )
    return base


def worklist_1_150_master_rows(master: list[dict[str, str]]) -> list[dict[str, str]]:
    """All export positions 1–150 joined to master (see ebsco_search_order)."""
    return load_worklist_1_150_from_master(master)


def build_evidence_rows(cohort_path: Path, master_path: Path) -> list[dict[str, str]]:
    _ = cohort_path  # retained for CLI compatibility
    master = load_csv(master_path)
    rows: list[dict[str, str]] = []
    for master_row in worklist_1_150_master_rows(master):
        rows.append(screen_with_evidence(master_row))
    rows.sort(
        key=lambda r: (
            int(r["ebsco_search_position"]) if (r.get("ebsco_search_position") or "").isdigit() else 9999,
            r.get("master_id", ""),
        )
    )
    return rows


def write_evidence_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EBSCO 1–150 screening evidence CSV")
    parser.add_argument("--cohort", type=Path, default=COHORT_PATH)
    parser.add_argument("--master", type=Path, default=MASTER_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = build_evidence_rows(args.cohort, args.master)
    scanned = sum(
        1
        for r in rows
        if r.get("decision") not in ("", "pending")
        and (r.get("pdf_evidence_snippet") or "").strip()
        and not (r.get("pdf_evidence_snippet") or "").startswith("PDF")
    )
    from collections import Counter

    decisions = Counter(r["decision"] for r in rows)
    print(f"Cohort rows: {len(rows)}")
    print(f"Scanned with evidence: {scanned}")
    for k in sorted(decisions.keys()):
        print(f"  {k}: {decisions[k]}")

    if args.dry_run:
        for mid in ("M0183", "M0244", "M0282"):
            row = next((r for r in rows if r["master_id"] == mid), None)
            if row:
                print(f"\n{mid}: {row['decision_reason_code']}")
                print(f"  {row['decision_reason_text'][:200]}…")
        return

    write_evidence_csv(rows, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
