# Manual Workflow — Master Article Registry

**Last updated**: 2026-06-24

This document describes how to import new EBSCO metadata exports and refresh `articles_master.csv`.

---

## EBSCO full-text PDF ingest (Downloads)

When you download **one article per PDF** from EBSCO (filename like `EBSCO-FullText-06_24_2026-N.pdf` in `~/Downloads`):

```bash
# Process all new EBSCO full-text PDFs in Downloads
python3 review/EBSCO/ingest_uploaded_pdfs.py --scan-downloads

# Preview matches without copying or updating master
python3 review/EBSCO/ingest_uploaded_pdfs.py --scan-downloads --dry-run

# Single file (Downloads, Safari temp path, etc.)
python3 review/EBSCO/ingest_uploaded_pdfs.py --pdf ~/Downloads/EBSCO-FullText-06_24_2026-4.pdf
```

The script parses each PDF, matches `articles_master.csv` (DOI, then title+year), copies to `review/EBSCO/pdfs/`, sets `has_pdf` / `pdf_path` / `pdf_status`, and appends `review/EBSCO/pdfs/INGEST_LOG.csv`. Batch reconciliation (exports 1–40): [`../EBSCO/pdfs/INGEST_BATCH_1_40_STATUS.md`](../EBSCO/pdfs/INGEST_BATCH_1_40_STATUS.md). If title parse fails but DOI is known: `--force-master-id M0xxx` (see INGEST_LOG `CORRECTION` notes).

**Concurrency:** Run **one ingest at a time**. Prefer a single `--scan-downloads` batch (PDFs processed serially inside one process). Do **not** launch multiple ingest agents in parallel (e.g. several `--pdf` runs at once) — concurrent writes can race on `articles_master.csv` even with file locking; the lock prevents corruption but one run may still overwrite another's in-flight update if matching against stale master state.

Then refresh progress and open the live dashboard:

```bash
python3 review/master/progress_counter.py
open review/PROGRESS_DASHBOARD.html
```

The dashboard has four tabs: **Progress** (download/examine counters), **PRISMA** (EBSCO strand flow with live PDF/coding counts), **Summary** (aggregated MV statistics from fully coded articles), and **Datasets** (row-level tables per article from `progress_results_data.json`).

**Audit trail** (after counter): `review/audit_results_report.md` (auto-generated; PASS/FAIL). To answer “how many PLS?” or trace a study: `python3 review/master/query_results.py --stat pls_count` — see [`../AUDIT_RESULTS_GUIDE.md`](../AUDIT_RESULTS_GUIDE.md).

### Audit workflow (before citing Summary numbers)

After any extraction CSV change or before citing counts in papers:

```bash
# Rebuild Datasets + Summary JSON and dashboard
python3 review/master/progress_counter.py

# Recompute metrics from Datasets and verify drill-down
python3 review/master/audit_results.py

# Query which studies belong to a count
python3 review/master/query_result.py --metric pls_cbsem --category CB-SEM
python3 review/master/query_result.py --study-order L142
```

Audit must **PASS** (exit 0). Report: [`../audit_results_report.md`](../audit_results_report.md). Methodology: [`../AUDIT_RESULTS_METHODOLOGY.md`](../AUDIT_RESULTS_METHODOLOGY.md).

For auto-refresh every 30s (optional — avoids `file://` JSON fetch limits):

```bash
cd review && python3 -m http.server 8765
# open http://localhost:8765/PROGRESS_DASHBOARD.html
```

Unmatched PDFs (status `unmatched` in the log) need manual review — often outside the 570 screening pool or missing metadata in master.

---

## When you share a new EBSCO export — duplicate check first

Before merging, run a duplicate preview:

```bash
# Check one new file against prior imports + legacy/extraction
python3 review/master/merge_sources.py --new-csv review/EBSCO/imports/EBSCO-Metadata-06_24_2026-N.csv

# Scan all configured batches without merging
python3 review/master/merge_sources.py --check-only
```

Outputs: `duplicate_report.md` (human summary) and `duplicates_flagged.csv` (machine flags).

A full merge (`python3 review/master/merge_sources.py`) prints duplicate warnings **before** writing `articles_master.csv`.

### Before coding or hunting a PDF — check examination status

```bash
python3 review/master/check_examination_status.py --summary
python3 review/master/check_examination_status.py --legacy-refid 142
python3 review/master/check_examination_status.py --unexamined --limit 20
```

Statuses: `not_read` → `read_snippet_only` → `partially_coded` → `fully_coded`. Do not re-extract if already `fully_coded` unless spot-checking. Refresh after bulk changes: `python3 review/master/backfill_examination_status.py`. See [`SCHEMA.md`](SCHEMA.md) and [`../REFACTOR_EXAMINATION_TRACKING.md`](../REFACTOR_EXAMINATION_TRACKING.md).

