# ULMC Systematic Review — Restart Checklist

**Created**: 2026-06-24  
**Updated**: 2026-06-24 — examination tracking refactor; final included set may exceed 182  
**Scope**: **182 legacy gold** (`review/legacy/legacy_extracted_data.csv`) plus EBSCO/supplementary rows; **`screening_status=included`** defines synthesis set (may grow past 182).  
**Master registry**: **`review/master/articles_master.csv`** — unified database (`merge_sources.py`; post-merge PDF links: `review/EBSCO/sync_pdf_links_from_ingest.py` (runs automatically); [`master/MANUAL_WORKFLOW.md`](master/MANUAL_WORKFLOW.md)). **Download/examination priority**: EBSCO native search order (`ebsco_search_position` 1–150) — [`EBSCO/EBSCO_PRIMARY_WORKLIST.md`](EBSCO/EBSCO_PRIMARY_WORKLIST.md); queue `review/EBSCO/download_queue_ebsco_order.csv`. **Before re-coding any study**: `python3 review/master/check_examination_status.py --legacy-refid N` (or `--doi` / `--article-id`). Plan: [`REFACTOR_EXAMINATION_TRACKING.md`](REFACTOR_EXAMINATION_TRACKING.md). **New EBSCO CSV → `--check-only` first**; see [`master/duplicate_report.md`](master/duplicate_report.md). **After each PDF download batch**: `python3 review/master/progress_counter.py` → [`DOWNLOAD_EXAMINATION_PROGRESS.md`](DOWNLOAD_EXAMINATION_PROGRESS.md) + live [`PROGRESS_DASHBOARD.html`](PROGRESS_DASHBOARD.html) (**Progress** | **Summary** | **Datasets** tabs; Summary includes **ULMC by journal**, **publisher outlet counts**, and **supplement/incomplete-main-text flags** — [`ULMC_BY_JOURNAL.md`](ULMC_BY_JOURNAL.md)) + audit report [`audit_results_report.md`](audit_results_report.md); trace Summary numbers via [`AUDIT_RESULTS_GUIDE.md`](AUDIT_RESULTS_GUIDE.md) / `query_results.py`. **Before citing Summary stats**: `python3 review/master/audit_results.py` (must PASS); drill-down via `python3 review/master/query_result.py` — see [`AUDIT_RESULTS_METHODOLOGY.md`](AUDIT_RESULTS_METHODOLOGY.md).  
**Purpose**: Orient a fresh screening/extraction pass on retained PDFs with explicit capture of procedural remedies, Harman's single-factor test deployment, **publisher outlet (MDPI/Frontiers)**, **supplement/incomplete-main-text flags**, and **Step 1 CMV presence evidence** (nested Δχ²/p-value).

> **Schema note (2026-06-25)**: Primary search = narrow PROSPERO query (`"unmeasured latent method construct" OR "unmeasured latent method factor"`). Expanded Boolean/OpenAlex = supplementary only. Extraction emphasizes `content_domain`, `construct_names`, model complexity; **deprecated**: fit indices (CFI/RMSEA/SRMR/TLI), Quality Indicators (response rate, power, reliability), `industry_sector`. See `VARIABLE_CODEBOOK.md` §Deprecated Fields.

> **Scope note (2026-06-24)**: The 100-row `review/EBSCO/systematic_extraction_40_studies.csv` is **supplementary**. Overlap with legacy 182: **69 exact** (`L{refid}` rows) + **2 probable** + **10 weak** fuzzy matches on numeric rows; **101 legacy-only**; **19 CSV-only** outside legacy 182. Row-level detail: [`legacy/legacy_182_overlap_report.csv`](legacy/legacy_182_overlap_report.csv). Do not let the 19 CSV-only rows expand scope unless explicitly decided later (B2 PLS, B13 new search).
> **Protocol change (2026-06-25)**: Geographic distribution / `country` extraction dropped from active schema. Historical CSV columns remain; see `VARIABLE_CODEBOOK.md` §`country` (deprecated).


**Audit snapshot (182 path)**:

| Metric | Count | Source |
|--------|------:|--------|
| Legacy included (`final_include=TRUE`) | **182** | `legacy/legacy_extracted_data.csv` |
| With DistillerSR text snippet (`text_extraction`) | **182** | same |
| With numeric `method_variance_pct` | **71** | same |
| **Exact overlap in extraction CSV** (`L{refid}`) | **69** | `EBSCO/systematic_extraction_40_studies.csv` |
| Probable + weak fuzzy overlap (numeric rows) | **12** | `legacy/legacy_182_overlap_report.csv` |
| Reusable extraction (exact + probable) | **71** | same |
| Legacy-only — no CSV row | **101** | same |
| CSV-only — not in legacy 182 | **19** | same |
| Journal mapped (`refid_journal_mapping.csv`) | **182/182** | `EBSCO/refid_journal_mapping.csv` |
| Legacy rows in CSV missing year | **65/69** | journal often filled; year `NA` |

Full phased workplan: **`review/LEGACY_182_WORKPLAN.md`**.

---

## Section A: Screening Fields Confirmed

### Procedural remedies

| Field | Type | Where defined |
|-------|------|---------------|
| `procedural_remedies_used` | Boolean | `review/config.yaml`, CSV, codebook, template Q2.7 |
| `procedural_remedies_list` | Semicolon-separated list (not intensity) | `review/config.yaml`, CSV, codebook, template Q2.8 |

**What we capture**: Whether authors report using any ex-ante procedural remedy (Podsakoff et al., 2003 style), and which specific remedies. Standard terms are documented in `review/EBSCO/VARIABLE_CODEBOOK.md` (anonymity, temporal/source/methodological separation, counterbalancing, item pretesting, cover story, objective measures, etc.). Use `"none"` when no remedies are reported.

**Validation rule**: If `procedural_remedies_list` is anything other than `"none"` or empty → `procedural_remedies_used` must be `TRUE`.

**Pipeline**: `review/EBSCO/enhanced_extraction_pipeline.R` regex-detects remedies (expanded 2026-06-24); manual extraction remains authoritative.

**Current CSV status**: Fields present in `review/EBSCO/systematic_extraction_40_studies.csv`. Some legacy rows have inconsistent boolean/list pairings (e.g., `procedural_remedies_used=FALSE` with remedies in `notes` or list) — needs spot-check on restart.

### Harman's single-factor test

