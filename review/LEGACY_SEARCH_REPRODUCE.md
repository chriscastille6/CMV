# Reproducing the Original ULMC Library Search (Legacy, 2012–2022)

This document isolates the **original** systematic-review search that produced **656 → 315 → 182** records. It is separate from later EBSCO exports (2026) and from the OpenAlex/Crossref API harvest.

**Primary sources:** `review/legacy/systematic_review_manuscript.txt`, `review/LEGACY_REVIEW_SUMMARY.md`, `review/EBSCO/PRISMA_DATABASE_BREAKDOWN.md`, `review/SYSTEMATIC_REVIEW_PROGRESS.md`.

---

## 1. Original legacy search (CONFIRMED)

| Element | Specification | Confidence |
|--------|----------------|------------|
| **Interface** | **Discovery Service** (institutional library federated search) | **Confirmed** — manuscript line 53: *"using the Discovery Service"* |
| **Underlying indexes** | **PsycINFO** + **Business Source Complete** | **Inferred** — `PRISMA_DATABASE_BREAKDOWN.md`; not named in the original manuscript |
| **Screening tool after export** | **DistillerSR** | **Confirmed** — manuscript line 65; not used to run the database query |
| **Search query** | See below | **Confirmed** |
| **Publication years** | **2012–2022** | **Confirmed** — manuscript scope + Figure 1 PRISMA box |
| **Initial hits** | **656** (prose) or **687** (Figure 1 box with date limiter) | **Ambiguous** — both in legacy manuscript; see §5 |
| **After deduplication** | **315** | **Confirmed** |
| **After Level 1 screening** | **182** (185 entered extraction; 182 in gold set) | **Confirmed** |

### Exact Boolean query (copy-paste)

```
"unmeasured latent method construct" OR "unmeasured latent method factor"
```

- Two **quoted phrases**, joined by **OR**.
- No `ULMC`, no CMV/Harman terms, no management/psychology domain terms in the **original** search (those are applied during screening, not in the query).
- Manuscript intent: capture in-text citations of the technique (Podsakoff et al. / Williams et al. wording).

### Filters / limiters (CONFIRMED)

Apply all of the following in Discovery Service:

| Limiter | Manuscript wording | Typical EBSCO Discovery checkbox |
|--------|---------------------|----------------------------------|
| Full text | *"full text" versions* | **Full Text** |
| Peer review | *"scholarly (peer reviewed) articles"* | **Scholarly (Peer Reviewed) Journals** or **Peer Reviewed** |
| Source type | *published in academic journals* | **Source Type: Academic Journals** (if shown separately) |
| Date | *published between 2012 and 2022* (Figure 1) | **Publication Date: 2012–2022** |

**Not documented in the legacy search:** English-only limiter (added in later PROSPERO/config for the 2025 update). If your interface offers **Language: English**, applying it may slightly change counts.

**Deduplication:** Done **inside Discovery Service** (*"duplicates were eliminated by Discovery Service"*). Expect **315** unique records after platform dedup—not a manual Zotero/Excel step in the original workflow.

---

## 2. Step-by-step: repeat in EBSCO Discovery Service

> **Institution:** The legacy docs say *"your university's discovery service"* but **do not record which university** (Northeastern, Nicholls, Wayne State, etc.). You must log in through **your current library**; hit counts can differ by subscription bundle. `RESTART_CHECKLIST.md` item B30 flags credentials as still open.

