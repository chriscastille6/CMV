# Articles to Find — Legacy 182 Pilot Batch (10)

**Created**: 2026-06-24  
**Purpose**: First working batch from the 101 legacy-only gaps (`legacy_182_gaps_only.csv`). Use this list to locate PDFs in Zotero/Google Scholar before structured extraction.

**Selection logic**: Not in Zotero (`in_zotero=no`) · has DistillerSR `text_extraction` · has numeric `method_variance_pct` · not already in `systematic_extraction_40_studies.csv` as `L{refid}` · mixed journals from `refid_journal_mapping.csv`.

**Zotero scan (2026-06-24)**: Live library searched (1,071 items; 839 with PDFs). **No new hunt-list PDFs** in live Zotero. RDF export `review/Zotero/ULMC – Sys. Review/ULMC – Sys. Review.rdf` has metadata for **142, 160, 172, 191** — import into live Zotero with `legacy-refid-{n}` tags. Rerun matcher: `python review/legacy/run_zotero_pdf_match.py` → `zotero_pdf_match_report.csv`.

---

## Search guidance

### General workflow

1. **Where to search** (in order)
   - **Google Scholar**: journal name + distinctive phrase + MV% (see per-article strings below).
   - **Library Discovery / EBSCO**: browse journal archive when Scholar returns too many hits; filter by ULMC / “unmeasured latent method”. To **repeat the original 182 search**, use [`LEGACY_SEARCH_REPRODUCE.md`](../LEGACY_SEARCH_REPRODUCE.md) (Discovery Service, two-phrase query, 2012–2022).
   - **Unpaywall** (`unpaywall.org`) or **DOI resolver**: once a probable DOI is found, check open-access PDF.
   - **Author / institutional pages**: ResearchGate, university repositories (especially for JWOP, IJHRM, EBR open copies).

   **EBSCO “Full Text” download note** (see [`review/EBSCO/EBSCO_FULLTEXT_06_24_2026.md`](../EBSCO/EBSCO_FULLTEXT_06_24_2026.md)): each export is **one article PDF**, not a multi-study bundle. Download one record at a time; run `parse_ebsco_fulltext_pdf.py` to file under `review/EBSCO/pdfs/`.

2. **How to verify the RIGHT paper**
   - **Journal** must match `refid_journal_mapping.csv` exactly (watch JWOP = Spanish *Revista de Psicología del Trabajo y de las Organizaciones*, ISSN 1576-5962).
   - **Method variance %** in the PDF methods/results should match legacy data (±0.5 pp acceptable for rounding).
   - **Distinctive phrase** from `text_extraction` must appear verbatim or near-verbatim in methods (not just a citation to Podsakoff et al.).
   - **Empirical ULMC**: confirm CB-SEM/CFA application, not a simulation or methodological critique paper.
   - Cross-check **fit indices or marker-variable details** listed per Refid (e.g., χ²(627)=1415.457 for Refid 142).

3. **When found — Zotero & file hygiene**
   - Import metadata (title, authors, year, DOI).
   - Tag: `legacy-refid-{n}` (e.g., `legacy-refid-142`).
   - Attach PDF; name file: `L{n}_{FirstAuthorLast}_et_al_{Year}_{ShortTitle}.pdf` under `review/EBSCO/pdfs/` (matches extraction pipeline paths).
   - Update `legacy_182_zotero_inventory.csv` (`in_zotero=yes`, Zotero key, DOI).
   - After extraction, mark done in `legacy_182_gaps_only.csv`.

4. **Red flags — likely WRONG paper**
   - Same journal but **different MV%** or no ULMC section.
   - **Simulation / Monte Carlo / PLS-only** ULMC critique (e.g., Chin et al. 2012 MISQ note) — excluded from legacy 182.
   - **PLS-SEM** study miscoded as ULMC (check methods for SmartPLS vs. Mplus/AMOS/LISREL).
   - Generic “common method bias” paragraph with Harman only and no ULMC test.
   - MDPI Sustainability paper that is finance/PLS, not management ULMC (see Refid 165 note below).

---

## 1. Refid 142 — **FOUND** (2026-06-24)