| Field | Type | Where defined |
|-------|------|---------------|
| `harman_deployed` | Boolean (**new 2026-06-24**) | `review/config.yaml`, codebook, template Q2.9a, pipeline |
| `harman_variance_pct` | Numeric (%) | CSV, codebook, template Q2.4 |
| `statistical_methods_mv` | Text list (includes "Harman single factor test" when used) | CSV, codebook |

**What we capture**: Deployment (did authors run/report the test?) is now separate from the reported variance percentage. A non-missing `harman_variance_pct` implies deployment. Studies that mention Harman without a % still need `harman_deployed=TRUE`.

**Coding rule (draft — finalize in Section B)**: Code `TRUE` when authors report running Harman's test, CFA-based Harman, unrotated single-factor PCA/EFA on all items, or equivalent. Code `FALSE` when Harman is cited only as background with no indication the test was performed.

**Current CSV status**: `harman_deployed` column present; values need backfill on existing 100 rows.

**Pipeline**: `enhanced_extraction_pipeline.R` now regex-detects Harman deployment and extracts `harman_variance_pct` when reported.

### MV inference criteria (why authors judge MV a problem or not)

| Field | Type | Where defined |
|-------|------|---------------|
| `mv_inference_criteria_used` | Boolean | config Q2.14, codebook, template, pipeline |
| `mv_inference_criteria_list` | Semicolon-separated | config Q2.15, codebook (Harman &lt;50%, fit unchanged, procedural remedies, etc.) |
| `mv_inference_criteria_detail` | Text | config, codebook |
| `mv_inferred_not_problem` | Boolean | config Q2.16 |
| `mv_inference_rationale_text` | Text quote | config Q2.17 |

**Relationship**: `author_conclusion_mv` = outcome; criteria fields = documented reasons. **PLS** (`pls_sem_used`, `pls_variant`, `not_pls`, Q1.3) — still captured; excluded from CB-SEM synthesis but retained for inappropriate-method prevalence (`include_pls: true`).

**Current CSV status**: Columns added 2026-06-24; all rows `NA` until coded on next extraction pass.

### Model complexity (constructs, indicators, content domain)

| Field | Type | Where defined |
|-------|------|---------------|
| `content_domain` | Text | config Q2.19, codebook, template |
| `construct_names` | Text (semicolon-separated) | config Q2.19a, codebook, template |
| `num_constructs` | Numeric | config, codebook, template Q2.20, pipeline |
| `num_indicators` | Numeric | config, codebook, template Q2.21, pipeline |
| `complexity_ratio` | Numeric | config, codebook, template Q2.22, pipeline |
| `underpowered_heuristic` | Boolean (derived) | dashboard Summary/Datasets only (`build_results_tables.py`) |

**Deprecated (do not code new rows)**: `industry_sector` — use `content_domain`.

### Step 1 CMV presence evidence (nested Δχ² / p-value)

| Field | Type | Where defined |
|-------|------|---------------|
| `step1_presence_delta_chisq_reported` | Boolean | config, codebook, template, `extract_ebsco_on_hand_batch.py` |
| `step1_presence_delta_chisq` | Numeric | config Q2.26a, codebook, pipeline |
| `step1_presence_pvalue` | Numeric | config Q2.26b, codebook, pipeline |
| `step1_cmv_indicated` | Boolean | config Q2.26c, codebook, template |

**Not extracted**: CFI, RMSEA, SRMR, TLI fit indices (deprecated).

**What we capture**: Size of the **tested ULMC CFA/SEM** — content domain, construct names, how many latent constructs, how many total indicators/items, and indicators-per-construct ratio.

**Coding definitions**:

- `content_domain` = substantive topic/phenomenon (primary contextual field)
- `construct_names` = latent construct labels in tested ULMC model
- `num_constructs` = latent constructs in tested structural/measurement model
- `num_indicators` = total items across all substantive scales in ULMC CFA
- `complexity_ratio` = `num_indicators / num_constructs`

**Underpowered heuristic** (coding guidance, not a statistical test): `TRUE` when any of — indicators < 15, ratio < 3, constructs > 10. See `VARIABLE_CODEBOOK.md`, `EXTRACTION_FEEDBACK_LOOP.md`, `AUDIT_RESULTS_METHODOLOGY.md` §Model complexity.

**Current CSV status**: Complexity columns present in `systematic_extraction_40_studies.csv`; `content_domain` and `construct_names` added to schema 2026-06-25 (not yet in CSV header). ~36 rows with `num_constructs`, ~18 with `num_indicators`, ~16 with `complexity_ratio`.

### Author business-school affiliation

| Field | Type | Where defined |
|-------|------|---------------|
| `authors_business_school` | Boolean | config Q2.18, codebook, template, pipeline |
| `author_affiliation_detail` | Text | config Q2.18a, codebook |

**Relationship**: `management_domain` = journal/topic; `authors_business_school` = at least one author at a business/management school (title-page coding). Extraction-time only — not on master registry (EBSCO lacks reliable affiliation).

### Publisher outlet & supplement flags

| Field | Type | Notes |
|-------|------|-------|
| `publisher_outlet` | Categorical | MDPI, Frontiers, Elsevier, … (DOI prefix + journal; see `publisher_outlet.py`) |
| `details_in_supplement` | Boolean | Key coding details only in supplement/appendix |
| `extraction_incomplete_main_text` | Boolean | ULMC/construct/indicator details missing from main PDF |

Summary tab includes **publisher-outlet counts** and **supplement/incomplete-main-text flag counts**; pool CSV gets auto-inferred `publisher_outlet` on `progress_counter.py` run.

### Alignment summary (post-audit)

| Artifact | Procedural remedies | Harman deployed | Harman % |
|----------|--------------------|-----------------|----------|
| `review/config.yaml` | ✅ | ✅ (added) | ✅ (added) |
| `review/schema.json` | ❌ (bibliographic only; not extraction CSV) | ❌ | ❌ |
| `VARIABLE_CODEBOOK.md` | ✅ | ✅ (added) | ✅ |
| `SYSTEMATIC_EXTRACTION_TEMPLATE.md` | ✅ (aligned) | ✅ (added) | ✅ |
| `systematic_extraction_40_studies.csv` | ✅ | ✅ column present | ✅ |
| `enhanced_extraction_pipeline.R` | ✅ (expanded regex) | ✅ (added) | ✅ (added) |
| Model complexity (`num_constructs`, `num_indicators`, `complexity_ratio`) | ✅ (clarified 2026-06-24) | — | — |
| `legacy/legacy_extracted_data.csv` | ❌ (text only) | ❌ (text only) | ❌ |

