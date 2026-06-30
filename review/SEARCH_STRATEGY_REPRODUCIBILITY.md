# Search Strategy – Reproducibility Reference

This document consolidates the search strategies used (or specified) for the ULMC systematic review so results can be reproduced.

**Primary identification** uses the **narrow PROSPERO query** only. Expanded Boolean and OpenAlex/Crossref searches are **supplementary/sensitivity** (optional) and are not the basis for primary PRISMA identification counts.

---

## 1. Primary identification (PROSPERO narrow query)

**Source**: `PROSPERO_DRAFT_REGISTRATION_FINAL.md`, `PRISMA_PROTOCOL.md`, `config.yaml` (`search.primary`).

| Element | Specification |
|--------|----------------|
| **Strategy** | **Primary** — narrow in-text ULMC phrases |
| **Core query** | `"unmeasured latent method construct" OR "unmeasured latent method factor"` |
| **Standard limiters** | Full text (when available); scholarly (peer-reviewed) journal articles; English |
| **Date range** | January 1, 2010 to December 31, 2026 |
| **Databases** | Institutional Discovery Service / EBSCO (PsycINFO + Business Source Complete) ONLY |
| **Screening** | Domain (management/OB/psychology), empirical ULMC use, and PLS tagging applied **after** search — not in query string |

**Rationale**: Capture scholars' usage of ULMC when cited in-text; high specificity. Aligns with legacy search that produced 656 → 315 → 182 included (see Section 2).

**To reproduce (primary)**:
```
"unmeasured latent method construct" OR "unmeasured latent method factor"
```
Apply standard limiters above → deduplicate (DOI/title) → Level 1 screening (management/OB/psych domain, empirical, ULMC, PLS flag).

---

## 2. Original legacy search (historical reference)

**Source**: `LEGACY_REVIEW_SUMMARY.md` (original review, circa 2012–2022).

| Element | Specification |
|--------|----------------|
| **Database** | Discovery Service (institutional library database) |
| **Search query** | Same narrow phrases (OR): `"unmeasured latent method construct"` OR `"unmeasured latent method factor"` |
| **Filters** | Full text only; Scholarly (peer reviewed) articles; Published in academic journals |
| **Result** | 656 records → 315 after deduplication → 182 passed Level 1 → 69 in current extraction CSV |

This is the **same narrow query** now designated as primary identification.

---

## 3. Expanded Boolean strategy (supplementary / sensitivity — optional)

**Source**: `PRISMA_PROTOCOL.md` §4 supplementary, `config.yaml` (`search.supplementary.expanded_boolean`, `search.terms.expanded`).

| Element | Specification |
|--------|----------------|
| **Status** | **Not primary identification** — optional sensitivity or gap-filling |
| **Databases** | Same primary databases if run |
| **Date range** | 2010–2026 |
| **Language** | English |

**Expanded ULMC terms (OR):**  
`"unmeasured latent method construct"` OR `"unmeasured latent method factor"` OR `"ULMC"` OR `"single method factor"` OR `"common latent factor"`

**Method variance terms (OR):**  
`"common method variance"` OR `"common method bias"` OR `"method variance"` OR `"Harman single factor"` OR `"Harman test"` OR `"marker variable"` OR `"procedural remedy"` OR `"separation of measurement"`

**Full Boolean (reproducible string):**
```
(("unmeasured latent method construct" OR "unmeasured latent method factor" OR "ULMC" OR "single method factor") 
AND 
("common method variance" OR "common method bias" OR "method variance"))
AND
(management OR organizational OR "human resource" OR psychology OR "applied psychology")
AND
(empirical OR survey OR questionnaire OR "structural equation")
```

Domain and empirical terms are embedded here (unlike the primary narrow query). Use only for supplementary searches.

---

## 4. Programmatic search — OpenAlex / Crossref (supplementary — optional)

**Source**: `review/config.yaml` (`search.supplementary.programmatic`), `review/01_search_harvest.R`.

| Element | Value |
|--------|--------|
| **Status** | **Not primary identification** — optional programmatic harvest |
| **Time window** | `start: 2010`, `end: 2026` |
| **Terms** | See `search.terms.expanded` in config |
| **Language** | en |

To reproduce: run from project root with `config.yaml` and API keys used in `01_search_harvest.R`. Merge results only as supplementary/sensitivity — do not combine with primary identification counts without deduplication and explicit labeling.

---

## 5. Quick reference

| Purpose | Query | Notes |
|---------|-------|-------|
| **Primary identification** | `"unmeasured latent method construct" OR "unmeasured latent method factor"` + standard limiters | PROSPERO; PRISMA identification counts |
| **Legacy reproduction** | Same as primary | Compare to 315 / 182 counts |
| **Sensitivity / gap-fill** | Expanded Boolean (§3) or OpenAlex/Crossref (§4) | Optional; label separately in PRISMA |

---

**File locations**  
- Legacy summary: `review/LEGACY_REVIEW_SUMMARY.md`  
- Protocol (full strategy): `review/PRISMA_PROTOCOL.md`  
- Config (terms, dates): `review/config.yaml`  
- PROSPERO (narrow strategy): `review/PROSPERO_DRAFT_REGISTRATION_FINAL.md`  
- Harvest script (supplementary): `review/01_search_harvest.R`
