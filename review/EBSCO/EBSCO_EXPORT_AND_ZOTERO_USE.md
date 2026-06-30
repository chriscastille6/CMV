# Using the EBSCO Metadata Export (02/23/2026) + Zotero

## What the EBSCO PDF Is

**File**: `EBSCO-Metadata-02_23_2026.pdf` (in Downloads)

- **Content**: EBSCO export of **50 records** from a search run on 02/23/2026.
- **Format**: Table of contents (titles + page numbers) then **full metadata** for each record:
  - **PublicationDate** (YYYYMMDD)
  - **Contributors** (authors)
  - **Source** (journal name)
  - **Volume**, **Issue**, **PageStart**–**PageEnd**
  - **DOI** (when present)
  - **AN** (EBSCO accession number)
  - **Abstract**, **Language**, **plink** (URL)

## How This Helps

1. **Reproducibility**  
   The export is a snapshot of what the EBSCO search returned on that date. You can:
   - Re-run the same search and compare hit counts and ANs.
   - Document “search date” and “records exported” for PRISMA.

2. **Verifying/correcting our extraction**  
   Many of the 50 titles match studies already in `systematic_extraction_40_studies.csv`, e.g.:
   - #34 Moral disengagement and moral judgment (Chen et al. – Ethics & Behavior)
   - #35 Heavy-Work Investment (Shkoler et al.)
   - #39 Ladders for Learning (Janson et al.)
   - #42 ASSESSING COMMON METHOD BIAS: PROBLEMS WITH THE ULMC TECHNIQUE
   - #43 Moral Leadership and Unethical Pro-organizational Behavior (Wang & Li)
   - #46 Give a Man a Fish or Teach a Man to Fish (Zhu et al.)
   - #48 Four Research Designs (Williams & McGonagle)
   - #49 Servant Leadership and Goal Attainment (diary study)

   You can match by title (or DOI) and use the export to:
   - Confirm or fix **year**, **authors**, **journal**, **DOI** in the extraction CSV.

3. **New candidates**  
   Any of the 50 that are not yet in the extraction can be added, with metadata taken straight from the export.

4. **Legacy studies**  
   The 50 are from a **recent** EBSCO search, so they are mostly post-2010. Legacy studies (69) came from the **original** Discovery search; overlap is possible but not guaranteed. For legacy papers that you also have in **Zotero**, Zotero is the better source for year/title/authors if the PDF export doesn’t contain them.

## Using Zotero Together

- **EBSCO export**: Use for the **current EBSCO search results** (the 50 records), reproducibility, and to fill/check metadata in the extraction sheet.
- **Zotero**: Use for:
  - **Legacy studies**: If a legacy study is in your Zotero library, pull year, title, authors, journal, DOI from Zotero to fill the extraction or `legacy_studies_year_entry_template.csv`.
  - **Cross-check**: For any study in both Zotero and the EBSCO export, compare and prefer Zotero when you’ve curated it (e.g. after attaching PDFs and fixing metadata).

**Practical workflow**

1. Parse the EBSCO PDF (or a CSV export from EBSCO) into a table: Title, Authors, Year, Journal, DOI, AN.
2. Match that table to `systematic_extraction_40_studies.csv` by title/DOI and update year, authors, journal, DOI where needed.
3. For legacy studies still missing year/title/authors: search your Zotero library (e.g. by journal + distinctive phrase or DOI if you have it) and fill from Zotero when you find a match.

## Parser Script and Output CSV

- **Script**: `review/EBSCO/parse_ebsco_export_pdf.py`  
  - Reads the EBSCO metadata PDF and writes `review/EBSCO/ebsco_export_50_records.csv`.
- **Run** (from project root or from `review/EBSCO`):
  ```bash
  python3 -m pip install pypdf   # once
  python3 review/EBSCO/parse_ebsco_export_pdf.py "/path/to/EBSCO-Metadata-02_23_2026.pdf"
  ```
  Default path if no argument: `~/Downloads/EBSCO-Metadata-02_23_2026.pdf`
- **Output CSV columns**: `record_num`, `title`, `authors`, `year`, `journal`, `volume`, `issue`, `doi`, `an`, `cover_date`, `plink`

The CSV is already generated at `review/EBSCO/ebsco_export_50_records.csv` (50 records). Use it to match by title or DOI to `systematic_extraction_40_studies.csv` and to verify or fill year, authors, journal, DOI.

## Full-Text Export (06/24/2026)

**File**: `imports/EBSCO-FullText-06_24_2026.pdf` — see **`EBSCO_FULLTEXT_06_24_2026.md`** for details.

- Single article (Pfrombeck et al., 2020, JOOP; DOI 10.1111/joop.12306), not a 50-record metadata bundle.
- Parsed with `parse_ebsco_fulltext_pdf.py` → `ebsco_fulltext_export_06_24_2026.csv`.
- **0 / 10** matches to `ARTICLES_TO_FIND_10.md` legacy hunt list.
- Fills a prior failed download (`download_results_31_60.csv`, study #56).
