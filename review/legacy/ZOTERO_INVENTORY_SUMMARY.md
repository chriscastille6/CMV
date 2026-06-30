# Zotero Inventory Summary — Legacy 182 Gold Corpus

**Date**: 2026-06-24  
**Scope**: Map `final_include=TRUE` Refids (N=182) to Zotero library via MCP search + prior `zotero_inventory.csv` crosswalk.

---

## Headline Counts

| Metric | Count | % of 182 |
|--------|------:|---------:|
| **In Zotero (any evidence)** | **8** | **4.4%** |
| — High confidence | 3 | 1.6% |
| — Medium confidence | 2 | 1.1% |
| — Low confidence | 3 | 1.6% |
| **With PDF attachment** | **8** | **4.4%** |
| **Not in Zotero** | **174** | **95.6%** |

Full row-level inventory: [`legacy_182_zotero_inventory.csv`](legacy_182_zotero_inventory.csv)

---

## Comparison to Prior `zotero_inventory.csv` (32 items)

| Prior snapshot | This inventory |
|----------------|----------------|
| 32 PDFs in "ULMC – Sys. Review" folder | 32 unchanged locally |
| 30 screened + 2 methodological | Only **8** of 32 map to a legacy-182 Refid |
| Assumed overlap with legacy corpus | **24** Zotero items are EBSCO/new-search studies **outside** the 182 gold set |
| No Refid linkage | 3 Refids have MCP `journalArticle` keys; 5 more via local PDF filename crosswalk only |

**Interpretation**: The existing Zotero folder is an EBSCO screening stash, not a legacy-182 archive. Prior Jan 2026 search ([`EBSCO/ZOTERO_SEARCH_RESULTS.md`](../EBSCO/ZOTERO_SEARCH_RESULTS.md)) correctly reported that legacy empirical studies were absent; this inventory quantifies that gap at **174/182**.

---

## MCP Search Results

### Tags / collections
| Query | Result |
|-------|--------|
| `tag:ULMC` | **0 items** |
| `tag:CMV` | **0 items** |
| `tag:systematic review` | **0 items** |
| `tag:method variance` | **0 items** |
| `qmode=everything` "unmeasured latent method" | 38 items (mostly methodological papers, reviews, attachments) |
| `qmode=everything` "ULMC systematic review" | 4 items (none are legacy 182 empirical studies) |

### Distinctive legacy text phrases (69 L-prefix studies)
Spot-checks and batch searches on `zotero_search_plan.csv` phrases (e.g., Refid 2 MV 17.2% snippet, Refid 16 Harman criticism, Refid 84 nursing 24% variance) returned **no journalArticle matches**. Legacy included studies are not indexed in the connected Zotero library.

### MCP metadata successes (high confidence)
| Refid | Zotero key | Title | PDF |
|------:|------------|-------|-----|
| 4 | `74ZMKM9E` | Liu et al. 2021 — creative role expectations (JBP) | yes (1 attachment) |
| 5 | `J2MRMKZM` | Owens et al. 2016 — relational energy (JAP) | yes (`YLV9G27Y`) |

### Local ULMC collection PDFs (no MCP parent key)
| Refid | Confidence | Source |
|------:|------------|--------|
| 16 | high | Hutchins 2018 HRDQ — L16 extraction row |
| 175 | medium | Cho 2020 Current Psychology — probable fuzzy match |
| 181 | medium | Ahmad 2021 Sustainability — probable fuzzy match |
| 19 | low | Igalla 2020 PMR — weak journal-only |
| 151 | low | Moon 2020 JBE — weak MV% match |
| 171 | low | Brouer 2015 JAP — weak journal-only |

---

## Limitations

1. **MCP search ceiling**: Default `limit=10–100`; broad journal queries return generic `PDF` attachments without parent metadata — unsuitable for automated Refid matching.
2. **No collection-scoped search**: "ULMC – Sys. Review" is not exposed as a tag; collection harvest was not possible via MCP.
3. **Attachment-only indexing**: Many folder PDFs are stored as bare attachments; `titleCreatorYear` mode often returns empty while `everything` mode is noisy.
4. **Fulltext spot-check**: `zotero_item_fulltext` on `74ZMKM9E` returned **404** (fulltext not indexed locally).
5. **Fuzzy crosswalk risk**: 3 Refids (19, 151, 171) rely on weak overlap heuristics — treat as provisional until DOI/title verified.

---

## Top 3 Recommendations

1. **Bulk import legacy 182 into Zotero** (Phase 2 / checklist B24): Use `refid_journal_mapping.csv` + DistillerSR metadata; tag each item `legacy-refid-{n}` for deterministic joins.
2. **Prioritize PDF acquisition for the 101 gap Refids** ([`legacy_182_gaps_only.csv`](legacy_182_gaps_only.csv)) before re-extraction — Zotero cannot substitute for missing source PDFs.
3. **Reconcile the 32-item folder**: Keep EBSCO supplements separate; do not assume folder coverage implies legacy-182 completeness (only 4.4% overlap confirmed).

---

## Regeneration

```bash
python3 review/legacy/build_legacy_182_zotero_inventory.py
```

Update `MCP_META` / `ZINV_TO_REFID` in that script when new MCP matches are confirmed.
