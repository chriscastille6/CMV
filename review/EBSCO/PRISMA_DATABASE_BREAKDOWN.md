# PRISMA Database Breakdown - Options

## Your Databases

Based on your search documentation:

1. **Discovery Services** (Legacy, 2012-2022): 656 records
   - Accesses: PsycINFO, Business Source Complete
   - Your university's discovery service

2. **OpenAlex/Crossref** (New, 2023-2025): 82,906 records
   - Programmatic API search
   - Different from discovery services

3. **EBSCO Research** (2026-06-24 rerun, legacy query): **1,031** records
   - Same Boolean + limiters as legacy Discovery search (`LEGACY_SEARCH_REPRODUCE.md`)
   - Supersedes Feb 2026 partial export (50 records)
   - Export in progress: 200 raw / 194 unique in master (see `EBSCO_SEARCH_06_24_2026.md`)

4. **Zotero** (32 records)
   - From book chapter work
   - Not a database search

## PRISMA2020 Options

The package allows you to specify databases in the "Databases" section. Options:

### Option A: List Specific Databases
```
Records identified from: Databases
  - Discovery Services (PsycINFO, Business Source Complete): 656
  - OpenAlex: 82,906
  - EBSCO: 50
  Total: 83,612
```

### Option B: Group by Search Type
```
Records identified from: Databases
  - Discovery Services: 656
  - OpenAlex/Crossref (API): 82,906
  - EBSCO: 50
  Total: 83,612
```

### Option C: Show as Single "Databases" with Breakdown
```
Records identified from: Databases (n = 83,612)
  Discovery Services: 656
  OpenAlex/Crossref: 82,906
  EBSCO: 50
```

### Option D: Keep Simple (Current)
```
Records identified from: Databases (n = 83,644)
```
(Includes Zotero 32 in total)

## Questions

1. **Should we list specific databases** in the PRISMA diagram?
   - Yes - more transparent
   - No - keep simple

2. **How to handle Zotero (32)**?
   - Include in databases total?
   - Show separately?
   - Exclude (since it's from previous work)?

3. **Preferred format**?
   - Option A: Detailed list
   - Option B: Grouped
   - Option C: Single number with breakdown
   - Option D: Simple total

4. **EBSCO (50)**: 
   - Is this a separate database search, or part of discovery services?
   - Should it be listed separately?

---

**Your preference?** I can update the diagram once you decide!

