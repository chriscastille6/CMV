#!/usr/bin/env python3
"""Automated pre-fill extraction for EBSCO on-hand included articles.

Appends to review/EBSCO/systematic_extraction_ebsco_on_hand.csv (never legacy file).
Updates articles_master study_order and examination_status.

Usage:
  python3 review/EBSCO/extract_ebsco_on_hand_batch.py --limit 20
  python3 review/EBSCO/extract_ebsco_on_hand_batch.py --master-id M0183 --dry-run
  python3 review/EBSCO/extract_ebsco_on_hand_batch.py --force-reextract --limit 0
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
COHORT_CSV = EBSCO_DIR / "examination_cohort_on_hand.csv"
EXTRACTION_PATH = EBSCO_DIR / "systematic_extraction_ebsco_on_hand.csv"
LEGACY_EXTRACTION = EBSCO_DIR / "systematic_extraction_40_studies.csv"
PDF_DIR = EBSCO_DIR / "pdfs"

MASTER_DIR = ROOT / "review" / "master"
sys.path.insert(0, str(MASTER_DIR))
from examination import is_fully_coded_row  # noqa: E402

sys.path.insert(0, str(EBSCO_DIR))
from parse_ebsco_fulltext_pdf import extract_text  # noqa: E402
from publisher_outlet import infer_publisher_outlet  # noqa: E402

ULMC_PATTERNS = [
    r"unmeasured\s+latent\s+method\s+(?:construct|factor|variable)",
    r"\bulmc\b",
    r"common\s+latent\s+factor",
    r"single\s+method\s+factor",
    r"latent\s+method\s+factor",
    r"common\s+method\s+factor",
]
APOSTROPHE = r"['\u2019\u2018]"
HARMAN_PATTERNS = [
    rf"harman{APOSTROPHE}?s?\s+(?:single[- ]factor|one[- ]factor)",
    rf"harman{APOSTROPHE}?s?\s+test",
    rf"harman{APOSTROPHE}?\s+single[- ]factor",
    r"CFA[- ]based\s+version\s+of\s+Harman",
    r"unrotated\s+(?:PCA|factor|CFA)",
    r"exploratory\s+factor\s+analysis.*?(?:single|one)\s+(?:factor|component)",
    r"all\s+items.*?(?:single|one)\s+(?:factor|component)",
    r"harman\s+single[- ]factor\s+test",
]
PLS_PATTERNS = [
    r"partial\s+least\s+squares?",
    r"\bpls[- ]sem\b",
    r"\bsmartpls\b",
]
PROCEDURAL_PATTERNS = [
    (r"anonym", "anonymity"),
    (r"temporal\s+separ|time[- ]lag|two[- ]wave|multi[- ]wave", "temporal separation"),
    (r"different\s+time\s+points|intervals?\s+of\s+\d+\s+weeks|longitudinal\s+responses", "temporal separation"),
    (r"item\s+pretest|pilot\s+test", "item pretesting"),
    (r"counterbalanc", "counterbalancing"),
    (r"attention[- ]check", "attention checks"),
    (r"procedural\s+remed", "procedural remedies cited"),
]
MULTISOURCE_SAME_CONSTRUCT_PATTERNS = [
    r"360[- ]?(?:degree|°)?\s*(?:feedback|evaluation|rating|assessment)",
    r"multi[- ]?rater",
    r"self[- ](?:and|&|\+).{0,40}(?:other|peer|supervisor|subordinate|manager|coworker|colleague).{0,80}(?:report|rating|rat(?:e|ed|ings)).{0,80}(?:same|identical|each|correspond|converg)",
    r"(?:peer|supervisor|subordinate|manager|other|coworker|colleague).{0,40}(?:and|&).{0,20}self[- ].{0,80}(?:report|rating|rat(?:e|ed|ings)).{0,80}(?:same|identical|each|converg)",
    r"(?:self|other)[- ]report.{0,40}(?:and|&).{0,20}(?:self|other)[- ]report",
    r"convergen(?:ce|t).{0,40}self[- ](?:and|&).{0,30}(?:other|peer|supervisor)",
    r"\bmtmm\b",
    r"multi[- ]trait[- ]multi[- ]method",
]
DIFFERENT_SOURCES_IV_DV_PATTERNS = [
    r"(?:supervisor|leader|manager)[- ](?:rated|reported|assessed).{0,120}(?:employee|subordinate|follower|member)[- ](?:rated|reported|assessed)",
    r"(?:employee|subordinate|follower|member)[- ](?:rated|reported|assessed).{0,120}(?:supervisor|leader|manager)[- ](?:rated|reported|assessed)",
    r"different (?:informants?|sources?).{0,80}(?:for|on|of|between).{0,40}(?:predictor|criterion|independent|dependent|iv|dv|variables?)",
    r"(?:predictor|criterion|independent|dependent|iv|dv).{0,60}(?:from|came from|collected from).{0,40}different (?:informants?|sources?)",
    r"(?:iv|dv|independent|dependent|predictor|criterion).{0,60}different (?:informants?|sources?)",
    r"matched dyad",
    r"source separation",
    r"podsakoff.{0,40}(?:remed|procedur).{0,40}(?:different|separat).{0,40}(?:source|informant)",
    r"data (?:were|was) collected from.{0,40}(?:leaders?|supervisors?|managers?).{0,80}(?:and|&|,).{0,40}(?:subordinates?|employees?|followers?|members?)",
]
DISTINCT_SOURCES_OTHER_PATTERNS = [
    r"multi[- ]level.{0,40}multi[- ]?source|multi[- ]?source.{0,40}multi[- ]level",
    r"\barchival\b",
    r"secondary (?:data|source|database|records?)",
    r"multi[- ]?stage",
    r"from.{0,40}(?:archives|administrative records|company records|hr records)",
]
RICHARDSON_PATTERNS = [
    r"richardson\s+et\s+al\.?\s*\(\s*2009\s*\)",
    r"richardson\s+et\s+al\.?\s*,\s*2009",
    r"richardson.{0,40}2009",
    r"richardson.{0,30}simmering.{0,30}sturman",
    r"tale\s+of\s+three\s+perspectives.{0,40}2009",
    r"Richardson,\s+H\.\s+A\..{0,80}2009",
]
METHOD_R_PATTERNS = [
    r"trait\s*/\s*method[- ]r",
    r"trait[- ]method[- ]r",
    r"trait/method-r",
    r"method[- ]r\s+model",
]
STEP1_PRESENCE_PATTERNS = [
    r"trait[- ]only.*trait.*method",
    r"nested.*(?:chi|χ).*square.*(?:ulmc|method\s+factor|method\s+construct)",
    r"(?:nested|difference|delta|Δ).{0,60}(?:chi|χ).{0,120}(?:ulmc|method\s+factor|common\s+method)",
    r"(?:ulmc|method\s+factor).*(?:significantly|sig\.).*improv",
]
STEP3_CONTAMINATION_PATTERNS = [
    r"indicator.*method.*(?:variance|loading|loadings)",
    r"construct.*method.*variance",
    r"method.*variance.*(?:indicator|item|construct)",
    r"method[- ]factor.*loadings?",
]
STEP1_CMV_INDICATED_PATTERNS = [
    r"(?:ulmc|method\s+(?:factor|construct)).*(?:significantly|sig\.).*(?:improv|better|fit)",
    r"nested.*(?:chi|χ).*square.*signific",
    r"cmv|common\s+method.*(?:present|detected|evidence)",
    r"method\s+variance.*(?:present|detected|substantial)",
]
STEP2_BIAS_TEST_PATTERNS = [
    r"trait/method[- ]r.*trait/method",
    r"trait[- ]method[- ]r.*(?:vs\.?|versus|compared).*trait[- ]method",
    r"method[- ]r\s+model.*(?:nested|compared|comparison).*(?:chi|χ)",
    r"delta.*(?:chi|χ).*square.*(?:trait[- ]method[- ]r|method[- ]r\s+model)",
]
STEP2_BIAS_INDICATED_PATTERNS = [
    r"substantive\s+bias",
    r"method[- ]r.*signific",
    r"trait/method[- ]r.*signific",
    r"bias.*(?:significant|detected)",
]
STEP3_CONSTRUCT_MV_PATTERNS = [
    r"construct[- ]level.*method.*variance",
    r"method.*variance.*(?:per|across)\s+construct",
    r"variance.*(?:explained|accounted).*(?:construct|factor)",
]
NO_BIAS_PATTERNS = [
    r"no\s+substantive\s+bias",
    r"method[- ]r.*(?:not\s+signific|non[- ]signific)",
    r"did\s+not\s+indicate\s+bias",
    r"no\s+evidence\s+of\s+bias",
]

CANONICAL_THREE_STEP_FIELDS = [
    "step1_presence_delta_chisq_reported",
    "step1_presence_delta_chisq",
    "step1_presence_pvalue",
    "step1_cmv_indicated",
    "step2_method_r_model_reported",
    "step2_method_r_bias_test_reported",
    "step2_bias_indicated",
    "step3_contamination_reported",
    "step3_indicator_level_mv_reported",
    "step3_construct_level_mv_reported",
    "method_variance_reported_despite_no_bias",
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


def normalize_pdf_text(text: str) -> str:
    """Join soft-hyphen and hard-hyphen line breaks common in pdftotext output."""
    text = text.replace("\u00ad", "")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return text


BUSINESS_SCHOOL_PATTERNS = [
    r"\bbusiness\s+school\b",
    r"\bschool\s+of\s+business\b",
    r"\bcollege\s+of\s+business\b",
    r"\bschool\s+of\s+business\s+administration\b",
    r"\bschool\s+of\s+business\s+and\s+economics\b",
    r"\bfaculty\s+of\s+management\b",
    r"\bschool\s+of\s+management\b",
    r"\bdepartment\s+of\s+management\b",
    r"\bschool\s+of\s+economics\s+and\s+management\b",
    r"\bcollege\s+of\s+management\b",
    r"\bfaculty\s+of\s+business\b",
    r"\bgraduate\s+school\s+of\s+business\b",
    r"\bmanagement\s+school\b",
    r"\b(?:\w+\s+){1,4}school\s+of\s+business\b",
]
AFFILIATION_SIGNAL = re.compile(
    r"\b(?:university|college|institute|school|faculty|department)\b",
    re.I,
)
HEADER_END_MARKERS = [
    r"\babstract\b",
    r"\b1[\.\s]+introduction\b",
    r"\bkeywords\s*:",
    r"\bkey\s+words\s*:",
]


def extract_affiliation_header(text: str) -> str:
    """Title-page / byline region before abstract or introduction."""
    text = normalize_pdf_text(text)
    window = text[:12000]
    end = len(window)
    for marker in HEADER_END_MARKERS:
        m = re.search(marker, window, re.I)
        if m:
            end = min(end, m.start())
    return window[:end]


def _affiliation_chunks(header: str) -> list[str]:
    """Merge broken affiliation lines (common in MDPI/Frontiers PDF text)."""
    chunks: list[str] = []
    buf: list[str] = []
    for raw in header.splitlines():
        ln = raw.strip()
        if not ln:
            if buf:
                chunks.append(" ".join(buf))
                buf = []
            continue
        if re.match(r"^\d+$", ln) or re.match(r"^[*†‡§]$", ln):
            if buf:
                chunks.append(" ".join(buf))
                buf = []
            continue
        if re.match(r"^(?:correspondence|received|revised|accepted|published|copyright|licensee|"
                    r"academic editor|citation|article|doi|open access|edited by|reviewed by)\b", ln, re.I):
            continue
        if AFFILIATION_SIGNAL.search(ln) or (buf and re.search(r"[,;]|@|china|united states|university", ln, re.I)):
            buf.append(ln)
        elif buf:
            chunks.append(" ".join(buf))
            buf = []
    if buf:
        chunks.append(" ".join(buf))
    return [c for c in chunks if len(c) >= 20 and AFFILIATION_SIGNAL.search(c)]


def extract_business_school_affiliation(text: str) -> tuple[str, str]:
    """Return (authors_business_school, author_affiliation_detail) from PDF title-page text."""
    header = extract_affiliation_header(text)
    header_flat = re.sub(r"\s+", " ", header)
    business_hits: list[str] = []
    for pat in BUSINESS_SCHOOL_PATTERNS:
        for m in re.finditer(pat, header_flat, re.I):
            start = max(0, m.start() - 80)
            end = min(len(header_flat), m.end() + 120)
            snippet = header_flat[start:end].strip(" ,;")
            if snippet and snippet not in business_hits:
                business_hits.append(snippet)
    if business_hits:
        detail = "; ".join(business_hits[:3])
        return "TRUE", detail[:500]
    chunks = _affiliation_chunks(header)
    if chunks or re.search(r"\buniversity\b|\binstitute\b|\bdepartment\b", header, re.I):
        return "FALSE", ""
    return "NA", ""


CMV_DISCUSSED = re.compile(
    r"common\s+method|method\s+(?:variance|bias)|\bcmv\b|\bcmb\b|harman",
    re.I,
)


def extract_mv_pct(text: str) -> str:
    """Extract ULMC method-variance percentage (not Harman's test)."""
    patterns = [
        r"(?i)(?:latent\s+(?:method\s+)?factor|method\s+factor|ulmc|unmeasured\s+latent\s+method).{0,120}(\d+(?:\.\d+)?)\s*%\s*of\s*(?:the\s+)?(?:total\s+)?variance",
        r"(?i)(?:method\s+(?:factor|construct)|ulmc).{0,60}r[²2]\s*[=:]?\s*([0-9.]+)",
        r"(?i)(?:common\s+method|method\s+variance|method\s+bias|\bulmc\b).{0,120}(\d+(?:\.\d+)?)\s*%\s*of\s*(?:the\s+)?(?:total\s+)?variance",
    ]
    values: list[float] = []
    for p in patterns:
        for m in re.finditer(p, text, re.DOTALL):
            window = text[max(0, m.start() - 150) : min(len(text), m.end() + 50)].lower()
            if re.search(r"harman|single[- ]factor|one[- ]factor|principal\s+component|unrotated", window):
                continue
            if re.search(
                r"model\s+(?:explained|accounted)|variance\s+in\s+\w|hypothesis\s+\d",
                window,
            ) and not re.search(
                r"common\s+method|method\s+(?:variance|bias|factor)|ulmc|latent\s+method|cmb|cmv",
                window,
            ):
                continue
            val = m.group(1)
            try:
                num = float(val)
                if num <= 1.0:
                    num *= 100
                if 0 <= num <= 100:
                    values.append(num)
            except ValueError:
                pass
    if not values:
        return ""
    typical = [v for v in values if 5 <= v <= 80]
    return str(round((typical or values)[0], 2))


def extract_harman_variance_pct(text: str) -> str:
    """Extract Harman single-factor variance percentage."""
    patterns = [
        rf"(?is)harman{APOSTROPHE}?s?(?:\s+(?:single|one)[-\s]factor)?\s+test.*?(\d+(?:\.\d+)?)\s*%",
        r"(?i)first\s+(?:un[- ]?rotated\s+)?(?:factor|component).{0,80}(?:accounted\s+for|explained).{0,40}(\d+(?:\.\d+)?)\s*%\s*of\s*(?:the\s+)?(?:total\s+)?variance",
        r"(?i)(?:single|one)[-\s]factor.{0,80}(?:accounted\s+for|explained|variance).{0,40}(\d+(?:\.\d+)?)\s*%",
        rf"(?is)harman.{0,250}?(\d+(?:\.\d+)?)\s*%\s*of\s*(?:the\s+)?(?:total\s+)?variance",
    ]
    values: list[float] = []
    for p in patterns:
        for m in re.finditer(p, text, re.DOTALL):
            window = text[max(0, m.start() - 120) : min(len(text), m.end() + 50)].lower()
            if not re.search(r"harman|single[- ]factor|one[- ]factor|unrotated|principal\s+component|cmb|cmv|common\s+method", window):
                continue
            try:
                num = float(m.group(1))
                if 0 <= num <= 100:
                    values.append(num)
            except ValueError:
                pass
    if not values:
        return ""
    typical = [v for v in values if 5 <= v <= 80]
    return str(round((typical or values)[0], 2))


def extract_model_complexity(text: str) -> dict[str, str]:
    """Regex hints for num_constructs, num_indicators, complexity_ratio."""
    text_lower = text.lower()
    num_constructs = ""
    num_indicators = ""

    construct_patterns = [
        r"(\d+)\s*(?:construct|factor|latent\s*variable|scale|dimension)(?:s)?(?!\s*(?:participant|respondent|sample|n\s*=|participant))",
        r"(?:construct|factor|latent\s*variable|scale|dimension)(?:s)?\s*(?:of|:)?\s*(\d+)(?!\s*(?:participant|respondent|sample))",
        r"(?:\d+)\s*(?:factor|construct)\s*(?:model|analysis|structure|were|was|included)",
    ]
    for pat in construct_patterns:
        for m in re.finditer(pat, text_lower, re.I):
            nums = [int(x) for x in re.findall(r"\d+", m.group(0)) if 2 <= int(x) <= 20]
            if nums:
                num_constructs = str(max(nums))
                break
        if num_constructs:
            break

    indicator_patterns = [
        r"(\d+)\s*(?:indicator|item|variable|measure)(?:s)?(?!\s*(?:participant|respondent|sample|n\s*=|were\s+collected))",
        r"(?:indicator|item|variable|measure)(?:s)?\s*(?:of|:)?\s*(\d+)(?!\s*(?:participant|respondent|sample))",
        r"(?:total|\d+)\s*(?:item|indicator)(?:s)?\s*(?:were|was|used|included|measured)",
        r"(?:\d+)\s*(?:item|indicator)(?:s)?\s*(?:scale|measurement|questionnaire)",
    ]
    for pat in indicator_patterns:
        for m in re.finditer(pat, text_lower, re.I):
            nums = [int(x) for x in re.findall(r"\d+", m.group(0)) if 5 <= int(x) <= 200]
            if nums:
                num_indicators = str(max(nums))
                break
        if num_indicators:
            break

    if not num_constructs:
        m = re.search(
            r"(\d+)\s*(?:construct|factor)(?:s)?.*?(?:with|of|,)\s*(?:\d+)\s*(?:item|indicator)(?:s)?",
            text_lower,
            re.I,
        )
        if m:
            nums = [int(x) for x in re.findall(r"\d+", m.group(0)) if 2 <= int(x) <= 20]
            if nums:
                num_constructs = str(max(nums))

    complexity_ratio = ""
    if num_constructs and num_indicators:
        try:
            complexity_ratio = str(round(int(num_indicators) / int(num_constructs), 2))
        except (ValueError, ZeroDivisionError):
            pass

    return {
        "num_constructs": num_constructs,
        "num_indicators": num_indicators,
        "complexity_ratio": complexity_ratio,
    }


def extract_ulmc_outcomes(text: str) -> dict[str, str]:
    """Regex hints for ulmc_improves_fit and ulmc_in_final."""
    improves = bool(
        re.search(
            r"(?:ulmc|method\s+factor|latent\s+method).{0,80}(?:significantly|sig\.|substantially).{0,40}(?:improv|better).{0,40}(?:fit|chi)",
            text,
            re.I,
        )
    )
    no_improve = bool(
        re.search(
            r"(?:ulmc|method\s+factor|latent\s+method).{0,80}(?:no|not|did\s+not|failed\s+to).{0,40}(?:improv|better|significant).{0,40}(?:fit|chi)",
            text,
            re.I,
        )
    )
    in_final = bool(
        re.search(
            r"(?:ulmc|method\s+factor|latent\s+method).{0,80}(?:final|retained|included\s+in).{0,40}(?:model|analysis|structural)",
            text,
            re.I,
        )
        or re.search(
            r"(?:final|retained).{0,40}(?:model|analysis).{0,80}(?:ulmc|method\s+factor|latent\s+method)",
            text,
            re.I,
        )
    )
    excluded = bool(
        re.search(
            r"(?:ulmc|method\s+factor).{0,80}(?:excluded|removed|dropped|not\s+included).{0,40}(?:final|model|analysis)",
            text,
            re.I,
        )
    )
    ulmc_improves_fit = ""
    if improves and not no_improve:
        ulmc_improves_fit = "TRUE"
    elif no_improve and not improves:
        ulmc_improves_fit = "FALSE"

    ulmc_in_final = ""
    if in_final and not excluded:
        ulmc_in_final = "TRUE"
    elif excluded and not in_final:
        ulmc_in_final = "FALSE"

    return {
        "ulmc_improves_fit": ulmc_improves_fit,
        "ulmc_in_final": ulmc_in_final,
    }


def extract_mv_inference(text: str) -> dict[str, str]:
    """Regex hints for MV inference criteria and author conclusion."""
    not_problem_patterns = [
        r"common\s+method\s+(?:variance|bias).{0,60}(?:not\s+a\s+(?:concern|problem|threat|issue)|no\s+(?:concern|problem|threat))",
        r"(?:cmv|cmb|common\s+method).{0,40}(?:unlikely|minimal|does\s+not\s+(?:pose|represent|affect)|not\s+(?:serious|substantial))",
        r"method\s+(?:variance|bias).{0,40}(?:not\s+responsible|did\s+not\s+(?:affect|influence|bias))",
        r"common\s+method\s+bias\s+(?:was\s+)?not\s+a\s+(?:significant\s+)?(?:concern|problem|issue|threat)",
    ]
    inferred_not_problem = any(re.search(p, text, re.I) for p in not_problem_patterns)

    criteria_patterns = [
        ("Harman single factor below 50%", r"(?:harman|single[- ]factor|one[- ]factor).{0,120}(?:below|less\s+than|lower\s+than|under)\s*(?:50|fifty)"),
        ("no improvement in model fit with ULMC", r"(?:ulmc|method\s+factor).{0,80}(?:no|not|did\s+not).{0,40}(?:improv|better|significant).{0,40}(?:fit|chi)"),
        ("procedural remedies employed", r"(?:procedural|ex\s+ante).{0,60}(?:remed|address|reduce|minimiz).{0,40}(?:common\s+method|cmv|method\s+bias)"),
        ("ULMC method variance below threshold", r"(?:method\s+variance|ulmc).{0,80}(?:low|small|minimal|below|less\s+than|only)\s*(?:\d+|<)"),
    ]
    criteria_found = [label for label, pat in criteria_patterns if re.search(pat, text, re.I)]
    criteria_used = bool(criteria_found)
    if inferred_not_problem and not criteria_used and re.search(
        r"(?:common\s+method|cmv).{0,40}(?:not\s+a\s+concern|not\s+a\s+problem)", text, re.I
    ):
        criteria_found.append("CMV not a concern (unspecified)")
        criteria_used = True

    mv_inferred = ""
    if inferred_not_problem:
        mv_inferred = "TRUE"
    elif re.search(
        r"(?:cmv|common\s+method|method\s+bias).{0,60}(?:concern|threat|problem|bias(?:es)?|affect)",
        text,
        re.I,
    ) and not inferred_not_problem:
        mv_inferred = "FALSE"

    return {
        "mv_inference_criteria_used": "TRUE" if criteria_used else ("FALSE" if CMV_DISCUSSED.search(text) else ""),
        "mv_inference_criteria_list": "; ".join(dict.fromkeys(criteria_found)),
        "mv_inferred_not_problem": mv_inferred,
    }


def extract_sample_n(text: str) -> str:
    patterns = [
        r"(?i)(?:final\s+)?sample\s+(?:of|size|consisted\s+of|included)\s*(?:n\s*=?\s*)?(\d[\d,]*)",
        r"(?i)\bn\s*=\s*(\d[\d,]*)",
        r"(?i)(\d[\d,]*)\s+(?:participants|respondents|employees|students|subjects)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            n = m.group(1).replace(",", "")
            try:
                val = int(n)
                if 20 <= val <= 100000:
                    return str(val)
            except ValueError:
                pass
    return ""


def extract_estimator_software(text: str) -> tuple[str, str]:
    text_l = text.lower()
    estimator = ""
    if re.search(r"pls[- ]sem|partial least squares|smartpls", text_l):
        estimator = "PLS-SEM"
    elif re.search(r"cb[- ]sem|covariance[- ]based|lisrel|amos|mplus|lavaan", text_l):
        estimator = "CB-SEM"
    software = ""
    for name in ("Mplus", "AMOS", "LISREL", "Lavaan", "SmartPLS", "Stata", "SPSS", "R"):
        if re.search(rf"\b{re.escape(name)}\b", text, re.I):
            software = name
            break
    return estimator, software


def extract_statistical_methods(text: str) -> tuple[str, str]:
    methods: list[str] = []
    ulmc = any_match(text, ULMC_PATTERNS)
    harman = any_match(text, HARMAN_PATTERNS)
    if ulmc:
        methods.append("ULMC")
    if harman:
        methods.append("Harman single factor test")
    if re.search(r"marker\s+variable", text, re.I):
        methods.append("Lindell & Whitney marker variable")
    if re.search(r"lindell\s+&?\s+whitney", text, re.I):
        methods.append("Lindell & Whitney marker variable")
    if not methods and CMV_DISCUSSED.search(text):
        if re.search(r"latent\s+method\s+factor|common\s+method\s+factor|controlling\s+for.*method\s+factor", text, re.I):
            methods.append("ULMC")
            ulmc = True
        elif harman:
            methods.append("Harman single factor test")
    detail_parts = []
    if ulmc:
        detail_parts.append("unmeasured latent method construct (ulmc)")
    if harman:
        detail_parts.append("Harman's single factor test")
    return "; ".join(methods), "; ".join(detail_parts)


def extract_procedural(text: str) -> dict[str, str]:
    found: list[str] = []
    for pat, label in PROCEDURAL_PATTERNS:
        if re.search(pat, text, re.I):
            found.append(label)

    ms_same = any_match(text, MULTISOURCE_SAME_CONSTRUCT_PATTERNS)
    diff_iv_dv = any_match(text, DIFFERENT_SOURCES_IV_DV_PATTERNS)
    distinct_other = any_match(text, DISTINCT_SOURCES_OTHER_PATTERNS)
    generic_multisource = bool(re.search(r"\bmulti[- ]?source\b", text, re.I))

    if generic_multisource and not ms_same and not diff_iv_dv:
        distinct_other = True

    if ms_same:
        found.append("multisource_same_construct")
    if diff_iv_dv:
        found.append("different_sources_iv_dv")
    if distinct_other:
        found.append("distinct_sources_other")

    found = list(dict.fromkeys(found))
    used = "TRUE" if found else "FALSE"
    return {
        "procedural_remedies_used": used,
        "procedural_remedies_list": "; ".join(found),
        "multisource_same_construct": "TRUE" if ms_same else "FALSE",
        "different_sources_iv_dv": "TRUE" if diff_iv_dv else "FALSE",
        "distinct_sources_other": "TRUE" if distinct_other else "FALSE",
    }


def extract_step1_presence_stats(text: str) -> tuple[str, str]:
    """Regex hints for Step 1 CMV presence nested Δχ² and p-value; verify manually."""
    delta = ""
    pvalue = ""
    delta_patterns = [
        r"(?i)(?:delta|Δ)\s*(?:chi|χ)[²2].{0,40}?[=:]\s*(\d+(?:\.\d+)?)",
        r"(?i)(?:nested|difference).{0,60}(?:chi|χ)[²2].{0,40}?[=:]\s*(\d+(?:\.\d+)?)",
        r"(?i)(?:trait[- ]only|baseline).{0,80}(?:trait\+|with).{0,40}(?:ulmc|method).{0,80}(?:delta|Δ)\s*(?:chi|χ)[²2].{0,20}?[=:]\s*(\d+(?:\.\d+)?)",
    ]
    for p in delta_patterns:
        m = re.search(p, text)
        if m:
            delta = m.group(1)
            break
    p_patterns = [
        r"(?i)(?:delta|nested|difference).{0,80}(?:chi|χ)[²2].{0,80}?p\s*[=<]\s*(0\.\d+|\.\d+)",
        r"(?i)(?:trait[- ]only|baseline).{0,120}(?:ulmc|method\s+factor).{0,120}?p\s*[=<]\s*(0\.\d+|\.\d+)",
        r"(?i)(?:presence|cmv|common\s+method).{0,80}(?:chi|χ)[²2].{0,60}?p\s*[=<]\s*(0\.\d+|\.\d+)",
    ]
    for p in p_patterns:
        m = re.search(p, text)
        if m:
            pvalue = m.group(1).lstrip(".")
            if pvalue.startswith("."):
                pvalue = "0" + pvalue
            break
    return delta, pvalue


def extract_three_step_hints(text: str) -> dict[str, str]:
    """Minimal regex pre-fill for three-step ULMC fields; human verification required."""
    delta_chisq, presence_p = extract_step1_presence_stats(text)
    step1 = any_match(text, STEP1_PRESENCE_PATTERNS) or bool(delta_chisq)
    step1_cmv = any_match(text, STEP1_CMV_INDICATED_PATTERNS) or (
        bool(presence_p) and float(presence_p) < 0.05
    )
    method_r = any_match(text, METHOD_R_PATTERNS)
    bias_test = any_match(text, STEP2_BIAS_TEST_PATTERNS) or (
        method_r and re.search(r"(?:nested|delta).*(?:chi|χ)", text, re.I)
    )
    bias_indicated = any_match(text, STEP2_BIAS_INDICATED_PATTERNS)
    step3 = any_match(text, STEP3_CONTAMINATION_PATTERNS)
    step3_indicator = bool(
        re.search(
            r"indicator.*method.*(?:variance|loading|loadings)|method.*(?:variance|loading).*(?:indicator|item)",
            text,
            re.I,
        )
    )
    step3_construct = any_match(text, STEP3_CONSTRUCT_MV_PATTERNS) or bool(
        re.search(r"method.*variance.*\d+(?:\.\d+)?\s*%", text, re.I)
    )
    no_bias = any_match(text, NO_BIAS_PATTERNS)
    mv_despite_no_bias = step3 and (no_bias or (bias_test and not bias_indicated))
    three_step_used = step1 or method_r or step3 or any_match(text, RICHARDSON_PATTERNS)
    three_step_complete = (
        step1
        and bias_test
        and step3
    )
    return {
        "three_step_approach_used": "TRUE" if three_step_used else "",
        "step1_presence_delta_chisq_reported": "TRUE" if step1 else "",
        "step1_presence_delta_chisq": delta_chisq,
        "step1_presence_pvalue": presence_p,
        "step1_cmv_indicated": "TRUE" if step1_cmv else "",
        "step1_baseline_reported": "TRUE" if step1 else "",
        "step2_method_r_model_reported": "TRUE" if method_r else "",
        "step2_method_r_bias_test_reported": "TRUE" if bias_test else "",
        "step2_bias_indicated": "TRUE" if bias_indicated else "",
        "step2_ulmc_reported": "TRUE" if bias_test else "",
        "step3_contamination_reported": "TRUE" if step3 else "",
        "step3_indicator_level_mv_reported": "TRUE" if step3_indicator else "",
        "step3_construct_level_mv_reported": "TRUE" if step3_construct else "",
        "method_variance_reported_despite_no_bias": "TRUE" if mv_despite_no_bias else "",
        "step3_chisq_diff_reported": "TRUE" if step3 else "",
        "three_step_complete": "TRUE" if three_step_complete else "FALSE",
    }


def extract_author_conclusion(text: str) -> str:
    patterns = [
        r"(?i)common method (?:variance|bias).{0,60}(not a (?:concern|problem|threat|issue))",
        r"(?i)(?:cmv|cmb).{0,40}(?:not (?:a )?(?:concern|problem|threat|issue)|minimal|unlikely)",
        r"(?i)method (?:variance|bias).{0,40}(?:serious|substantial|significant)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            snippet = m.group(0)[:120].strip()
            if "not a" in snippet.lower() or "not " in snippet.lower():
                return "not a concern - " + snippet[:80]
            return "concern - " + snippet[:80]
    return ""


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


def get_extraction_fieldnames() -> list[str]:
    legacy = load_csv(LEGACY_EXTRACTION)
    if legacy:
        names = list(legacy[0].keys())
    else:
        names = [
            "study_order", "study_title", "authors", "year", "journal", "doi",
            "publisher_outlet", "publisher_outlet_detail", "empirical_ulmc", "not_pls",
            "pls_sem_used", "statistical_methods_mv", "statistical_method_detail",
            "method_variance_pct", "harman_deployed", "sample_n", "estimator", "software",
            "author_conclusion_mv", "procedural_remedies_used", "procedural_remedies_list",
            "richardson_2009_cited", "notes",
        ]
    if "predatory_journal_flag" not in names:
        idx = names.index("publisher_outlet_detail") + 1 if "publisher_outlet_detail" in names else len(names)
        names.insert(idx, "predatory_journal_flag")
    proc_idx = names.index("procedural_remedies_list") + 1 if "procedural_remedies_list" in names else len(names)
    for field in ("multisource_same_construct", "different_sources_iv_dv", "distinct_sources_other"):
        if field not in names:
            names.insert(proc_idx, field)
            proc_idx += 1
    if "three_step_approach_used" in names:
        insert_at = names.index("three_step_approach_used") + 1
        for field in reversed(CANONICAL_THREE_STEP_FIELDS):
            if field not in names:
                names.insert(insert_at, field)
    for tail in ("master_id", "extraction_source", "coding_mode"):
        if tail not in names:
            names.append(tail)
    return names


def existing_study_orders() -> set[str]:
    orders: set[str] = set()
    for path in (EXTRACTION_PATH, LEGACY_EXTRACTION):
        for row in load_csv(path):
            if row.get("study_order"):
                orders.add(row["study_order"])
    return orders


def eligible_for_extraction(master: dict[str, str]) -> bool:
    status = master.get("screening_status", "")
    if status not in ("included", "pending"):
        return False
    if status == "pending" and master.get("screening_level1_include") != "True":
        return False
    return True


def build_extraction_row(row: dict[str, str], text: str, *, auto_promote: bool = False) -> dict[str, str]:
    text = normalize_pdf_text(text)
    mid = row["article_id"]
    title = row.get("title") or ""
    authors = row.get("authors") or ""
    year = row.get("year") or ""
    journal = row.get("journal") or ""
    doi = row.get("doi") or "NA"

    outlet, outlet_detail = infer_publisher_outlet(doi, journal)
    stat_methods, stat_detail = extract_statistical_methods(text)
    estimator, software = extract_estimator_software(text)
    proc = extract_procedural(text)
    three_step = extract_three_step_hints(text)
    mv_pct = extract_mv_pct(text)
    harman_pct = extract_harman_variance_pct(text)
    complexity = extract_model_complexity(text)
    ulmc_outcomes = extract_ulmc_outcomes(text)
    mv_inference = extract_mv_inference(text)
    sample_n = extract_sample_n(text)
    biz_school, biz_detail = extract_business_school_affiliation(text)
    pls_used = any_match(text, PLS_PATTERNS)
    empirical_ulmc = any_match(text, ULMC_PATTERNS)
    harman = any_match(text, HARMAN_PATTERNS) or bool(harman_pct)

    note_flags: list[str] = []
    cmv_discussed = bool(CMV_DISCUSSED.search(text))
    if not mv_pct and cmv_discussed:
        mv_pct = "not reported"
        note_flags.append("method_variance_pct not reported in PDF")
    if not proc["procedural_remedies_list"] and cmv_discussed:
        proc = {**proc, "procedural_remedies_list": "none reported"}
        note_flags.append("procedural_remedies none reported in PDF")

    short_title = title[:80] + ("..." if len(title) > 80 else "")
    study_title = f"{authors.split(';')[0].strip() if authors else mid} ({year}) - {short_title}"

    ext = {
        "study_order": mid,
        "master_id": mid,
        "study_title": study_title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": doi or "NA",
        "publisher_outlet": outlet or "NA",
        "publisher_outlet_detail": outlet_detail or "NA",
        "predatory_journal_flag": "TRUE" if outlet == "MDPI" else "FALSE",
        "management_domain": "TRUE" if row.get("screening_level1_include") == "True" else "",
        "empirical_ulmc": "TRUE" if empirical_ulmc else "FALSE",
        "not_pls": "FALSE" if pls_used else "TRUE",
        "pls_sem_used": "TRUE" if pls_used else "FALSE",
        "statistical_methods_mv": stat_methods,
        "statistical_method_detail": stat_detail,
        "method_variance_pct": mv_pct,
        "harman_variance_pct": harman_pct,
        "harman_deployed": "TRUE" if harman else "FALSE",
        "sample_n": sample_n,
        "estimator": estimator,
        "software": software,
        "author_conclusion_mv": extract_author_conclusion(text),
        "procedural_remedies_used": proc["procedural_remedies_used"],
        "procedural_remedies_list": proc["procedural_remedies_list"],
        "multisource_same_construct": proc["multisource_same_construct"],
        "different_sources_iv_dv": proc["different_sources_iv_dv"],
        "distinct_sources_other": proc["distinct_sources_other"],
        "richardson_2009_cited": "TRUE" if any_match(text, RICHARDSON_PATTERNS) else "FALSE",
        "authors_business_school": biz_school,
        "author_affiliation_detail": biz_detail,
        **ulmc_outcomes,
        **complexity,
        **mv_inference,
        **three_step,
        "extraction_source": f"extract_ebsco_on_hand_batch.py {date.today().isoformat()}",
        "notes": "Automated pre-fill; requires human verification"
        + ("; " + "; ".join(note_flags) if note_flags else ""),
    }
    if auto_promote and is_fully_coded_row(ext):
        ext["coding_mode"] = "ai_autonomous"
        ext["notes"] = "AI-autonomous pre-fill (>=4 key fields); spot-check recommended"
        if note_flags:
            ext["notes"] += "; " + "; ".join(note_flags)
    return ext


def append_extractions(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    write_header = not EXTRACTION_PATH.exists()
    with open(EXTRACTION_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerows(rows)


def write_extractions(rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with open(EXTRACTION_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def upsert_extractions(rows: list[dict[str, str]], fieldnames: list[str]) -> tuple[int, int]:
    """Update existing study_order rows in place; append new ones. Returns (updated, appended)."""
    existing_rows = load_csv(EXTRACTION_PATH)
    by_order = {r.get("study_order", ""): r for r in existing_rows if r.get("study_order")}
    updated = appended = 0
    for row in rows:
        key = row.get("study_order", "")
        if not key:
            continue
        if key in by_order:
            merged = {**by_order[key], **row}
            by_order[key] = merged
            updated += 1
        else:
            by_order[key] = row
            appended += 1
    order = [r.get("study_order", "") for r in existing_rows if r.get("study_order")]
    for row in rows:
        key = row.get("study_order", "")
        if key and key not in order:
            order.append(key)
    out = [by_order[k] for k in order if k in by_order]
    write_extractions(out, fieldnames)
    return updated, appended


def update_master_extractions(
    results: list[dict[str, str]], dry_run: bool = False, *, auto_promote: bool = False
) -> tuple[int, int]:
    by_id = {r["master_id"]: r for r in results}
    today = date.today().isoformat()
    promoted = 0
    with master_file_lock():
        rows = load_csv(MASTER_PATH)
        fieldnames = list(rows[0].keys())
        updated = 0
        for row in rows:
            mid = row.get("article_id", "")
            if mid not in by_id:
                continue
            ext_row = by_id[mid]
            row["study_order"] = mid
            row["extraction_file"] = str(EXTRACTION_PATH.relative_to(ROOT))
            row["examination_updated_at"] = today
            row["updated_at"] = today
            if auto_promote and is_fully_coded_row(ext_row):
                row["examination_status"] = "fully_coded"
                row["extraction_status"] = "complete"
                row["examination_source"] = "ai_autonomous"
                promoted += 1
            else:
                row["extraction_status"] = "prefilled"
                row["examination_status"] = "partially_coded"
                row["examination_source"] = "extract_ebsco_on_hand_batch"
            updated += 1
        if not dry_run:
            write_master(rows, fieldnames)
    return updated, promoted


def get_targets(
    master_by_id: dict[str, dict[str, str]],
    limit: int | None,
    master_ids: list[str] | None,
    force_reextract: bool = False,
) -> list[str]:
    done = existing_study_orders() if not force_reextract else set()
    cohort_rows = load_csv(COHORT_CSV)
    cohort_ids = {r["article_id"] for r in cohort_rows if r.get("article_id")}
    included_ids = {
        r["article_id"]
        for r in cohort_rows
        if r.get("article_id") and r.get("screening_status") == "included"
    }

    if master_ids:
        return [m for m in master_ids if m in cohort_ids and (force_reextract or m not in done)]

    if force_reextract and included_ids:
        pool = sorted(included_ids)
    else:
        pool = sorted(cohort_ids)

    targets = []
    for mid in pool:
        row = master_by_id.get(mid)
        if not row:
            continue
        if mid in done:
            continue
        if not eligible_for_extraction(row):
            continue
        if not resolve_pdf_path(row):
            continue
        targets.append(mid)
        if limit and len(targets) >= limit:
            break
    return targets


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for r in rows if (r.get(field) or "").strip().upper() == "TRUE")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch extraction for EBSCO on-hand cohort")
    parser.add_argument("--limit", type=int, default=20, help="Max extractions (default 20; 0 = no limit)")
    parser.add_argument("--master-id", action="append", help="Extract specific master_id(s)")
    parser.add_argument(
        "--force-reextract",
        action="store_true",
        help="Re-run PDF extraction for cohort rows already in the on-hand CSV (upsert, no duplicates)",
    )
    parser.add_argument(
        "--auto-promote",
        action="store_true",
        help="Promote rows with >=4 key MV fields to fully_coded (coding_mode=ai_autonomous)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    limit = None if args.limit == 0 else args.limit

    master_rows = load_csv(MASTER_PATH)
    master_by_id = {r["article_id"]: r for r in master_rows}
    targets = get_targets(master_by_id, limit, args.master_id, force_reextract=args.force_reextract)

    if not targets:
        print("No eligible articles for extraction.")
        return

    print(f"Extracting {len(targets)} articles...")
    fieldnames = get_extraction_fieldnames()
    new_rows: list[dict[str, str]] = []

    for mid in targets:
        row = master_by_id[mid]
        pdf = resolve_pdf_path(row)
        if not pdf:
            print(f"  SKIP {mid}: PDF missing")
            continue
        try:
            text, _ = extract_text(pdf)
        except Exception as exc:
            print(f"  SKIP {mid}: {exc}")
            continue
        ext_row = build_extraction_row(row, text, auto_promote=args.auto_promote)
        new_rows.append(ext_row)
        print(f"  + {mid}: MV%={ext_row.get('method_variance_pct') or 'NA'} N={ext_row.get('sample_n') or 'NA'}")

    if not new_rows:
        print("No rows extracted.")
        return

    if args.dry_run:
        action = "upsert" if args.force_reextract else "append"
        print(f"[dry-run] Would {action} {len(new_rows)} rows to {EXTRACTION_PATH}")
        return

    if args.force_reextract:
        updated_rows, appended = upsert_extractions(new_rows, fieldnames)
        print(f"Upserted {len(new_rows)} rows ({updated_rows} updated, {appended} appended) in {EXTRACTION_PATH}")
    else:
        append_extractions(new_rows, fieldnames)
        print(f"Appended {len(new_rows)} rows to {EXTRACTION_PATH}")

    updated, promoted = update_master_extractions(new_rows, dry_run=False, auto_promote=args.auto_promote)
    print(f"Updated {updated} master rows ({promoted} promoted to fully_coded via ai_autonomous)")

    all_rows = load_csv(EXTRACTION_PATH)
    summary_fields = [
        "step1_presence_delta_chisq_reported",
        "step2_method_r_bias_test_reported",
        "step3_contamination_reported",
        "three_step_complete",
        "predatory_journal_flag",
    ]
    print("Summary (on-hand CSV):")
    for field in summary_fields:
        print(f"  {field}: {count_true(all_rows, field)}/{len(all_rows)} TRUE")


if __name__ == "__main__":
    main()
