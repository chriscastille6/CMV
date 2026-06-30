# Manual L1 review — include/exclude rationales

**Generated:** 2026-06-26  
**Scope:** Organizational / work-related applied psychology (see `CLASSIFICATION_REVIEW.md`).  
**Already excluded:** M0244, M0282.

Full per-paper bullets were produced in chat; this file records **lean recommendations** and reason codes. Verify via `ebsco_150_screening_evidence.csv`.

| Done | master_id | EBSCO # | Lean | Reason code (flag) | One-line rationale |
|:----:|-----------|--------:|------|--------------------|--------------------|
| [x] | M0247 | 66 | **Exclude** | `MANUAL_REVIEW_DOMAIN_BORDERLINE_STUDENT_SAMPLE` | Korean college students; exercise adherence — no work context |
| [x] | M0251 | 70 | **Exclude** | `MANUAL_REVIEW_DOMAIN_BORDERLINE_STUDENT_SAMPLE` | Student social-media/anxiety; Harman-only CMV, weak ULMC bar |
| [x] | M0252 | 71 | **Exclude** | `MANUAL_REVIEW_DOMAIN_BORDERLINE_COMMUNITY` | Community residents; public-health epidemic literacy (like M0244) |
| [x] | M0255 | 74 | **Exclude** | `MANUAL_REVIEW_DOMAIN_BORDERLINE_STUDENT_SAMPLE` | University student AI learning — education, not workplace |
| [x] | M0289 | 109 | **Exclude** | `MANUAL_REVIEW_LOW_CONFIDENCE_ALL_PASS` | Higher-ed classroom silence; no employee sample |
| [x] | M0293 | 113 | **Exclude** | `MANUAL_REVIEW_LOW_CONFIDENCE_ALL_PASS` | SLA cooperative learning in language classrooms |
| [x] | M0323 | 143 | **Exclude** | `MANUAL_REVIEW_DOMAIN_BORDERLINE_CLINICAL_PATIENTS` | IBD clinical patients (same pattern as M0282) |
| [x] | M0353 | — | **Exclude** | `MANUAL_REVIEW_DOMAIN_BORDERLINE_PARENTING` | Parenting burnout → adolescent outcomes |
| [x] | M0474 | — | **Exclude** | `MANUAL_REVIEW_DOMAIN_BORDERLINE_CONSUMER` | Consumer brand preference — excluded (domain out of scope) |

## Apply decisions

```bash
# Chat: e.g. "M0247 exclude" or "apply all nine excludes"
python3 review/EBSCO/apply_classification_feedback.py
python3 review/master/progress_counter.py
```

Update checkboxes in `MANUAL_L1_REVIEW_QUEUE.md` after feedback is applied.

## Retracted publications (Q1.4)

Studies formally retracted by the publisher are excluded at Level 1 (`level1_fail`; `EXCLUDE_RETRACTED`) regardless of domain/ULMC/PLS.

| master_id | Citation | Status |
|-----------|----------|--------|
| — | Fernández-Fernández et al. (2023). RETRACTED: The impact of teleworking technostress on satisfaction, anxiety and performance. *Heliyon* 9(6), e17201. | Cut from corpus (not in `articles_master.csv`); user-reported retraction 2026-06-30 |
