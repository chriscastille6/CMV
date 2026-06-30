# EBSCO export 06_26_2026 vs project first-150

Generated: 2026-06-26

## Status

**Primary worklist** is now EBSCO native search order — see [`EBSCO_PRIMARY_WORKLIST.md`](EBSCO_PRIMARY_WORKLIST.md).

| | EBSCO export (06_26) | Prior project rule (deprecated) |
|--|----------------------|----------------------------------|
| Sort | Native search order (`ebsco_search_position`) | Recent-first (year ↓, `pool_id`) |
| First batch | Positions **1–150** | P0001–P0150 by year |
| Queue file | `download_queue_ebsco_order.csv` | ~~`download_queue_recent_first.csv`~~ |

## Your export

Three files in `review/EBSCO/imports/`:

- `EBSCO-Metadata-06_26_2026.csv` — EBSCO positions **1–50**
- `EBSCO-Metadata-06_26_2026-2.csv` — positions **51–100**
- `EBSCO-Metadata-06_26_2026-3.csv` — positions **101–150**

**150 rows** total (149 with DOI).

## Merge outcome

- **132 in-pool overlaps:** enriched via `merge_sources.py` → `ebsco_search_position` + abstracts.
- **5 off-pool:** skipped (no new master rows).
- **17 export-only pool rows** (pool articles at `pool_id` P0160+): now mapped by `ebsco_search_position` within 1–150.
- **Missed PDFs:** regenerated under EBSCO positions 1–150 → `missed_in_first_150.csv`.

## Positions 151–200 (batch 4 vs batch 5)

| File | Positions | Role |
|------|-----------|------|
| `EBSCO-Metadata-06_26_2026-4.csv` | **151–200** | **Canonical** — master enrichment, download queue, screening |
| `EBSCO-Metadata-06_26_2026-5.csv` | 151–200 (partial re-export) | **Archival only** — matches batch 4 at 151–163; **diverges at 164** (EBSCO pagination drift). Do not re-merge 164–200 from batch 5. |

**In-pool PDFs still needed (6):** see `missed_in_ebsco_151_200.csv`.

## Regenerate

```bash
python3 review/master/merge_sources.py
python3 review/master/progress_counter.py
```
