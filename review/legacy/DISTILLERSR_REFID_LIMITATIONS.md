# DistillerSR Refid Limitations

**Last updated**: 2026-06-24

## What Refid is

DistillerSR **Refid** is an internal row identifier assigned inside your DistillerSR project. It is **not** a DOI, PMID, or EBSCO accession number. Refids are stable *within* a project export but must not be treated as globally unique bibliographic keys.

In this repository, `legacy_refid` on `articles_master.csv` links a master row to the legacy gold-standard corpus (`legacy_extracted_data.csv`, 182 included studies from a 315-record DistillerSR export).

## Why Refid alone is unreliable for deduplication

| Issue | Example in this project |
|-------|-------------------------|
| Same study, two master rows | **M0073** (legacy, refid 142) and **M0400** (EBSCO batch 6) share DOI `10.5093/jwop2019a2` but only M0073 has `legacy_refid=142` |
| Refid present on one strand only | EBSCO imports do not carry DistillerSR refids; linkage is inferred via DOI/title |
| Export / re-import drift | Refids can shift if studies are deleted and re-added in DistillerSR |
| Journal-only weak matches | `ebsco_legacy_weak_matches.csv` — 101 journal-only gaps, 12 fuzzy title matches needing review |
| Hunt list refids | 10 refids (142, 147, 153, 160, 161, 163, 165, 166, 172, 191) flagged in `merge_sources.py` for manual PDF hunt |

**Rule**: Never collapse master rows using `legacy_refid` alone when DOI or title evidence disagrees.

## Preferred merge / link key priority

Use this order (matches `review/master/SCHEMA.md` and `merge_sources.py`):

1. **DOI** (normalized, lowercase, strip `https://doi.org/`) — **confirmed** duplicate when identical
2. **EBSCO accession number** (`ebsco_an`) — confirmed when identical
3. **Normalized title** (exact) or **title + year** fuzzy (ratio ≥ 0.92) — **probable**; human review required
4. **legacy_refid** — use only when **exactly one** master row holds that refid **and** DOI/title agree

## Handling known gap patterns

### 101 journal-only gaps

Legacy included studies with no DOI match in EBSCO exports often appear in `ebsco_legacy_weak_matches.csv` with `match_type=journal_only`. These are **not** duplicates — they are **candidate hunts**. Verify title, year, and MV% snippet before setting `legacy_refid`.

### 12 fuzzy title matches

Rows with `match_type=fuzzy_title` (e.g. refid 175 vs Korean correctional officers EBSCO title) need manual adjudication. Do not auto-merge; compare DistillerSR snippet to EBSCO abstract.

### Hunt list (10 refids)

For refids **142, 147, 153, 160, 161, 163, 165, 166, 172, 191**:

1. Search Zotero / EBSCO / manual PDF folders
2. Tag acquired PDFs `legacy-refid-{n}` in Zotero
3. Run ingest with `--force-master-id M####` if DOI is ambiguous
4. Update `legacy_182_zotero_inventory.csv` after confirmation

Refid **142** is resolved: PDF ingested to **M0073**; pool alias **M0400** synced via `sync_doi_aliases`.

## Workflow when Refid and DOI conflict

```
DistillerSR export says refid 142 → Study A
EBSCO import says DOI X → Study A (richer metadata)
Master already has M0073 (legacy refid 142) and M0400 (EBSCO, same DOI)
```

**Recommended action**:

1. Treat as **one study** (confirmed DOI duplicate)
2. **Keep** M0073 as canonical legacy row (`legacy_refid`, snippet, screening)
3. **Merge or link** M0400 metadata (authors, abstract, ebsco_an) into M0073
4. Retire duplicate `article_id` only after adjudication in `probable_duplicates_review.csv`

## Tools

| Command | Purpose |
|---------|---------|
| `python3 review/master/find_duplicates.py` | Master-row duplicate audit |
| `python3 review/master/merge_sources.py --check-only` | EBSCO import duplicate scan |
| `python3 review/master/check_examination_status.py --legacy-refid N` | Status before re-coding |
| `python3 review/master/merge_candidates.py` | Read-only merge preview |

## References

- `review/master/DUPLICATE_AUDIT_REPORT.md` — current duplicate counts
- `review/master/ebsco_legacy_weak_matches.csv` — weak legacy↔EBSCO links
- `review/legacy/ARTICLES_TO_FIND_10.md` — hunt list detail
- `review/EBSCO/pdfs/INGEST_LOG.csv` — PDF→master match audit trail