1. Open your library homepage → **Discovery** / **Library Search** / **EBSCO Discovery Service** (not the standalone `research.ebsco.com` product unless that *is* your library's discovery layer).
2. Open **Advanced Search** (recommended so the query is unambiguous).
3. Paste the query into the main search box (default field is usually **Select a Field (optional)** or **TX All Text**—legacy search targeted phrases appearing **in the article text**).
4. Set **Publication Date** to **01/01/2012 – 12/31/2022**.
5. Enable limiters:
   - **Full Text**
   - **Scholarly (Peer Reviewed) Journals** (or equivalent)
   - **Academic Journals** if listed separately
6. Run search. **Record:** query string, date, limiters, hit count, search date.
7. Use the platform **Remove duplicates** / deduplication feature if offered; legacy workflow relied on Discovery Service dedup → target **~315** records.
8. Export results (RIS/CSV) for screening; original review used **DistillerSR** for Level 1/2.

### Optional: search individual subscribed databases

If Discovery is unavailable, PROSPERO draft (`PROSPERO_DRAFT_REGISTRATION_FINAL.md`) states the same core query was intended for:

- **PsycINFO**
- **Business Source Complete** (protocol also mentions *Business Source Premier*—treat as the same EBSCO business bundle unless your library names differ)

Run the **same query and limiters** in each, merge, then deduplicate manually by DOI/title. Counts will **not** match 656/315 exactly unless you replicate the federated index set.

---

## 3. What happens after the search (screening, not part of the query)

Level 1 criteria (from manuscript Table 1 / `LEGACY_REVIEW_SUMMARY.md`):

- **Include:** management, HRM, OB, applied psychology; business ethics & strategy; empirical ULMC for CMV
- **Exclude:** IS, advertising, marketing journals; simulations/theory; ULMC for substantive effects; **PLS estimation** (24 excluded)

These filters explain **315 → 182**, not the database query itself.

---

## 4. Later searches (NOT the original library search)

### A. EBSCO metadata export — Feb 23, 2026 (50 records)

| Element | Status |
|--------|--------|
| **What** | Direct **EBSCO** export (`EBSCO-Metadata-02_23_2026.pdf` → `ebsco_export_50_records.csv`) |
| **Count** | **50** records |
| **Query string** | **Not documented** in the repository |
| **Relation to legacy** | **Separate** supplemental search (`EBSCO_EXPORT_AND_ZOTERO_USE.md`); mostly post-2010; overlap with legacy 182 is partial |
| **URLs** | Records use `https://research.ebsco.com/plink/...` |

To reproduce: re-run whatever search produced those 50 ANs, or compare accession numbers in `review/EBSCO/ebsco_export_50_records.csv`. **Do not assume** the Feb 2026 query equals the legacy two-phrase Discovery query unless you recover it from EBSCO search history.

### B. EBSCO full-text PDFs — Jun 24, 2026

Single-article downloads for manual PDF acquisition (`EBSCO_FULLTEXT_06_24_2026.md`). **Not** a literature search.

### C. OpenAlex / Crossref automated harvest (2025 update)

| Element | Specification |
|--------|----------------|
| **Script** | `review/01_search_harvest.R`, `review/comprehensive_ulmc_search.R` |
| **Config** | `review/config.yaml` |
| **Databases** | OpenAlex API, Crossref API |
| **Date window** | **2010 to date (2026)** (config) |
| **Terms** | Expanded: primary + secondary CMV terms, optional domain concepts |
| **Hits** | ~**82,906** in PRISMA planning docs |
| **Relation to legacy** | **Different** search entirely—broader terms, programmatic, not Discovery Service |

Expanded Boolean (2025 protocol—not legacy):

```
(("unmeasured latent method construct" OR "unmeasured latent method factor" OR "ULMC" OR "single method factor")
AND
("common method variance" OR "common method bias" OR "method variance"))
AND
(management OR organizational OR "human resource" OR psychology OR "applied psychology")
AND
(empirical OR survey OR questionnaire OR "structural equation")
```

---

## 5. Hit-count ambiguity (be aware when validating)

| Stage | Count | Source |
|-------|------:|--------|
| Initial search | **656** | Manuscript body; `LEGACY_REVIEW_SUMMARY.md`; `SYSTEMATIC_REVIEW_PROGRESS.md` |
| Initial search (with 2012–2022 in PRISMA box) | **687** | Figure 1 in `systematic_review_manuscript.txt` |
| Duplicates removed | **372** (figure) | Figure 1 → 687 − 372 = **315** |
| After deduplication | **315** | All legacy summaries |
| After Level 1 | **182** | DistillerSR / `legacy_extracted_data.csv` |

Possible explanations for 656 vs 687: different limiter sets, date filter applied in figure but not in early prose, or a recount between draft and figure. **315 after dedup is the stable anchor** for reproduction checks.

---

## 6. Quick validation checklist

After re-running Discovery search:

- [ ] Query is exactly the two OR'd phrases (quoted).
- [ ] Full Text + Scholarly/Peer Reviewed + Academic Journals limiters on.
- [ ] Publication date **2012–2022**.
- [ ] Note raw hit count (expect **~656–687**, institution-dependent).
- [ ] Apply Discovery deduplication → expect **~315**.
- [ ] Export and compare to `review/EBSCO/legacy_all_315_inventory.csv` if available.

---

## 7. File index

| File | Relevance |
|------|-----------|
| `review/legacy/systematic_review_manuscript.txt` | Authoritative legacy query + filters + PRISMA counts |
| `review/LEGACY_REVIEW_SUMMARY.md` | Methodology summary |
| `review/SEARCH_STRATEGY_REPRODUCIBILITY.md` | Consolidated strategies (legacy + 2025) |
| `review/EBSCO/PRISMA_DATABASE_BREAKDOWN.md` | Discovery → PsycINFO + Business Source Complete |
| `review/EBSCO/EBSCO_EXPORT_AND_ZOTERO_USE.md` | Feb 2026 EBSCO 50-record export |
| `review/config.yaml` + `review/01_search_harvest.R` | OpenAlex/Crossref (not legacy) |
| `review/PRISMA_PROTOCOL.md` | Expanded 2025 multi-database protocol |

---

*Last updated: 2026-06-24*