### PRISMA flow diagram (work to date)

Yes — PRISMA 2020 assets under `review/EBSCO/`. **Current default diagram** (`PRISMA2020_final.svg`) uses the **EBSCO strand**: **1,036** identification → **570** screened/FT-assessed → **182** included. See [`ANALYSIS_STATUS_REPORT.md`](ANALYSIS_STATUS_REPORT.md) for coding inventory, analyzed vs pending, and PDF gaps.

| Asset | Role |
|-------|------|
| **`review/EBSCO/PRISMA2020_final.svg`** | EBSCO strand (1,036 → 570 → 182); regenerated 2026-06-24 |
| `review/ANALYSIS_STATUS_REPORT.md` | **Coding schema, analyzed vs pending, PDF status** |
| `review/analysis_status_summary.csv` | Machine-readable counts for same |
| `review/EBSCO/PRISMA_06_24_2026_UPDATE.md` | PRISMA numbers, 570 vs master (506) discrepancy |
| `review/EBSCO/EBSCO_SEARCH_06_24_2026.md` | Export log (1,031 platform count), batch progress, gap 251–300 |
| `review/EBSCO/create_prisma2020_final_corrected.R` | Regen script (`PRISMA_MODE=ebsco_strand` default) |

**Known version conflicts** (resolve before publication): export log **1,031** vs PRISMA identification **1,036** (+5); PRISMA screened pool **570** vs **511** unique EBSCO rows in master (−59; export gap 251–300 still open + merge dedup). **2026-06-25**: merged `EBSCO-Metadata-06_25_2026-1.csv` (50 rows; mostly overlap with batches 5–6—not true 251–300 export; +5 net pool rows).; legacy PDFs **9/182** confirmed in Zotero. JAP draft still has `[PLACEHOLDER: Full PRISMA 2020 flow]`.

---

## Section B: Things for You to Look Into

### 1. Decisions to make

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B1 | ~~**Scope: 182 legacy vs. 100 current vs. full new search**~~ **RESOLVED: 182 legacy** | Target N = **182** (`legacy/legacy_extracted_data.csv`, `final_include=TRUE`). 100-study CSV is supplementary (69 overlap + 31 EBSCO). New search (~1,873) deferred unless B13 reopened. | ~~Large~~ **Done** |
| B2 | **Include PLS studies?** | `config.yaml` has `include_pls: true`; legacy excluded 24 PLS studies (`COMPLETE_315_REVIEW_PLAN.md`). Decide whether PLS rows stay in main analysis or tagged subgroup. | **Medium** |
| B3 | **Date range extension (2023–2026)** | Original: 2012–2022. Config end year: 2026 (2010 to date (2026)). EBSCO export Feb 2026 exists (`EBSCO_EXPORT_AND_ZOTERO_USE.md`). Refresh search? | **Large** |
| B4 | **Harman coding rules — finalize definition** | Draft rule in Section A. Edge cases: PCA vs. CFA Harman, "one factor did not explain majority" without %, citation-only mentions. Document in codebook. | **Quick** |
| B5 | **Procedural remedies coding rules** | No intensity scale — boolean + list only. Decide whether design features (e.g., longitudinal waves) count as "temporal separation" vs. `study_design`. | **Quick** |
| B6 | **AI screening validation scope** | Options in `SYSTEMATIC_REVIEW_PROGRESS.md` Q1: all 315 vs. sample vs. disagreements only. | **Medium** |

### 2. Metadata gaps

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B7 | **69 legacy studies missing journal/year** | `JOURNAL_YEAR_UPDATE_REQUIRED.md` — 69/69 legacy rows lack journal + year in CSV. Sources: Zotero, PDF headers, Crossref. | **Large** |
| B8 | **Study 3 metadata fix verified; spot-check others** | Study 3 journal/year was corrupted and fixed. Audit remaining EBSCO rows for swapped fields. | **Quick** |
| B9 | **Legacy studies not in Zotero** | **Audited 2026-06-24**: only **8/182** Refids in Zotero (8 with PDF). Prior 32-item folder = 8 legacy + 24 EBSCO supplements. See `legacy/ZOTERO_INVENTORY_SUMMARY.md`. **Action**: bulk import 174 gaps with `legacy-refid-{n}` tags (B24). | **Large** |

### 3. PDF acquisition blockers

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B10 | **EBSCO PDFs incomplete** | `PDF_DOWNLOAD_STATUS.md` — 23+ PDFs still needed for studies 31–60; 8 found at last count (`FINAL_STATUS_60_STUDIES.md`). | **Medium** |
| B11 | **PDF naming/location convention** | Expected: `review/EBSCO/pdfs/EBSCO/XXX_[Title].pdf`. Verify pipeline `pdf_dir` matches actual folder. | **Quick** |
| B12 | **New search records without PDFs** | ~1,476 filtered records need screening before PDF acquisition (`ZOTERO_SCREENING_STATUS.md`). | **Large** |

### 4. Search refresh

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B13 | **Re-run deduplicated search 2023–2026** | Repeat **primary narrow query**: [`SEARCH_STRATEGY_REPRODUCIBILITY.md`](SEARCH_STRATEGY_REPRODUCIBILITY.md) §1 (`"unmeasured latent method construct" OR "unmeasured latent method factor"` + standard limiters). Expanded Boolean/OpenAlex = supplementary only. Compare to legacy 656→315 pipeline. | **Large** |
| B14 | **PRISMA source categorization** | Open decisions in `PRISMA_DATA_QUESTIONS.md` (database vs. other methods columns). | **Medium** |
| B15 | **MDPI / publisher filters** | `config.yaml` excludes MDPI; some extracted studies are MDPI (`systematic_extraction_40_studies.csv` rows 4, 8, 12). Reconcile filter vs. retained set. | **Quick** |

