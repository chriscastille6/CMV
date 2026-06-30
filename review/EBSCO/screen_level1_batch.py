#!/usr/bin/env python3
"""
Level 1 eligibility screening (Q1.4, Q1.1–Q1.3) for EBSCO-ingested articles.

Reads PDF text, applies config.yaml Level 1 rules, updates articles_master.csv
(with file locking), and writes a batch screening CSV.

Usage:
  python3 review/EBSCO/screen_level1_batch.py --batch-date 2026-06-24
  python3 review/EBSCO/screen_level1_batch.py --master-id M0184 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import re
import sys
from contextlib import contextmanager
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EBSCO_DIR = Path(__file__).resolve().parent
MASTER_PATH = ROOT / "review" / "master" / "articles_master.csv"
MASTER_LOCK_PATH = MASTER_PATH.with_suffix(".csv.lock")
INGEST_LOG = EBSCO_DIR / "pdfs" / "INGEST_LOG.csv"
PDF_DIR = EBSCO_DIR / "pdfs"

sys.path.insert(0, str(EBSCO_DIR))
from parse_ebsco_fulltext_pdf import extract_text  # noqa: E402

# --- Q1.1 management domain (from 02_ai_validation_screening.R) ---
INCLUDE_DOMAIN_KW = [
    "management", "leadership", "employee", "organization", "organisation",
    "workplace", "human resource", "hrm", "personnel", "job", "work", "staff",
    "organizational behavior", "organisational behaviour", "applied psychology",
    "business ethics", "strategy", "strategic", "performance management",
    "occupational", "vocational", "industrial-organizational", "industrial organisational",
    "entrepreneur", "supervisor", "team", "organizational citizenship",
    "public administration", "nonprofit", "non-profit",
]

EXCLUDE_DOMAIN_KW = [
    "information system", "advertising", "social media marketing",
    "consumer behavior", "consumer behaviour", "brand equity",
    "retail marketing", "tourism marketing", "health care informatics",
    "clinical psychology", "psychiatric", "neuroscience", "medicine",
    "nursing", "pharmacology", "education technology", "k-12",
    "computer science", "machine learning", "deep learning",
]

MANAGEMENT_JOURNAL_HINTS = [
    "journal of applied psychology", "journal of organizational behavior",
    "journal of organisational behaviour", "journal of management",
    "academy of management", "personnel psychology", "human relations",
    "human resource", "leadership quarterly", "organizational research methods",
    "journal of business", "business ethics", "management science",
    "european journal of work", "work and stress", "group & organization",
    "group and organization", "international journal of selection",
    "public administration", "nonprofit", "voluntas",
    "applied psychology", "psychology of sport", "sport management",
    "tourism management", "hospitality", "service industry",
    "employee relations", "industrial marketing management",
]

# --- Q1.2 empirical ULMC ---
ULMC_PATTERNS = [
    r"unmeasured\s+latent\s+method\s+(?:construct|factor|variable)",
    r"\bulmc\b",
    r"common\s+latent\s+factor",
    r"single\s+method\s+factor",
    r"method\s+factor\s+model",
    r"williams\s+and\s+mcgonagle",
    r"richardson\s+et\s+al\.?\s*\(\s*2009\s*\).*ulmc",
]

HARMAN_ONLY_PATTERNS = [
    r"harman['']?s?\s+(?:single[- ]factor|one[- ]factor)",
    r"harman\s+test",
    r"exploratory\s+factor\s+analysis.*harman",
]

MARKER_ONLY_PATTERNS = [
    r"marker\s+variable",
    r"marker\s+technique",
    r"cfa\s+marker",
    r"correlational\s+marker",
    r"linguistic\s+marker",
]

EMPIRICAL_PATTERNS = [
    r"\bsurvey\b", r"\bsample\b", r"\bparticipant", r"\brespondent",
    r"data\s+(?:were|was)\s+collect", r"\bempirical\b",
    r"\bcfa\b", r"\bsem\b", r"structural\s+equation",
    r"\bn\s*=\s*\d", r"\b\d+\s+employee",
]

NON_EMPIRICAL_PATTERNS = [
    r"\bsimulation\b", r"monte\s+carlo", r"synthetic\s+data",
    r"\bmeta[- ]analy", r"\bsystematic\s+review\b", r"\bconceptual\b",
    r"\btheoretical\s+(?:paper|framework|model)\b", r"\bnarrative\s+review\b",
]

PLS_PATTERNS = [
    r"partial\s+least\s+squares?",
    r"\bpls[- ]sem\b", r"\bpls\s+sem\b",
    r"\bsmartpls\b", r"component[- ]based\s+sem",
    r"\bplsc\b", r"consistent\s+pls",
    r"\bpls\s+path\s+model",
]

# --- Q1.4 publisher retraction (evaluated before Q1.1–Q1.3) ---
RETRACTION_TITLE_PATTERNS = [
    r"^retracted\s*:",
    r"^retracted\s+article\s*:",
]

RETRACTION_TEXT_PATTERNS = [
    r"\bthis\s+article\s+has\s+been\s+retracted\b",
    r"\bnotice\s+of\s+retraction\b",
    r"\bretraction\s+notice\b",
    r"\bpublisher'?s?\s+note\b.*\bretracted\b",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@contextmanager
def master_file_lock():
    MASTER_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MASTER_LOCK_PATH, "w", encoding="utf-8") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def write_master(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with open(MASTER_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def any_match(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def count_matches(text: str, patterns: list[str]) -> int:
    return sum(1 for p in patterns if re.search(p, text, re.I))


def check_management_domain(title: str, abstract: str, journal: str, full_text: str) -> tuple[bool, str, str]:
    """Q1.1: management/HRM/OB/applied psychology domain."""
    text = " ".join(filter(None, [title, abstract, journal])).lower()
    full_lower = full_text.lower()[:15000] if full_text else ""

    journal_l = (journal or "").lower()
    for hint in MANAGEMENT_JOURNAL_HINTS:
        if hint in journal_l or hint in full_lower[:5000]:
            return True, "management journal/outlet match", "high"

    if any(kw in text for kw in EXCLUDE_DOMAIN_KW):
        if not any(kw in text for kw in INCLUDE_DOMAIN_KW):
            return False, "non-management domain keywords (exclude list)", "medium"

    include_hits = sum(1 for kw in INCLUDE_DOMAIN_KW if kw in text)
    if include_hits >= 1:
        return True, f"management-domain keywords in metadata (n={include_hits})", "medium"

    # Fall back to full text intro
    intro = full_lower[:8000]
    include_hits_ft = sum(1 for kw in INCLUDE_DOMAIN_KW if kw in intro)
    if include_hits_ft >= 2:
        return True, f"management-domain keywords in PDF intro (n={include_hits_ft})", "low"

    if any(kw in intro for kw in EXCLUDE_DOMAIN_KW):
        return False, "non-management domain in PDF intro", "medium"

    return False, "no management-domain signal; flag for manual review", "low"


def check_retracted(title: str, full_text: str) -> tuple[bool, str, str]:
    """Q1.4: formally retracted by publisher — exclude regardless of other criteria."""
    title_l = (title or "").strip().lower()
    if any_match(title_l, RETRACTION_TITLE_PATTERNS) or title_l.startswith("retracted"):
        return True, "title indicates formal publisher retraction", "high"
    intro = (full_text or "")[:8000].lower()
    if any_match(intro, RETRACTION_TEXT_PATTERNS):
        return True, "publisher retraction notice in PDF", "high"
    return False, "no retraction signal detected", "high"


def check_empirical_ulmc(title: str, abstract: str, full_text: str) -> tuple[bool | None, str, str]:
    """Q1.2: empirical study using ULMC to test CMV."""
    text = " ".join(filter(None, [title, abstract, full_text])).lower()

    if any_match(text, NON_EMPIRICAL_PATTERNS):
        # Allow if clearly empirical ULMC despite 'review' in limitations
        if not any_match(text, ULMC_PATTERNS):
            kind = "conceptual/review/simulation"
            for p in NON_EMPIRICAL_PATTERNS:
                if re.search(p, text, re.I):
                    kind = p.replace("\\b", "").replace("\\s+", " ")
                    break
            return False, f"non-empirical study ({kind})", "high"

    ulmc_hits = count_matches(text, ULMC_PATTERNS)
    has_ulmc = ulmc_hits > 0

    harman_hits = count_matches(text, HARMAN_ONLY_PATTERNS)
    marker_hits = count_matches(text, MARKER_ONLY_PATTERNS)

    if not has_ulmc:
        if harman_hits > 0 and marker_hits == 0:
            return False, "Harman-only CMV test; no ULMC", "high"
        if marker_hits > 0:
            return False, "marker-variable CMV approach only; no ULMC", "high"
        if any_match(text, [r"common\s+method\s+(?:variance|bias)", r"\bcmv\b", r"\bcmb\b"]):
            return False, "CMV discussed but ULMC not identified", "medium"
        return False, "ULMC not mentioned", "high"

    # ULMC present — verify empirical
    if not any_match(text, EMPIRICAL_PATTERNS):
        return None, "ULMC mentioned but empirical evidence unclear; manual review", "low"

    # ULMC + Harman: include if ULMC clearly deployed
    ulmc_deployed = any_match(
        text,
        [
            r"ulmc\s+(?:approach|technique|procedure|test|model|analysis)",
            r"unmeasured\s+latent\s+method\s+(?:construct|factor).*(?:cfa|sem|model|fit|variance|load)",
            r"(?:cfa|sem|model).*(?:ulmc|unmeasured\s+latent\s+method)",
            r"method\s+(?:factor|construct).*(?:variance|fit|load|explained)",
            r"added\s+(?:a|an)\s+(?:unmeasured\s+)?(?:latent\s+)?method",
        ],
    )
    if not ulmc_deployed and harman_hits > 0 and marker_hits == 0:
        return False, "Harman primary CMV test; ULMC mention insufficient", "medium"

    if marker_hits > 0 and not ulmc_deployed:
        return False, "marker-variable approach; ULMC mention insufficient", "medium"

    return True, f"empirical ULMC detected (ulmc_signals={ulmc_hits})", "high"


def check_not_pls(title: str, abstract: str, full_text: str) -> tuple[bool, bool, str, str]:
    """Q1.3: TRUE if NOT PLS. Returns (not_pls, pls_used, rationale, confidence)."""
    text = " ".join(filter(None, [title, abstract, full_text])).lower()

    pls_used = any_match(text, PLS_PATTERNS)

    # Disambiguate "PLS" in unrelated contexts (e.g., "pls see")
    if pls_used:
        strong_pls = any_match(
            text,
            [
                r"partial\s+least\s+squares?",
                r"\bpls[- ]sem\b",
                r"\bsmartpls\b",
                r"component[- ]based\s+sem",
            ],
        )
        if not strong_pls:
            pls_used = False

    if pls_used:
        return False, True, "PLS-SEM estimation detected", "high"
    return True, False, "no PLS-SEM detected", "high"


# Borderline domain signals — used for manual_review reason codes (not auto-exclude).
DOMAIN_BORDERLINE_PATTERNS: list[tuple[str, str, list[str]]] = [
    (
        "DOMAIN_BORDERLINE_CLINICAL_PATIENTS",
        "Clinical patient sample — verify organizational vs. clinical scope",
        [
            "inflammatory bowel",
            "ibd patient",
            "patients with inflammatory",
            "patients with",
            "patient with",
            "clinical sample",
            "frontiers in psychiatry",
            "frontiers in medicine",
        ],
    ),
    (
        "DOMAIN_BORDERLINE_STUDENT_SAMPLE",
        "Student sample — verify workplace/organizational relevance",
        [
            "college student",
            "university student",
            "undergraduate student",
            "high school student",
            "kindergarten",
        ],
    ),
    (
        "DOMAIN_BORDERLINE_PARENTING",
        "Parenting / adolescent sample — verify organizational scope",
        ["parental burnout", "parenting style", "adolescent social adaptation"],
    ),
    (
        "DOMAIN_BORDERLINE_COMMUNITY",
        "Community-resident sample — verify management-domain scope",
        ["community resident", "community health literacy", "community residents"],
    ),
    (
        "DOMAIN_BORDERLINE_CONSUMER",
        "Consumer / brand sample — verify management vs. marketing scope",
        ["consumer behavior", "consumer behaviour", "global brand", "local brand", "brand preference"],
    ),
    (
        "DOMAIN_BORDERLINE_PUBLIC_HEALTH",
        "Public health / epidemics framing — verify management-domain scope",
        ["public health", "epidemic", "epidemics", "frontiers in public health"],
    ),
]


def _q11_reason_code(q11: bool, q11_r: str, q11_c: str) -> tuple[str, str]:
    if q11:
        if "journal/outlet match" in q11_r:
            return "DOMAIN_PASS_JOURNAL_OUTLET", q11_r
        if "metadata" in q11_r:
            return "DOMAIN_PASS_KEYWORDS_METADATA", q11_r
        if "PDF intro" in q11_r:
            return "DOMAIN_PASS_KEYWORDS_INTRO", q11_r
        return "DOMAIN_PASS", q11_r
    if "exclude list" in q11_r:
        return "DOMAIN_FAIL_EXCLUDE_KEYWORDS", q11_r
    if "PDF intro" in q11_r:
        return "DOMAIN_FAIL_EXCLUDE_INTRO", q11_r
    if "no management-domain signal" in q11_r:
        return "DOMAIN_FAIL_NO_SIGNAL", q11_r
    return "DOMAIN_FAIL", q11_r


def _q12_reason_code(q12: bool | None, q12_r: str) -> tuple[str, str]:
    if q12 is True:
        return "ULMC_PASS_EMPIRICAL", q12_r
    if q12 is None:
        return "ULMC_AMBIGUOUS", q12_r
    if "Harman-only" in q12_r or "Harman primary" in q12_r:
        return "ULMC_FAIL_HARMAN_ONLY", q12_r
    if "marker-variable" in q12_r or "marker" in q12_r.lower():
        return "ULMC_FAIL_MARKER_ONLY", q12_r
    if "non-empirical" in q12_r:
        return "ULMC_FAIL_NON_EMPIRICAL", q12_r
    if "not identified" in q12_r or "CMV discussed" in q12_r:
        return "ULMC_FAIL_CMV_NO_ULMC", q12_r
    if "not mentioned" in q12_r:
        return "ULMC_FAIL_NOT_MENTIONED", q12_r
    return "ULMC_FAIL", q12_r


def _q13_reason_code(q13: bool, pls_used: bool, q13_r: str) -> tuple[str, str]:
    if q13:
        return "PLS_PASS_NOT_DETECTED", q13_r
    if pls_used:
        return "PLS_FAIL_SEM_DETECTED", q13_r
    return "PLS_FAIL", q13_r


def detect_domain_borderline(
    title: str, abstract: str, journal: str, full_text: str | None = None
) -> tuple[str, str] | None:
    """Return (code, text) when sample/journal framing is borderline for Q1.1."""
    hay = " ".join(filter(None, [title, abstract, journal])).lower()
    for code, text, patterns in DOMAIN_BORDERLINE_PATTERNS:
        if any(p in hay for p in patterns):
            return code, text
    return None


def derive_decision_reasons(
    *,
    title: str,
    abstract: str,
    journal: str,
    full_text: str,
    retracted: bool = False,
    q14_r: str = "",
    q11: bool,
    q11_r: str,
    q11_c: str,
    q12: bool | None,
    q12_r: str,
    q12_c: str,
    q13: bool,
    pls_used: bool,
    q13_r: str,
    q13_c: str,
    decision: str,
    overall_conf: str,
) -> dict[str, str]:
    """
    Structured, human-readable reason codes for Level 1 screening decisions.

    Returns q1_*_reason_code/text per criterion plus decision_reason_code/text.
    """
    if retracted:
        return {
            "q1_1_reason_code": "",
            "q1_1_reason_text": "",
            "q1_2_reason_code": "",
            "q1_2_reason_text": "",
            "q1_3_reason_code": "",
            "q1_3_reason_text": "",
            "decision_reason_code": "EXCLUDE_RETRACTED",
            "decision_reason_text": (
                f"Q1.4 FAIL (RETRACTION_FAIL_PUBLISHER): {q14_r}. "
                "Decision: excluded — formally retracted by publisher (Level 1 eligibility fail)."
            ),
        }

    q11_code, q11_text = _q11_reason_code(q11, q11_r, q11_c)
    q12_code, q12_text = _q12_reason_code(q12, q12_r)
    q13_code, q13_text = _q13_reason_code(q13, pls_used, q13_r)

    borderline = detect_domain_borderline(title, abstract, journal, full_text)
    if borderline and q11:
        q11_code, q11_text = borderline

    q11_label = "PASS" if q11 else "FAIL"
    q12_label = "PASS" if q12 is True else ("AMBIGUOUS" if q12 is None else "FAIL")
    q13_label = "PASS" if q13 else "FAIL"

    criterion_summary = (
        f"Q1.1 {q11_label} ({q11_code}): {q11_text}. "
        f"Q1.2 {q12_label} ({q12_code}): {q12_text}. "
        f"Q1.3 {q13_label} ({q13_code}): {q13_text}."
    )

    if decision == "included":
        decision_code = "INCLUDE_ALL_CRITERIA_PASS"
        decision_text = f"{criterion_summary} Decision: included — all Level 1 criteria pass."
    elif decision == "excluded_pls":
        decision_code = "EXCLUDE_Q1_3_PLS"
        decision_text = (
            f"{criterion_summary} Decision: excluded_pls — PLS-SEM detected (Q1.3 fail); "
            "not a hard reject of domain/ULMC."
        )
    elif decision == "excluded":
        if not q11:
            decision_code = "EXCLUDE_Q1_1_DOMAIN"
        elif q12 is False:
            decision_code = "EXCLUDE_Q1_2_ULMC"
        elif not q13:
            decision_code = "EXCLUDE_Q1_3_PLS"
        else:
            decision_code = "EXCLUDE_LEVEL1_FAIL"
        decision_text = f"{criterion_summary} Decision: excluded — Level 1 eligibility fail."
    elif decision == "manual_review":
        if q12 is None:
            decision_code = "MANUAL_REVIEW_ULMC_AMBIGUOUS"
            decision_text = (
                f"{criterion_summary} Decision: manual_review — ULMC evidence unclear; "
                "not excluded pending human check."
            )
        elif borderline and q11 and q12 and q13:
            decision_code = f"MANUAL_REVIEW_{borderline[0]}"
            decision_text = (
                f"{criterion_summary} Decision: manual_review — {borderline[1]}; "
                "Q1.1–Q1.3 auto-pass but domain/sample borderline (not excluded)."
            )
        elif overall_conf == "low" and q11 and q12 and q13:
            decision_code = "MANUAL_REVIEW_LOW_CONFIDENCE_ALL_PASS"
            decision_text = (
                f"{criterion_summary} Decision: manual_review — low-confidence include; "
                "all criteria pass in automation but verify domain/sample (not excluded)."
            )
        else:
            decision_code = "MANUAL_REVIEW"
            decision_text = (
                f"{criterion_summary} Decision: manual_review — flagged for human verification "
                "(not excluded)."
            )
    elif decision == "pending":
        decision_code = "PENDING"
        decision_text = f"{criterion_summary} Decision: pending — screening incomplete."
    else:
        decision_code = decision.upper()
        decision_text = f"{criterion_summary} Decision: {decision}."

    return {
        "q1_1_reason_code": q11_code,
        "q1_1_reason_text": q11_text,
        "q1_2_reason_code": q12_code,
        "q1_2_reason_text": q12_text,
        "q1_3_reason_code": q13_code,
        "q1_3_reason_text": q13_text,
        "decision_reason_code": decision_code,
        "decision_reason_text": decision_text,
    }


def resolve_pdf_path(row: dict[str, str]) -> Path | None:
    rel = (row.get("pdf_path") or "").strip()
    if rel:
        p = ROOT / rel
        if p.exists():
            return p
    mid = row.get("article_id", "")
    if mid:
        matches = list(PDF_DIR.glob(f"EBSCO_{mid}_*.pdf"))
        if matches:
            return matches[0]
    return None


def get_cohort_on_hand_ids() -> list[str]:
    """All on-hand EBSCO PDFs in examination cohort (excludes legacy 182 holdout)."""
    cohort_csv = EBSCO_DIR / "examination_cohort_on_hand.csv"
    if cohort_csv.exists():
        rows = load_csv(cohort_csv)
        return sorted(r["article_id"] for r in rows if r.get("article_id"))

    # Fallback: regenerate cohort inline
    from define_examination_cohort import build_cohort  # noqa: WPS433

    cohort, _ = build_cohort()
    return sorted(r["article_id"] for r in cohort if r.get("article_id"))


def get_unscreened_cohort_ids() -> list[str]:
    """Cohort members with screening_status pending or empty."""
    master = {r["article_id"]: r for r in load_csv(MASTER_PATH)}
    return [
        mid
        for mid in get_cohort_on_hand_ids()
        if master.get(mid, {}).get("screening_status", "") in ("", "pending")
    ]


def get_batch_master_ids(batch_date: str) -> list[str]:
    """Articles from ingest on batch_date that still need Level 1 screening."""
    ingest = load_csv(INGEST_LOG)
    master = {r["article_id"]: r for r in load_csv(MASTER_PATH)}

    ids: set[str] = set()
    for row in ingest:
        if not row.get("master_id"):
            continue
        if batch_date in (row.get("processed_at") or ""):
            ids.add(row["master_id"].strip())

    # Also include pending articles in M0183–M0262 + M0679 range from today's cohort
    for mid, row in master.items():
        if row.get("screening_status") != "pending":
            continue
        if row.get("examination_status") not in ("not_read", ""):
            continue
        m = re.match(r"M(\d+)", mid)
        if not m:
            continue
        num = int(m.group(1))
        if (183 <= num <= 262) or num == 679:
            ids.add(mid)

    return sorted(ids)


def screen_article(row: dict[str, str]) -> dict:
    mid = row["article_id"]
    title = row.get("title") or ""
    abstract = row.get("abstract") or ""
    journal = row.get("journal") or ""

    pdf_path = resolve_pdf_path(row)
    if not pdf_path:
        return {
            "master_id": mid,
            "title": title,
            "Q1_1_management_domain": "",
            "Q1_2_empirical_ulmc": "",
            "Q1_3_not_pls": "",
            "decision": "pending",
            "rationale": "PDF missing or text extraction unavailable",
            "confidence": "n/a",
            "screening_status": "pending",
            "screening_level1_include": "",
            "examination_status": row.get("examination_status") or "not_read",
            "screening_notes": "Level1 batch 2026-06-24: PDF missing",
        }

    try:
        full_text, _meta = extract_text(pdf_path)
    except Exception as exc:
        return {
            "master_id": mid,
            "title": title,
            "Q1_1_management_domain": "",
            "Q1_2_empirical_ulmc": "",
            "Q1_3_not_pls": "",
            "decision": "pending",
            "rationale": f"PDF text extraction failed: {exc}",
            "confidence": "n/a",
            "screening_status": "pending",
            "screening_level1_include": "",
            "examination_status": row.get("examination_status") or "not_read",
            "screening_notes": f"Level1 batch 2026-06-24: extraction failed — {exc}",
        }

    if len(full_text.strip()) < 200:
        return {
            "master_id": mid,
            "title": title,
            "Q1_1_management_domain": "",
            "Q1_2_empirical_ulmc": "",
            "Q1_3_not_pls": "",
            "decision": "pending",
            "rationale": "PDF text too short (<200 chars); likely scan or parse failure",
            "confidence": "n/a",
            "screening_status": "pending",
            "screening_level1_include": "",
            "examination_status": row.get("examination_status") or "not_read",
            "screening_notes": "Level1 batch 2026-06-24: insufficient extracted text",
        }

    q14, q14_r, q14_c = check_retracted(title, full_text)
    if q14:
        reasons = derive_decision_reasons(
            title=title,
            abstract=abstract,
            journal=journal,
            full_text=full_text,
            retracted=True,
            q14_r=q14_r,
            q11=False,
            q11_r="",
            q11_c="",
            q12=None,
            q12_r="",
            q12_c="",
            q13=True,
            pls_used=False,
            q13_r="",
            q13_c="",
            decision="excluded",
            overall_conf=q14_c,
        )
        return {
            "master_id": mid,
            "title": title,
            "Q1_4_retracted": "TRUE",
            "Q1_1_management_domain": "",
            "Q1_2_empirical_ulmc": "",
            "Q1_3_not_pls": "",
            "decision": "excluded",
            "rationale": f"Q1.4: {q14_r}",
            "confidence": q14_c,
            "screening_status": "level1_fail",
            "screening_level1_include": "False",
            "examination_status": "read_snippet_only",
            "screening_notes": (
                f"L1 batch {date.today().isoformat()}; Q1.4=retracted; {q14_r}"
            ),
            **reasons,
        }

    q11, q11_r, q11_c = check_management_domain(title, abstract, journal, full_text)
    q12, q12_r, q12_c = check_empirical_ulmc(title, abstract, full_text)
    q13, pls_used, q13_r, q13_c = check_not_pls(title, abstract, full_text)

    confidences = [q11_c, q12_c, q13_c]
    overall_conf = "low" if "low" in confidences else ("medium" if "medium" in confidences else "high")

    # Manual review flag
    if q12 is None:
        decision = "manual_review"
        screening_status = "manual_review"
        level1_include = ""
        rationale = f"Q1.2 ambiguous: {q12_r}"
    elif q11 and q12 and q13:
        decision = "included"
        screening_status = "included"
        level1_include = "True"
        rationale = "Q1.1–Q1.3 all pass"
    elif pls_used:
        decision = "excluded_pls"
        screening_status = "excluded_pls"
        level1_include = "False"
        rationale = f"PLS-SEM excluded (Q1.3): {q13_r}; domain={q11}; ulmc={q12}"
    else:
        decision = "excluded"
        screening_status = "level1_fail"
        level1_include = "False"
        fails = []
        if not q11:
            fails.append(f"Q1.1: {q11_r}")
        if q12 is False:
            fails.append(f"Q1.2: {q12_r}")
        if not q13:
            fails.append(f"Q1.3: {q13_r}")
        rationale = "; ".join(fails) if fails else "Level 1 fail"

    if overall_conf == "low" and decision == "included":
        decision = "manual_review"
        screening_status = "manual_review"
        level1_include = ""
        rationale = f"Low confidence include — verify manually. {rationale}"

    reasons = derive_decision_reasons(
        title=title,
        abstract=abstract,
        journal=journal,
        full_text=full_text,
        retracted=False,
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

    note_parts = [
        f"L1 batch {date.today().isoformat()}",
        f"Q1.1={q11}",
        f"Q1.2={q12}",
        f"Q1.3={q13}",
        q11_r[:80],
    ]
    if pls_used:
        note_parts.append("PLS tagged (include_pls policy)")

    return {
        "master_id": mid,
        "title": title,
        "Q1_4_retracted": "FALSE",
        "Q1_1_management_domain": str(q11) if q11 is not None else "",
        "Q1_2_empirical_ulmc": str(q12) if q12 is not None else "",
        "Q1_3_not_pls": str(q13),
        "decision": decision,
        "rationale": rationale,
        "confidence": overall_conf if decision != "pending" or overall_conf != "high" else "n/a",
        "screening_status": screening_status,
        "screening_level1_include": level1_include,
        "examination_status": (
            "read_snippet_only"
            if screening_status not in ("pending", "manual_review")
            else (row.get("examination_status") or "not_read")
        ),
        "screening_notes": "; ".join(note_parts),
        **reasons,
    }


def apply_results_to_master(results: list[dict], dry_run: bool = False) -> None:
    by_id = {r["master_id"]: r for r in results}

    with master_file_lock():
        rows = load_csv(MASTER_PATH)
        if not rows:
            raise RuntimeError("articles_master.csv empty")
        fieldnames = list(rows[0].keys())
        today = date.today().isoformat()
        updated = 0

        for row in rows:
            mid = row.get("article_id", "")
            if mid not in by_id:
                continue
            res = by_id[mid]
            row["screening_status"] = res["screening_status"]
            if res["screening_level1_include"]:
                row["screening_level1_include"] = res["screening_level1_include"]
            row["screening_notes"] = res["screening_notes"]
            row["examination_status"] = res["examination_status"]
            row["updated_at"] = today
            if res["examination_status"] == "read_snippet_only":
                row["pdf_status"] = "available"
                row["corpus_tier"] = row.get("corpus_tier") or "ebsco_screened"
            updated += 1

        if dry_run:
            print(f"[dry-run] Would update {updated} master rows")
            return

        write_master(rows, fieldnames)
        print(f"Updated {updated} rows in {MASTER_PATH}")


def write_batch_csv(results: list[dict], out_path: Path) -> None:
    cols = [
        "master_id", "title",
        "Q1_4_retracted", "Q1_1_management_domain", "Q1_2_empirical_ulmc", "Q1_3_not_pls",
        "decision", "rationale", "confidence",
        "q1_1_reason_code", "q1_1_reason_text",
        "q1_2_reason_code", "q1_2_reason_text",
        "q1_3_reason_code", "q1_3_reason_text",
        "decision_reason_code", "decision_reason_text",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"Wrote {len(results)} screening rows to {out_path}")


def print_summary(results: list[dict]) -> None:
    from collections import Counter

    decisions = Counter(r["decision"] for r in results)
    print("\n=== Level 1 Screening Summary ===")
    print(f"Total screened: {len(results)}")
    for k in sorted(decisions.keys()):
        print(f"  {k}: {decisions[k]}")

    excluded = [r for r in results if r["decision"] == "excluded"]
    if excluded:
        print("\nExcluded reasons (sample):")
        reason_counts = Counter()
        for r in excluded:
            if "Q1.1" in r["rationale"]:
                reason_counts["Q1.1 domain fail"] += 1
            elif "Q1.2" in r["rationale"]:
                reason_counts["Q1.2 empirical ULMC fail"] += 1
            else:
                reason_counts["other"] += 1
        for k, v in reason_counts.most_common():
            print(f"  {k}: {v}")

    manual = [r for r in results if r["decision"] in ("manual_review", "pending")]
    if manual:
        print(f"\nFlagged pending/manual review: {len(manual)}")
        for r in manual[:10]:
            print(f"  {r['master_id']}: {r['rationale'][:100]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Level 1 batch screening")
    parser.add_argument("--batch-date", default="2026-06-24", help="Ingest date YYYY-MM-DD")
    parser.add_argument("--master-id", action="append", help="Screen specific master_id(s)")
    parser.add_argument(
        "--cohort-on-hand",
        action="store_true",
        help="Screen all unscreened rows in examination_cohort_on_hand.csv",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output",
        default=str(EBSCO_DIR / "screening_batch_2026_06_24.csv"),
        help="Batch results CSV path",
    )
    args = parser.parse_args()

    master_rows = load_csv(MASTER_PATH)
    master_by_id = {r["article_id"]: r for r in master_rows}

    if args.master_id:
        ids = args.master_id
    elif args.cohort_on_hand:
        ids = get_unscreened_cohort_ids()
    else:
        ids = get_batch_master_ids(args.batch_date)

    print(f"Screening {len(ids)} articles...")
    results = []
    for mid in ids:
        row = master_by_id.get(mid)
        if not row:
            print(f"  WARN: {mid} not in master")
            continue
        res = screen_article(row)
        results.append(res)
        sym = {"included": "+", "excluded": "-", "excluded_pls": "P", "manual_review": "?", "pending": "~"}.get(
            res["decision"], " "
        )
        print(f"  [{sym}] {mid}: {res['decision']} ({res.get('confidence','')})")

    out_path = Path(args.output)
    write_batch_csv(results, out_path)

    if not args.dry_run:
        apply_results_to_master(results, dry_run=False)

    print_summary(results)


if __name__ == "__main__":
    main()
