# Legacy 182 Workplan — 182-First Restart

**Created**: 2026-06-24  
**Scope decision**: The **182 legacy included studies** (`legacy/legacy_extracted_data.csv`, `final_include=TRUE`) are the gold corpus for restart. The 100-row extraction CSV is a partial, overlapping subset—not the scope anchor.

---

## Overlap Summary (legacy 182 × `systematic_extraction_40_studies.csv`)

| Category | Count | Notes |
|----------|------:|-------|
| **Legacy included (gold)** | **182** | Confirmed: `final_include=TRUE` in `legacy_extracted_data.csv` |
| **Extraction CSV rows** | **100** | Filename says "40"; actual row count is 100 |
| **Exact overlap (Refid `L{n}` prefix)** | **69** | Same DistillerSR Refid encoded as `study_order=L{refid}` in CSV |
| **Probable overlap (fuzzy)** | **2** | Journal + MV% match on non-`L` rows (Refids 175, 181) |
| **Weak overlap (manual review)** | **10** | Journal-only or MV%-only fuzzy match on non-`L` rows |
| **Legacy-only (no CSV row)** | **101** | Need fresh structured extraction |
| **CSV-only (not in legacy 182)** | **19** | New EBSCO/search studies; keep as supplement, not in 182 scope |

### CSV composition

| Subset | Rows |
|--------|-----:|
| Legacy `L{refid}` rows | 69 |
| Non-legacy numeric `study_order` rows | 31 |
| Non-legacy rows matched to additional legacy Refids | 12 |
| Non-legacy rows with no legacy-182 match | 19 |

### Reuse vs. fresh work

| Tier | Studies | Action |
|------|--------:|--------|
| **Reuse now** | **69** | L-prefix rows: spot-check + backfill new fields (`harman_deployed`, procedural hygiene) |
| **Reuse after quick verify** | **2–12** | Probable + weak fuzzy matches: confirm Refid ↔ `study_order` link, then reuse extraction |
| **Conservative reusable total** | **71** | Exact + probable only |
| **Optimistic reusable total** | **81** | If all 10 weak matches confirmed |
| **Fresh extraction required** | **101–111** | No CSV row (101) plus unconfirmed weak matches (up to 10) |

**Bottom line**: ~**39%** of the 182 can reuse existing CSV extraction immediately (69); up to **~45%** (81) if weak matches are confirmed. **~55%** (101+) need new structured extraction passes.

Detailed row-level report: [`legacy/legacy_182_overlap_report.csv`](legacy/legacy_182_overlap_report.csv).  
Fresh-extraction queue (`no_match`): [`legacy/legacy_182_gaps_only.csv`](legacy/legacy_182_gaps_only.csv) (**101** Refids).  
Fuzzy matches to adjudicate: [`legacy/legacy_182_fuzzy_review.csv`](legacy/legacy_182_fuzzy_review.csv) (**12** Refids).

---

## Example Matches

### 5 matched pairs (exact Refid ↔ CSV)

| Legacy Refid | Journal | CSV `study_order` | CSV title |
|-------------|---------|-------------------|-----------|
| 2 | Journal of Business & Psychology | L2 | Legacy Refid 2 — ULMC Study (MV 17.2%) |
| 4 | Journal of Business & Psychology | L4 | Legacy Refid 4 — ULMC Study (MV 4.98%) |
| 16 | Human Resource Development Quarterly | L16 | Legacy Refid 16 — ULMC Study (MV 28%) |
| 29 | Journal of Business Ethics | L29 | Legacy Refid 29 — ULMC Study (MV 5%) |
| 84 | — | L84 | Legacy Refid 84 — ULMC Study (MV 24%) |

### 5 legacy-only (not in CSV)

| Refid | Journal | Notes |
|------:|---------|-------|
| 41 | Journal of Business & Psychology | No CSV row; has legacy text extraction |
| 48 | Sustainability | No CSV row |
| 142 | Journal of Work and Organizational Psychology | MV 19.4%; not extracted to CSV |
| 143 | PLoS ONE | No CSV row |
| 146 | British Journal of Management | MV 0.9%; not extracted to CSV |

### 5 CSV-only (not in legacy 182)

| `study_order` | Title |
|--------------|-------|
| 6 | Wang and Mangmeechai (2021) — environmental intention gap |
| 7 | Niu et al. (2022) — leader bottom-line mentality |
| 8 | Ahmad et al. (2021) — antecedents/consequences (different from Refid 181 match candidate) |
| 9 | Jiang et al. (2020) — negative informal information |
| 10 | Eastman et al. (2020) — future time perspective |

---

## Phased Plan (182-first)

### Phase 0 — Lock scope (done)

- [x] Confirm N=182 included (`final_include=TRUE`)
- [x] Quantify overlap with 100-study CSV
- [x] Row-level overlap report generated

