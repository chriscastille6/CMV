# Master Article Registry Schema

Canonical schema for `articles_master.csv` — unified article registry for the ULMC systematic review (182 legacy gold standard + new EBSCO harvests + extraction rows).

**Last updated**: 2026-06-24 (examination tracking)

---

## Merge keys (deduplication priority)

| Priority | Field | Normalization |
|----------|-------|---------------|
| 1 | `legacy_refid` | Integer Refid (when present on both sides) |
| 2 | `doi` | Lowercase, strip `https://doi.org/` prefix |
| 3 | `ebsco_an` | EBSCO accession number (`an` in raw export) |
| 4 | `title` + `year` | Title normalized (lowercase, alnum only); fuzzy ratio ≥ 0.92 |

When records merge, `sources` is unioned (semicolon-separated). Richer non-empty metadata wins field-by-field.

---

## Field groups

### Identification

| Column | Type | Description |
|--------|------|-------------|
| `article_id` | string | Stable internal ID (`M0001`, assigned at merge) |
| `title` | string | Article title |
| `authors` | string | Author list (EBSCO `contributors` or extraction `authors`) |
| `year` | integer | Publication year |
| `journal` | string | Source journal name |
| `volume` | string | Volume |
| `issue` | string | Issue |
| `doi` | string | Digital Object Identifier |
| `ebsco_an` | string | EBSCO accession number |
| `abstract` | string | Abstract text (when available) |
| `ebsco_db` | string | EBSCO database name (`longDBName` or `shortDBName`) |
| `ebsco_plink` | string | EBSCO permalink URL |
| `cover_date` | string | Cover date string from EBSCO |

### Sources (provenance)

| Column | Type | Description |
|--------|------|-------------|
| `sources` | string | Semicolon-separated source tags (see below) |
| `source_import_file` | string | Most recent import filename(s) |
| `ebsco_batch` | integer | EBSCO download batch number (1 = records 1–50, 2 = 51–100, …) |

**Source tag values**:

| Tag | Meaning |
|-----|---------|
| `legacy_182` | Included in legacy gold standard (`final_include=TRUE`) |
| `ebsco_2026_06_batch1` | EBSCO metadata export June 2026, records 1–50 (`EBSCO-Metadata-06_24_2026-2.csv`) |
| `ebsco_2026_06_batch2` | EBSCO metadata export June 2026, records 51–100 (`EBSCO-Metadata-06_24_2026-3.csv`) |
| `ebsco_2026_02` | Prior EBSCO export from Feb 2026 PDF parse (`ebsco_export_50_records.csv`) |
| `extraction_csv` | Row in `systematic_extraction_40_studies.csv` |
| `zotero_inventory` | Metadata from `legacy_182_zotero_inventory.csv` |

### Legacy linkage

| Column | Type | Description |
|--------|------|-------------|
| `legacy_refid` | integer | DistillerSR Refid (1–315 corpus; 182 included) |
| `legacy_final_include` | boolean | Legacy gold-standard flag |
| `legacy_text_snippet` | string | DistillerSR text extraction snippet |
| `legacy_mv_pct` | float | Legacy `method_variance_pct` when numeric |
| `legacy_match_method` | string | How legacy_refid was linked (`refid_direct`, `doi`, `title_fuzzy`, `overlap_report`, `manual`) |
| `legacy_match_confidence` | string | `exact`, `probable`, `weak`, `none` |

### Screening

| Column | Type | Description |
|--------|------|-------------|
| `screening_status` | string | `pending`, `level1_pass`, `level1_fail`, `excluded_pls`, `included` |
| `screening_level1_include` | boolean | Legacy Q1 chain result when known |
| `screening_notes` | string | Free-text adjudication notes |

Screening questions align with `review/config.yaml` Level 1 (Q1.1 domain, Q1.2 empirical ULMC, Q1.3 PLS exclude).

### Extraction

