# EBSCO Search — 2026-06-24 Rerun

**Search date**: 2026-06-24  
**Interface**: EBSCO Research (`research.ebsco.com`)  
**Query** (exact legacy string from `review/LEGACY_SEARCH_REPRODUCE.md`):

```
"unmeasured latent method construct" OR "unmeasured latent method factor"
```

**Limiters** (as documented in `LEGACY_SEARCH_REPRODUCE.md`):

| Limiter | Setting |
|---------|---------|
| Full Text | On |
| Scholarly (Peer Reviewed) Journals | On |
| Source Type | Academic Journals |
| Publication Date | 2012–2022 |

## Total hits

| Metric | Count |
|--------|------:|
| **Total search results** | **1,031** |
| Raw rows exported (batches 2–12) | 520 |
| Cross-batch duplicate ANs/DOIs (merge script) | 29 |
| **Unique EBSCO rerun records in `articles_master.csv`** | **491** |
| **Records remaining to export** | **540** (1,031 − 491 unique) |

**Export gap**: Positions **251–300** are not yet exported. Batch 6 (`-7.csv`) covers result positions **301–350**, skipping the missing chunk after batch 5 (201–250).

**Final export note**: Batch 12 (`-12.csv`) returned only **20** rows (positions 551–570), not a full 50-record chunk. **40%** of those rows were cross-batch duplicates of earlier exports (mostly batch 5 / 201–250), suggesting EBSCO pagination returned recycled results near the end of the export run.

## Export batches

| File | Result positions | Rows | `ebsco_batch` | Status |
|------|------------------|-----:|---------------|--------|
| `imports/EBSCO-Metadata-06_24_2026-2.csv` | 1–50 | 50 | 1 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-3.csv` | 51–100 | 50 | 2 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-4.csv` | 101–150 | 50 | 3 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-5.csv` | 151–200 | 50 | 4 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-6.csv` | 201–250 | 50 | 5 | Merged |
| *(not yet exported)* | **251–300** | — | — | **Gap** |
| `imports/EBSCO-Metadata-06_24_2026-7.csv` | 301–350 | 50 | 6 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-8.csv` | 351–400 | 50 | 7 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-9.csv` | 401–450 | 50 | 8 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-10.csv` | 451–500 | 50 | 9 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-11.csv` | 501–550 | 50 | 10 | Merged |
| `imports/EBSCO-Metadata-06_24_2026-12.csv` | 551–570 | 20 | 11 | Merged (final) |

Filename suffix (`-2` … `-12`) is EBSCO's export chunk index; `ebsco_batch` in master is 1–11.

## Cross-batch duplicates (29 unique AN/DOI overlaps)

