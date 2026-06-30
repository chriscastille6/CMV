# Extraction Feedback Loop

Short guide for humans and agents correcting EBSCO systematic extraction rows.

## Workflow

```text
enhanced_extraction_pipeline.R  →  pre-fill hints (enhanced_extraction_results.csv)
        ↓
Human / agent codes             →  systematic_extraction_40_studies.csv (authoritative)
        ↓
log_extraction_correction.py    →  extraction_corrections.csv (audit trail)
        ↓
extraction_feedback_report.py   →  extraction_feedback_report.md + summary CSV
```

Manual extraction remains authoritative. The pipeline assists; corrections are logged, not silently overwritten.

## Log a correction

```bash
python3 review/EBSCO/log_extraction_correction.py \
  --study-order 3 --field pls_sem_used --old TRUE --new FALSE \
  --note "CB-SEM study"

# Apply to extraction CSV in the same step:
python3 review/EBSCO/log_extraction_correction.py \
  --study-order 3 --field harman_deployed --old NA --new TRUE --apply
```

| Flag | Purpose |
|------|---------|
| `--study-order` | `study_order` in extraction CSV |
| `--field` | Column name |
| `--old` / `--new` | Previous and corrected values (`NA` if missing) |
| `--source` | `manual` (default), `agent`, or `pipeline` |
| `--note` | Rationale or quote from PDF |
| `--pdf-path` | Optional traceability |
| `--apply` | Also update `systematic_extraction_40_studies.csv` |

## Run feedback report (after batch coding)

```bash
python3 review/EBSCO/extraction_feedback_report.py
```

Outputs:

- `extraction_feedback_report.md` — field counts, study counts, pipeline hint alignment, top-5 regex candidates
- `extraction_feedback_summary.csv` — one row per correction with pipeline vs CSV comparison

## Files

| File | Role |
|------|------|
| `extraction_corrections.csv` | Append-only correction log |
| `log_extraction_correction.py` | CLI to append corrections |
| `extraction_feedback_report.py` | Aggregate report generator |
| `enhanced_extraction_results.csv` | Pipeline pre-fill (from `enhanced_extraction_pipeline.R`) |
| `systematic_extraction_40_studies.csv` | Authoritative coded rows |

## Future work (not automated)

The report lists the top 5 most-corrected fields as candidates for `enhanced_extraction_pipeline.R` regex updates. **Do not auto-modify regex from corrections** — review the report and update R patterns deliberately.

See also: `VARIABLE_CODEBOOK.md`, `review/master/MANUAL_WORKFLOW.md`, `review/RESTART_CHECKLIST.md` (B18).

## Model complexity and ULMC power (coding guidance)

**Purpose**: `num_constructs`, `num_indicators`, and `complexity_ratio` support descriptive synthesis of whether ULMC tests are likely underpowered — this is **coding guidance**, not a formal power analysis.

**Field definitions** (authoritative CSV columns):

| Field | Meaning |
|-------|---------|
| `num_constructs` | Latent constructs in the tested ULMC CFA/SEM |
| `num_indicators` | Total items/indicators in the measurement model |
| `complexity_ratio` | `num_indicators / num_constructs` |

**Derived flag** (`underpowered_heuristic` in dashboard Summary): `TRUE` when **any** of:

1. `num_indicators` < 15
2. `complexity_ratio` < 3 (~fewer than three indicators per construct)
3. `num_constructs` > 10

**Rationale**: Richardson et al. (2009) note that ULMC detection is sensitive to model size and specification; conventional CFA guidance treats sparse measurement models and large factor structures as challenging for stable variance decomposition. Use the flag for corpus-level prevalence counts, not per-study statistical inference.

**Pipeline**: `enhanced_extraction_pipeline.R` regex pre-fills counts from phrases like "9 constructs", "37 items", "five factors"; manual coding from measurement tables remains authoritative when regex conflicts with tables.
