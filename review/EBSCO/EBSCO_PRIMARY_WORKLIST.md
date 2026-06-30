# EBSCO primary worklist — native search order

**Updated**: 2026-06-26

## Rule

Download and examination priority for the EBSCO screening strand uses **native EBSCO search order** (`ebsco_search_position`), not the year-desc `pool_id` ranks (P0001–P0150).

| Artifact | Sort / scope |
|----------|----------------|
| `ebsco_search_position` | Positions **1–200** from `EBSCO-Metadata-06_26_2026*.csv` (4 × 50 rows) |
| `download_queue_ebsco_order.csv` | Missing PDFs, ascending `ebsco_search_position` |
| `missed_in_first_150.csv` | In-pool rows at positions 1–150 still missing a PDF |
| `ebsco_screening_pool_570.csv` | Full 570 pool; `pool_id` remains year-desc for registry |

## Import files (search order source)

| File | EBSCO positions |
|------|-----------------|
| `imports/EBSCO-Metadata-06_26_2026.csv` | 1–50 |
| `imports/EBSCO-Metadata-06_26_2026-2.csv` | 51–100 |
| `imports/EBSCO-Metadata-06_26_2026-3.csv` | 101–150 |
| `imports/EBSCO-Metadata-06_26_2026-4.csv` | 151–200 |

Position = export file order + batch offset (row 1 in file 2 → position 51).

## Batch 4 (151–200) — 2026-06-26

- **50** export rows; **18** in-pool (enrich existing master); **32** off-pool (skip, no new master rows).
- Position **151** = herpes zoster vaccination intention (Chongqing) — off-pool, exclude (public health).
- Position **199** = item-level CMV correction methods paper — off-pool (not in 570 registry).

## Metadata merge policy

- **132 in-pool DOI overlaps:** enrich existing `articles_master.csv` rows (abstract, plink, `ebsco_search_position`); no new master rows.
- **5 export-only rows** (positions 21, 89, 148, 149, 150): added to master 2026-06-26 via `add_export_only_master_rows.py` with user L1 decisions — see [`EBSCO_OFF_POOL_EXCLUSIONS.md`](EBSCO_OFF_POOL_EXCLUSIONS.md) (archived off-pool status).
- **17 export-only pool rows** (positions map to pool articles ranked P0160+): receive `ebsco_search_position` on enrich; they are in scope for positions 1–150 even if `pool_id` > P0150.

## Regenerate

```bash
python3 review/master/merge_sources.py      # enrich master from search-order export
python3 review/master/progress_counter.py   # pool, queue, missed-in-150, dashboards
```

## Related docs

- Prior comparison (recent-first vs export): `EBSCO_METADATA_06_26_2026_COMPARISON.md`
- Download progress: `../DOWNLOAD_EXAMINATION_PROGRESS.md`
- Config: `../config.yaml` → `ebsco_worklist`
