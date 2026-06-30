# EBSCO classification review

**Updated:** 2026-06-26

Interactive review queue for Level 1 screening decisions that need human judgment. Automated L1 passed Q1.1–Q1.3 on these articles but confidence was low, or the article sits outside the primary EBSCO position map.

Structured rationale for every worklist row: `ebsco_150_screening_evidence.csv` (`decision_reason_code`, `decision_reason_text`). Verification sample (3 papers): `VERIFICATION_SAMPLE.md`.

## Scope decision rule

**Include** studies in organizational / work-related applied psychology (management, OB, HR, workplace behavior). **Exclude** studies whose primary domain or sample is outside that scope — e.g. public-health / epidemic communication, clinical patient populations, school/community samples with no work context, or other non-organizational settings — even when Q1.1–Q1.3 auto-pass on ULMC/PLS checks.

## How to give feedback

### Option A — Chat (fastest for a few articles)

Tell the agent your decision using `master_id` + action:

```
M0244 include
M0282 exclude
M0474 exclude — wrong PDF on disk
```

The agent runs:

```bash
python3 review/EBSCO/apply_classification_feedback.py --decision M0244 include
python3 review/master/progress_counter.py
```

### Option B — CSV (batch)

1. Open [`classification_feedback.csv`](classification_feedback.csv)
2. Fill `user_decision` with one of: `include`, `exclude`, `exclude_pls`, `manual_review`
3. Optional: add `user_notes`
4. Run:

```bash
python3 review/EBSCO/apply_classification_feedback.py
python3 review/master/progress_counter.py
```

Rows with `applied=Y` are skipped on re-run.

### Valid decisions

| user_decision | screening_status in master |
|---------------|---------------------------|
| `include` | `included` (triggers extraction pre-fill) |
| `exclude` | `level1_fail` |
| `exclude_pls` | `excluded_pls` |
| `manual_review` | `manual_review` (stay in queue) |

---

## Priority queue — manual L1 review (9)

Automated L1 flagged **low-confidence include** — verify management domain and ULMC relevance.

| master_id | EBSCO # | Title | Notes |
|-----------|--------:|-------|-------|
| ~~M0244~~ | ~~63~~ | ~~Beyond coexistence: health risk/promotion pathways (epidemics)~~ | **Excluded** — public health/epidemics, out of scope |
| M0247 | 66 | Social support → exercise adherence (Korean college students) | |
| M0251 | 70 | Social media addiction & social anxiety (college students) | |
| M0252 | 71 | Social capital → health literacy (community residents) | |
| M0255 | 74 | AI risk perception, learning anxiety → AI usage capability | |
| ~~M0282~~ | ~~102~~ | ~~Flourishing in IBD patients~~ | **Excluded** — clinical patient sample, out of scope |
| M0289 | 109 | Interpersonal satisfaction & classroom silence | |
| M0293 | 113 | Self-transcendence values → cooperative behaviors | |
| M0323 | 143 | Social support, QoL, demoralization (IBD patients) | |
| M0353 | — | Parental burnout → adolescents' social adaptation | Outside EBSCO 1–150 export |
| M0474 | — | Global vs local brands preference formation | **Wrong PDF on disk** — re-acquire before include |

PDFs: `review/EBSCO/pdfs/EBSCO_<master_id>_*.pdf`

---

## Optional — borderline auto-excluded (5)

Low-confidence **Q1.1 domain fail** exclusions you may want to overturn. Not pre-filled in the feedback CSV; add a row or use chat if you disagree with the auto-exclude.

| master_id | EBSCO # | Title | Auto rationale |
|-----------|--------:|-------|----------------|
| M0187 | 5 | School disconnectedness & adolescent internet addiction | No management-domain signal |
| M0195 | 13 | Cumulative family risk & migrant children's school adjustment | No management-domain signal |
| M0200 | 18 | Urban Restorative Potential Scale (Philippines) | No management-domain signal |
| M0225 | 44 | (see batch CSV) | Domain + ULMC ambiguity |
| M0226 | 45 | Beyond prompt engineering (GenAI composition) | No management-domain signal |

Full rationales: [`screening_batch_cohort_on_hand_2026_06_25.csv`](screening_batch_cohort_on_hand_2026_06_25.csv)

---

## Related files

| File | Purpose |
|------|---------|
| [`classification_feedback.csv`](classification_feedback.csv) | User decisions (11 pre-populated) |
| [`apply_classification_feedback.py`](apply_classification_feedback.py) | Apply CSV/chat decisions to master |
| [`MANUAL_L1_REVIEW_QUEUE.md`](MANUAL_L1_REVIEW_QUEUE.md) | Checklist mirror of manual queue |
| [`../PROGRESS_DASHBOARD.html`](../PROGRESS_DASHBOARD.html) | **EBSCO 1–150** tab — scanned counts |

## After feedback

```bash
python3 review/EBSCO/apply_classification_feedback.py
python3 review/master/progress_counter.py
```

Included articles are queued for `extract_ebsco_on_hand_batch.py` automatically.
