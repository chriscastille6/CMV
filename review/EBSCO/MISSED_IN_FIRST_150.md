# Missed PDFs in EBSCO search positions 1–150

Generated: 2026-06-30

## Top line

**135 of 138** in-pool articles mapped to EBSCO positions 1–150 already have a PDF. **3** still need a download.

Registry snapshot: pool **570**, master-linked **548**, EBSCO PDFs downloaded **179**.

## How “first 150” is defined

**Primary worklist:** native EBSCO search order from `review/EBSCO/imports/EBSCO-Metadata-06_26_2026*.csv` (positions **1–150**).

Download queue (`download_queue_ebsco_order.csv`) sorts missing PDFs by `ebsco_search_position` ascending—not recent-first year sort.

`pool_id` P0001–P0150 remains year-desc for the full 570 registry; use `ebsco_search_position` for examination/download priority.

PDF present = `has_pdf` is true or `pdf_path` is non-empty in `articles_master.csv`.

## Counts

| Metric | Value |
|--------|------:|
| Screening pool | 570 |
| In master registry | 548 |
| EBSCO positions 1–150 mapped in pool | 138 |
| Positions 1–150 — have PDF | 135 |
| **Positions 1–150 — missing PDF** | **3** |

## Still to download (EBSCO positions 1–150 only)

| EBSCO pos | master_id | pool_id | Year | DOI | Title (short) |
|----------:|-----------|---------|-----:|-----|-----------------|
| 89 | M0721 | P0072 | 2026 | 10.1039/d5rp00404g | The relationship between teacher–student relationship and chemistry a… |
| 148 | M0722 | P0148 | 2025 | 10.3389/fpsyg.2025.1662636 | The impact of social support on the quality of sports participation a… |
| 150 | M0724 | P0158 | 2025 | 10.1007/s43621-025-02087-8 | The roles of finance opinion and income source in the link between fi… |

## Files

- CSV: `review/EBSCO/missed_in_first_150.csv` (3 rows)
- Worklist rule: `review/EBSCO/EBSCO_PRIMARY_WORKLIST.md`
- Regenerate: `python3 review/master/progress_counter.py`
