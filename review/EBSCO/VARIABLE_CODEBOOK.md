# Variable Codebook: Systematic Extraction Data

**File**: `systematic_extraction_40_studies.csv`  
**Total Variables**: 70  
**Last Updated**: 2026-06-25 (search strategy + extraction schema realignment)

This codebook documents all variables in the systematic extraction CSV file. Use this as a reference when extracting data to ensure consistency and completeness.

---

## Table of Contents

1. [Study Identification](#study-identification)
2. [Level 1 Screening](#level-1-screening)
3. [Statistical Methods](#statistical-methods)
4. [Method Variance Measures](#method-variance-measures)
5. [ULMC Fit Assessment](#ulmc-fit-assessment)
6. [Procedural Remedies](#procedural-remedies)
7. [Richardson et al. (2009) Citation](#richardson-et-al-2009-citation)
8. [Three-Step ULMC Approach](#three-step-ulmc-approach)
9. [Sample Characteristics](#sample-characteristics)
10. [Author Conclusions](#author-conclusions)
11. [Study Characteristics](#study-characteristics)
12. [Publisher / Outlet Family](#publisher--outlet-family)
13. [Supplement / Incomplete Main Text](#supplement--incomplete-main-text)
14. [Verification](#verification)
15. [Validation Rules](#validation-rules)

---

## Study Identification

### study_order
- **Type**: Text/String
- **Description**: Unique identifier for each study in the extraction
- **Format**: Numeric (e.g., "3", "37") or Legacy identifier (e.g., "L2", "L17")
- **Valid Values**: Any unique identifier
- **Examples**: "3", "37", "40", "L2", "L17"
- **Notes**: Must be unique across all studies. Legacy studies use "L" prefix.

### study_title
- **Type**: Text/String
- **Description**: Full title of the study
- **Format**: Full citation title, typically "Author et al. (Year) - Title"
- **Valid Values**: Any text
- **Examples**: "Hutchins et al. (2018) - What imposters risk at work"
- **Notes**: Can be empty for legacy studies with incomplete metadata

### authors
- **Type**: Text/String
- **Description**: Author names (comma-separated or "et al." format)
- **Format**: "Last1, First1; Last2, First2" or "Last1 et al." or "Legacy Study"
- **Valid Values**: Any text
- **Examples**: "Hutchins, Penney, Sublett", "Ahmad et al.", "Legacy Study"
- **Notes**: Can be empty for legacy studies

### year
- **Type**: Numeric/Text
- **Description**: Publication year
- **Format**: YYYY (4-digit year)
- **Valid Values**: Numeric (e.g., "2018", "2021") or "NA" if not available
- **Examples**: "2018", "2021", "NA"
- **Notes**: Must be "NA" (not empty string) if missing

### journal
- **Type**: Text/String
- **Description**: Journal name where the study was published
- **Format**: Full journal name
- **Valid Values**: Any text or empty string
- **Examples**: "Human Resource Development Quarterly", "Sustainability (MDPI)"
- **Notes**: Can be empty for legacy studies

### doi
- **Type**: Text/String
- **Description**: Digital Object Identifier
- **Format**: Full DOI (e.g., "10.1111/1748-8583.12272") or "NA" if not available
- **Valid Values**: DOI string or "NA"
- **Examples**: "10.1111/1748-8583.12272", "10.3390/su13179675", "NA"
- **Notes**: Must be "NA" (not empty string) if missing

### publisher_outlet
- **Type**: Categorical/Text
- **Description**: Publisher or outlet family for the article (MDPI, Frontiers, etc.)
- **Valid Values**: `MDPI`, `Frontiers`, `Elsevier`, `Springer`, `Wiley`, `SAGE`, `Taylor & Francis`, `Emerald`, `APA/PSYC`, `Other`, `NA`
- **Inference rules** (auto-fill when DOI/journal available; manual override authoritative):
  - DOI prefix `10.3390/` → `MDPI`
  - DOI prefix `10.3389/` → `Frontiers`
  - DOI prefixes: `10.1016/` Elsevier; `10.1007/` or `10.1186/` Springer; `10.1002/` or `10.1111/` Wiley; `10.1177/` SAGE; `10.1080/` Taylor & Francis; `10.1108/` Emerald; `10.1037/` APA/PSYC
  - Journal contains `Frontiers in` → `Frontiers`
  - Journal contains `(MDPI)` or known MDPI titles (Sustainability, Behavioral Sciences, Administrative Sciences, IJERPH, JTAER) → `MDPI`
- **Examples**: `MDPI`, `Frontiers`, `Wiley`, `NA`
- **Notes**: Code `Other` when publisher is known but not in list; `NA` when unknown. Many EBSCO pool articles are MDPI/Frontiers — always code explicitly.

### publisher_outlet_detail
- **Type**: Text/String (optional)
- **Description**: Full journal name or outlet clarification when `publisher_outlet` alone is insufficient
- **Valid Values**: Any text or empty string
- **Examples**: `Sustainability (MDPI)`, `Frontiers in Psychology`
- **Notes**: Often mirrors `journal`; use when journal field is empty but outlet inferred from DOI

### predatory_journal_flag
- **Type**: Boolean
- **Description**: Study published in a predatory or questionable outlet (e.g., MDPI per Beall-style lists)
- **Valid Values**: "TRUE", "FALSE", "NA"
- **Coding rule**: Code "TRUE" when `publisher_outlet` matches `tag_predatory_publishers` in `config.yaml` (currently MDPI) or other documented questionable publisher. **Do not exclude** these studies — include in main analysis and use flag for **sensitivity analysis** (see `PRISMA_PROTOCOL.md`).
- **Inference**: Auto-flag when `publisher_outlet` = "MDPI"; manual override authoritative
- **Notes**: Distinct from journal quality ratings; documents outlet for subgroup/sensitivity reporting only

---

## Level 1 Screening

### retracted_publication
- **Type**: Boolean
- **Description**: Has the study been formally retracted by the publisher? (Q1.4 — evaluated before Q1.1–Q1.3)
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE" if not retracted; "NA" if not determined
- **Notes**: If "TRUE", exclude regardless of domain/ULMC/PLS. Set `screening_status` = `level1_fail` and `decision_reason_code` = `EXCLUDE_RETRACTED`. Signals: title prefix `RETRACTED:` / `RETRACTED ARTICLE:`, EBSCO metadata `retracted` flag, publisher retraction notice in PDF. Example cut: Fernández-Fernández et al. (2023), *Heliyon* e17201.

### management_domain
- **Type**: Boolean
- **Description**: Is the study in management/HRM/OB/Applied Psychology domain?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "NA" if not determined
- **Notes**: Must be "TRUE" for inclusion in review. Must be "NA" (not empty string) if missing.
- **Relationship to `authors_business_school`**: `management_domain` screens **journal/topic** (Q1.1 — is the outlet/content in management, HRM, OB, or applied psychology?). `authors_business_school` codes **author institutional affiliation** (Q2.18 — is at least one author at a business school?). A study can be management-domain (`TRUE`) with non–business-school authors (e.g., I-O psychology department) or business-school authors in a non-management journal. Code independently.

### empirical_ulmc
- **Type**: Boolean
- **Description**: Is this an empirical study that uses ULMC to test CMV?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "NA" if not determined
- **Notes**: Must be "TRUE" for inclusion. Must be "NA" (not empty string) if missing.

### not_pls
- **Type**: Boolean
- **Description**: Does the study NOT use PLS estimation?
- **Valid Values**: "TRUE", "FALSE", "NA"
- **Notes**: 
  - "TRUE" = included (CB-SEM study)
  - "FALSE" = excluded (PLS study)
  - "NA" = not determined
  - Must be "NA" (not empty string) if missing

### pls_sem_used
- **Type**: Boolean
- **Description**: Was PLS-SEM used?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **Notes**: 
  - **Always extract and retain** — PLS studies are captured for prevalence/misuse documentation even when excluded from CB-SEM synthesis.
  - If "TRUE", study is **excluded from CB-SEM synthesis** (`not_pls` = "FALSE"; Level 1 Q1.3 = Yes → exclude) but **not dropped** from the extraction corpus.
  - `config.yaml` sets `include_pls: true` and `tag_pls: true` so PLS misuse can be reported separately from the CB-SEM evidence base.
  - Must be "NA" (not empty string) if missing

### pls_variant
- **Type**: Categorical/Text
- **Description**: Which PLS variant was used (if applicable)
- **Valid Values**: "PLS", "PLSc", "consistent PLS", "NA", or empty string
- **Examples**: "PLS", "PLSc"
- **Notes**: Only relevant if `pls_sem_used` = "TRUE". PLS-ULMC combinations are **inappropriate** for this review's CB-SEM focus but are **flagged, not omitted**. Must be "NA" (not empty string) if not applicable.

---

## Statistical Methods

### statistical_methods_mv
- **Type**: Text/String (semicolon-separated list)
- **Description**: All statistical methods used to address method variance
- **Format**: Semicolon-separated list of methods
- **Valid Values**: 
  - "ULMC"
  - "Harman single factor test" or "Harman one-factor test"
  - "Marker variable"
  - "Lindell & Whitney"
  - "CFA marker"
  - "correlational marker"
  - "MTMM"
  - "Hybrid"
  - Combinations separated by semicolons
- **Examples**: 
  - "ULMC; Harman single factor test"
  - "ULMC; Marker variable"
  - "ULMC; Harman single factor test; Lindell & Whitney marker variable"
- **Notes**: List ALL methods mentioned, separated by semicolons. Can be empty string if not applicable.

### statistical_method_detail
- **Type**: Text/String
- **Description**: Detailed description of how ULMC/statistical methods were implemented
- **Format**: Free text describing the method implementation
- **Valid Values**: Any text
- **Examples**: 
  - "unmeasured latent method construct (ulmc); Harman's single factor test"
  - "unmeasured latent method construct (ULMC) technique (Podsakoff et al. 2003; Richardson et al. 2009)"
- **Notes**: Can be empty string if not applicable.

---

## Method Variance Measures

### method_variance_pct
- **Type**: Numeric (percentage)
- **Description**: Percentage of variance explained by method factor from ULMC analysis
- **Format**: Numeric value (no % sign)
- **Valid Values**: Numeric (0-100), "NA" if not reported
- **Examples**: "28", "4.6", "17.2", "NA"
- **Notes**: 
  - This is the ULMC method variance %, NOT Harman's test %
  - Must be "NA" (not empty string) if not reported
  - Separate from `harman_variance_pct`

### harman_deployed
- **Type**: Boolean
- **Description**: Was Harman's single-factor test deployed (run or reported), regardless of whether a variance % was reported?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **Coding rule**: Code "TRUE" if authors report running Harman's test, a CFA/PCA unrotated single-factor solution, or equivalent (e.g., "Harman's one-factor test", "unrotated factor analysis with all items"). Code "FALSE" if Harman is only cited generically with no indication the test was performed. A reported `harman_variance_pct` implies "TRUE".
- **Notes**: 
  - Separate from `harman_variance_pct` (deployment vs. numeric result)
  - Also captured in `statistical_methods_mv` when listed (e.g., "Harman single factor test")
  - **Not yet a column** in `systematic_extraction_40_studies.csv`; add on next extraction pass
  - Must be "NA" (not empty string) if missing

### harman_variance_pct
- **Type**: Numeric (percentage)
- **Description**: Percentage of variance from Harman's single-factor test
- **Format**: Numeric value (no % sign)
- **Valid Values**: Numeric (0-100), "NA" if not reported
- **Examples**: "34", "39.97", "31", "NA"
- **Notes**: 
  - Separate from ULMC method variance %
  - Must be "NA" (not empty string) if not reported

### lindell_whitney_r2_substantive
- **Type**: Numeric (0-1)
- **Description**: R² for substantive variance from Lindell & Whitney marker variable approach
- **Format**: Numeric value between 0 and 1
- **Valid Values**: Numeric (0-1), "NA" if not reported
- **Examples**: "0.256", "NA"
- **Notes**: Must be "NA" (not empty string) if not reported

### lindell_whitney_r2_method
- **Type**: Numeric (0-1)
- **Description**: R² for method variance from Lindell & Whitney marker variable approach
- **Format**: Numeric value between 0 and 1
- **Valid Values**: Numeric (0-1), "NA" if not reported
- **Examples**: "0.516", "NA"
- **Notes**: Must be "NA" (not empty string) if not reported

### avg_factor_loading_change
- **Type**: Numeric
- **Description**: Average change in factor loadings when ULMC is added to the model
- **Format**: Numeric value (typically 0-1)
- **Valid Values**: Numeric, "NA" if not reported
- **Examples**: "0.20", "0.06", "NA"
- **Notes**: Must be "NA" (not empty string) if not reported

---

## ULMC Fit Assessment

### ulmc_improves_fit
- **Type**: Boolean
- **Description**: Did adding ULMC improve model fit?
- **Valid Values**: "TRUE", "FALSE", "NA"
- **Notes**: 
  - "TRUE" = fit improved
  - "FALSE" = no improvement or worse fit
  - "NA" = not determined or not reported
  - Must be "NA" (not empty string) if missing

### ulmc_in_final
- **Type**: Boolean
- **Description**: Was ULMC included in the final analysis/model?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **Notes**: 
  - Most studies exclude ULMC from final model even if it improved fit
  - Must be "NA" (not empty string) if missing

### author_fit_claims
- **Type**: Text/String
- **Description**: Exact text or summary of authors' claims about ULMC model fit
- **Format**: Free text
- **Valid Values**: Any text
- **Examples**: 
  - "∆χ2/df = 2.75 < 3.84"
  - "Trait/method-R model not significantly different from trait/method model"
  - "TLI 0.87 (trait/method) vs 0.90 (five-factor) - no improvement"
- **Notes**: Can be empty string if not applicable.

---

## Procedural Remedies

**Source-diversity distinction** (Podsakoff et al., 2003; Williams et al., 2010): Scholars often claim "multisource data" when they mean distinct sources, not true multisource. Code source-related remedies into **three mutually informative categories** below — do not use the legacy blanket term `"multisource data"`.

| Category | Field | Meaning |
|----------|-------|---------|
| **True multisource (strict)** | `multisource_same_construct` | Self **and** other informant(s) rate the **same construct of interest** (e.g., 360° feedback on leadership, self- and supervisor-rated OCB on the same scale) |
| **Different sources IV/DV** | `different_sources_iv_dv` | Predictor and criterion from **different informants** / different constructs (Podsakoff 2003 procedural remedy for CMV) |
| **Distinct sources (other)** | `distinct_sources_other` | Other multi-source claims that are **not** strict multisource: archival + survey, multi-wave, multi-level nesting, multistage collection, generic "multisource" without same-construct or IV/DV separation |

**Common mislabeling**: "Multisource" in an abstract often means leader + subordinate data on **different** variables, or multilevel/multi-wave design — code `different_sources_iv_dv` or `distinct_sources_other`, not `multisource_same_construct`. Reserve `multisource_same_construct` for explicit self/other ratings of the **same** construct.

### procedural_remedies_used
- **Type**: Boolean
- **Description**: Were any procedural remedies reported/used?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **CRITICAL VALIDATION RULE**: 
  - If `procedural_remedies_list` contains anything other than "none", "none reported", or empty string, then `procedural_remedies_used` MUST be "TRUE"
  - If `procedural_remedies_list` is "none" or empty, then `procedural_remedies_used` MUST be "FALSE"
- **Notes**: Must be "NA" (not empty string) if missing. Check `notes` field for mentions of procedural remedies.

### multisource_same_construct
- **Type**: Boolean
- **Description**: True multisource (strict): at least two different sources (self **and** other) on the **same construct of interest**
- **Valid Values**: "TRUE", "FALSE"
- **Coding rule**: Code "TRUE" when authors report self- and other-ratings (peer, supervisor, subordinate, coworker) of the **same** construct/scale, 360°/multirater feedback on one construct, or MTMM with same-trait across informants. Code "FALSE" when "multisource" only means different variables from different informants, multi-wave, multi-level, or archival + survey.
- **Examples**: "TRUE" — self- and supervisor-rated organizational citizenship on the same scale; 360° leadership feedback. "FALSE" — leader-rated climate and employee-rated satisfaction (different constructs → `different_sources_iv_dv`).

### different_sources_iv_dv
- **Type**: Boolean
- **Description**: Predictor and criterion collected from different informants (Podsakoff et al., 2003 source-separation remedy)
- **Valid Values**: "TRUE", "FALSE"
- **Coding rule**: Code "TRUE" when IV and DV (or predictor/criterion) come from different sources — e.g., supervisor-rated X and employee-rated Y, matched dyads with informant separation across variables. Not same-construct multisource.
- **Examples**: "TRUE" — supervisor-rated abusive supervision, subordinate-rated deviance; leader UPB predicting team climate from separate leader/member reports.

### distinct_sources_other
- **Type**: Boolean
- **Description**: Distinct sources that scholars may label "multisource" but are **not** strict same-construct multisource or IV/DV source separation
- **Valid Values**: "TRUE", "FALSE"
- **Coding rule**: Code "TRUE" for archival + survey, secondary/administrative data, multi-wave or multistage collection touted as source diversity, multi-level nested "multisource" designs, or generic "multisource" claims without evidence of same-construct or IV/DV separation. May co-occur with `temporal separation` when waves are the primary remedy.
- **Examples**: "TRUE" — multilevel multisource employee-in-organization data; time-lagged multisource study with leader/member reports on different constructs; generic "we used multisource data" in methods.

### procedural_remedies_list
- **Type**: Text/String (semicolon-separated list)
- **Description**: List of procedural remedies used
- **Format**: Semicolon-separated list of remedy types
- **Valid Values**: 
  - If no remedies: "none"
  - If remedies used: List separated by semicolons
- **Standard Terms** (use these consistently):
  - **Source diversity** (use instead of legacy `"multisource data"` or `"source separation"`):
    - `multisource_same_construct`
    - `different_sources_iv_dv`
    - `distinct_sources_other`
  - **Other remedies**:
    - "anonymity"
    - "temporal separation" (specify details in parentheses when helpful: "temporal separation (T1 T2)", etc.)
    - "separation between measures"
    - "methodological separation"
    - "confidentiality"
    - "item pretesting"
    - "counterbalancing"
    - "cover story"
    - "objective measures"
    - "attention checks"
    - "fact-based unambiguous questions"
    - "on-the-spot questionnaire collection"
    - "procedural remedies cited" (generic mention only)
- **Examples**: 
  - "anonymity; temporal separation; different_sources_iv_dv"
  - "anonymity; multisource_same_construct; item pretesting"
  - "anonymity; temporal separation; distinct_sources_other"
  - "none"
- **CRITICAL RULE**: 
  - If any standardized term appears (including the three source categories), `procedural_remedies_used` MUST be "TRUE"
  - When `multisource_same_construct`, `different_sources_iv_dv`, or `distinct_sources_other` is "TRUE", the matching term MUST appear in this list
  - Always check `notes` field for mentions of procedural remedies that might be missing
- **Notes**: Can be empty string if not applicable, but "none" is preferred for clarity. **Do not** use `"multisource data"` — map to the appropriate category term above.

---

## Richardson et al. (2009) Citation

### richardson_2009_cited
- **Type**: Boolean
- **Description**: Was Richardson et al. (2009) cited anywhere in the paper?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **Notes**: 
  - Check both references AND text
  - Must be "NA" (not empty string) if missing

### richardson_citation_context
- **Type**: Categorical
- **Description**: How was Richardson cited?
- **Valid Values**: "supportive", "critical", "neutral", "misuse", or empty string
- **Notes**: 
  - "supportive" = cited as supporting ULMC use
  - "critical" = cited acknowledging critique
  - "neutral" = cited without taking position
  - "misuse" = cited incorrectly or out of context
  - Must be "NA" (not empty string) if not applicable

### richardson_critique_acknowledged
- **Type**: Boolean
- **Description**: Did authors acknowledge Richardson's critique of ULMC?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **Notes**: 
  - Most studies do NOT acknowledge the critique
  - Must be "NA" (not empty string) if missing

### richardson_citation_text
- **Type**: Text/String
- **Description**: Exact text where Richardson is cited (for verification)
- **Format**: Free text (quote or paraphrase)
- **Valid Values**: Any text
- **Examples**: 
  - "Following Podsakoff et al. (2003) suggestion and Richardson et al. (2009) procedure"
  - "Richardson et al. (2009) cited in references"
- **Notes**: Can be empty string if not applicable.

---

## Three-Step ULMC Approach

**Reference procedure** (Williams & McGonagle, 2016):

| Step | Purpose | Canonical field(s) |
|------|---------|-------------------|
| **Step 1** | **CMV presence** — nested Δχ² comparing trait-only vs trait+ULMC models | `step1_presence_delta_chisq_reported`, `step1_presence_delta_chisq`, `step1_presence_pvalue`, `step1_cmv_indicated` |
| **Step 2** | **Substantive bias** — trait/method-R model (substantive correlations fixed to baseline); compare to trait/method | `step2_method_r_model_reported`, `step2_method_r_bias_test_reported`, `step2_bias_indicated` |
| **Step 3** | **Contamination reporting** — indicator- and/or construct-level method variance/decomposition, **even when Step 2 shows no bias** | `step3_contamination_reported`, `step3_indicator_level_mv_reported`, `step3_construct_level_mv_reported`, `method_variance_reported_despite_no_bias` |

**Legacy CSV aliases** (retained for backward compatibility; map to Step 1–3 semantics above):
- `step1_baseline_reported` → Step 1 presence Δχ² reported (not merely baseline fit indices)
- `step2_ulmc_reported` → Step 2 Method-R / bias test reported (not merely trait/method fit)
- `step3_chisq_diff_reported` → **deprecated misnomer**; use `step3_contamination_reported` for Step 3

### three_step_approach_used
- **Type**: Boolean
- **Description**: Did authors use or claim the Williams & McGonagle (2016) three-step ULMC procedure (trait-only → trait/method → trait/method-R with contamination reporting)?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **Notes**: Must be "NA" (not empty string) if missing

### step1_presence_delta_chisq_reported
- **Type**: Boolean
- **Description**: **Step 1 (presence)** — Was the nested χ² test comparing trait-only vs trait+ULMC (or equivalent CMV-presence test) reported?
- **Valid Values**: "TRUE", "FALSE"
- **Alias**: `step1_baseline_reported` (legacy column name)
- **Notes**: Code "TRUE" when nested Δχ² (or equivalent nested model comparison for CMV presence) is reported — **not** when only standalone CFI/RMSEA/SRMR are listed without the trait-only vs trait+ULMC comparison. Fit indices alone are **not** extracted (see Deprecated Fields).

### step1_presence_delta_chisq
- **Type**: Numeric
- **Description**: **Step 1 (presence)** — Reported nested Δχ² value from trait-only vs trait+ULMC comparison (CMV presence test)
- **Format**: Numeric (typically ≥ 0) or "NA"
- **Valid Values**: Numeric or "NA"
- **Examples**: "12.45", "87.3", "NA"
- **Notes**: Record the Δχ² (or equivalent nested χ² difference) authors report for the **presence** test. If authors report only χ² values for each model, compute Δχ² only when df difference is clear; otherwise "NA". Distinct from Step 2 Method-R nested tests.

### step1_presence_pvalue
- **Type**: Numeric
- **Description**: **Step 1 (presence)** — p-value for the nested CMV presence test (trait-only vs trait+ULMC)
- **Format**: Numeric (0–1) or "NA"
- **Valid Values**: Numeric or "NA"
- **Examples**: "0.001", "0.042", "NA"
- **Notes**: Significant p-value (typically p < .05) supports `step1_cmv_indicated` = "TRUE" when authors interpret accordingly. Code "NA" when not reported.

### step1_cmv_indicated
- **Type**: Boolean
- **Description**: **Step 1 outcome** — Did the nested presence test indicate CMV is present (significant improvement when ULMC added)?
- **Valid Values**: "TRUE", "FALSE", "NA"
- **Notes**: "NA" when Step 1 not reported or test non-significant and authors do not interpret as present/absent

### step2_method_r_model_reported
- **Type**: Boolean
- **Description**: **Step 2** — Was the trait/method-R model reported (substantive factor correlations constrained to trait-only baseline)?
- **Valid Values**: "TRUE", "FALSE"
- **Notes**: Also called "Method-R" or "method R" in some papers

### step2_method_r_bias_test_reported
- **Type**: Boolean
- **Description**: **Step 2 (bias test)** — Was trait/method-R compared to trait/method (nested Δχ² or equivalent) to test substantive bias?
- **Valid Values**: "TRUE", "FALSE"
- **Alias**: `step2_ulmc_reported` when used for Step 2 reporting (legacy)
- **Notes**: Non-significant trait/method-R vs trait/method → no substantive bias indicated

### step2_bias_indicated
- **Type**: Boolean
- **Description**: **Step 2 outcome** — Did the Method-R comparison indicate substantive bias (significant difference from trait/method)?
- **Valid Values**: "TRUE", "FALSE", "NA"

### step3_contamination_reported
- **Type**: Boolean
- **Description**: **Step 3** — Did authors report indicator- and/or construct-level method variance, loadings on the method factor, or other contamination/decomposition results?
- **Valid Values**: "TRUE", "FALSE"
- **Notes**: Step 3 applies **even when Step 2 shows no bias** — contamination can exist without biasing substantive estimates

### step3_indicator_level_mv_reported
- **Type**: Boolean
- **Description**: **Step 3 detail** — Indicator-level method variance, method-factor loadings per item, or item-level decomposition reported
- **Valid Values**: "TRUE", "FALSE"

### step3_construct_level_mv_reported
- **Type**: Boolean
- **Description**: **Step 3 detail** — Construct-level method variance percentages or construct-level decomposition reported
- **Valid Values**: "TRUE", "FALSE"
- **Notes**: Often overlaps with `method_variance_pct` when a single overall % is given; code both when applicable

### method_variance_reported_despite_no_bias
- **Type**: Boolean
- **Description**: Authors report method variance/contamination (Step 3) **despite** Step 2 indicating no substantive bias (non-significant trait/method-R vs trait/method)
- **Valid Values**: "TRUE", "FALSE", "NA"
- **Coding rule**: Code "TRUE" when Step 2 shows no bias (or is not significant) AND authors still report MV %, indicator loadings, or construct-level contamination. Captures proper Step 3 practice per Williams & McGonagle (2016).

### three_step_complete
- **Type**: Boolean
- **Description**: Were all three steps appropriately reported per the reference procedure?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "FALSE"
- **CRITICAL VALIDATION RULE**: 
  - If `three_step_complete` = "TRUE", then ALL of the following MUST be "TRUE":
    - `step1_presence_delta_chisq_reported` (or legacy `step1_baseline_reported`)
    - `step2_method_r_bias_test_reported` (or legacy `step2_ulmc_reported` when Step 2 bias test)
    - `step3_contamination_reported` (not legacy `step3_chisq_diff_reported` alone)
- **Notes**: Step 3 completeness does **not** require Step 2 to indicate bias

### step3_chisq_diff_reported (legacy — deprecated)
- **Type**: Boolean
- **Description**: **Deprecated.** Previously mislabeled as "Step 3 chi-square difference." Do **not** use for Step 3 compliance. Map to `step3_contamination_reported` on re-coding. Retained only for existing CSV rows.

---

## Sample Characteristics

### sample_n
- **Type**: Numeric/Text
- **Description**: Sample size
- **Format**: Numeric value or "NA"
- **Valid Values**: Numeric or "NA"
- **Examples**: "310", "303", "366", "NA"
- **Notes**: 
  - For multiple studies, specify: "Study 1: 161; Study 2: 205" or use total
  - Must be "NA" (not empty string) if not reported

### num_constructs
- **Type**: Numeric
- **Description**: Number of **latent constructs in the tested (structural) model** — i.e., substantive factors included in the ULMC CFA/SEM the authors fit (not control covariates unless modeled as latent factors in the same analysis)
- **Format**: Integer or "NA"
- **Valid Values**: Integer ≥ 2 or "NA"
- **Examples**: "5", "9", "NA"
- **Coding guidance**:
  - Count constructs in the **measurement + structural model** used for ULMC assessment (same model reported in CFA/SEM tables)
  - Include substantive latent variables only; exclude the ULMC/method factor itself unless the paper explicitly counts it among modeled constructs
  - Do **not** count manifest controls, single-item proxies, or second-order factors twice
- **Notes**: Must be "NA" (not empty string) if not reported or not inferable from methods/tables

### num_indicators
- **Type**: Numeric
- **Description**: **Total indicators/items in the measurement model** — sum of all scale items loading on substantive constructs in the ULMC CFA (all scales combined)
- **Format**: Integer or "NA"
- **Valid Values**: Integer ≥ 3 or "NA"
- **Examples**: "37", "16", "NA"
- **Coding guidance**:
  - Prefer the authors' stated total (e.g., "37 items measuring nine constructs")
  - If not stated, sum items across constructs from the measurement model table
  - Count **observed indicators** only (not error terms or method-factor loadings unless authors report a combined item count)
- **Notes**: Must be "NA" (not empty string) if not reported or not inferable

### complexity_ratio
- **Type**: Numeric
- **Description**: Model complexity ratio: `num_indicators / num_constructs` (average indicators per construct; alias: items per construct)
- **Format**: Numeric (typically 1–2 decimal places) or "NA"
- **Valid Values**: Numeric > 0 or "NA"
- **Examples**: "4.11", "3.2", "NA"
- **Notes**:
  - Compute when both `num_constructs` and `num_indicators` are known; may be recorded directly if authors report it
  - Must be "NA" (not empty string) if either parent field is missing

### underpowered_heuristic (derived — dashboard/synthesis only)
- **Type**: Boolean (computed; not a CSV extraction column)
- **Description**: **Coding guidance flag**, not a statistical power test — `TRUE` when any conventional ULMC/CFA complexity risk factor is met among populated fields
- **Rules** (any one triggers `TRUE`):
  1. `num_indicators` < 15 (small total measurement model)
  2. `complexity_ratio` < 3 (fewer than ~3 indicators per construct on average)
  3. `num_constructs` > 10 (high structural complexity)
- **`FALSE`**: At least one criterion evaluable and none triggered
- **`NA`**: Insufficient data to evaluate any criterion
- **Rationale**: Richardson et al. (2009) and standard CFA practice emphasize that ULMC tests lose sensitivity as models grow and item counts shrink relative to parameters; this flag supports descriptive synthesis of likely underpowered tests (see `AUDIT_RESULTS_METHODOLOGY.md` §Model complexity)

---

## Author Conclusions

### author_conclusion_mv
- **Type**: Text/String
- **Description**: Authors' **bottom-line conclusion** about method variance/CMV (outcome statement)
- **Format**: Free text (exact quote or summary)
- **Valid Values**: Any text
- **Common Values**:
  - "not a concern"
  - "not a problem"
  - "not a serious threat"
  - "unlikely"
  - "low probability"
  - "does not pose a significant threat"
- **Examples**: 
  - "not a concern - insufficient evidence"
  - "common method variance is not responsible for the results"
- **Relationship to MV inference criteria fields**:
  - `author_conclusion_mv` = **what** authors concluded (outcome).
  - `mv_inference_criteria_*` and `mv_inference_rationale_text` = **why** they reached that conclusion (evidence/criteria cited).
  - A study may have a conclusion without articulated criteria (`mv_inference_criteria_used` = "FALSE"); conversely, criteria may be stated without an explicit all-clear (`mv_inferred_not_problem` = "FALSE").
- **Notes**: Can be empty string if not applicable.

---

## MV Inference Criteria (Author-Stated)

Fields capturing **criteria authors cite** when inferring whether common method variance is or is not a problem in their data — distinct from which **statistical tests** they ran (`statistical_methods_mv`).

### mv_inference_criteria_used
- **Type**: Boolean
- **Description**: Did authors articulate **explicit criteria or reasons** for judging MV as present/absent or threatening/non-threatening?
- **Valid Values**: "TRUE", "FALSE"
- **Coding rule**: Code "TRUE" if authors state a rule, threshold, test result, design feature, or procedural remedy as justification (not merely "CMV may exist" in passing). Code "FALSE" if they only acknowledge CMV as a generic limitation without inferential criteria.
- **Default**: "NA" if not determined

### mv_inference_criteria_list
- **Type**: Text/String (semicolon-separated list)
- **Description**: Standardized terms for criteria authors cite when inferring MV status
- **Valid Values** (use these terms where possible; combine with `; `):
  - "ULMC method variance below threshold"
  - "Harman single factor below 50%"
  - "no improvement in model fit with ULMC"
  - "marker variable nonsignificant"
  - "procedural remedies employed"
  - "longitudinal/temporal separation"
  - "multisource data"
  - "CMV not a concern (unspecified)"
  - "fit indices acceptable without ULMC"
  - "factor loadings unchanged"
  - "discriminant validity supported"
  - "none" — authors discuss CMV but cite no inferential criteria
- **Examples**:
  - "Harman single factor below 50%; procedural remedies employed"
  - "no improvement in model fit with ULMC; factor loadings unchanged"
  - "none"
- **Notes**: Use `mv_inference_criteria_detail` for criteria that do not map to the list. Empty string if not applicable.

### mv_inference_criteria_detail
- **Type**: Text/String
- **Description**: Free-text catch-all for author-stated criteria not captured in `mv_inference_criteria_list`
- **Format**: Free text (brief summary or quote fragment)
- **Examples**:
  - "CFA one-factor model showed poor fit, interpreted as evidence against CMV"
  - "correlations below 0.90 rule of thumb"
- **Notes**: Can be empty string if all criteria are in the standardized list.

### mv_inferred_not_problem
- **Type**: Boolean
- **Description**: Do authors conclude that CMV/MV is **NOT** a meaningful threat to their findings?
- **Valid Values**: "TRUE", "FALSE"
- **Coding rule**: Code "TRUE" when authors state CMV/MV is not a concern, not a problem, unlikely, minimal, does not affect results, etc. Code "FALSE" when they treat CMV as a substantive threat, leave the threat unresolved, or conclude MV may bias results.
- **Relationship**: Often aligns with `author_conclusion_mv` phrasing but is structured for synthesis counts. When both are filled, they should be consistent.
- **Default**: "NA" if not determined

### mv_inference_rationale_text
- **Type**: Text/String
- **Description**: Verbatim or near-verbatim quote where authors state criteria and/or conclude about MV
- **Format**: Direct quote from limitations, robustness, or methods section (≤ ~500 words)
- **Examples**:
  - "The one-factor model accounted for only 27 percent of the variance, which is much lower than the acceptable cutoff of 50 percent, suggesting that common method bias is not a serious problem."
- **Notes**: Prefer the most complete single passage. Can be empty string if not extracted.

---

## Author Affiliation — Business School

Fields capturing whether **publishing authors** are affiliated with a business school or equivalent management faculty — to characterize outlets of interest to the business/management community. Code from the **title page, author byline, or author footnote affiliations** (not journal name alone).

### business_school_coding_rule

**Code `authors_business_school` = "TRUE"** when at least one author lists an affiliation matching any of:

- "School of Business" / "Business School" / "College of Business"
- "School of Business Administration" / "School of Business and Economics"
- "Faculty of Management" / "School of Management"
- "Department of Management" within a university (not standalone consultancy)
- Named business schools (e.g., "Fox School of Business", "Stern School of Business", "Kelley School of Business")
- Equivalent non-English labels when clearly a business/management faculty unit

**Code "FALSE"** when all listed author affiliations are:

- Psychology department/school only (e.g., "Department of Psychology", "Institute of Psychology")
- Medical school / nursing / public health only
- Education college only (unless joint appointment with business school is stated)
- Engineering, computer science, or other non-business units only

**Joint appointments**: If an author lists both a psychology (or other) unit **and** a business school, code "TRUE" and record the business-school line in `author_affiliation_detail`.

**Ambiguous cases**: Use "NA" when affiliations are not reported or cannot be determined from available text. Do not infer from journal brand alone (e.g., *Journal of Business Ethics* does not imply business-school authors).

### authors_business_school
- **Type**: Boolean
- **Description**: Is at least one author affiliated with a business school, school of management, college of business, or equivalent management faculty?
- **Valid Values**: "TRUE", "FALSE"
- **Default**: "NA" if not determined
- **Coding rule**: See `business_school_coding_rule` above.
- **Examples**:
  - "TRUE" — "aBusiness School, Harbin Institute of Technology" on title page
  - "FALSE" — all authors at "Department of Psychology, University of X"
  - "NA" — no affiliations on title page and not found in PDF text

### author_affiliation_detail
- **Type**: Text/String
- **Description**: Verbatim or lightly normalized affiliation line(s) supporting the business-school coding
- **Format**: Single affiliation string, or semicolon-separated if multiple lead authors have distinct business-school units
- **Valid Values**: Any text; empty string if `authors_business_school` = "FALSE" or not applicable
- **Examples**:
  - "Fox School of Business, Temple University"
  - "School of Business Administration, Shanxi University of Finance and Economics"
  - "Business School, Beijing Normal University; School of Economics and Management, Tsinghua University"
- **Notes**: Optional but recommended when `authors_business_school` = "TRUE". Pipeline regex may pre-fill hints — verify manually.

---

## Study Characteristics

**Priority**: Code **content domain** and **model complexity** (constructs, indicators, ratio) before optional contextual fields. Industry/sector and response-rate fields are **deprecated** (retained in legacy CSV columns only).

### content_domain
- **Type**: Text/String
- **Description**: Substantive **content domain** or topic of the study (what constructs/phenomena are studied — not industry classification)
- **Format**: Free text; use consistent phrasing where possible
- **Valid Values**: Any text
- **Examples**: "Authentic leadership and well-being", "Employee turnover intentions", "Safety climate and accidents", "Workplace incivility"
- **Coding guidance**: Summarize the primary substantive focus from title, hypotheses, or construct list. Prefer phenomenon/topic over employer type.
- **Notes**: **Primary** contextual field for synthesis subgrouping. Can be empty string if not determined.

### construct_names
- **Type**: Text/String (semicolon-separated list)
- **Description**: Names of **latent constructs** in the tested ULMC CFA/SEM (substantive factors only)
- **Format**: Semicolon-separated construct labels as authors name them
- **Valid Values**: Any text
- **Examples**: "Servant leadership; LMX; Proactive behavior", "Job satisfaction; Organizational commitment; OCB"
- **Coding guidance**: List constructs included in the ULMC measurement/structural model. Exclude the ULMC/method factor unless authors count it among substantive constructs. Pairs with `num_constructs` — count should align when both are populated.
- **Notes**: Can be empty string if not reported or not inferable.

### estimator
- **Type**: Categorical
- **Description**: Statistical estimator used
- **Valid Values**: "CB-SEM", "PLS-SEM", "NA"
- **Notes**: 
  - CB-SEM = Covariance-based SEM
  - PLS-SEM = Partial Least Squares SEM
  - Must be "NA" (not empty string) if missing

### software
- **Type**: Text/String
- **Description**: Statistical software used
- **Format**: Software name and version
- **Valid Values**: Any text
- **Examples**: "Mplus Version 8", "AMOS 22.0", "Mplus 7.4"
- **Notes**: Can be empty string if not reported.

### country (deprecated)
- **Type**: Text/String
- **Description**: **Deprecated — do not code on new extraction passes.** Legacy column retained in existing CSVs only.
- **Format**: Country name(s)
- **Valid Values**: Any text (historical rows only)
- **Examples**: "United States", "China", "Multiple countries (12 samples)"
- **Notes**: Removed from active protocol (2026-06-25). Geographic distribution is not a synthesis outcome.

### industry_sector (deprecated)
- **Type**: Text/String
- **Description**: **Deprecated — do not code on new extraction passes.** Legacy column retained in existing CSVs only.
- **Replacement**: Use `content_domain` for substantive topic; note organizational setting in `content_domain` or `notes` if relevant.
- **Notes**: Historical rows may contain values (e.g., "Higher education (university faculty)"). Do not require for new studies.

### study_design
- **Type**: Text/String
- **Description**: Study design
- **Valid Values**: 
  - "Cross-sectional"
  - "Longitudinal (two-wave)"
  - "Longitudinal (three-wave)"
  - "Longitudinal (12 months, T1-T2-T3)"
  - "Experimental"
  - "Review paper"
  - Other descriptive text
- **Examples**: 
  - "Cross-sectional"
  - "Longitudinal (two-wave)"
  - "Longitudinal (12 months, T1-T2-T3)"
- **Notes**: Can be empty string if not reported.

### data_collection_method
- **Type**: Text/String
- **Description**: How data were collected
- **Format**: Free text
- **Valid Values**: Any text
- **Examples**: "Web-based survey", "Survey", "Online survey", "On-site questionnaire"
- **Notes**: Can be empty string if not reported.

### response_rate (deprecated)
- **Type**: Text/String (percentage)
- **Description**: **Deprecated — do not code on new extraction passes.** Part of removed Quality Indicators block (response rate, missing data, power analysis, reliability).
- **Notes**: Legacy column retained in existing CSVs only.

---

## Deprecated Fields (Do Not Extract)

The following were removed from the active extraction schema (2026-06-25). **Do not add to new rows.** Historical CSV columns and pipeline output columns may still exist for backward compatibility.

| Field / group | Reason |
|---------------|--------|
| `industry_sector` | De-prioritized; use `content_domain` |
| `response_rate` | Quality Indicators section removed |
| Power analysis reporting | Quality Indicators section removed |
| Missing data handling | Quality Indicators section removed |
| Reliability coefficients (Cronbach's α) | Quality Indicators section removed |
| Model fit indices (CFI, RMSEA, SRMR, TLI, etc.) | Not required; Step 1 uses nested Δχ²/p-value for CMV **presence**, not fit-index extraction |
| `step1_baseline_cfi`, `step1_baseline_rmsea`, `step1_baseline_srmr`, `step2_ulmc_cfi`, etc. | Pipeline legacy columns; deprecated in favor of `step1_presence_delta_chisq` / `step1_presence_pvalue` |

`author_fit_claims` and `ulmc_improves_fit` remain active — they capture **author-stated claims** about fit, not numeric fit-index extraction.

**Synthesis (out of scope)**: Do not plan histograms, distributions, or completeness summaries of CFI/RMSEA/SRMR/χ² across studies; numeric fit-index fields remain deprecated.

---

## Supplement / Incomplete Main Text

### details_in_supplement
- **Type**: Boolean
- **Description**: Authors refer to online supplement, appendix, or supplementary materials for methods/results relevant to coding
- **Valid Values**: `TRUE`, `FALSE`, `NA`
- **Coding rule**: Code `TRUE` when main text points to supplementary materials for tables, fit indices, Harman results, construct counts, etc. (e.g., "see online supplement", "Appendix S1", "Table S1", "online appendix", "supplementary materials")
- **Pipeline**: `enhanced_extraction_pipeline.R` regex-detects supplement references; verify manually

### extraction_incomplete_main_text
- **Type**: Boolean
- **Description**: Required ULMC/MV coding fields (method variance %, Harman %, construct/indicator counts, three-step fit) are **not fully reported in the main PDF** and coder must consult supplement or cannot code the field
- **Valid Values**: `TRUE`, `FALSE`, `NA`
- **Relationship to `details_in_supplement`**: If `extraction_incomplete_main_text` = `TRUE`, then `details_in_supplement` should usually be `TRUE` (soft validation). Can be `TRUE` without supplement when information is simply not reported anywhere.

### supplement_notes
- **Type**: Text/String
- **Description**: What coding-relevant information is missing and where authors refer readers (section, appendix ID, URL)
- **Valid Values**: Any text or empty string
- **Examples**: "Harman % in Appendix S2 only", "CFA fit table in online supplement; main text reports conclusion only"

---

## Verification

### verification_table
- **Type**: Text/String
- **Description**: Reference to verification table file (if created)
- **Format**: Filename or "NA"
- **Valid Values**: Any text
- **Examples**: "study3_verification_table.csv", "NA"
- **Notes**: Can be empty string if not applicable.

### notes
- **Type**: Text/String
- **Description**: Additional notes, corrections, or important details
- **Format**: Free text
- **Valid Values**: Any text
- **Notes**: Use this field to document:
  - Corrections made to original data
  - Important details not captured in other fields
  - Inconsistencies found
  - Multiple studies in one paper
  - Procedural remedies mentioned but not in structured field
  - Can be empty string if no notes needed.

---

## Validation Rules

### Cross-Field Dependencies

1. **Procedural Remedies Logic**:
   - If `procedural_remedies_list` != "none" AND != "none reported" AND != "", then `procedural_remedies_used` MUST be "TRUE"
   - If `procedural_remedies_list` == "none" OR empty, then `procedural_remedies_used` MUST be "FALSE"
   - If `multisource_same_construct`, `different_sources_iv_dv`, or `distinct_sources_other` is "TRUE", the matching standardized term MUST appear in `procedural_remedies_list`
   - Do not use legacy term `"multisource data"` — map to one of the three source category fields/terms

2. **Three-Step Complete Logic**:
   - If `three_step_complete` = "TRUE", then ALL of the following MUST be "TRUE":
     - `step1_presence_delta_chisq_reported` (or legacy `step1_baseline_reported`)
     - `step2_method_r_bias_test_reported` (or legacy `step2_ulmc_reported` when coding Step 2)
     - `step3_contamination_reported`
   - `method_variance_reported_despite_no_bias` = "TRUE" requires Step 3 reporting and Step 2 indicating no bias (or non-significant Method-R test)

3. **PLS Studies**:
   - If `pls_sem_used` = "TRUE", then `not_pls` should be "FALSE" (these studies are **excluded from CB-SEM synthesis** but **retained** in extraction for PLS prevalence/misuse reporting)
   - If `pls_sem_used` = "TRUE", `estimator` should be "PLS-SEM" when known

4. **MV Inference Criteria Logic**:
   - If `mv_inference_criteria_list` contains any term other than "none" (non-empty), then `mv_inference_criteria_used` MUST be "TRUE"
   - If `mv_inference_criteria_list` == "none", then `mv_inference_criteria_used` MUST be "FALSE"
   - If `mv_inferred_not_problem` = "TRUE", `author_conclusion_mv` should not contradict (e.g., should not say "major concern")

5. **Business School Affiliation Logic**:
   - If `author_affiliation_detail` contains a business-school unit name, then `authors_business_school` SHOULD be "TRUE"
   - If `authors_business_school` = "TRUE", `author_affiliation_detail` is recommended (soft check) but may be empty if affiliation text was not extractable

6. **Publisher Outlet**:
   - `publisher_outlet` MUST be one of: MDPI, Frontiers, Elsevier, Springer, Wiley, SAGE, Taylor & Francis, Emerald, APA/PSYC, Other, NA
   - When DOI or journal supports inference, prefer auto-inferred value; manual coding overrides pipeline

7. **Supplement / Incomplete Main Text Logic** (soft):
   - If `extraction_incomplete_main_text` = "TRUE", `details_in_supplement` SHOULD be "TRUE" unless information is absent from both main text and supplement
   - If `supplement_notes` is non-empty, `details_in_supplement` SHOULD be "TRUE"

8. **Missing Values**:
   - **Structured fields** (Boolean, Numeric, Categorical) MUST use "NA" (not empty string) for missing values
   - **Text fields** can use empty string for missing values

### Structured Fields (Must Use "NA" for Missing)

**Boolean Fields**:
- `management_domain`
- `empirical_ulmc`
- `not_pls`
- `pls_sem_used`
- `ulmc_improves_fit`
- `ulmc_in_final`
- `harman_deployed`
- `procedural_remedies_used`
- `multisource_same_construct`
- `different_sources_iv_dv`
- `distinct_sources_other`
- `richardson_2009_cited`
- `richardson_critique_acknowledged`
- `three_step_approach_used`
- `step1_presence_delta_chisq_reported`
- `step1_cmv_indicated`
- `step2_method_r_model_reported`
- `step2_method_r_bias_test_reported`
- `step2_bias_indicated`
- `step3_contamination_reported`
- `step3_indicator_level_mv_reported`
- `step3_construct_level_mv_reported`
- `method_variance_reported_despite_no_bias`
- `step1_baseline_reported`
- `step2_ulmc_reported`
- `step3_chisq_diff_reported`
- `three_step_complete`
- `predatory_journal_flag`
- `mv_inference_criteria_used`
- `mv_inferred_not_problem`
- `authors_business_school`
- `details_in_supplement`
- `extraction_incomplete_main_text`

**Numeric Fields**:
- `year`
- `method_variance_pct`
- `harman_variance_pct`
- `lindell_whitney_r2_substantive`
- `lindell_whitney_r2_method`
- `avg_factor_loading_change`
- `sample_n`
- `num_constructs`
- `num_indicators`
- `complexity_ratio`
- `step1_presence_delta_chisq`
- `step1_presence_pvalue`

**Categorical Fields**:
- `pls_variant`
- `richardson_citation_context`
- `estimator`
- `publisher_outlet`

### Text Fields (Can Use Empty String)

- `study_title`
- `authors`
- `journal`
- `doi`
- `statistical_methods_mv`
- `statistical_method_detail`
- `procedural_remedies_list`
- `richardson_citation_text`
- `author_conclusion_mv`
- `mv_inference_criteria_list`
- `mv_inference_criteria_detail`
- `mv_inference_rationale_text`
- `author_affiliation_detail`
- `author_fit_claims`
- `software`
- `country` *(deprecated)*
- `content_domain`
- `construct_names`
- `study_design`
- `data_collection_method`
- `verification_table`
- `notes`
- `publisher_outlet_detail`
- `supplement_notes`

---

## Common Issues and Notes

1. **Procedural Remedies**: Always check the `notes` field for mentions of procedural remedies that might not be in `procedural_remedies_list`. Distinguish **true multisource** (`multisource_same_construct`), **IV/DV source separation** (`different_sources_iv_dv`), and **other distinct sources** (`distinct_sources_other`) — do not code generic "multisource" as strict multisource. Common keywords: "anonymity", "temporal", "separation", "confidentiality", "pretest", "counterbalance", "360", "multirater", "multilevel", "multi-wave".

2. **Method Variance**: Distinguish between `method_variance_pct` (from ULMC) and `harman_variance_pct` (from Harman's test). These are separate measures.

3. **Three-Step Approach**: Step 1 = presence nested Δχ²/p-value (trait-only vs trait+ULMC) — **not** standalone fit indices; Step 2 = Method-R bias test; Step 3 = contamination reporting (even without bias). Many studies report fit indices without the correct nested comparisons — only mark `three_step_complete` = "TRUE" when all three steps meet codebook definitions.

4. **Richardson Citation**: Check both the references section AND the text. Many studies cite Richardson in references but don't discuss it in the text.

5. **Multiple Studies**: If a paper reports multiple studies, document this in the `notes` field and specify sample sizes for each study.

6. **Legacy Studies**: Legacy studies may have incomplete metadata (authors, journal, year). Use "Legacy Study" as author and leave other fields empty or use "NA" appropriately.

7. **Extraction feedback loop**: Pipeline pre-fill (`enhanced_extraction_pipeline.R` → `enhanced_extraction_results.csv`) is assistive; manual CSV rows are authoritative. Log overrides with `log_extraction_correction.py`; run `extraction_feedback_report.py` after batch coding. See [`EXTRACTION_FEEDBACK_LOOP.md`](EXTRACTION_FEEDBACK_LOOP.md).

---

**End of Codebook**
