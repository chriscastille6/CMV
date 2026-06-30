#!/usr/bin/env python3
"""Audit and flag probable duplicate rows in articles_master.csv."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_DIR = ROOT / "review" / "master"
MASTER_PATH = MASTER_DIR / "articles_master.csv"
REVIEW_CSV = MASTER_DIR / "probable_duplicates_review.csv"
AUDIT_REPORT = MASTER_DIR / "DUPLICATE_AUDIT_REPORT.md"
INGEST_LOG = ROOT / "review" / "EBSCO" / "pdfs" / "INGEST_LOG.csv"
DUPLICATES_FLAGGED = MASTER_DIR / "duplicates_flagged.csv"

TITLE_FUZZY_THRESHOLD = 0.92
MIN_FUZZY_TITLE_LEN = 25
PLACEHOLDER_TITLE_RE = re.compile(r"^legacy refid \d+ ulmc study$", re.I)

REVIEW_COLUMNS = [
    "group_id",
    "article_id_a",
    "article_id_b",
    "match_type",
    "confidence",
    "title_a",
    "title_b",
    "doi",
    "legacy_refid",
    "recommendation",
]

CONFIRMED_MATCH_TYPES = frozenset({"doi", "ebsco_an", "legacy_refid", "norm_title_exact"})
PROBABLE_MATCH_TYPES = frozenset({"title_fuzzy", "title_year_fuzzy", "cross_source_same_doi"})


def norm_doi(value: str | None) -> str:
    if not value:
        return ""
    v = value.strip().lower()
    if v in {"na", "n/a", "none", "null", "nan", "-"}:
        return ""
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if v.startswith(prefix):
            v = v[len(prefix) :]
    return v.rstrip(".,;)")


def norm_title(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def fuzzy_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def is_placeholder_title(title: str) -> bool:
    return bool(PLACEHOLDER_TITLE_RE.match(norm_title(title)))


def title_eligible_for_fuzzy(title: str) -> bool:
    nt = norm_title(title)
    return len(nt) >= MIN_FUZZY_TITLE_LEN and not is_placeholder_title(title)


def pair_dedupe_key(aid_a: str, aid_b: str) -> tuple[str, str]:
    return tuple(sorted([aid_a, aid_b]))


def source_flags(row: dict[str, str]) -> dict[str, bool]:
    sources = row.get("sources") or ""
    return {
        "legacy": "legacy_182" in sources,
        "ebsco": "ebsco_" in sources,
        "extraction": "extraction_csv" in sources,
        "zotero": "zotero_inventory" in sources,
    }


@dataclass
class DuplicatePair:
    article_id_a: str
    article_id_b: str
    match_type: str
    confidence: str
    title_a: str
    title_b: str
    doi: str = ""
    legacy_refid: str = ""
    score: float = 1.0
    group_key: str = ""

    def recommendation(self) -> str:
        if self.match_type in {"doi", "ebsco_an", "legacy_refid"}:
            return "merge"
        if self.match_type == "norm_title_exact":
            return "merge"
        if self.match_type == "cross_source_same_doi":
            return "link"
        if self.match_type in {"title_fuzzy", "title_year_fuzzy"}:
            if self.score >= 0.98:
                return "merge"
            return "link"
        return "keep_separate"

    def pair_key(self) -> tuple[str, str, str]:
        a, b = sorted([self.article_id_a, self.article_id_b])
        return (a, b, self.match_type)


@dataclass
class AuditStats:
    total_rows: int = 0
    doi_clusters: dict[str, list[str]] = field(default_factory=dict)
    title_clusters: dict[str, list[str]] = field(default_factory=dict)
    ebsco_an_clusters: dict[str, list[str]] = field(default_factory=dict)
    legacy_refid_clusters: dict[str, list[str]] = field(default_factory=dict)
    fuzzy_pairs: list[DuplicatePair] = field(default_factory=list)
    all_pairs: list[DuplicatePair] = field(default_factory=list)
    crosswalk_splits: list[dict[str, str]] = field(default_factory=list)
    ingest_ambiguous: list[dict[str, str]] = field(default_factory=list)
    ebsco_import_flags: int = 0
    placeholder_title_rows: int = 0


def cluster_by(rows: list[dict[str, str]], key_fn) -> dict[str, list[str]]:
    clusters: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        key = key_fn(row)
        if key:
            clusters[key].append(row.get("article_id", ""))
    return {k: v for k, v in clusters.items() if len(v) > 1}


def find_fuzzy_pairs(rows: list[dict[str, str]], threshold: float) -> list[DuplicatePair]:
    pairs: list[DuplicatePair] = []
    seen: set[tuple[str, str]] = set()
    eligible = [r for r in rows if title_eligible_for_fuzzy(r.get("title", ""))]
    for i, a in enumerate(eligible):
        for b in eligible[i + 1 :]:
            aid_a = a.get("article_id", "")
            aid_b = b.get("article_id", "")
            if not aid_a or not aid_b:
                continue
            nt_a = norm_title(a.get("title", ""))
            nt_b = norm_title(b.get("title", ""))
            if nt_a == nt_b:
                continue
            year_a = (a.get("year") or "").strip()
            year_b = (b.get("year") or "").strip()
            if year_a and year_b and year_a != year_b:
                continue
            score = fuzzy_ratio(a.get("title", ""), b.get("title", ""))
            if score < threshold:
                continue
            pair_ids = pair_dedupe_key(aid_a, aid_b)
            if pair_ids in seen:
                continue
            seen.add(pair_ids)
            match_type = "title_year_fuzzy" if year_a and year_b and year_a == year_b else "title_fuzzy"
            pairs.append(
                DuplicatePair(
                    article_id_a=aid_a,
                    article_id_b=aid_b,
                    match_type=match_type,
                    confidence="probable",
                    title_a=(a.get("title") or "").strip(),
                    title_b=(b.get("title") or "").strip(),
                    doi=norm_doi(a.get("doi")) or norm_doi(b.get("doi")),
                    legacy_refid=(a.get("legacy_refid") or b.get("legacy_refid") or "").strip(),
                    score=score,
                )
            )
    return pairs


def pairs_from_clusters(
    clusters: dict[str, list[str]],
    rows_by_id: dict[str, dict[str, str]],
    match_type: str,
    confidence: str,
    cluster_key_label: str = "",
) -> list[DuplicatePair]:
    pairs: list[DuplicatePair] = []
    for cluster_key, ids in clusters.items():
        for aid_a, aid_b in combinations(sorted(ids), 2):
            a = rows_by_id[aid_a]
            b = rows_by_id[aid_b]
            doi = norm_doi(a.get("doi")) or norm_doi(b.get("doi"))
            refid = (a.get("legacy_refid") or b.get("legacy_refid") or "").strip()
            if match_type == "doi" and not doi:
                continue
            pairs.append(
                DuplicatePair(
                    article_id_a=aid_a,
                    article_id_b=aid_b,
                    match_type=match_type,
                    confidence=confidence,
                    title_a=(a.get("title") or "").strip(),
                    title_b=(b.get("title") or "").strip(),
                    doi=doi if match_type == "doi" else (doi if doi else cluster_key_label or cluster_key),
                    legacy_refid=refid if match_type == "legacy_refid" else refid,
                    group_key=cluster_key,
                )
            )
    return pairs


def find_crosswalk_splits(rows: list[dict[str, str]], doi_clusters: dict[str, list[str]]) -> list[dict[str, str]]:
    splits: list[dict[str, str]] = []
    for doi, ids in sorted(doi_clusters.items()):
        if len(ids) < 2:
            continue
        involved = [r for r in rows if r.get("article_id") in ids]
        flags = [source_flags(r) for r in involved]
        has_legacy = any(f["legacy"] for f in flags)
        has_ebsco = any(f["ebsco"] for f in flags)
        has_extraction = any(f["extraction"] for f in flags)
        if sum([has_legacy, has_ebsco, has_extraction]) < 2:
            continue
        splits.append(
            {
                "doi": doi,
                "article_ids": ";".join(sorted(ids)),
                "legacy": str(has_legacy),
                "ebsco": str(has_ebsco),
                "extraction": str(has_extraction),
                "count": str(len(ids)),
            }
        )
    return splits


MATCH_TYPE_RANK = {
    "legacy_refid": 0,
    "doi": 1,
    "ebsco_an": 2,
    "norm_title_exact": 3,
    "title_year_fuzzy": 4,
    "title_fuzzy": 5,
}


def collapse_pair_list(pairs: list[DuplicatePair]) -> list[DuplicatePair]:
    """One row per article_id pair; keep strongest match type."""
    best: dict[tuple[str, str], DuplicatePair] = {}
    for p in pairs:
        key = pair_dedupe_key(p.article_id_a, p.article_id_b)
        existing = best.get(key)
        if existing is None:
            best[key] = p
            continue
        p_rank = MATCH_TYPE_RANK.get(p.match_type, 99)
        e_rank = MATCH_TYPE_RANK.get(existing.match_type, 99)
        if p_rank < e_rank or (p_rank == e_rank and p.score > existing.score):
            best[key] = p
    return sorted(
        best.values(),
        key=lambda p: (
            0 if p.confidence == "confirmed" else 1,
            MATCH_TYPE_RANK.get(p.match_type, 99),
            -p.score,
            p.article_id_a,
            p.article_id_b,
        ),
    )


def assign_group_ids(pairs: list[DuplicatePair]) -> dict[tuple[str, str], str]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for p in pairs:
        union(p.article_id_a, p.article_id_b)

    roots: dict[str, list[str]] = defaultdict(list)
    for p in pairs:
        for aid in (p.article_id_a, p.article_id_b):
            roots[find(aid)].append(aid)

    group_map: dict[tuple[str, str], str] = {}
    for idx, (_root, members) in enumerate(sorted(roots.items(), key=lambda x: min(x[1])), start=1):
        gid = f"G{idx:04d}"
        member_set = sorted(set(members))
        for p in pairs:
            key = pair_dedupe_key(p.article_id_a, p.article_id_b)
            if p.article_id_a in member_set and p.article_id_b in member_set:
                group_map[key] = gid
    return group_map


def audit_master(rows: list[dict[str, str]]) -> AuditStats:
    stats = AuditStats(total_rows=len(rows))
    rows_by_id = {r["article_id"]: r for r in rows if r.get("article_id")}

    stats.doi_clusters = cluster_by(rows, lambda r: norm_doi(r.get("doi")))
    stats.title_clusters = cluster_by(
        rows,
        lambda r: norm_title(r.get("title"))
        if title_eligible_for_fuzzy(r.get("title", ""))
        else "",
    )
    stats.ebsco_an_clusters = cluster_by(rows, lambda r: (r.get("ebsco_an") or "").strip())
    stats.legacy_refid_clusters = cluster_by(rows, lambda r: (r.get("legacy_refid") or "").strip())

    pairs: list[DuplicatePair] = []
    pairs.extend(
        pairs_from_clusters(stats.doi_clusters, rows_by_id, "doi", "confirmed")
    )
    pairs.extend(
        pairs_from_clusters(stats.ebsco_an_clusters, rows_by_id, "ebsco_an", "confirmed")
    )
    pairs.extend(
        pairs_from_clusters(stats.legacy_refid_clusters, rows_by_id, "legacy_refid", "confirmed")
    )
    pairs.extend(
        pairs_from_clusters(stats.title_clusters, rows_by_id, "norm_title_exact", "confirmed")
    )

    stats.fuzzy_pairs = find_fuzzy_pairs(rows, TITLE_FUZZY_THRESHOLD)

    confirmed_keys = {
        pair_dedupe_key(p.article_id_a, p.article_id_b) for p in pairs
    }
    for fp in stats.fuzzy_pairs:
        key = pair_dedupe_key(fp.article_id_a, fp.article_id_b)
        if key not in confirmed_keys:
            pairs.append(fp)
            confirmed_keys.add(key)

    stats.all_pairs = collapse_pair_list(pairs)
    stats.crosswalk_splits = find_crosswalk_splits(rows, stats.doi_clusters)
    stats.placeholder_title_rows = sum(
        1 for r in rows if is_placeholder_title(r.get("title", ""))
    )
    stats.ebsco_import_flags = len(read_csv(DUPLICATES_FLAGGED))

    for log_row in read_csv(INGEST_LOG):
        if "ambiguous" in (log_row.get("match_type") or ""):
            stats.ingest_ambiguous.append(log_row)

    return stats


def count_cluster_rows(clusters: dict[str, list[str]]) -> int:
    return sum(len(ids) for ids in clusters.values())


def write_review_csv(pairs: list[DuplicatePair], out_path: Path) -> None:
    group_map = assign_group_ids(pairs)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for p in pairs:
            key = pair_dedupe_key(p.article_id_a, p.article_id_b)
            writer.writerow(
                {
                    "group_id": group_map.get(key, ""),
                    "article_id_a": p.article_id_a,
                    "article_id_b": p.article_id_b,
                    "match_type": p.match_type,
                    "confidence": p.confidence,
                    "title_a": p.title_a,
                    "title_b": p.title_b,
                    "doi": p.doi,
                    "legacy_refid": p.legacy_refid,
                    "recommendation": p.recommendation(),
                }
            )


def format_pair_line(p: DuplicatePair, rank: int) -> str:
    rec = p.recommendation()
    doi_part = f" DOI `{p.doi}`" if p.doi else ""
    refid_part = f" refid {p.legacy_refid}" if p.legacy_refid else ""
    score_part = f" score={p.score:.3f}" if p.match_type.startswith("title") else ""
    return (
        f"{rank}. **{p.article_id_a}** ↔ **{p.article_id_b}** "
        f"({p.match_type}, {p.confidence}{score_part}) — *{rec}*{doi_part}{refid_part}\n"
        f"   - A: {p.title_a[:100]}{'…' if len(p.title_a) > 100 else ''}\n"
        f"   - B: {p.title_b[:100]}{'…' if len(p.title_b) > 100 else ''}"
    )


def write_audit_report(stats: AuditStats, out_path: Path) -> None:
    today = date.today().isoformat()
    confirmed = [p for p in stats.all_pairs if p.confidence == "confirmed"]
    probable = [p for p in stats.all_pairs if p.confidence == "probable"]
    doi_row_dupes = count_cluster_rows(stats.doi_clusters)
    title_row_dupes = count_cluster_rows(stats.title_clusters)
    fuzzy_only = [p for p in probable if p.match_type.startswith("title")]

    lines = [
        "# Master Duplicate Audit Report",
        "",
        f"**Generated**: {today}",
        f"**Script**: `review/master/find_duplicates.py`",
        f"**Master file**: `articles_master.csv` ({stats.total_rows} rows)",
        "",
        "## Executive summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total master rows | {stats.total_rows} |",
        f"| Rows in duplicate DOI clusters | {doi_row_dupes} |",
        f"| Rows in duplicate normalized-title clusters | {title_row_dupes} |",
        f"| Rows in duplicate EBSCO AN clusters | {count_cluster_rows(stats.ebsco_an_clusters)} |",
        f"| Legacy refids mapping to >1 master row | {len(stats.legacy_refid_clusters)} refids ({count_cluster_rows(stats.legacy_refid_clusters)} rows) |",
        f"| Fuzzy title pairs (≥ {TITLE_FUZZY_THRESHOLD}, not exact norm title) | {len(fuzzy_only)} |",
        f"| Total adjudication pairs (review CSV) | {len(stats.all_pairs)} |",
        f"| Confirmed duplicate pairs | {len(confirmed)} |",
        f"| Probable duplicate pairs | {len(probable)} |",
        f"| Cross-source splits (legacy+EBSCO+extraction, same DOI) | {len(stats.crosswalk_splits)} |",
        f"| INGEST_LOG ambiguous DOI matches | {len(stats.ingest_ambiguous)} |",
        f"| EBSCO import flags (`duplicates_flagged.csv`) | {stats.ebsco_import_flags} |",
        f"| Placeholder legacy titles (excluded from fuzzy) | {stats.placeholder_title_rows} |",
        "",
        "Cross-batch EBSCO duplicates (30) are collapsed at merge time; see `duplicate_report.md`.",
        "",
        "## DOI duplicate clusters",
        "",
    ]

    if stats.doi_clusters:
        for doi, ids in sorted(stats.doi_clusters.items()):
            lines.append(f"- `{doi}` → {', '.join(sorted(ids))} ({len(ids)} rows)")
    else:
        lines.append("- None.")

    lines.extend(["", "## Legacy refid collisions", ""])
    if stats.legacy_refid_clusters:
        for refid, ids in sorted(stats.legacy_refid_clusters.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            lines.append(f"- refid **{refid}** → {', '.join(sorted(ids))}")
    else:
        lines.append("- None (each legacy_refid maps to at most one row).")

    lines.extend(["", "## EBSCO AN collisions", ""])
    if stats.ebsco_an_clusters:
        for an, ids in sorted(stats.ebsco_an_clusters.items()):
            lines.append(f"- AN `{an}` → {', '.join(sorted(ids))}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Cross-source crosswalk (same DOI, separate article_ids)", ""])
    if stats.crosswalk_splits:
        for s in stats.crosswalk_splits:
            lines.append(
                f"- `{s['doi']}` → {s['article_ids']} "
                f"(legacy={s['legacy']}, ebsco={s['ebsco']}, extraction={s['extraction']})"
            )
    else:
        lines.append("- None detected.")

    lines.extend(["", "## Top 10 pairs for human review", ""])
    top10 = stats.all_pairs[:10]
    if top10:
        for i, p in enumerate(top10, start=1):
            lines.append(format_pair_line(p, i))
            lines.append("")
    else:
        lines.append("- No duplicate pairs flagged.")

    lines.extend(
        [
            "## Ingest ambiguous matches",
            "",
        ]
    )
    if stats.ingest_ambiguous:
        for row in stats.ingest_ambiguous:
            lines.append(
                f"- `{row.get('filename')}` → **{row.get('master_id')}** "
                f"({row.get('match_type')}); PDF: `{row.get('pdf_path')}`"
            )
    else:
        lines.append("- None in INGEST_LOG.")

    lines.extend(
        [
            "",
            "## Recommended workflow",
            "",
            "1. Review `probable_duplicates_review.csv` — sort by `confidence` then `recommendation`.",
            "2. **Confirmed** (`doi`, `ebsco_an`, `legacy_refid`, `norm_title_exact`): adjudicate merge vs link.",
            "3. **Probable** (`title_fuzzy`): verify year/journal/authors before merge.",
            "4. For legacy+EBSCO splits (e.g. M0073/M0400): prefer **link** or merge into legacy row; keep `legacy_refid`.",
            "5. Do **not** dedupe on DistillerSR refid alone — see `review/legacy/DISTILLERSR_REFID_LIMITATIONS.md`.",
            "6. After adjudication, run `python3 review/master/merge_candidates.py` (read-only preview) before any manual merge.",
            "7. Re-run `python3 review/master/find_duplicates.py` after master edits.",
            "",
            "## Related files",
            "",
            "- `review/master/probable_duplicates_review.csv` — adjudication queue",
            "- `review/master/duplicates_flagged.csv` — EBSCO import-time flags (`merge_sources.py`)",
            "- `review/master/duplicate_report.md` — EBSCO batch duplicate scan",
            "- `review/master/ebsco_legacy_weak_matches.csv` — weak legacy↔EBSCO links",
            "- `review/legacy/DISTILLERSR_REFID_LIMITATIONS.md` — refid guidance",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def print_summary(stats: AuditStats) -> None:
    confirmed = sum(1 for p in stats.all_pairs if p.confidence == "confirmed")
    probable = sum(1 for p in stats.all_pairs if p.confidence == "probable")
    print(f"Master rows: {stats.total_rows}")
    print(f"DOI duplicate clusters: {len(stats.doi_clusters)} ({count_cluster_rows(stats.doi_clusters)} rows)")
    print(f"Legacy refid collisions: {len(stats.legacy_refid_clusters)}")
    print(f"EBSCO AN collisions: {len(stats.ebsco_an_clusters)}")
    print(f"Adjudication pairs: {len(stats.all_pairs)} (confirmed={confirmed}, probable={probable})")
    print(f"Cross-source splits: {len(stats.crosswalk_splits)}")
    print("\nTop 10 pairs:")
    for i, p in enumerate(stats.all_pairs[:10], start=1):
        print(
            f"  {i}. {p.article_id_a} <-> {p.article_id_b} "
            f"[{p.match_type}/{p.confidence}] -> {p.recommendation()}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit articles_master.csv for duplicates")
    parser.add_argument(
        "--master",
        type=Path,
        default=MASTER_PATH,
        help="Path to articles_master.csv",
    )
    parser.add_argument("--no-write", action="store_true", help="Print summary only; do not write outputs")
    args = parser.parse_args()

    rows = read_csv(args.master)
    if not rows:
        print(f"No rows in {args.master}", file=sys.stderr)
        return 1

    stats = audit_master(rows)
    print_summary(stats)

    if not args.no_write:
        write_review_csv(stats.all_pairs, REVIEW_CSV)
        write_audit_report(stats, AUDIT_REPORT)
        print(f"\nWrote {REVIEW_CSV}")
        print(f"Wrote {AUDIT_REPORT}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
