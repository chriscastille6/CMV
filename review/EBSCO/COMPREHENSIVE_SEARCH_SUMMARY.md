# Comprehensive Search Summary: Finding Year for Legacy Studies

**Date**: 2026-01-08 (updated 2026-02-23)  
**Status**: In progress — 2 legacy studies fixed (L4, L16); 67 still need year

---

## ✅ Completed Tasks

### 1. Journal Information
- ✅ Found `systematic review/journals.xlsx` with Refid → Journal mapping (185 studies)
- ✅ Updated all 69 legacy studies in `systematic_extraction_40_studies.csv` with journal information
- ✅ Created `refid_journal_mapping.csv` for reference

### 2. Search Files Created
- ✅ `legacy_studies_online_search.csv` - Search queries for all 69 studies
- ✅ `legacy_studies_search_priority.csv` - Prioritized list (HIGH/MEDIUM/LOW)
- ✅ `legacy_studies_year_entry_template.csv` - Manual entry template
- ✅ `ONLINE_SEARCH_STRATEGY.md` - Detailed search instructions

### 3. PDF Sources Checked
- ✅ Checked Zotero library - Legacy studies not found
- ✅ Checked DistillerSR exports - No bibliographic data
- ✅ Found 158 PDFs in project (mostly EBSCO studies, not legacy)

---

## 📊 Current Status

### Legacy Studies (69 total)
- ✅ **Journal**: 69/69 (100%) - COMPLETE
- 🔄 **Year**: 4/69 (6%) - L4, L16, L5, L60 filled from **our database** (see below); 65 need search
- 🔄 **Title**: 4/69 - L4, L16, L5, L60 filled
- 🔄 **Author**: 4/69 - L4 (Liu et al.), L16 (Hutchins et al.), L5 (Owens et al.), L60 (Chen et al.)

---

## 🔍 Search Priority Breakdown

### HIGH Priority (1 study) — ✅ FOUND
- **L4**: Liu et al. (2021), "To Be (Creative), or not to Be (Creative)? A Sensemaking Perspective to Creative Role Expectations", Journal of Business & Psychology. (Duplicate of EBSCO Study 30.)

### MEDIUM Priority (29 studies)
**Moderate chance** - Has either unique phrase OR method variance %:
- Examples: L2 (17.2% MV), L29 (5% MV), L37 (2% MV), L39 (7.9% MV), etc.
- Search using: Journal + MV% OR Journal + unique phrase

### LOW Priority (39 studies)
**Most challenging** - Only has journal name:
- Examples: L17, L20, L26, etc.
- May require browsing journal archives or checking if PDFs exist

---

## 📝 Files for Manual Search

### 1. `legacy_studies_search_priority.csv`
**Use this file to prioritize your searches:**
- Start with HIGH priority studies
- Then work through MEDIUM priority
- Finally tackle LOW priority

**Columns:**
- `priority`: HIGH/MEDIUM/LOW
- `study_order`: L2, L4, etc.
- `journal`: Journal name
- `method_variance_pct`: MV% if available
- `unique_phrases`: Unique identifying phrases
- `search_query`: Ready-to-use search query

### 2. `legacy_studies_year_entry_template.csv`
**Use this file to record findings:**
- Fill in `year` as you find it
- Optionally fill in `title` and `first_author` if found
- Update `status`: NOT FOUND → FOUND → VERIFIED

**Columns:**
- `study_order`: L2, L4, etc.
- `refid`: Reference ID
- `journal`: Journal name (already filled)
- `year`: [TO BE FILLED]
- `title`: [OPTIONAL - if found]
- `first_author`: [OPTIONAL - if found]
- `method_variance_pct`: MV% for verification
- `search_priority`: HIGH/MEDIUM/LOW
- `status`: NOT FOUND / FOUND / VERIFIED

---

## 🔎 Search Methods

### Method 1: Google Scholar (Recommended)
1. Go to https://scholar.google.com
2. Use the search query from `legacy_studies_search_priority.csv`
3. Look for papers that:
   - Match the journal name
   - Contain the unique phrases (if any)
   - Report similar method variance percentages
4. Extract: **Year**, Title, Author

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

## 📋 Step-by-Step Process

### Step 1: Start with HIGH Priority
1. Open `legacy_studies_search_priority.csv`
2. Filter for `priority == "HIGH"`
3. Use the `search_query` column to search Google Scholar
4. When found, extract year (and title/author if possible)
5. Update `legacy_studies_year_entry_template.csv`