PDF verified: `review/EBSCO/pdfs/EBSCO_M0073_Hu_2019_Disconnecting_to_detach_The_role_of_impaired_rec.pdf` (master **M0073**, legacy refid 142; DOI `10.5093/jwop2019a2`). Pool alias **M0400** synced to same path.

| Field | Value |
|-------|-------|
| **Journal** | Journal of Work and Organizational Psychology |
| **Method variance %** | 19.4 |
| **Probable match** | Hu, Santuzzi, & Barber (2019). *Disconnecting to Detach: The Role of Impaired Recovery in Negative Consequences of Workplace Telepressure.* JWOP, 35(1), 9–15. DOI: [10.5093/jwop2019a2](https://doi.org/10.5093/jwop2019a2) |
| **Fuller distinctive quote** | Given that our variables were measured based on self-reported experiences, we tested the presence and magnitude of common method variance in our data using a single unmeasured latent method factor technique… Mplus version 8.0… nine-factor measurement model… variance partitioning showed that **19.40%** of variance was attributed to the method factor. |
| **ULMC improves fit?** | Yes — inclusion of ULMC improved fit (orthogonal method factor vs. nine-factor only). |
| **Author conclusion** | Common method bias does not pose a significant threat to the study conclusions. |
| **Procedural remedies** | None explicit in snippet (statistical ULMC only). |
| **Harman mentioned?** | No |
| **Google Scholar search** | `"Journal of Work and Organizational Psychology" ULMC "19.4"` OR `"nine-factor measurement model" "orthogonal method factor" ULMC` |
| **Alternate search strings** | `"telepressure" Mplus "1415.457"` · `"variance partitioning" "19.40%" JWOP` · Crossref/DOI: `10.5093/jwop2019a2` |
| **Why prioritized** | Unmatched in Zotero; full ULMC snippet with distinctive 19.4% MV; JWOP adds journal diversity. |

**Verification checklist**
- Methods report Mplus 8.0, nine-factor + orthogonal method factor, χ²(627)=1415.457.
- MV partitioning ≈ **19.40%** (below Williams et al. 25% benchmark).
- Topic: workplace telepressure / recovery (not leadership MLQ nine-factor papers).

---

## 2. Refid 147

| Field | Value |
|-------|-------|
| **Journal** | International Journal of Human Resource Management |
| **Method variance %** | 18.0 |
| **Probable match** | Year unknown — not in `legacy_studies_online_search.csv`. Search IJHRM archive + Crossref with MV% anchor. |
| **Fuller distinctive quote** | Second, we conducted an unmeasured latent method factor test… Mplus… five-factor model (χ²(153)=226.69, CFI=.97)… the **variance extracted by the common factor was .18**, which is much lower than the criterion (25%) suggested by Williams, Cote, and Buckley (1989). |
| **ULMC improves fit?** | Yes — but authors note fit did not meaningfully change (“no change in model fit” in fit-claims field). |
| **Author conclusion** | Whether common method bias is or is not a significant threat remains **unclear** (ambiguous conclusion). |
| **Procedural remedies** | None explicit in snippet. |
| **Harman mentioned?** | No |
| **Google Scholar search** | `"International Journal of Human Resource Management" ULMC "variance extracted by the common factor was .18"` |
| **Alternate search strings** | `"IJHRM" Mplus "five-factor" ULMC ".18"` · `"v2 (153) = 226.69" ULMC` · site:tandfonline.com `"09585192" ULMC 18%` |
| **Why prioritized** | Unmatched; explicit MV=.18 vs Williams 25% threshold; IJHRM (first of two in batch). |

**Verification checklist**
- Five-factor CFA in **Mplus** with ULMC; common-factor variance **≈18%**.
- Phrase “variance extracted by the common factor was .18”.
- Authors’ CMV conclusion is **non-committal** (not a clear “no threat” dismissal).

---

## 3. Refid 153

| Field | Value |
|-------|-------|
| **Journal** | Journal of International Business Studies |
| **Method variance %** | 16.0 |
| **Probable match** | Year unknown. Highly distinctive **Chinese stroke-count marker variable** — search JIBS + that phrase first. |
| **Fuller distinctive quote** | Following best practices for handling CMV in IB research (Chang, van Witteloostuijn, & Eden, 2010)… marker variable test… **whether the number of strokes of the company name in Chinese was even**… variance extracted by the method factor was only **0.16**… |
| **ULMC improves fit?** | Yes — but increase in fit from ULMC was **not significant**. |
| **Author conclusion** | Common method bias does not pose a significant threat to the study conclusions. |
| **Procedural remedies** | Multi-source data, time lag, split questionnaire, complicated interactions, Harman PCA, **Lindell–Whitney marker** (Chinese strokes), ULMC. |
| **Harman mentioned?** | Yes (principal components / one-factor test) |
| **Google Scholar search** | `"Journal of International Business Studies" "common method variance" ULMC 16%` OR `"CMV in IB research" Chang van Witteloostuijn Eden ULMC` |
| **Alternate search strings** | `"strokes of the company name in Chinese" JIBS` · `"number of strokes" "even" marker variable IB` · `"variance extracted by the method factor was only 0.16" JIBS` |
| **Why prioritized** | Unmatched; IB-specific CMV procedural + statistical controls; distinctive JIBS venue. |

**Verification checklist**
- Cites Chang et al. (2010) IB CMV best practices.
- Marker variable: **even number of Chinese name strokes** (theory-unrelated dummy).
- ULMC method variance **≈16%**; five-part CMV battery in methods.

---

## 4. Refid 160

| Field | Value |
|-------|-------|
| **Journal** | Journal of Business Ethics |
| **Method variance %** | 25.0 |
| **Probable match** | Braun & Peus (2018). *Crossover of Work–Life Balance Perceptions: Does Authentic Leadership Matter?* JBE, 149(4), 875–893. DOI: [10.1007/s10551-016-3078-x](https://doi.org/10.1007/s10551-016-3078-x) |
| **Fuller distinctive quote** | Three a priori models… one-factor vs. four-factor (authentic leadership, leader work–life balance, follower work–life balance, job satisfaction) vs. **five-factor with unmeasured latent method factor**… five-factor χ²(288,121)=475.396, CFI=.910… |
| **ULMC improves fit?** | Yes — five-factor ULMC model fits better than four-factor, but authors still use four-factor substantively. |
| **Author conclusion** | Common method bias does not pose a significant threat (despite acknowledging method factor). |
| **Procedural remedies** | None explicit in snippet (statistical comparison of 1/4/5-factor models). |
| **Harman mentioned?** | No |
| **Google Scholar search** | `"Journal of Business Ethics" ULMC "authentic leadership" "work-life balance" 25%` |
| **Alternate search strings** | `"Braun" "Peus" ULMC crossover work-life balance` · DOI `10.1007/s10551-016-3078-x` · `"five-factor model with an unmeasured latent method factor" JBE` |
| **Why prioritized** | Unmatched; rich construct names (authentic leadership, work–life balance); MV at 25% threshold. |

**Verification checklist**
- Four substantive factors: **authentic leadership**, leader/follower **work–life balance**, **job satisfaction**.
- CFA compares 1-, 4-, and 5-factor (ULMC) models; BIC/CFI/RMSEA reported.
- Published **2018**, JBE Vol. 149 Issue 4.

---

## 5. Refid 161

| Field | Value |
|-------|-------|
| **Journal** | European Management Review |
| **Method variance %** | 3.15 |
| **Probable match** | Year unknown. Search EMR for **.015/.477=3.15%** ratio — very distinctive. |
| **Fuller distinctive quote** | We used several **procedural techniques** (proximal separation, reverse-coded items)… unmeasured latent method factor… average substantive explained variance is **0.477**, average method variance **0.015** (.015/.477=**3.15%**). |
| **ULMC improves fit?** | Yes — but no clear author claim about relative fit improvement. |
| **Author conclusion** | Common method bias does not pose a significant threat. |
| **Procedural remedies** | **Proximal separation** of items, **reverse-coded items**, then ULMC. |
| **Harman mentioned?** | No |
| **Google Scholar search** | `"European Management Review" ULMC "3.15%"` OR `"average method variance is 0.015" ULMC` |
| **Alternate search strings** | `"0.477" "0.015" ULMC EMR` · `"proximal separation" "reverse-coded" ULMC "European Management Review"` · Wiley EMR archive + ULMC |
| **Why prioritized** | Unmatched; unusually precise MV ratio (.015/.477); low-MV anchor for search contrast. |

**Verification checklist**
- Reports substantive vs. method variance ratio **0.015/0.477 ≈ 3.15%**.
- Lists **proximal separation** and **reverse-coded items** as procedural controls.
- ULMC added as latent method factor to all indicators.

---

## 6. Refid 163

| Field | Value |
|-------|-------|
| **Journal** | Business Ethics: A European Review |
| **Method variance %** | 18.78 |
| **Probable match** | Year unknown. Journal renamed **Business Ethics, the Environment & Responsibility (BEER)** in 2020 — search both titles. |
| **Fuller distinctive quote** | Harman’s one-factor test… **five distinct factors… 69.12%** total variance, first factor **30.06%**… ULMC… common method factor accounted for **18.78%** of total variance (below 25% Williams benchmark). |
| **ULMC improves fit?** | Yes — ULMC improved model fit. |
| **Author conclusion** | Common method bias does not pose a significant threat. |
| **Procedural remedies** | None explicit (Harman EFA + ULMC). |
| **Harman mentioned?** | Yes — Harman (1976) one-factor test with five-factor extraction |
| **Google Scholar search** | `"Business Ethics: A European Review" ULMC "18.78%"` OR `Harman "69.12%" ULMC "18.78%"` |
| **Alternate search strings** | `"69.12%" "30.06%" Harman ULMC ethics` · `"five distinct factors" "18.78%" BEER OR "Business Ethics: A European Review"` · ISSN 0962-8770 + ULMC |
| **Why prioritized** | Unmatched; dual Harman + ULMC with specific variance figures; distinct ethics journal. |

**Verification checklist**
- Harman: **5 factors, 69.12%** total variance, first factor **30.06%**.
- ULMC: **18.78%** method variance (<25%).
- Journal is BEER / Business Ethics: A European Review (Wiley).

---

## 7. Refid 165

| Field | Value |
|-------|-------|
| **Journal** | Sustainability (MDPI) |
| **Method variance %** | 17.0 |
| **Probable match** | Year unknown. **MDPI filter note**: `config.yaml` excludes MDPI for new EBSCO search, but Refid 165 is in legacy 182 gold set — **include for legacy extraction**. |
| **Fuller distinctive quote** | …self-report scales… unmeasured latent method factor… **three-factor model** + method factor… method factor accounted for **17%** of total variance (below 26% self-report average)… Δχ²(8)=148.02. |
| **ULMC improves fit?** | Yes — model with method factor fit better (CFI=1.00, RMSEA=.00 in snippet). |
| **Author conclusion** | Common method bias does not pose a significant threat. |
| **Procedural remedies** | None explicit (same-time self-report acknowledged). |
| **Harman mentioned?** | No |
| **Google Scholar search** | `"Sustainability" MDPI ULMC "17%"` OR `"unmeasured latent method factor" "three-factor model" Sustainability` |
| **Alternate search strings** | `"method factor accounted for 17%" MDPI` · `"AIC = 15016" ULMC Sustainability` · `"three-factor model" ULMC site:mdpi.com` |
| **Why prioritized** | Unmatched; open-access MDPI venue; clear ULMC rationale when method source unknown. |

**Verification checklist**
- **Three-factor** hypothesized model + ULMC in CB-SEM (not PLS).
- Method variance **≈17%**; cites Podsakoff et al. [42] ULMC approach.
- Confirm **management/organizational** empirical study (exclude finance Fama-French papers).

---

## 8. Refid 166

| Field | Value |
|-------|-------|
| **Journal** | International Journal of Human Resource Management |
| **Method variance %** | 22.94 |
| **Probable match** | Year unknown. Cites **Castanheira (2015)** for non-nested ULMC comparison — search IJHRM + Castanheira + ULMC. |
| **Fuller distinctive quote** | Harman one-factor CFA misfit (χ²[119]=**1137.10**, CFI=.57)… three-factor + ULMC (χ²[99]=201.15, CFI=.96)… method factor **22.94%** (<25–40% Williams range)… CFI change **.03** (<.05 rule). |
| **ULMC improves fit?** | Yes — method factor slightly increased fit. |
| **Author conclusion** | Common method bias does not pose a significant threat. |
| **Procedural remedies** | None explicit (Harman + ULMC sequence). |
| **Harman mentioned?** | Yes — Harman one-factor CFA before ULMC |
| **Google Scholar search** | `"International Journal of Human Resource Management" ULMC "22.94%"` OR `"one-factor model" χ2 1137 ULMC Castanheira` |
| **Alternate search strings** | `"1137.10" "201.15" ULMC IJHRM` · `"Castanheira, 2015" ULMC "three-factor"` · `"CFI change was .03" ULMC` |
| **Why prioritized** | Unmatched; second IJHRM with different MV% (22.94%); Harman CFA misfit then ULMC follow-up. |

**Verification checklist**
- One-factor model χ²=**1137.10**, df=119, CFI=.57 (poor fit).
- Three-factor + ULMC: χ²=**201.15**, df=99; **22.94%** method variance.
- Uses **ΔCFI=.03** rule (Bagozzi & Yi, 1990) for non-nested comparison.

---

## 9. Refid 172

| Field | Value |
|-------|-------|
| **Journal** | Eurasian Business Review |
| **Method variance %** | 21.0 |
| **Probable match** | Schepers, Voordeckers, Steijvers, & Laveren (2021). *Entrepreneurial intention-action gap in family firms: bifurcation bias and the board of directors…* EBR, 11(3), 451–475. DOI: [10.1007/s40821-021-00183-z](https://doi.org/10.1007/s40821-021-00183-z) — **verify ULMC paragraph in PDF**. |
| **Fuller distinctive quote** | …**concealed interest in criterion and predictor variables in the cover story**… pre-test with experts… **3-way interaction**… Harman (five factors, none >33%)… ULMC on EI, EA, bifurcation bias → **21%** common variance… marker: **participative decision making** (Covin et al., 2006). |
| **ULMC improves fit?** | Yes — but no clear author fit claim. |
| **Author conclusion** | Authors **do not provide** a clear CMV conclusion (snippet ends with procedural + statistical battery). |
| **Procedural remedies** | Survey pre-test, simplified wording, **cover story concealment**, predictor/criterion separation, 3-way interaction argument (Siemsen et al.). |
| **Harman mentioned?** | Yes — Harman single-factor (1967), five factors, none >33% |
| **Google Scholar search** | `"Eurasian Business Review" ULMC "21%"` OR `"concealed interest in criterion and predictor variables" ULMC` |
| **Alternate search strings** | `"bifurcation bias" ULMC "participative decision making"` · DOI `10.1007/s40821-021-00183-z` · `"three-way interaction" CMV Eurasian Business Review` |
| **Why prioritized** | Unmatched; rare journal in corpus; procedural + statistical CMV controls described. |

**Verification checklist**
- Constructs include **entrepreneurial intentions (EI)**, **entrepreneurial actions (EA)**, **bifurcation bias**.
- ULMC common variance **≈21%** (0.462); marker-variable test **≈11%**.
- **Cover story** language and Covin et al. PDM marker in methods.

---

## 10. Refid 191

| Field | Value |
|-------|-------|
| **Journal** | Public Personnel Management |
| **Method variance %** | 39.0 |
| **Probable match** | Mostafa & El-Motalib (2019). *Servant Leadership, Leader–Member Exchange and Proactive Behavior in the Public Health Sector.* PPM, 48(3), 309–324. DOI: [10.1177/0091026018816340](https://doi.org/10.1177/0091026018816340) |
| **Fuller distinctive quote** | …**servant leadership and LMX were rated by nurses** whereas **proactive behaviors were rated by supervisors**… ULMC on SL + LMX… χ²(62)=139.18, CFI=.946… average variance extracted by common factor **0.39** (<.50 Fornell–Larcker threshold). |
| **ULMC improves fit?** | Yes — but no explicit fit-comparison claim. |
| **Author conclusion** | Common method bias does not pose a significant threat (despite 39% AVE by method factor). |
| **Procedural remedies** | **Multi-source** design (nurses vs. supervisors), anonymity, reduced item ambiguity. |
| **Harman mentioned?** | No |
| **Google Scholar search** | `"Public Personnel Management" ULMC "39%"` OR `"servant leadership" LMX nurses ULMC` |
| **Alternate search strings** | `"Egyptian public hospital nurses" servant leadership ULMC` · DOI `10.1177/0091026018816340` · `"average variance extracted" "0.39" LMX nurses` |
| **Why prioritized** | Unmatched; highest MV% in this batch (39%); distinctive multi-source design (nurses vs supervisors). |

**Verification checklist**
- Sample: **Egyptian public hospital nurses**; SL & LMX same source, proactive behavior from supervisors.
- ULMC χ²(62)=**139.18**, CFI=**.946**; method-factor AVE **≈0.39**.
- Published **2019**, Public Personnel Management.

---

## After locating each article

1. Add PDF to Zotero and tag with `legacy-refid-{n}`.
2. Update `legacy_182_zotero_inventory.csv` (`in_zotero=yes`, item key, DOI if found).
3. Run structured extraction into `systematic_extraction_40_studies.csv` as `L{n}` row.
4. Remove or mark done in `legacy_182_gaps_only.csv` once verified.

**Remaining gaps after this batch**: 91 Refids in `legacy_182_gaps_only.csv`.

---

## Appendix

### A. Full journal list (182 Refids)

Complete Refid → journal mapping: [`review/EBSCO/refid_journal_mapping.csv`](../EBSCO/refid_journal_mapping.csv) (182/182 journals mapped).

### B. MDPI Sustainability (Refid 165) — inclusion note

The **new-search pipeline** excludes MDPI via `config.yaml` (see RESTART_CHECKLIST B15). Refid **165** is nonetheless in the **legacy 182 gold corpus** (`final_include=TRUE`). Treat it as **in-scope for legacy extraction**; do not discard solely because of the MDPI publisher filter used for EBSCO screening.

### C. Common false positives in ULMC searches

| Trap | Why it fails verification | Example to avoid |
|------|---------------------------|------------------|
| Methodological ULMC critique papers | Simulation/opinion, not empirical ULMC application | Chin, Thatcher & Wright (2012) MISQ; Richardson et al. simulation papers |
| PLS-SEM “ULMC” in SmartPLS | Legacy 182 requires `not_pls=TRUE` | Liang et al. (2007) PLS ULMC studies |
| Wrong journal, similar MV% | Journal mismatch is hard fail | Any JBE paper when targeting Refid 160 without authentic-leadership constructs |
| Leadership “nine-factor” MLQ papers | Refid 142 is telepressure/JWOP, not MLQ FRLT | Bass & Avolio nine-factor leadership CFA papers |
| Finance / sustainability economics MDPI | Wrong domain; often PLS | Fama-French three-factor MDPI papers (not Refid 165) |
| IJHRM HPWS / voice (2023) | Same journal as Refids 147 & 166 but wrong paper: ULMC with no exact MV%; χ²(479)=1052.35; HPWS/TL constructs | Ehrnrooth et al. (2023) DOI `10.1080/09585192.2022.2163418` — **not** hunt-list |
| Castanheira name collision | Refid 166 cites Castanheira (2015) as method precedent; author need not be Castanheira | Castanheira CSR papers in other journals |
| “Common method bias” without ULMC | Harman-only papers fail legacy ULMC criterion | Papers reporting only Harman’s single-factor test |

### D. Supporting search files

| File | Use |
|------|-----|
| `legacy_extracted_data.csv` | Full `text_extraction`, `ulmc_improves_fit`, `author_conclusion` |
| `legacy_studies_search_terms.csv` | Pre-built MV% + phrase queries for all 182 |
| `legacy_studies_identifying_info.csv` | Overlap with prior extraction rows |
| `ONLINE_SEARCH_STRATEGY.md` | General year/title discovery workflow |

**Year gap**: `legacy_studies_online_search.csv` has no rows for these 10 Refids. Use probable-match DOIs above or distinctive-phrase Scholar searches; record year in Zotero once confirmed.
