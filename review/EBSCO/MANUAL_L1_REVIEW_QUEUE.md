# Manual Level 1 review queue

Generated: 2026-06-26

**0 articles** remaining with PDFs on hand flagged `manual_review` in `screening_batch_cohort_on_hand_2026_06_25.csv`.  
All manual L1 decisions applied 2026-06-26 (9 excluded — domain out of organizational/work-related scope).

Record decisions in master (`screening_status`) or re-run `screen_level1_batch.py` after updating rules.

## Scope decision rule

**Include** studies in organizational / work-related applied psychology (management, OB, HR, workplace behavior). **Exclude** studies whose primary domain or sample is outside that scope — e.g. public-health / epidemic communication, clinical patient populations, school/community samples with no work context, or other non-organizational settings — even when Q1.1–Q1.3 auto-pass on ULMC/PLS checks.

**Why each item was flagged:** see `decision_reason_code` / `decision_reason_text` in `ebsco_150_screening_evidence.csv`. **For/against rationales:** `MANUAL_L1_REVIEW_RATIONALES.md`.

| Done | master_id | EBSCO # | Title | Notes |
|:----:|-----------|--------:|-------|-------|
| [x] | M0244 | 63 | Beyond coexistence: health risk/promotion pathways (epidemics) | **Excluded** — public health/epidemics, out of scope |
| [x] | M0247 | 66 | Social support → exercise adherence (Korean college students) | **Excluded** — student exercise; no workplace context |
| [x] | M0251 | 70 | Social media addiction & social anxiety (college students) | **Excluded** — student social media/anxiety; no workplace context |
| [x] | M0252 | 71 | Social capital → health literacy (community residents) | **Excluded** — community public-health literacy; not organizational |
| [x] | M0255 | 74 | AI risk perception, learning anxiety → AI usage capability | **Excluded** — university student AI learning; not workplace |
| [x] | M0282 | 102 | Flourishing in IBD patients | **Excluded** — clinical patient sample, out of scope |
| [x] | M0289 | 109 | Interpersonal satisfaction & classroom silence | **Excluded** — classroom silence in higher ed; not organizational |
| [x] | M0293 | 113 | Self-transcendence values → cooperative behaviors | **Excluded** — language classroom cooperative learning; not organizational |
| [x] | M0323 | 143 | Social support, QoL, demoralization (IBD patients) | **Excluded** — clinical IBD patients; not organizational |
| [x] | M0353 | — | Parental burnout → adolescents' social adaptation | **Excluded** — parenting/adolescent outcomes; not organizational |
| [x] | M0474 | — | Global vs local brands preference formation | **Excluded** — consumer brand preference; not organizational/work context |

**Related:** EBSCO positions 1–150 → `EBSCO_PRIMARY_WORKLIST.md` (0 missing PDFs). **Bad PDF:** M0284 @ EBSCO #105. **Manual L1 queue cleared** (2026-06-26).