| Title (short) | Key | Batches |
|---------------|-----|---------|
| School Disconnectedness … Internet Addiction | 191221051 | 1 ↔ 3 |
| Green Transformational Leadership … | 191221021 | 1 ↔ 3 |
| Wearable Devices … Treatment Adherence | 191299637 | 1 ↔ 3 |
| Peer overqualification … dualistic work passion | 190570738 | 1 ↔ 3 |
| Information literacy … physical education | 189750102 | 1 ↔ 3 |
| Vitality and learning … mobile technology | 179805623 | 2 ↔ 4 |
| Supervisors as enhancers … resilience training | 10.1027/1866-5888/a000384 | 3 ↔ 12 |
| Pleasant hostility … brand crisis | 148204790 | 4 ↔ 7; also 4 ↔ 8; also 7 ↔ 8 |
| Empowering potential of intergroup leadership | 147379690 | 4 ↔ 8 |
| Follower Strengths-based Leadership … | 144580244 | 4 ↔ 8 |
| Understanding employee branding capability … | 183556440 | 4 ↔ 9 |
| Does legal registration help or hurt? | 150167173 | 7 ↔ 8 |
| Perceived justice and service recovery … | 149484660 | 7 ↔ 8 |
| To Be (Creative), or not to Be (Creative)? | 148041419 | 7 ↔ 8 |
| Appraisal of economic crisis … absenteeism | 145372473 | 7 ↔ 8 |
| Employee Entitlement, Engagement, and Performance | 148565526 | 7 ↔ 8 |
| From top to bottom … leader UPOB → team unethical climate | 10.1007/s12144-024-06958-7 | 5 ↔ 10 |
| Strengths-based leadership … knowledge sharing | 10.1007/s12144-024-06417-3 | 5 ↔ 10 |
| Friendship leading the darkness? … UPOB | 10.1007/s12144-024-06406-6 | 5 ↔ 10 |
| The role of affective states in goal setting | 10.1007/s12144-024-06130-1 | 5 ↔ 10 |
| LMX differentiation … psychological strain | 10.1007/s12144-024-05960-3 | 5 ↔ 10 |
| Mothers' parental burnout … parenting style | 10.1007/s12144-024-06045-x | 5 ↔ 12 |
| Boundary spanning … creative performance | 10.1007/s12144-024-05911-y | 5 ↔ 12 |
| Employee voice backfires … workplace deviance | 10.1007/s12144-023-05587-w | 5 ↔ 12 |
| Celebrity, peer, personal norms … fandom philanthropy | 10.1007/s12144-023-05588-9 | 5 ↔ 12 |
| Managerial coaching … psychological distress | 10.1007/s12144-023-05530-z | 5 ↔ 12 |
| Mobile technology use … innovative behavior | 10.1007/s12144-023-05446-8 | 5 ↔ 12 |
| Supervisor support for strengths use | 10.1007/s12144-023-04921-6 | 6 ↔ 12 |

See `review/master/duplicate_report.md` for full titles and DOIs.

## Legacy 182 crosswalk (cumulative)

| Refid | Batch / positions | Title (short) |
|-------|-------------------|---------------|
| 142 | batch 5 / 201–250 | Disconnecting to Detach … workplace telepressure |
| 4 | batch 7 / 351–400; batch 8 / 401–450 | To Be (Creative), or not to Be (Creative)? |
| 175 | batch 8 / 401–450 | Examining the JD-R model … Korean correctional officers |
| 5 | batch 12 / 551–570 | Relational energy at work … job engagement |

Batch 9 (451–500): **0** legacy 182 hits. Hunt-list refids (10-pilot): **0** hits in batch 9.

Batch 10 (501–550): **0** legacy 182 hits. Hunt-list refids (10-pilot): **0** hits in batch 10.

Batch 12 (551–570): **1** legacy 182 hit (refid **5**). Hunt-list refids (10-pilot): **0** hits.

## Relationship to legacy 656 → 315 pipeline

| Run | Interface | Hits (pre-dedup) | After platform dedup | Notes |
|-----|-----------|------------------|----------------------|-------|
| **Legacy (2012 review)** | University Discovery Service | 656 (or 687 w/ date box) | **315** | PsycINFO + Business Source Complete; DistillerSR screening → 182 |
| **2026-06-24 rerun** | EBSCO Research | **1,031** | *not yet run* | Same Boolean + limiters; broader federated index |

**Why 1,031 ≠ 656?** Plausible drivers (not mutually exclusive):

1. **Index bundle** — EBSCO Research searches more databases than the legacy PsycINFO + BSC pair inferred for Discovery Service.
2. **Platform deduplication** — Legacy workflow deduped inside Discovery to **315** before export; the 2026 rerun count is **pre-dedup** hits.
3. **Corpus drift** — Retrospective indexing may add records published 2012–2022 that were not indexed in the original search window.
4. **Interface / limiter encoding** — Full Text and Academic Journals checkboxes may not map 1:1 between Discovery Service and EBSCO Research.

**Workflow implication**: Treat the 2026 EBSCO rerun as the **active identification strand** for the legacy query. Do not assume the 491 unique exports so far are a subset of the legacy 315 until cross-matched.

## Next steps

1. Export positions **251–300** (fill gap) if additional unique records are needed.
2. Re-run `merge_sources.py` after any new batch.
3. After full export, cross-match against legacy 315/182 and update PRISMA screening counts.
4. Consider whether remaining **540** unexported hits are reachable via stable pagination or require alternative export (e.g., re-sort, smaller chunks, platform dedup view).