**Download / examination progress** (570 pool): `python3 review/master/progress_counter.py` → [`../DOWNLOAD_EXAMINATION_PROGRESS.md`](../DOWNLOAD_EXAMINATION_PROGRESS.md). **Zotero full crosswalk**: `python3 review/legacy/zotero_full_crosswalk.py` then `python3 review/master/backfill_zotero_keys.py`.

### Download / examination progress (570-pool)

After each PDF download batch, refresh the counter and download queue:

```bash
python3 review/master/progress_counter.py
open review/PROGRESS_DASHBOARD.html
```

Outputs: [`../PROGRESS_DASHBOARD.html`](../PROGRESS_DASHBOARD.html) (Progress + **PRISMA** + **Summary** + **Datasets** tabs), [`../progress_dashboard_data.json`](../progress_dashboard_data.json), [`../prisma_flow_data.json`](../prisma_flow_data.json), [`../progress_results_data.json`](../progress_results_data.json), [`../progress_summary_data.json`](../progress_summary_data.json), [`../DOWNLOAD_EXAMINATION_PROGRESS.md`](../DOWNLOAD_EXAMINATION_PROGRESS.md), [`../EBSCO/download_queue_ebsco_order.csv`](../EBSCO/download_queue_ebsco_order.csv), [`../audit_results_report.md`](../audit_results_report.md). **Audit queries**: [`../AUDIT_RESULTS_GUIDE.md`](../AUDIT_RESULTS_GUIDE.md) + `python3 review/master/query_results.py`.

**PRISMA tab**: static identification/dedup counts (1,036 → 570) from `review/EBSCO/PRISMA_06_24_2026_UPDATE.md`; live **PDFs downloaded** and **fully coded** from the counter. Override legacy included count: `python3 review/master/progress_counter.py --included 182`.

### What counts as a duplicate

| Match key | Rule |
|-----------|------|
| EBSCO AN | Exact accession number (`an` column) |
| DOI | Normalized DOI (lowercase, no URL prefix) |
| Title + year | Same year and title similarity ≥ 0.92 |

Reported scopes: **within-batch** (same CSV), **cross-batch** (two import files), **vs legacy 182** (Zotero inventory), **vs extraction CSV**.

### What to do

| Scope | Action |
|-------|--------|
| Within-batch | Remove the extra row from the export |
| Cross-batch | Merge collapses to one row — skip duplicate on re-export or delete from later batch |
| vs legacy / extraction | Review linkage; confirm `legacy_refid` or `study_order` |

---

## Quick refresh (after new EBSCO export)

```bash
# 1. Copy export into imports folder
cp ~/Downloads/EBSCO-Metadata-06_24_2026-N.csv review/EBSCO/imports/

# 2. Run duplicate check on the new file
python3 review/master/merge_sources.py --new-csv review/EBSCO/imports/EBSCO-Metadata-06_24_2026-N.csv

# 3. If this is a new batch, register it in merge_sources.py (see Multi-batch pattern below)

# 4. Re-run merge
python3 review/master/merge_sources.py

# 5. Review outputs
open review/master/duplicate_report.md
open review/master/merge_report.md
open review/master/articles_master.csv
```

---

## Multi-batch EBSCO import pattern

EBSCO Research exports are downloaded in **50-record chunks** from saved search results. Each chunk gets its own CSV in `review/EBSCO/imports/`.

| File | Records | `ebsco_batch` | `sources` tag | Status |
|------|---------|---------------|---------------|--------|
| `EBSCO-Metadata-06_24_2026-2.csv` | 1–50 | `1` | `ebsco_2026_06_batch1` | Merged |
| `EBSCO-Metadata-06_24_2026-3.csv` | 51–100 | `2` | `ebsco_2026_06_batch2` | Merged |
| `EBSCO-Metadata-06_24_2026-4.csv` | 101–150 | `3` | `ebsco_2026_06_batch3` | Merged |
| `EBSCO-Metadata-06_24_2026-5.csv` | 151–200 | `4` | `ebsco_2026_06_batch4` | Merged |
| `EBSCO-Metadata-06_24_2026-6.csv` | 201–250 | `5` | `ebsco_2026_06_batch5` | Merged |
| `EBSCO-Metadata-06_24_2026-7.csv` | 301–350 | `6` | `ebsco_2026_06_batch6` | Merged |
| `EBSCO-Metadata-06_24_2026-8.csv` | 351–400 | `7` | `ebsco_2026_06_batch7` | Merged |
| `EBSCO-Metadata-06_24_2026-9.csv` | 401–450 | `8` | `ebsco_2026_06_batch8` | Merged |
| `EBSCO-Metadata-06_24_2026-10.csv` | 451–500 | `9` | `ebsco_2026_06_batch9` | Merged |
| `EBSCO-Metadata-06_24_2026-11.csv` | 501–550 | `10` | `ebsco_2026_06_batch10` | Merged |
| `EBSCO-Metadata-06_24_2026-12.csv` | 551–570 | `11` | `ebsco_2026_06_batch11` | Merged (final export; 20 rows) |
| *(gap — not exported)* | **251–300** | — | — | Pending |