### Step 2: Continue with MEDIUM Priority
1. Filter for `priority == "MEDIUM"`
2. Search using journal + MV% or journal + unique phrase
3. Verify matches by checking MV% in the paper
4. Update template as you find them

### Step 3: Handle LOW Priority
1. Filter for `priority == "LOW"`
2. These are most challenging - may need to:
   - Browse journal archives by year
   - Check if you have PDFs for these studies
   - Use other identifying information if available

### Step 4: Update Main File
Once you have years in the template:
1. Use the template to update `systematic_extraction_40_studies.csv`
2. Run validation to ensure all data is correct

---

## 🎯 Example Searches

### Study L4 (HIGH Priority)
- **Journal**: Journal of Business & Psychology
- **Search**: `"Journal of Business & Psychology" "creative role expectations" "creative self-expectations" ULMC`
- **Look for**: Paper reporting 4.98% method variance
- **Verify**: Check if paper mentions "creative role expectations" and "creative self-expectations"

### Study L2 (MEDIUM Priority)
- **Journal**: Journal of Business & Psychology
- **Search**: `"Journal of Business & Psychology" "marker variable" "measured cause variable" ULMC`
- **Look for**: Paper reporting 17.2% method variance
- **Verify**: Check if paper mentions marker variable and measured cause variable

### Study L16 (MEDIUM Priority)
- **Journal**: Human Resource Development Quarterly
- **Search**: `"Human Resource Development Quarterly" "harman criticized insensitive" ULMC`
- **Look for**: Paper reporting 28% method variance
- **Verify**: Check if paper mentions Harman's test being criticized as insensitive

---

## ⚠️ Challenges

1. **No Title/Author**: We don't have these, so searches rely on:
   - Journal name
   - Unique phrases from text extraction
   - Method variance percentages

2. **Generic Phrases**: Some studies may have common phrases that appear in multiple papers

3. **MV% Verification**: Method variance percentages are strong identifiers when combined with journal

4. **Time-Consuming**: Manual search for 69 studies will take time, especially LOW priority ones

---

## 💡 Recommendations

1. **Start Small**: Begin with HIGH priority studies (just 1 study) to test the approach
2. **Batch Process**: Work through MEDIUM priority in batches of 5-10
3. **Document Findings**: Update the template as you go
4. **Verify Matches**: Always check MV% and unique phrases to confirm it's the right paper
5. **Consider Alternatives**: If search is too difficult, check if you have:
   - Original DistillerSR account with bibliographic export
   - PDF files for legacy studies
   - Master citation list from original review

---

## 📁 File Locations

All files are in: `/Users/ccastille/Documents/GitHub/CMV/review/EBSCO/`

- `legacy_studies_search_priority.csv` - Prioritized search list
- `legacy_studies_year_entry_template.csv` - Manual entry template
- `legacy_studies_online_search.csv` - All search queries
- `refid_journal_mapping.csv` - Refid → Journal mapping
- `ONLINE_SEARCH_STRATEGY.md` - Detailed search instructions
- `systematic_extraction_40_studies.csv` - Main extraction file (to be updated)

---

## 🔧 Applying legacy fixes

- **From our database**: Run `Rscript review/EBSCO/match_legacy_from_database.R` (from project root) to match legacy rows to EBSCO rows by **journal + method_variance_pct**. Fills year, title, authors for any legacy study that has the same journal and MV% as an EBSCO study in the extraction file. No manual search needed for those.
- **Script**: `apply_legacy_years.py` — reads `legacy_studies_year_entry_template.csv` and updates `systematic_extraction_40_studies.csv` (year, study_title, authors). Run after adding years to the template: `python apply_legacy_years.py`
- **Fixed so far (from database + manual)**:
  - **L4** = Liu et al. 2021 (Journal of Business and Psychology) — duplicate of EBSCO Study 30
  - **L16** = Hutchins et al. 2018 (Human Resource Development Quarterly) — duplicate of EBSCO Study 3
  - **L5** = Owens et al. 2016 (Journal of Applied Psychology, 2% MV) — matched to EBSCO Study 29
  - **L60** = Chen et al. 2021 (Ethics & Behavior) — matched to EBSCO Study 49

## ✅ Next Steps

1. **Search** for remaining 67 legacy studies using `legacy_studies_search_priority.csv` (Google Scholar, journal sites).
2. **Record findings** in `legacy_studies_year_entry_template.csv` (year, optional title and first_author, set status to FOUND/VERIFIED).
3. **Run** `python apply_legacy_years.py` to push template updates into the main extraction file.
4. **Repeat** until all 69 studies have year (and title/author where possible).

Good luck with the search! 🎯
