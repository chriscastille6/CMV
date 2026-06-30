# Audit Results Guide

**Purpose**: Every number on the Progress dashboard **Summary** and **Datasets** tabs must be traceable to source CSV rows and explicit rules. Use this guide for human review and agent queries.

**Last updated**: 2026-06-24

---

## Canonical data sources

| File | Role |
|------|------|
| `review/master/articles_master.csv` | Unified article registry; `examination_status`, `study_order`, `article_id` (M####), cohort tags |
| `review/EBSCO/systematic_extraction_40_studies.csv` | Structured MV extraction (100 rows); primary field values for Summary stats |
| `review/EBSCO/ebsco_screening_pool_570.csv` | PRISMA 570-pool download/examine progress (not used for Summary stats) |
| `review/progress_results_data.json` | Datasets tab — one row per fully coded study |
| `review/progress_summary_data.json` | Summary tab — aggregated metrics with `metric_id`, `filter_rule`, `study_orders` |
| `review/progress_dashboard_data.json` | Progress tab — PDF/examination counters for 570 pool |

---

## Provenance chain

```
articles_master.csv ──┐
                      ├── build_results_tables.py ──► progress_results_data.json
systematic_extraction │                              progress_summary_data.json
_40_studies.csv ──────┘                                      │
                                                             ▼
progress_counter.py ──────────────────────────────► PROGRESS_DASHBOARD.html
                                                             │
audit_results.py (validation) ◄──────────────────────────────┘
query_results.py (CLI answers)
```

Regenerate after extraction or master edits:

```bash
python3 review/master/progress_counter.py
```

The counter also runs `audit_results.py` and writes `review/audit_results_report.md` (warns on FAIL).

---

## Definitions

### Fully coded

A study appears in **Datasets** / Summary when **either**:

1. `examination_status == fully_coded` in `articles_master.csv`, **or**
2. Its extraction row has **≥ 4** of these key fields populated (non-empty, not `NA`):
   - `management_domain`
   - `empirical_ulmc`
   - `statistical_methods_mv`
   - `method_variance_pct`
   - `procedural_remedies_list`

Implementation: `review/master/examination.py` → `is_fully_coded_row()`; join logic in `build_results_tables.py`.

### PLS vs CB-SEM (`pls_cbsem_category`)

**Mutually exclusive** — one category per study:

| Category | Rule |
|----------|------|
| **PLS-SEM** | `pls_sem_used=TRUE` **or** `estimator` is PLS-SEM/PLS |
| **CB-SEM** | else if `estimator=CB-SEM` **or** `not_pls=TRUE` |
| **Other/Unknown** | else if any PLS signal field is set but none of the above |
| **NA** | no signal in `pls_sem_used`, `not_pls`, or `estimator` |

Conflicting combinations (e.g. `pls_sem_used=TRUE` and `not_pls=TRUE`) are flagged in Datasets `notes` and audit warnings. See `VARIABLE_CODEBOOK.md`.

### Harman mean (`harman.mean_pct`)

Arithmetic mean of **numeric** `harman_variance_pct` values in the fully coded corpus. Non-numeric / empty values are excluded. `n` = count of studies with a parseable percentage.

### Corpus splits (`cohort`)

| Cohort | Rule |
|--------|------|
| `legacy` | `corpus_tier=legacy_gold` or `legacy_182` in `sources` |
| `ebsco_pool` | `ebsco_2026` in `sources` or `corpus_tier=ebsco_screened` |
| `other` | everything else fully coded |

---

## Common questions — exact commands

| Question | Command |
|----------|---------|
| How many PLS studies? | `python3 review/master/query_results.py --stat pls_count` |
| How many CB-SEM? | `python3 review/master/query_results.py --stat cbsem_count` |
| Mean Harman %? | `python3 review/master/query_results.py --stat harman_mean` |
| How many fully coded? | `python3 review/master/query_results.py --stat fully_coded_total` |
| List all fully coded | `python3 review/master/query_results.py --list-fully-coded` |
| One study by order | `python3 review/master/query_results.py --study-order 3` |
| One study by master ID | `python3 review/master/query_results.py --master-id M0210` |
| Any metric by ID | `python3 review/master/query_results.py --metric-id pls_cbsem.CB-SEM` |
| List stat aliases | `python3 review/master/query_results.py --list-stats` |

Each query prints: **value**, **n**, **rule**, **source paths**, and **study_orders** (where applicable).

### Validation pass

```bash
python3 review/master/audit_results.py
# → review/audit_results_report.md (PASS/FAIL)
```

Checks: recompute Summary from CSV; diff vs `progress_summary_data.json`; PLS mutual exclusivity; Harman mean; required ID fields; PLS field conflicts; column misalignment suspects.

---

## JSON metric drill-down

Each Summary row in `progress_summary_data.json` (when regenerated) includes:

- `metric_id` — e.g. `pls_cbsem.PLS-SEM`, `harman.mean_pct`
- `value`, `n` — displayed statistic and denominator
- `definition` — human-readable rule
- `filter_rule` — machine-readable filter (`field`/`op`/`value` or named function)
- `study_orders` — list of `study_order` keys included in that metric

Agents should prefer `query_results.py` over reading JSON directly — it recomputes from source and cites CSV row numbers.

---

## Related files

| File | Role |
|------|------|
| `review/master/build_results_tables.py` | Builds results + summary JSON |
| `review/master/query_results.py` | CLI for audit-safe answers |
| `review/master/audit_results.py` | Validation + report |
| `review/audit_results_report.md` | Latest PASS/FAIL output |
| `review/master/MANUAL_WORKFLOW.md` | Operational workflow |
| `review/EBSCO/VARIABLE_CODEBOOK.md` | Field definitions |