### 5. AI validation of screening

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B16 | **Validate Level 1 against legacy 315** | Functions described in `SYSTEMATIC_REVIEW_PROGRESS.md`. Compare AI vs. DistillerSR Q1.1–Q1.3. | **Medium** |
| B17 | **Validate extraction fields on reexamined studies** | Studies 3–6 reexamined (`REEXAMINATION_STATUS.md`, `EXTRACTION_GAPS_ANALYSIS.md`). Use as gold-standard spot checks for Harman/procedural fields. | **Medium** |
| B18 | **Pipeline vs. manual discordance** | `enhanced_extraction_pipeline.R` is assistive; log overrides via `review/EBSCO/log_extraction_correction.py` + `extraction_feedback_report.py` ([`EXTRACTION_FEEDBACK_LOOP.md`](EBSCO/EXTRACTION_FEEDBACK_LOOP.md)). | **Quick** |

### 6. Harman & procedural remedies — extraction hygiene

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B19 | **Add `harman_deployed` column to CSV** | On next study extracted, add column to `systematic_extraction_40_studies.csv` header; backfill from `statistical_methods_mv` + `harman_variance_pct` for existing rows (no full re-read required). | **Quick** |
| B20 | **Audit procedural_remedies_used vs. list inconsistencies** | e.g., Study 10: `procedural_remedies_used=FALSE` but list has remedies. Fix on pass through. | **Medium** |
| B21 | **Distinguish ULMC `method_variance_pct` from `harman_variance_pct`** | Codebook rule exists; Study 6 shows contradictory Harman/L&W vs. ULMC conclusion — flag for narrative. | **Quick** |

### 7. Zotero / library workflow

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B22 | **Zotero folder hygiene** | 32 articles in "ULMC – Sys. Review" (`ZOTERO_SCREENING_STATUS.md`). Rule: screened articles must be in Zotero. | **Medium** |
| B23 | **Import EBSCO 50 + new search hits** | `EBSCO_EXPORT_AND_ZOTERO_USE.md`, `parse_ebsco_export_pdf.py`. | **Medium** |
| B24 | **Import legacy 182 for re-extraction** | May already have text in `legacy_extracted_data.csv` `text_extraction` column; PDFs may be elsewhere. | **Large** |

### 8. Manuscript integration

| # | Item | Context / files | Effort |
|---|------|-----------------|--------|
| B25 | **JAP Table A1 / appendix alignment** | Legacy inventory references Table A1 model comparisons (`legacy_all_315_inventory.csv`). Map extraction fields to manuscript tables (`SYSTEMATIC_REVIEW_PROGRESS.md` Step 5). | **Large** |
| B26 | **Update results narrative** | Procedural remedies prevalence, Harman deployment rates, Richardson (2009) citation patterns (`RICHARDSON_CITATION_ANALYSIS.md`). | **Medium** |
| B27a | **Study-level risk-of-bias / quality scoring** | Planned in early `PRISMA_PROTOCOL.md` §7 (STROBE-adapted); **not used — dropped per user decision**. No `config.yaml` extraction fields. | **N/A** |
| B27 | **PROSPERO / preregistration sync** | `PROSPERO_DRAFT_REGISTRATION_FINAL.md`, `PREREGISTRATION_PLAN.md` — ensure new fields reflected if registering update. | **Medium** |

### 9. Open questions from prior docs

| # | Question | Source |
|---|----------|--------|
| B28 | Potentially missed legacy Refids 6 and 85 — include? | `COMPLETE_315_REVIEW_PLAN.md` |
| B29 | PRISMA duplicate breakdown (81,771) — single line or by source? | `PRISMA_DATA_QUESTIONS.md` |
| B30 | Library Discovery Service credentials for search? | `SYSTEMATIC_REVIEW_PROGRESS.md` Q2 |
| B31 | Studies 31–32 are methodological papers — include in empirical synthesis? | `FINAL_STATUS_60_STUDIES.md` |
| B32 | `schema.json` is stale vs. `config.yaml` — update or deprecate? | This audit |

---

## Section C: Suggested Next Session Actions (182-legacy-first)

Ordered for the **182 legacy gold standard** path. See `review/LEGACY_182_WORKPLAN.md` for full detail.

1. **Reuse pass on 69–81 overlapping rows** — Backfill `harman_deployed` and fix procedural list/boolean pairs on legacy-linked rows in `systematic_extraction_40_studies.csv`; adjudicate 12 fuzzy matches in `legacy/legacy_182_overlap_report.csv` (2 probable + 10 weak).

2. **Metadata pass for all 182** (B7, B9) — Import Refids to Zotero; fill journal/year/DOI via `refid_journal_mapping.csv` (182/182 journals mapped) + Crossref; priority: 101 legacy-only rows, then fix 65 `L*` rows with `year=NA`.

3. **Locate first 10 PDFs** — Work through [`legacy/ARTICLES_TO_FIND_10.md`](legacy/ARTICLES_TO_FIND_10.md) (see **Search guidance** section for workflow, verification checklists, and probable DOIs); tag `legacy-refid-{n}` in Zotero; update `legacy_182_zotero_inventory.csv`.

4. **Fresh extraction queue for 101 legacy-only Refids** — All 182 have `text_extraction` snippets; run `enhanced_extraction_pipeline.R` where PDFs exist; manual template for procedural/Harman/three-step fields; append to master CSV with `legacy_refid` column.

---

## Section D: Automation vs. Your Manual Work

*Audit date: 2026-06-24*

