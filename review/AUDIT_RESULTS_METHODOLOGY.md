# Audit Results Methodology

**Last updated**: 2026-06-24

This document defines how every **Summary** tab statistic in `progress_summary_data.json` is computed from row-level **Datasets** in `progress_results_data.json`. Each metric includes drill-down via `study_orders` so any count can be traced to exact articles.

## Source pipeline

```
articles_master.csv  +  systematic_extraction_40_studies.csv
        ↓ build_results_tables.py (via progress_counter.py)
progress_results_data.json   →  Datasets tab (69 fully coded studies)
        ↓ build_summary_payload()
progress_summary_data.json   →  Summary tab (aggregated metrics)
        ↓ audit_results.py
review/audit_results_report.md
```

**Rebuild command**: `python3 review/master/progress_counter.py`  
**Audit command**: `python3 review/master/audit_results.py`  
**Query command**: `python3 review/master/query_result.py --metric-id <id>`

## Fully coded corpus

A study appears in Datasets when:

1. `examination_status == fully_coded` in `articles_master.csv`, **or**
2. Extraction row has ≥ 4 key MV fields populated (`examination.KEY_EXTRACTION_FIELDS`).

Join keys (in order): `study_order`, `legacy_refid`, normalized DOI.

## Identification fields (Datasets)

Every row must carry:

| Field | Source | Example |
|-------|--------|---------|
| `study_order` | master or extraction | `L142` |
| `article_id` | master | `M0047` |
| `master_id` | alias of `article_id` | `M0047` |
| `legacy_refid` | master | `98` |
| `doi` | master or extraction | `10.1000/...` or `NA` |

## Metric row schema

Each Summary row (except spacers/headers) includes:

| Key | Purpose |
|-----|---------|
| `metric_id` | Stable identifier for queries and audit |
| `value` | Primary statistic (count or numeric) |
| `n` | Denominator or sub-sample size |
| `definition` | Plain-English meaning |
| `filter_rule` | `{description, filter}` — human + machine filter |
| `study_orders` | Sorted list of matching `study_order` values |
| `cells` | Display values for dashboard table |

## Table: Corpus counts (`corpus_counts`)

| metric_id | Definition | Filter |
|-----------|------------|--------|
| `corpus_counts.total` | All fully coded studies | all studies |
| `corpus_counts.legacy` | Legacy 182 cohort | `cohort == legacy` |
| `corpus_counts.ebsco_pool` | EBSCO 570 screening pool | `cohort == ebsco_pool` |
| `corpus_counts.other` | Outside legacy and pool | `cohort == other` |

Cohort assignment (`build_results_tables.classify_cohort`):

- `ebsco_pool`: `sources` contains `ebsco_2026` or `corpus_tier == ebsco_screened`
- `legacy`: `corpus_tier == legacy_gold` or `sources` contains `legacy_182`
- else `other`

## Table: PLS vs CB-SEM (`pls_usage`)

**Mutually exclusive** — each study receives exactly one category via `classify_pls_cbsem`:

1. **PLS-SEM** if `pls_sem_used == TRUE` **or** `estimator == PLS-SEM`
2. Else **CB-SEM** if `estimator == CB-SEM` **or** `not_pls == TRUE`
3. Else **Other/Unknown** if any PLS signal field is populated
4. Else **NA**

| metric_id | Category |
|-----------|----------|
| `pls_cbsem.PLS-SEM` | PLS-SEM |
| `pls_cbsem.CB-SEM` | CB-SEM |
| `pls_cbsem.Other/Unknown` | Other/Unknown |
| `pls_cbsem.NA` | NA |

Conflicting extraction fields (e.g. `pls_sem_used=TRUE` and `estimator=CB-SEM`) are flagged in Datasets `notes` and reported as audit **warnings** — they do not double-count across categories.

## Table: Harman single-factor test (`harman_deployed`)

**Primary row (lead statistic)**:

| metric_id | Definition |
|-----------|------------|
| `harman.mean_pct` | Mean of numeric `harman_variance_pct` (rounded 2 dp); `n` = count with numeric value |
| `harman.numeric_count` | Studies with parseable numeric `harman_variance_pct` |

Numeric parsing (`parse_numeric`): strips `%`, commas; extracts first float.