**Cumulative EBSCO rerun records (raw exports)**: **520** as of 2026-06-24 (search total **1,031** — see `review/EBSCO/EBSCO_SEARCH_06_24_2026.md`). Twenty-nine AN/DOI overlaps across batches (see `merge_report.md` / `duplicate_report.md`); **491** unique EBSCO rerun articles in master; **540** remaining (1,031 − 491). Positions **251–300** skipped (export gap). Batch 9 (`-9.csv`) overlapped heavily with batches 5 and 7 (8 duplicate ANs). Batch 10 (`-10.csv`) had 1 duplicate AN with batch 5. Batch 11 (`-11.csv`) had 5 duplicate DOIs with batch 5. Batch 12 (`-12.csv`, final) had **8** duplicate DOIs (7× batch 5, 1× batch 6, 1× batch 3) and **1** legacy 182 hit (refid 5); **12** net-new unique articles.

### Adding batch 251–300 (or later)
1. **Copy** the new file to `review/EBSCO/imports/` (dated filename).

2. **Register** in `review/master/merge_sources.py` → `DEFAULT_EBSCO_BATCHES` (increment `ebsco_batch` and `record_range`).

3. **Update** this table and `SCHEMA.md` source-tag list if you introduce a new tag name.

4. **Re-run** `python3 review/master/merge_sources.py`.

5. **Check** `merge_report.md` for:
   - Duplicate ANs across batches (6 overlap as of batch 4 merge: 5× batch 1↔3, 1× batch 2↔4)
   - Crosswalk hits against legacy 182 / hunt-list refids
   - Total master row count vs. expected unique articles

---

## Column parity check

All June 2026 EBSCO metadata exports share **37 columns** (EBSCO Research CSV schema):

`longDBName`, `shortDBName`, `an`, `title`, `abstract`, `publicationDate`, `contributors`, … `retractionNote`

The older Feb 2026 export (`ebsco_export_50_records.csv`) uses a **reduced 11-column** layout from PDF parsing — it is merged separately, tagged `ebsco_2026_02`.

---

## After merge — manual adjudication

See `SCHEMA.md` § Manual fields. Priority for new EBSCO-only rows:

1. **`screening_status`** — apply Level 1 from `review/config.yaml`
2. **`legacy_refid`** — when `legacy_match_confidence=weak`, compare journal + MV% + text snippet
3. **`zotero_key`** / **`pdf_path`** — after PDF hunt (see `review/legacy/ARTICLES_TO_FIND_10.md`)
4. **`extraction_status`** — promote to `complete` after full template extraction

---

## Extraction correction feedback loop

After human or agent coding overrides pipeline pre-fill:

```bash
python3 review/EBSCO/log_extraction_correction.py \
  --study-order 3 --field pls_sem_used --old TRUE --new FALSE --note "CB-SEM study"

python3 review/EBSCO/extraction_feedback_report.py
```

See [`../EBSCO/EXTRACTION_FEEDBACK_LOOP.md`](../EBSCO/EXTRACTION_FEEDBACK_LOOP.md).

---

## Related files

| File | Role |
|------|------|
| `review/master/articles_master.csv` | Canonical merged registry |
| `review/master/merge_report.md` | Auto-generated merge statistics |
| `review/master/duplicate_report.md` | Auto-generated duplicate scan |
| `review/master/duplicates_flagged.csv` | Machine-readable duplicate flags |
| `review/master/ebsco_legacy_weak_matches.csv` | Journal-only EBSCO ↔ legacy gap overlaps — verify before linking `legacy_refid` |
| `review/master/merge_sources.py` | Merge script |
| `review/master/SCHEMA.md` | Column definitions |
| `review/EBSCO/imports/` | Raw EBSCO CSV exports (do not edit) |
| `review/legacy/legacy_extracted_data.csv` | Legacy 182 gold standard |
| `review/EBSCO/systematic_extraction_40_studies.csv` | Detailed extraction rows |
| `review/EBSCO/extraction_corrections.csv` | Logged manual/agent overrides |
| `review/EBSCO/EXTRACTION_FEEDBACK_LOOP.md` | Correction logging + feedback report workflow |
| `review/AUDIT_RESULTS_METHODOLOGY.md` | How Summary metrics are computed |
| `review/master/audit_results.py` | Recompute + validate Summary vs Datasets |
| `review/master/query_result.py` | Drill-down queries by metric or study id |