| Stage | Automation today | Script / tool | Still requires you (why) | Min manual | Recommended manual |
|-------|------------------|---------------|---------------------------|------------|---------------------|
| **Search & deduplication** | **High** (~85–90%) | `review/01_search_harvest.R`, `review/02_normalize_filter.R`, `review/comprehensive_ulmc_search.R` | EBSCO / library Discovery exports are manual; merging legacy 656 + new OpenAlex/Crossref requires scope decisions (B1, B13); title-only dedup misses near-duplicates | 1–2 h (re-run scripts + merge) | 4–8 h (extend date range, reconcile legacy vs. new counts) |
| **Level 1 screening** (domain, empirical ULMC, PLS) | **Medium** (~50–60%) | `review/02_ai_validation_screening.R`, `review/quick_screening.R`, `review/ebsco_app.R` (abstract-only), `review/EBSCO/process_pdfs.R` | Abstract keywords miss nuanced domain/PLS calls; PLS in methods section only needs full text; final include/exclude is a judgment call; `02_ai_validation_screening.R` saves functions but does not batch-run legacy 315 yet | 3–6 h (triage ~100 known includes) | 20–40 h (~1,873 new records: AI pre-sort + human on borderline ~30–40%) |
| **PDF acquisition** | **Low** (~15–25%) | `review/EBSCO/download_ebsco_pdfs.R` (DOI publisher patterns; writes `download_instructions_31_60.csv`) | Paywalls, EBSCO plinks, missing DOIs; script succeeds on open-access only (~8 found for studies 31–60 per prior status); you download and name per `pdfs/EBSCO/XXX_[Title].pdf` | 2–4 h (remaining EBSCO gaps) | 15–30 h (182 legacy + new-search includes) |
| **Text extraction** | **High** (~90–95%) | `review/EBSCO/enhanced_extraction_pipeline.R`, `review/EBSCO/process_pdfs.R` | Scanned PDFs, tables, multi-column layouts; path mismatch if PDFs not under `review/EBSCO/pdfs/` | 0.5 h (batch run) | 2–4 h (fix failures, re-OCR edge cases) |
| **Structured extraction** (procedural remedies, Harman, MV%, three-step, Richardson) | **Medium** (~40–55%) | `review/EBSCO/enhanced_extraction_pipeline.R`, `review/EBSCO/VARIABLE_CODEBOOK.md`, `SYSTEMATIC_EXTRACTION_TEMPLATE.md` | Regex pre-fills booleans/lists/% but misses paraphrases, multi-table fit stats, Richardson “neutral vs. misuse”; three-step often incomplete in papers; **manual extraction remains authoritative** (Section A) | 8–15 h (hygiene on 100 rows: backfill `harman_deployed`, fix list/boolean pairs) | 40–70 h (full human pass on 100; ~25–40 min/study on nuanced fields) |
| **Metadata repair** (journal/year for legacy) | **Medium** (~50–65%) | Zotero MCP (`zotero_search_items`, `zotero_item_metadata`), `tools/jap_reviewer/corpus/zotero.py`, `crossref.py`; `01_search_harvest.R` Crossref | 69/69 legacy rows lack journal+year (`JOURNAL_YEAR_UPDATE_REQUIRED.md`); PDF-header regex in pipeline is brittle; legacy 182 not in Zotero (B9) | 3–5 h (Crossref/Zotero for 69) | 8–12 h (verify ambiguous matches, APA strings) |
| **QA / disagreement resolution** | **Low–medium** (~25–35%) | `review/02_ai_validation_screening.R` (`validate_screening`), `review/validate_against_legacy.R`, pipeline vs. CSV discordance flags | No auto-adjudication; Studies 3–6 gold-standard reexam; procedural/Harman edge cases need reading | 3–5 h (spot-check ~20 flagged studies) | 10–15 h (systematic dual-code sample + overrides) |
| **PRISMA regeneration** | **High** (~80%) once counts fixed | `review/EBSCO/create_prisma2020_final_corrected.R`, `PRISMA2020_yourdata.csv`, `review/04_synthesis.R` | Open decisions in `PRISMA_DATA_QUESTIONS.md`; conflicting totals (83,612 vs 83,644; included 180 vs 208 vs ~100); JAP draft still has PRISMA placeholder | 1–2 h (update CSV + re-run) | 3–5 h (reconcile sources, publication-ready caption) |
| **Manuscript integration** | **Low** (~10–20%) | `review/04_synthesis.R` (tables/figures from `review/extract.csv`), `tools/jap_reviewer/` (corpus search, not extraction) | Prose, Table A1 mapping, Richardson narrative, PROSPERO sync (B25–B27); `04_synthesis.R` expects older `extract.csv` schema, not current EBSCO CSV | 4–8 h (refresh tables from current CSV) | 15–25 h (full results + appendix alignment) |

### Supporting tools (assistive, not end-to-end)

| Tool | Role | Automation |
|------|------|------------|
| **Zotero MCP** (verified live) | Search library, metadata, fulltext by item key | Metadata lookup, PDF discovery — not screening/extraction |
| **`tools/jap_reviewer/corpus/ebsco.py`** | Keyword search over extraction CSV | Query existing corpus only |
| **`review/ebsco_app.R`** | Shiny: paste abstract → keyword flags | Abstract-only; no PDF extraction |
| **`review/validate_against_legacy.R`** | Title/author match tests | Diagnostic; not production screening |

### Honest bottom line

**A) Refresh 100-study corpus only** (coding hygiene + pipeline assist, not full re-read of every PDF):

- **Minimum (~12–20 h)**: Backfill `harman_deployed` and fix list/boolean pairs; batch-run `enhanced_extraction_pipeline.R` on existing PDFs; resolve metadata for 69 legacy rows via Zotero MCP + Crossref; spot-QA flagged discordance; update PRISMA counts + regenerate SVG; refresh synthesis tables.
- **Recommended (~35–50 h)**: Above plus human verification of procedural remedies, Harman deployment, three-step fit, and Richardson context on all 100 studies (~20 min/study average on judgment fields).
- **You cannot skip**: Scope/PLS decisions (B1–B2), paywalled PDFs, and nuanced extraction (Harman cited vs. run, remedy wording).

**B) Full 182 legacy + new search** (~1,873 deduplicated post-filter):

- **Minimum (~80–120 h)**: Re-run search/dedup scripts; AI Level 1 pre-sort + human on borderline set; acquire PDFs for expanded include set; semi-automated extraction + QA sample; metadata for full legacy; PRISMA + manuscript update.
- **Recommended (~150–250 h)**: Dual screening on disagreements, full human extraction pass on 182+, complete PDF corpus, systematic QA, publication-ready PRISMA and results narrative.
- **Automate first, then you**: Run `01_search_harvest.R` → `02_normalize_filter.R` → `quick_screening.R` / saved screening functions → `enhanced_extraction_pipeline.R` → `create_prisma2020_final_corrected.R`; your time concentrates on paywalls, borderline includes, and regex misses.

---

## Files modified in this audit (2026-06-24; schema 2026-06-25)

- `review/config.yaml` — narrow primary search; `content_domain`, `construct_names`, Step 1 presence Δχ²/p-value fields; Quality Indicators removed from schema
- `review/PRISMA_PROTOCOL.md` — primary narrow search; supplementary OpenAlex/expanded; extraction schema updates
- `review/SEARCH_STRATEGY_REPRODUCIBILITY.md` — narrow query as primary identification
- `review/EBSCO/VARIABLE_CODEBOOK.md` — content domain, Step 1 presence stats, deprecated fields section
- `review/EBSCO/SYSTEMATIC_EXTRACTION_TEMPLATE.md` — aligned checklist; fit indices and Quality Assessment removed
- `review/EBSCO/extract_ebsco_on_hand_batch.py` — Step 1 Δχ²/p-value regex hints
- `review/EBSCO/enhanced_extraction_pipeline.R` — Step 1 presence extraction; fit indices deprecated (NA)
- `review/RESTART_CHECKLIST.md` — schema/search notes

