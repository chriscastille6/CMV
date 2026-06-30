# Download & Examination Progress — EBSCO Screening Pool

**Updated**: 2026-06-30  
**Canonical pool**: `review/EBSCO/ebsco_screening_pool_570.csv`  
**Download queue (EBSCO search order)**: `review/EBSCO/download_queue_ebsco_order.csv`

Regenerate after each download batch:

```bash
python3 review/master/progress_counter.py
```

---

## Screening pool (PRISMA EBSCO strand)

| Metric | Count |
|--------|------:|
| Screening pool (target) | **570** |
| In master registry | **548** |
| Pool gap (not yet in master) | **22** |

## PDF status (master-linked rows only)

| Status | Count |
|--------|------:|
| Downloaded (`has_pdf`, `pdf_path`, or Zotero PDF) | **179** |
| In Zotero (metadata, no PDF yet) | **0** |
| Missing | **369** |
| **Remaining to download** | **391** |

## Examination status (full 570 pool)

| Status | Count |
|--------|------:|
| fully_coded | **84** |
| partially_coded | **3** |
| read_snippet_only | **5** |
| not_read | **448** |
| not_in_master (pool gaps) | **22** |
| **Remaining to examine** (not fully_coded) | **486** |

---

## Gap notes

- **570** is the user-confirmed PRISMA deduplicated screening pool (`review/EBSCO/PRISMA_06_24_2026_UPDATE.md`).
- **548** unique EBSCO June 2026 rows are in `articles_master.csv` (expected ~511).
- **50** gap rows = EBSCO export positions **251–300** (not yet imported).
- **0** additional gap rows = reconcile with DistillerSR / remaining PRISMA pool.

## After downloading a PDF

1. Save the PDF under `review/pdfs/` (or your hunt folder).
2. Update the master row in `articles_master.csv`:
   - `has_pdf` = `True`
   - `pdf_path` = relative path to the file
   - `pdf_status` = `available` (optional; backfill script sets this)
   - `zotero_key` if added to Zotero
3. Re-run `python3 review/master/progress_counter.py` to refresh counts and the download queue.

Optional: run `python3 review/master/backfill_examination_status.py` after bulk master edits.