**Secondary rows** — tristate counts on `harman_deployed`:

| metric_id | Filter |
|-----------|--------|
| `harman_deployed.TRUE` | `harman_deployed == TRUE` |
| `harman_deployed.FALSE` | `harman_deployed == FALSE` |
| `harman_deployed.NA` | `harman_deployed == NA` |

## Table: ULMC fit and final model (`ulmc_fit_cross`)

Cross-tab of normalized tristate values:

- `ulmc_improves_fit` × `ulmc_in_final`
- metric_id pattern: `ulmc_fit_cross.{improves_fit}_{in_final}`

## Table: Procedural remedies (`procedural_remedies`)

| metric_id | Definition |
|-----------|------------|
| `procedural_remedies.any` | `procedural_remedies_used == TRUE` |
| `procedural_remedies.{term}` | Term appears in `procedural_remedies_list` (split on `;`, `|`, `,`) |

Top 10 remedy terms by frequency.

## Table: MV inference (`mv_inference`)

Tristate counts on `mv_inferred_not_problem`, plus top 10 criterion terms from `mv_inference_criteria_list`.

## Table: Business school authors (`business_school_authors`)

Tristate counts on `authors_business_school`.

## Table: Method variance % (`method_variance_pct`)

Numeric parsing on `method_variance_pct`:

| metric_id | Statistic |
|-----------|-----------|
| `method_variance_pct.count` | n with numeric value |
| `method_variance_pct.mean` | arithmetic mean |
| `method_variance_pct.median` | median |
| `method_variance_pct.min` | minimum |
| `method_variance_pct.max` | maximum |

Mean/median/min/max share the same `study_orders` (all studies with numeric MV%).

## Table: Model complexity (`model_complexity`)

Source fields from extraction CSV: `num_constructs`, `num_indicators`, `complexity_ratio`.

| metric_id | Definition |
|-----------|------------|
| `model_complexity.constructs_reported` | n with parseable `num_constructs` |
| `model_complexity.indicators_reported` | n with parseable `num_indicators` |
| `model_complexity.mean_constructs` | Mean `num_constructs` (subset with value) |
| `model_complexity.mean_indicators` | Mean `num_indicators` (subset with value) |
| `model_complexity.mean_ratio` | Mean `complexity_ratio` (subset with value) |
| `model_complexity.underpowered_heuristic` | n with derived `underpowered_heuristic == TRUE` |

**Field meanings** (see `VARIABLE_CODEBOOK.md`):

- `num_constructs` — latent constructs in the tested ULMC CFA/SEM
- `num_indicators` — total measurement-model items/indicators
- `complexity_ratio` — `num_indicators / num_constructs`

**Derived flag** `underpowered_heuristic` (Datasets column only; not in extraction CSV): `TRUE` when **any** of:

1. `num_indicators` < 15
2. `complexity_ratio` < 3
3. `num_constructs` > 10

This is **coding guidance** for synthesis (likely underpowered ULMC contexts), not a formal statistical power test. Rationale: Richardson et al. (2009) on ULMC sensitivity to model size; conventional CFA practice (~3+ indicators per factor, adequate items relative to parameters).

Denominator for the underpowered row: studies where the heuristic is evaluable (`TRUE` or `FALSE`), not `NA`.

## Table: Management domain (`management_domain`)

Tristate counts on `management_domain`.

## Audit checks (`audit_results.py`)

1. Recompute Summary from Datasets; assert each `metric_id` matches on `value`, `n`, `study_orders`
2. PLS/CB-SEM: no study appears in more than one category bucket
3. Harman mean equals `mean(parse_numeric(harman_variance_pct))` among numeric rows
4. Required identification fields present on every Datasets row
5. Extraction CSV PLS field conflicts reported as warnings

Exit code 0 only when all error checks pass.

## Query examples

```bash
# Which studies are CB-SEM?
python3 review/master/query_result.py --metric pls_cbsem --category CB-SEM

# Full metric metadata + study list
python3 review/master/query_result.py --metric-id harman.mean_pct

# Single study row
python3 review/master/query_result.py --study-order L142
python3 review/master/query_result.py --master-id M0210

# All metric_ids
python3 review/master/query_result.py --list-metrics
```