**Not modified**: `systematic_extraction_40_studies.csv` (no bulk re-extraction), `review/schema.json` (separate bibliographic schema).

## Section E: External automation — SciSciGPT (and alternatives)

### CMV baseline (for comparison)

This repo already automates substantial parts of the ULMC systematic review. SciSciGPT and other external tools should be judged against this baseline—not against a blank workflow.

| Stage | What CMV has | Maturity | Human still required |
|-------|--------------|----------|----------------------|
| **Search** | OpenAlex/Crossref scripts (`comprehensive_ulmc_search.R`, `refined_search_strategy.R`); EBSCO export + `parse_ebsco_export_pdf.py`; Zotero library ("ULMC – Sys. Review", 32 items); documented strategy in `SEARCH_STRATEGY_REPRODUCIBILITY.md`, `ONLINE_SEARCH_STRATEGY.md` | ✅ Run; counts in PRISMA assets (~83.6k identified) | Database credentials (B30); 2023–2026 refresh (B13); dedup rules |
| **Screening (L1)** | `review/config.yaml` Level 1 Q1.1–Q1.3 aligned to DistillerSR; `screening_functions.rds` + `02_ai_validation_screening.R` (domain, empirical ULMC, PLS) | ⚠️ Built, **not validated** (B6, B16) | Final include/exclude; ~1,476 Zotero records awaiting screening (B12) |
| **PDF acquisition** | `download_ebsco_pdfs.R`, `process_pdfs.R`; Shiny helpers (`ebsco_app.R`, `ebsco_pdf_app.R`); naming convention `review/EBSCO/pdfs/` | ⚠️ Partial (23+ PDFs missing for 31–60) | Paywalled downloads, manual retrieval |
| **Extraction (L2)** | `enhanced_extraction_pipeline.R` (regex assist for Harman, procedural remedies, ULMC fields); `SYSTEMATIC_EXTRACTION_TEMPLATE.md` + `VARIABLE_CODEBOOK.md`; `systematic_extraction_40_studies.csv` (100 rows); legacy 182 in `legacy_extracted_data.csv` | ✅ Assistive pipeline; manual authoritative | Nuanced coding (B4–B5, B18–B21); Richardson citation context |
| **Validation / QA** | `validate_extraction_data.R`, `validate_extractions.R`; reexamination notes (studies 3–6) | ⚠️ Spot-check only | Gold-standard discordance review |
| **PRISMA** | Multiple R generators; **`PRISMA2020_final.svg`**; CSV inputs; open count conflicts documented (Section A) | ✅ Visual exists; counts stale | Resolve B14, B29; regenerate after scope lock (B1) |
| **Library / refs** | Zotero MCP in Cursor; `EBSCO_EXPORT_AND_ZOTERO_USE.md` | ⚠️ Legacy 182 not in Zotero (B9) | Import hygiene (B22–B24) |
| **Config / schema** | `review/config.yaml` (search, filters, extraction fields, screening questions, outputs) | ✅ Source of truth for extraction | `schema.json` bibliographic-only (B32) |

**Bottom line for restart**: The critical path is scope decision → PDF unblock → validated screening/extraction on the **existing** R + CSV + Zotero stack—not standing up a new platform.

### What SciSciGPT is

