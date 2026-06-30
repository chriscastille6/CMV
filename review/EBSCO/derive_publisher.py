"""Alias for publisher_outlet inference (DOI prefix + journal name)."""

from publisher_outlet import (  # noqa: F401
    DOI_PREFIX_OUTLET,
    MDPI_JOURNAL_MARKERS,
    PUBLISHER_OUTLETS,
    infer_publisher_outlet,
    norm_doi,
)

__all__ = [
    "DOI_PREFIX_OUTLET",
    "MDPI_JOURNAL_MARKERS",
    "PUBLISHER_OUTLETS",
    "infer_publisher_outlet",
    "norm_doi",
]