| Column | Type | Description |
|--------|------|-------------|
| `extraction_status` | string | `none`, `partial`, `legacy_only`, `complete` (ranked; merge prefers higher) |
| `study_order` | string | Key in `systematic_extraction_40_studies.csv` (numeric or `L{refid}`) |
| `extraction_file` | string | Path to detailed extraction row source |

Detailed extraction fields (ULMC %, Harman, procedural remedies, author business-school affiliation, etc.) remain in `systematic_extraction_40_studies.csv` and are joined via `study_order` / `legacy_refid`. Do not duplicate the full extraction schema here.

**Extraction-time-only fields** (not columns on `articles_master.csv`):

| Field | Reason |
|-------|--------|
| `authors_business_school` | Author affiliations are not a structured EBSCO export column; some EBSCO abstracts embed partial affiliation text, but coverage is unreliable. Code from PDF title page during full-text extraction. |
| `author_affiliation_detail` | Same — verbatim affiliation lines require PDF/manual coding. |

### Examination (agent-facing)

Single source of truth for “has this study been examined for MV strategy?” — computed by `examination.py` on each merge/backfill.

| Column | Type | Description |
|--------|------|-------------|
| `examination_status` | string | `not_read`, `pdf_missing`, `read_snippet_only`, `partially_coded`, `fully_coded` |
| `pdf_status` | string | `unknown`, `missing`, `available` |
| `corpus_tier` | string | `legacy_gold`, `extraction_coded`, `ebsco_screened`, `supplementary` |
| `examination_source` | string | Semicolon-separated audit trail (how status was derived) |
| `examination_updated_at` | date | Last examination-status computation |

**`examination_status` values**:

| Value | Meaning |
|-------|---------|
| `not_read` | No snippet, no extraction row, not yet coded |
| `pdf_missing` | Included/queued but no PDF and no usable snippet |
| `read_snippet_only` | Legacy DistillerSR snippet only; structured CSV incomplete |
| `partially_coded` | Extraction CSV row exists; key MV fields incomplete |
| `fully_coded` | Structured extraction complete (≥4 key fields or `extraction_status=complete`) |

**`corpus_tier`**: Replaces hard “182 boundary” for agents. `legacy_gold` = `legacy_final_include=TRUE`; final included set may grow beyond 182 via new `screening_status=included` rows.

**Query CLI**: `python3 review/master/check_examination_status.py --help`

### Assets

| Column | Type | Description |
|--------|------|-------------|
| `zotero_key` | string | Zotero item key (e.g. `74ZMKM9E`) |
| `pdf_path` | string | Relative path to local PDF when known |
| `has_pdf` | boolean | PDF availability flag |

### Audit

| Column | Type | Description |
|--------|------|-------------|
| `notes` | string | General notes |
| `created_at` | date | First seen in master |
| `updated_at` | date | Last merge update |

---

## Relationship to other files

```
articles_master.csv          ← canonical registry (this schema)
├── legacy_extracted_data.csv     (182 included via legacy_refid)
├── refid_journal_mapping.csv     (journal backfill for legacy)
├── legacy_182_overlap_report.csv (prior overlap adjudication)
├── systematic_extraction_40_studies.csv  (detailed extraction; join on study_order)
├── legacy_182_zotero_inventory.csv       (Zotero/PDF status)
└── EBSCO/imports/*.csv               (raw EBSCO exports)
```

---

## Manual fields (user-maintained)

After each merge, review and fill as needed:

1. **`screening_status`** — for new EBSCO hits not in legacy 182
2. **`zotero_key`** / **`pdf_path`** — after PDF hunt and Zotero import
3. **`legacy_refid`** — when fuzzy match needs adjudication (`legacy_match_confidence=weak`)
4. **`screening_notes`** — document exclude/include rationale
5. **`extraction_status`** — promote to `complete` after full template extraction
6. **`examination_status`** — auto-computed on merge; use `check_examination_status.py` before re-coding a study