[SciSciGPT](https://github.com/Northwestern-CSSI/SciSciGPT) (Northwestern CSSI; [Nature Computational Science](https://doi.org/10.1038/s43588-025-00906-6), Dec 2025) is a **multi-agent research assistant for the field of Science of Science (SciSci)**, not a PRISMA systematic-review platform. It offers a public chat at [sciscigpt.com](https://sciscigpt.com) and an open-source stack (AGPL-3.0, TypeScript frontend + Python/FastAPI backend, ~131 GitHub stars; last push **2026-01-16**).

Five agents orchestrate ad hoc research tasks:

| Agent | Role |
|-------|------|
| ResearchManager | Task decomposition and coordination |
| LiteratureSpecialist | RAG over **SciSciCorpus** (SciSci papers on Pinecone) |
| DatabaseSpecialist | SQL over **SciSciNet** (BigQuery scholarly graph) |
| AnalyticsSpecialist | Python/R/Julia sandboxes for plots and stats |
| EvaluationSpecialist | Self-evaluation / reward scoring |

**Tech stack & prerequisites (self-hosted):** Anaconda Python 3.11, LangChain/LangGraph, **Google Cloud** (Vertex AI + Claude, BigQuery, Cloud Storage), **Pinecone**, **OpenAI** embeddings, **Upstash Redis** (frontend auth/history). Recommended: 16 GB+ RAM, 100 GB+ disk. Setup is multi-hour DevOps, not `pip install`.

**Versus a traditional SR workflow:** SciSciGPT excels at exploratory SciSci questions, bibliometric SQL, and agent-driven analytics. It does **not** implement dual screening, exclusion logging, structured extraction forms, inter-rater agreement, or PRISMA-compliant audit trails out of the box.

### Fit for this ULMC project: **Low** (core workflow) / **Medium** (optional exploration)

| SR stage | SciSciGPT could… | SciSciGPT cannot… | CMV already has… |
|----------|------------------|-------------------|------------------|
| **Search** | Semantic discovery in SciSci literature; SQL on SciSciNet metadata | Reproduce your EBSCO/OpenAlex query strings; management/psychology domain filters; PROSPERO-aligned search log | Documented ULMC search + exports |
| **Screening** | Chat-style relevance triage (informal) | Level 1 Q1.1–Q1.3 with reproducible rules; PLS exclusion logic; disagreement tracking | `screening_functions.rds` + config.yaml |
| **PDF / full text** | Analyze uploaded files in sandbox (generic) | Batch process `review/EBSCO/pdfs/` into `systematic_extraction_40_studies.csv`; paywall acquisition | `enhanced_extraction_pipeline.R`, download scripts |
| **Extraction** | Summarize papers in prose | Reliably code `harman_deployed`, `procedural_remedies_list`, Richardson context, ULMC model variants to codebook spec | Field-specific regex + manual template |
| **PRISMA / synthesis** | Generate one-off figures via AnalyticsSpecialist | Regenerate your PRISMA 2020 counts from CMV CSVs; manuscript Table A1 alignment | `create_prisma2020_final_corrected.R`, SVG assets |
| **Integration** | — | Native Zotero MCP, EBSCO CSV, or `config.yaml` schema | End-to-end repo wiring |

### Integration feasibility with CMV assets

| Asset | Feasible integration? | Notes |
|-------|----------------------|-------|
| Zotero MCP | ❌ No native link | SciSciGPT uses its own Pinecone corpus, not your Zotero library |
| `review/EBSCO/*.csv` | ❌ Manual export only | No importer for structured extraction CSV |
| `review/config.yaml` | ❌ | ULMC field schema is project-specific; would require custom agent/tools |
| `enhanced_extraction_pipeline.R` | ⚠️ Conceptual only | Could borrow multi-agent *ideas*, not drop-in code (different stack: Vertex vs. local R) |
| PRISMA R scripts | ❌ | SciSciGPT does not replace `PRISMA2020` package workflow |

**Practical bridge (if experimenting):** Export a small pilot set (5–10 titles/abstracts) and compare SciSciGPT summaries to your codebook manually—do not pipe outputs into the CSV without validation.

### Risks for publication-grade use

1. **Hallucination / over-summary** — Harman deployment vs. citation-only mentions (Section A edge cases) need human coding; LLM summaries are not auditable extraction rows.
2. **Wrong corpus** — SciSciCorpus indexes SciSci field papers, not your ULMC management/psychology target set.
3. **Paywalls** — No substitute for EBSCO/manual PDF workflow (B10–B12).
4. **Reproducibility** — Agent trajectories vary run-to-run; AGPL self-hosting adds infra cost; hard to document for JAP methods appendix vs. fixed R scripts + `config.yaml`.
5. **Scope creep** — SciSciNet analytics (citations, fields) are orthogonal to ULMC prevalence/procedural-remedy synthesis.

### Alternatives (better matched to SR stages)

| Tool | Best for | Fit vs. CMV |
|------|----------|-------------|
| **Extend CMV R scripts** | Screening validation, extraction assist, PRISMA regen | ✅ **Recommended** — schema and legacy gold standard already here |
| **ASReview** | Active-learning title/abstract screening | Medium — could accelerate ~1,476 Zotero records; export decisions back to repo |
| **Rayyan / Covidence** | Dual screening, exclusion reasons | Medium — if collaborating; re-import to CSV manually |
| **Elicit / Semantic Scholar** | Exploratory abstract search | Low–medium — search only; no ULMC coding |
| **SciSciGPT (demo or self-host)** | SciSci bibliometrics, exploratory agent analytics | Low for ULMC SR core |

### Prerequisites (if trying SciSciGPT anyway)

- **Quick look:** [sciscigpt.com](https://sciscigpt.com) — no install; test whether answers are useful for *background* SciSci questions (not ULMC coding).
- **Self-host pilot:** GCP project + service account, Pinecone + OpenAI keys, Upstash Redis, conda env, SciSciNet/SciSciCorpus notebook builds (~hours). Budget for cloud API usage.
- **License:** AGPL-3.0 — derivative deployments must share source; consider if that matters for any fork.

### Recommendation: **Hybrid — extend CMV scripts; optional SciSciGPT demo only**

| Priority | Action |
|----------|--------|
| 1 | **Extend CMV** — Validate `02_ai_validation_screening.R` on legacy 315 (B16); run pipeline on next PDF batch; lock Harman/procedural rules (B4–B5). |
| 2 | **Consider ASReview** (not SciSciGPT) if title/abstract screening backlog is the bottleneck for ~1,476 Zotero records. |
| 3 | **SciSciGPT** — Skip self-host for this project. Optionally spend 30 min on sciscigpt.com for SciSci background; do not wire into extraction CSV. |

**Decision rule:** If the task maps to a row in `config.yaml` or `VARIABLE_CODEBOOK.md`, use CMV tooling. If the task is exploratory SciSci bibliometrics unrelated to ULMC coding, SciSciGPT demo is sufficient—full adoption is not cost-effective.

## Section F: External tooling — dots.ocr (document parsing)

### What dots.ocr is

[dots.ocr](https://github.com/rednote-hilab/dots.ocr) (Xiaohongshu / REDnote HiLab; [arXiv:2512.02498](https://arxiv.org/abs/2512.02498)) is a **multilingual vision-language model (VLM)** for unified document layout parsing—not a systematic-review or extraction-coding tool. A single ~1.7B-parameter model (Qwen2.5-1.5B decoder + document-specialized vision encoder) performs layout detection, OCR, reading-order reconstruction, and content formatting in one pass.

| Capability | Output |
|------------|--------|
| Layout elements | JSON with bbox, category (Text, Title, Table, Formula, etc.), and text |
| Body text | Markdown per cell, concatenated to `.md` |
| Tables | HTML inside JSON (strong on OmniDocBench TableTEDS vs. Marker, Docling, Unstructured) |
| Formulas | LaTeX |
| PDF input | Page images via bundled `dots_ocr/parser.py` (uses **PyMuPDF** upstream) |
| Multilingual | Explicit low-resource language support; English management/psychology journals are in-distribution |

**Tech stack & prerequisites:** Python 3.10+ (3.12 recommended), PyTorch, `transformers`, optional **vLLM ≥0.11.0** (official integration; recommended for speed). Model weights on [Hugging Face](https://huggingface.co/rednote-hilab/dots.ocr) (~3B reported on HF card). **GPU strongly recommended** (16 GB VRAM minimum reported in community use; 24 GB safer for long pages); CPU inference documented but slow. Install is moderate DevOps (`pip install -e .`, download weights, CUDA alignment)—not a one-line R dependency.

**Maturity:** Released **2025-07-30**; **~9k GitHub stars**, 800+ forks; last push **2026-03-24**; **MIT License**; active issues (145 open). Related releases: `dots.ocr.base`, `dots.mocr` (2025-10). Authors acknowledge **throughput limits** on large PDF batches and imperfect complex tables/formulas.

### Fit for this ULMC project: **Medium** (conditional on PDFs)

| Dimension | Assessment |
|-----------|--------------|
| **Overall fit** | **Medium** — valuable as a **text-ingestion sidecar** for layout-hard PDFs; **not** a substitute for paywall acquisition or codebook extraction |
| **Scanned PDFs** | **High** relative to `pdftools::pdf_text()` — core use case |
| **Multi-column / reading order** | **High** — explicit reading-order benchmark strength; pdftools often jumbles columns |
| **Fit-index tables (CFI, RMSEA, χ²)** | **Medium** — tables export as HTML/Markdown; better than pdftools on structure, but authors warn complex tables are imperfect; **numeric QA still required** for three-step ULMC fields |
| **Structured ULMC coding** | **None** — does not output `harman_deployed`, procedural remedies, or Richardson context; downstream `enhanced_extraction_pipeline.R` + manual template still authoritative |
| **182-batch feasibility** | **Medium** — technically batchable (`parser.py` multithreaded PDF mode); expect **hours–days** on a single consumer GPU, not minutes like pdftools |
| **Current blocker** | **PDF acquisition** — audit shows **0 legacy PDFs matched** in repo; dots.ocr does not solve paywalls |

### What it automates vs. `pdftools` (current CMV default)

| Step | `pdftools::pdf_text()` (`enhanced_extraction_pipeline.R`) | dots.ocr |
|------|-----------------------------------------------------------|----------|
| Born-digital PDF text layer | ✅ Fast, reproducible, in-R | Overkill; pymupdf/pdftools sufficient |
| Scanned / image-only PDFs | ❌ Empty or garbage | ✅ OCR + layout |
| Multi-column Methods/Results | ⚠️ Column merge errors | ✅ Reading-order reconstruction |
| Tables (fit indices, Harman %) | ⚠️ Whitespace collapse, row loss | ✅ HTML table structure (verify numbers) |
| Regex extraction (Harman, remedies, ULMC) | ✅ In same R script | ❌ Not included — feed `.txt`/`.md` into R separately |
| Reproducibility for methods appendix | ✅ Fixed R + package versions | ⚠️ Pin model hash, vLLM version, DPI (200 recommended); VLM outputs can vary slightly by backend |

**Practical bridge:** Python sidecar writes `review/EBSCO/text/{refid}.md` (or `.txt`); extend `enhanced_extraction_pipeline.R` to accept pre-extracted text paths when `pdf_text()` fails or returns &lt;N characters—no need to rewrite regex logic.

### Strengths vs. common alternatives

| Tool | Role | vs. dots.ocr for ULMC PDFs |
|------|------|----------------------------|
| **pdftools** | R-native `pdf_text` | ✅ Default for born-digital; dots.ocr only for failures |
| **pymupdf / pymupdf4llm** | Text layer → markdown | ✅ Lighter, faster for digital journal PDFs; try first |
| **marker** | PDF→markdown pipeline | Similar niche; OmniDocBench tables/read-order below dots.ocr; heavier install |
| **docling** (IBM) | Layout + export | Weaker end-to-end scores on OmniDocBench; good if already in stack |
| **unstructured** | Generic partition | Poor table scores; not ideal for fit-index tables |
| **LandingAI ADE** | Commercial layout API | Strong hosted option if no local GPU; cost + data-handling policy for paywalled PDFs |

### Risks for publication-grade SR use

1. **Numeric fidelity** — CFI/RMSEA/χ² and Harman % in dense tables may be misread; always spot-check against PDF for `step1_*` / `harman_variance_pct` fields.
2. **VLM repetition / omission** — Known failure on `...` and `_`; may truncate or loop on boilerplate tables.
3. **Hallucination** — Prompt constrains to original text, but VLMs can still insert characters; treat output as **assistive**, not gold text.
4. **Reproducibility** — Document model revision (`rednote-hilab/dots.ocr`), vLLM/transformers versions, and DPI in methods if used beyond a pilot.
5. **Scope creep** — Parsing is Phase 3 sub-step; do not delay PDF hunt (Phase 3.2) with parser setup.

### Prerequisites (if piloting)

| Tier | Requirements |
|------|----------------|
| **Quick look** | [Hugging Face model card](https://huggingface.co/rednote-hilab/dots.ocr) + 1 demo PDF via `python dots_ocr/parser.py` (no full 182 run) |
| **Local pilot (5–10 PDFs)** | NVIDIA GPU 16–24 GB VRAM, Python 3.12, CUDA-matched PyTorch, model weights, vLLM optional; output to `review/EBSCO/text/` |
| **R integration** | Thin wrapper: if `pdf_text()` &lt; threshold chars → read `.md` sidecar; else existing path |
| **License** | MIT — permissive for academic use |

### Recommendation: **Hybrid — pdftools first; dots.ocr pilot on parse failures only**

| Priority | Action |
|----------|--------|
| 1 | **Unblock PDFs** (Phase 3.2) — dots.ocr is irrelevant until files exist under `review/EBSCO/pdfs/` or per-Refid paths |
| 2 | **Default path** — `enhanced_extraction_pipeline.R` + `pdftools` (and try **pymupdf4llm** for stubborn but digital PDFs) |
| 3 | **Pilot dots.ocr on N=5–10** — Select Refids with known scanned pages, multi-column Results, or garbled `text_extraction` vs. legacy snippet; compare table numerics manually |
| 4 | **Skip full adoption** unless pilot shows &gt;90% usable text on failure cases and saves substantial manual time |

### When to use in 182 workplan phases

| Phase | dots.ocr role |
|-------|----------------|
| **Phase 0–1** (reuse 69–81 CSV rows) | **Skip** — legacy snippets + CSV suffice for spot-QA |
| **Phase 2** (metadata / Zotero) | **Skip** — bibliographic only |
| **Phase 3.1–3.2** (PDF acquisition) | **Skip** — not an acquisition tool |
| **Phase 3.3** (text ingest before extraction) | **Use selectively** — after `pdf_text()` failure or layout QA flag; batch remaining failures only |
| **Phase 3.4** (structured extraction) | **Indirect** — feeds text into existing R regex + manual template; no change to authoritative coding |
| **Phase 5** (PRISMA / synthesis) | **Methods note only** if parser used — record tool version and failure rate |

**Decision rule:** If `pdf_text()` returns clean Methods/Results prose and fit tables are readable, stay in R. If the PDF is scanned, columns are shuffled, or fit-index tables are broken, pilot dots.ocr on that Refid before hand-transcribing.
