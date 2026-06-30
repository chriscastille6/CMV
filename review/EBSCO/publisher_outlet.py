"""Infer publisher_outlet from DOI prefix and journal name (extraction + screening pool)."""

from __future__ import annotations

PUBLISHER_OUTLETS: tuple[str, ...] = (
    "MDPI",
    "Frontiers",
    "Elsevier",
    "Springer",
    "Wiley",
    "SAGE",
    "Taylor & Francis",
    "Emerald",
    "APA/PSYC",
    "Other",
    "NA",
)

DOI_PREFIX_OUTLET: tuple[tuple[str, str], ...] = (
    ("10.3390/", "MDPI"),
    ("10.3389/", "Frontiers"),
    ("10.1016/", "Elsevier"),
    ("10.1007/", "Springer"),
    ("10.1186/", "Springer"),
    ("10.1002/", "Wiley"),
    ("10.1111/", "Wiley"),
    ("10.1177/", "SAGE"),
    ("10.1080/", "Taylor & Francis"),
    ("10.1108/", "Emerald"),
    ("10.1037/", "APA/PSYC"),
)

MDPI_JOURNAL_MARKERS: tuple[str, ...] = (
    "(mdpi)",
    "sustainability",
    "behavioral sciences",
    "administrative sciences",
    "international journal of environmental research and public health",
    "journal of theoretical & applied electronic commerce research",
)


def norm_doi(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if v.startswith(prefix):
            v = v[len(prefix) :]
    return v.strip()


def infer_publisher_outlet(doi: str | None, journal: str | None) -> tuple[str, str]:
    """Return (publisher_outlet, publisher_outlet_detail). Detail defaults to journal when inferred."""
    doi_norm = norm_doi(doi)
    journal_raw = (journal or "").strip()
    journal_lower = journal_raw.lower()

    for prefix, outlet in DOI_PREFIX_OUTLET:
        if doi_norm.startswith(prefix):
            detail = journal_raw if journal_raw and journal_raw.upper() != "NA" else ""
            return outlet, detail

    if "frontiers in" in journal_lower or journal_lower.startswith("frontiers "):
        return "Frontiers", journal_raw

    if any(marker in journal_lower for marker in MDPI_JOURNAL_MARKERS):
        return "MDPI", journal_raw

    if not doi_norm and not journal_lower:
        return "NA", ""

    return "NA", journal_raw if journal_raw and journal_raw.upper() != "NA" else ""
