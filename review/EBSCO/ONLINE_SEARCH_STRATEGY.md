# Online Search Strategy for Legacy Studies

**Date**: 2026-01-08  
**Goal**: Find publication year (and title/author if possible) for 69 legacy studies

---

## Current Status

### ✅ What We Have:
- **Journal**: All 69 legacy studies now have journal information
- **Refid**: Internal DistillerSR reference ID
- **Method Variance %**: Some studies have specific MV% values
- **Unique Phrases**: Some studies have unique identifying phrases

### ❌ What We're Missing:
- **Title**: Not available (generic "Legacy Refid X - ULMC Study")
- **Author**: Not available (generic "Legacy Study")
- **Year**: Not available (this is what we need to find)

---

## Search Strategy

Since we don't have title or author, we'll search using:
1. **Journal name** (we have this)
2. **Unique identifiers**:
   - Method variance percentages (e.g., 17.2%, 4.98%, 28%)
   - Unique phrases from text extraction (e.g., "creative role expectations", "harman criticized insensitive")
   - ULMC-related terms

---

## Prioritized Search List

### High Priority (1 study)
Studies with both unique phrases AND method variance %:
- **L4**: Journal of Business & Psychology
  - MV%: 4.98%
  - Unique phrase: "creative role expectations"
  - Search: `"Journal of Business & Psychology" "creative role expectations" ULMC 4.98%`

### Medium Priority (29 studies)
Studies with either unique phrases OR method variance %:
- These have some identifying information but may require more manual verification

### Low Priority (39 studies)
Studies with only journal name:
- These will be most challenging and may require browsing journal archives

---

## Search Methods

### Method 1: Google Scholar
1. Go to https://scholar.google.com
2. Use advanced search with:
   - Journal name in "Return articles published in"
   - Unique phrases in "with the exact phrase"
   - Method variance % in "with all of the words"
3. Look for papers that:
   - Match the journal
   - Contain the unique phrases
   - Report similar method variance percentages

### Method 2: Journal Website
1. Go to the journal's official website
2. Search their archive using:
   - Unique phrases from text extraction
   - ULMC or "unmeasured latent method construct"
   - Method variance percentages
3. Browse articles to find matches

### Method 3: Database Search (Scopus, Web of Science)
1. Search by journal name
2. Filter by keywords: "ULMC", "unmeasured latent method construct", "common method variance"
3. Look for papers with matching method variance percentages

---

## Example Searches

### Study L4 (High Priority)
- **Journal**: Journal of Business & Psychology
- **Search Query**: `"Journal of Business & Psychology" "creative role expectations" "creative self-expectations" ULMC`
- **Look for**: Paper reporting 4.98% method variance

### Study L2
- **Journal**: Journal of Business & Psychology
- **Search Query**: `"Journal of Business & Psychology" "marker variable" "measured cause variable" ULMC`
- **Look for**: Paper reporting 17.2% method variance

### Study L16
- **Journal**: Human Resource Development Quarterly
- **Search Query**: `"Human Resource Development Quarterly" "harman criticized insensitive" ULMC`
- **Look for**: Paper reporting 28% method variance

---

## Verification

When you find a potential match:
1. **Check journal**: Must match exactly
2. **Check method variance %**: Should match (or be very close)
3. **Check unique phrases**: Should appear in the paper
4. **Extract year**: From the citation or article metadata
5. **Extract title/author**: If found, update these fields too

---

## Files Created

1. **`legacy_studies_online_search.csv`**: All studies with search queries
2. **`legacy_studies_search_priority.csv`**: Prioritized list (HIGH/MEDIUM/LOW)
3. **`refid_journal_mapping.csv`**: Refid → Journal mapping

---

## Next Steps

1. Start with HIGH priority studies (easiest to find)
2. Work through MEDIUM priority studies
3. For LOW priority studies, may need to:
   - Browse journal archives by year
   - Check if you have PDFs for these studies
   - Use other identifying information if available

---

## Notes

- Some studies may be difficult to find without title/author
- Method variance percentages are unique identifiers when combined with journal
- Unique phrases from text extraction are strong identifiers
- Consider checking if you have PDFs or other documentation for these studies