### Phase 1 — Reuse existing extraction (~69–81 studies, ~1–2 weeks)

**Zotero inventory (2026-06-24)**: MCP + local crosswalk found only **8/182** legacy Refids in Zotero (3 high, 2 medium, 3 low confidence); **174 unmatched**. The prior 32-item `EBSCO/zotero_inventory.csv` snapshot maps to just 8 legacy Refids—the rest are EBSCO/new-search supplements. Distinctive L-prefix text searches returned no hits; ULMC/CMV tags are empty in the connected library. See [`legacy/legacy_182_zotero_inventory.csv`](legacy/legacy_182_zotero_inventory.csv) and [`legacy/ZOTERO_INVENTORY_SUMMARY.md`](legacy/ZOTERO_INVENTORY_SUMMARY.md). **Implication**: Phase 1 reuse can proceed from CSV + legacy text, but Zotero PDF workflow requires bulk import (Phase 2) before attachment-backed QA.

1. **Backfill schema gaps** on all CSV rows touching legacy 182:
   - Add `harman_deployed` column; infer from `statistical_methods_mv` / `harman_variance_pct`
   - Fix `procedural_remedies_used` vs. `procedural_remedies_list` inconsistencies
2. **Adjudicate 12 fuzzy matches** (2 probable + 10 weak) in `legacy_182_overlap_report.csv`:
   - Confirm or reject; update `matched_study_order` and add `legacy_refid` column to CSV for linked rows
3. **Spot-QA** L-prefix rows against legacy `text_extraction` for MV%, fit claims, author conclusions

### Phase 2 — Metadata for legacy 182 (~182 studies, parallel with Phase 3)

1. Import legacy 182 into Zotero (`B9`, `B24`)
2. Fill journal/year gaps using `refid_journal_mapping.csv` (182/182 mapped), Crossref, PDF headers
3. Resolve 69-row gap: `legacy_studies_identifying_info.csv` covers only the 69 L-prefix extractions

### Phase 3 — Fresh extraction for legacy-only 101 (~6–10 weeks)

1. Prioritize studies with existing `text_extraction` in `legacy_extracted_data.csv` (reduces PDF hunt)
2. Acquire PDFs for remaining Refids (no row in CSV, no text snippet)
3. Run `enhanced_extraction_pipeline.R` + manual template pass per study  
   - Default: `pdftools::pdf_text()`; for scanned/multi-column/table failures, pilot **dots.ocr** on parse-failure PDFs only — see `RESTART_CHECKLIST.md` Section F
4. Append to master extraction file with `legacy_refid` column (not `L{n}` study_order — use sequential order + Refid link)

### Phase 4 — Optional supplement: 19 CSV-only studies

- Decide whether the 19 non-legacy CSV rows expand scope beyond 182 or stay as sensitivity/supplement sample
- Default for 182-first restart: **defer** until core 182 pass complete

### Phase 5 — PRISMA & synthesis

1. Regenerate PRISMA with included N=182 (not 100 or 208)
2. Update `PRISMA2020_yourdata.csv` included box
2. Point `04_synthesis.R` at unified extraction file (182 rows minimum)
3. Manuscript Table A1 / appendix alignment (`B25`)

---

## Join Keys Reference

| File | Key | Role |
|------|-----|------|
| `legacy/legacy_extracted_data.csv` | `Refid` | Gold include flag (`final_include`) |
| `EBSCO/refid_journal_mapping.csv` | `Refid` → `Journal` | 182/182 included Refids mapped |
| `EBSCO/legacy_studies_identifying_info.csv` | `refid`, `order` (`L{n}`) | Text snippets for 69 extracted legacy studies |
| `EBSCO/systematic_extraction_40_studies.csv` | `study_order` (`L{n}` or numeric) | Structured extraction (100 rows) |
| `EBSCO/legacy_all_315_inventory.csv` | `Refid`, `status` | Full 315 screening audit trail |

**Matching methods used** (see overlap report): Refid `L{n}` prefix (exact) → DOI (sparse in legacy) → normalized title fuzzy → author+year+journal + MV% concordance.

---

## Related Checklist Items

See [`RESTART_CHECKLIST.md`](RESTART_CHECKLIST.md): B1 resolved (182 gold); Section C updated for 182-first actions.

---

## Article recovery pilot (10 studies)

**2026-06-24**: First locate-and-extract batch for legacy-only gaps — [`legacy/ARTICLES_TO_FIND_10.md`](legacy/ARTICLES_TO_FIND_10.md). Ten Refids selected from `legacy_182_gaps_only.csv` (not in Zotero, with DistillerSR text + MV%, no existing `L{refid}` row). Work through the list to add PDFs to Zotero, then extract as `L{n}` rows.
