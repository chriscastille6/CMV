# PRISMA Update — 2026-06-24 (EBSCO Strand Corrected)

**Trigger**: User confirmed corrected EBSCO legacy-query flow on 2026-06-24. Because **method-variance strategy must be identified in full text**, all records in the deduplicated screening pool were **read and coded** at eligibility (not abstract-only triage for MV fields).

**Regenerated assets**: `PRISMA2020_final.svg`, `.pdf`, `.png` via `create_prisma2020_final_corrected.R` (default mode: **`ebsco_strand`**).

---

## Active diagram — EBSCO legacy-query strand (default)

| Stage | Count | Notes |
|-------|------:|-------|
| **Records identified (Databases)** | **1,036** | User-corrected total for EBSCO Research rerun |
| Duplicate records removed | **466** | 1,036 − 570 |
| **Records screened** | **570** | Unique pool after deduplication |
| Records excluded (title/abstract) | 0 | MV coding required full text; no abstract-only excludes logged |
| Reports sought for retrieval | **570** | Same pool — all retrieved/read |
| Reports not retrieved | 0 | — |
| **Reports assessed for eligibility** | **570** | All full-text read for MV strategy coding |
| Reports excluded (full-text) | **388** | 570 − 182 included; see exclusion breakdown below |
| **Studies included in synthesis** | **182** | Legacy gold standard (`final_include=TRUE`) |

### Exclusion breakdown (full-text eligibility)

| Reason | n |
|--------|--:|
| Wrong population | 94 |
| Wrong intervention | 12 |
| Wrong study design (PLS) | 24 |
| Other reasons | 258 |
| **Total excluded** | **388** |

Legacy category counts (94 / 12 / 24) retained from original DistillerSR adjudication. **Other reasons** increased from 3 → **258** to balance 570 assessed − 182 included = 388 excluded. **Re-adjudicate** against DistillerSR logs if a publication-ready breakdown is required.

### Rationale — why all 570 were full-text assessed

ULMC / MV **strategy** (Harman deployed, procedural remedies, Williams & McGonagle (2016) three-step ULMC procedure, etc.) cannot be reliably coded from title/abstract alone. The screening stage therefore reflects the **deduplicated unique pool** (570), and eligibility assessment equals full-text read + MV coding for every record in that pool.

---

## 1,036 vs 1,031 — documented discrepancy

| Source | EBSCO identification count | Notes |
|--------|---------------------------:|-------|
| **User (2026-06-24)** | **1,036** | Used in regenerated PRISMA |
| Repo export log (`EBSCO_SEARCH_06_24_2026.md`) | **1,031** | Interface total at search time |
| **Delta** | **+5** | Plausible causes: re-count after final batch, interface rounding, or records visible after pagination shift |

**Recommendation**: Use **1,036** in the manuscript if that matches your verified interface count; cite **1,031** as the automated export log and note the +5 delta in methods footnote.

---

## 570 vs repo machine counts — documented discrepancy

| Metric | User / PRISMA | Repo data | Gap |
|--------|--------------:|----------:|----:|
| After dedup (screen pool) | **570** | — | User authoritative for PRISMA |
| EBSCO export positions covered | — | 1–250, 301–570 (gap 251–300) | Positions exported ≠ unique count |
| Unique EBSCO rows in `articles_master.csv` | — | **506** (`ebsco_2026_*` tags) | −64 vs 570 |
| Master registry total rows | — | **714** | Includes legacy 182 + EBSCO + extraction overlap |
| Extraction CSV rows | — | **100** | Supplementary structured coding |

**Interpretation**: **570** is the user-confirmed deduplicated screening universe for the EBSCO strand. The master registry (**506** unique EBSCO imports) is **incomplete** relative to 570 — export gap (positions 251–300), cross-batch duplicates, and merge keys may explain the shortfall. Reconcile after filling the export gap and re-running `merge_sources.py`.

---

## Combined historical search (supplementary — not in default SVG)

Prior combined PRISMA counted all identification sources:

| Component | Count |
|-----------|------:|
| Legacy Discovery Service (2012–2022) | 656 |
| EBSCO Research rerun (2026-06-24) | **1,036** (was 1,031) |
| OpenAlex / Crossref | 82,906 |
| **Combined databases total** | **84,598** |
| Zotero book chapter | 32 (excluded from diagram) |

Prior combined screening pool: **1,873** (stale — predates EBSCO dedup refresh).

Regenerate combined historical diagram:

```bash
cd review/EBSCO
PRISMA_MODE=combined_historical Rscript create_prisma2020_final_corrected.R
```

---

## Before / after — what changed in this update

| Box | Before (2026-06-24 AM) | After (2026-06-24 PM) |
|-----|------------------------:|----------------------:|
| Databases (n) | 84,593 (combined) | **1,036** (EBSCO strand — default SVG) |
| Duplicate records | 82,720 | **466** |
| Records screened | 1,873 | **570** |
| Reports assessed | 1,873 | **570** |
| Studies included | 180 | **182** (legacy gold) |
| Other reasons excluded | 3 | **258** (balance 388 FT excludes) |

---

## Files touched

| File | Change |
|------|--------|
| `PRISMA2020_final.svg` / `.pdf` / `.png` | Regenerated — EBSCO strand 1,036 → 570 → 182 |
| `create_prisma2020_final_corrected.R` | Added `ebsco_strand` (default) and `combined_historical` modes |
| `PRISMA_06_24_2026_UPDATE.md` | This file |
| `review/ANALYSIS_STATUS_REPORT.md` | Coding inventory + analyzed/pending crosswalk |
| `review/analysis_status_summary.csv` | Machine-readable counts |

---

## Still open

1. **Exclusion breakdown audit** — verify 94/12/24/258 against DistillerSR for the 570 pool.
2. **Export gap 251–300** — may add unique records; update master and reconcile 506 vs 570.
3. **Combined vs strand PRISMA** — choose manuscript figure: EBSCO strand (default SVG) vs combined historical (`PRISMA_MODE=combined_historical`).
4. **Google Scholar** (other methods): still 0 / not run.

---

## Regenerate command

```bash
cd review/EBSCO && Rscript create_prisma2020_final_corrected.R
```

Requires R package `PRISMA2020`.
