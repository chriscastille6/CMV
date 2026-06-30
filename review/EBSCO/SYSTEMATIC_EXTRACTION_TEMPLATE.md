# Systematic Extraction Template
## Complete Field Extraction Checklist for Each Study

Based on `review/config.yaml` extraction schema

---

## STUDY IDENTIFICATION
- [ ] Study number/order
- [ ] Full title
- [ ] Authors
- [ ] Year
- [ ] Journal
- [ ] DOI
- [ ] APA citation

### Publisher / Outlet Family (Q2.22-Q2.22a)
*Many EBSCO articles are MDPI or Frontiers — code explicitly.*

- [ ] Q2.22: Publisher outlet family (`publisher_outlet`) — MDPI, Frontiers, Elsevier, Springer, Wiley, SAGE, Taylor & Francis, Emerald, APA/PSYC, Other, NA
- [ ] Q2.22a: Outlet detail (`publisher_outlet_detail`) — full journal name if needed
- [ ] Predatory/questionable outlet flag (`predatory_journal_flag`) — include study; flag for sensitivity analysis (auto when MDPI)
- **Auto-infer when possible**: DOI `10.3390/` → MDPI; `10.3389/` → Frontiers; journal "Frontiers in …" → Frontiers; "(MDPI)" or Sustainability / Behavioral Sciences / IJERPH / JTAER → MDPI

### Supplement / Incomplete Main Text (Q2.23-Q2.24a)
*Flag when coding-relevant details are in supplementary materials or missing from main PDF.*

- [ ] Q2.23: Authors refer to supplement/appendix for methods or results needed for coding? (`details_in_supplement`)
- [ ] Q2.24: ULMC/MV/Harman/construct fields incomplete in main PDF — must check supplement or cannot code? (`extraction_incomplete_main_text`)
- [ ] Q2.24a: What is missing / where referred? (`supplement_notes`)

### Author Affiliation — Business School (Q2.18-Q2.18a)
*Is at least one author from a business school? Check **title page / author footnotes** (not journal name alone).*

- [ ] Q2.18: At least one author at a business school / school of management / college of business? (Boolean — `authors_business_school`)
- [ ] Q2.18a: Affiliation detail (Text — `author_affiliation_detail`; semicolon-separated if multiple lead authors)

**Coding rule (summary)**: Code `TRUE` for School/College/Faculty of Business, Business School, School of Management, Department of Management in a university business context. Code `FALSE` for psychology-only, medical-only, or education-only affiliations unless a joint business-school appointment is stated. See `VARIABLE_CODEBOOK.md` (`business_school_coding_rule`).

**Distinct from Q1.1 (`management_domain`)**: Q1.1 = journal/topic domain; Q2.18 = **author institutional affiliation**.

---

## LEVEL 1 SCREENING (Q1.1-Q1.3)
- [ ] Q1.1: Management/HRM/OB/Applied Psychology domain? (Boolean)
- [ ] Q1.2: Empirical ULMC study? (Boolean)
- [ ] Q1.3: Uses PLS estimation? (Boolean — Yes = **exclude from CB-SEM synthesis**, but **still extract** PLS fields for misuse/prevalence reporting)

---

## LEVEL 2 EXTRACTION - CORE ULMC FIELDS

### Q2.1: Authors' Conclusions (Text)
- [ ] Exact text extraction regarding authors' conclusions about CMV/MV

### Q2.2: ULMC Fit Claims
- [ ] Claims about relative fit of ULMC model (Text)

### Q2.3: ULMC Fit Improvement
- [ ] Did ULMC improve model fit? (Boolean)

### Q2.4: Method Variance Percentage
- [ ] Method variance percentage reported? (Boolean)
- [ ] Method variance percentage value (Numeric)
- [ ] Harman's single-factor test deployed? (Boolean — separate from % reported)
- [ ] Harman's test variance percentage (Numeric — `harman_variance_pct`, if reported)

### Q2.5: Author Conclusion
- [ ] Author conclusion about method bias (Text: "not a concern", "minor concern", "major concern", etc.) — `author_conclusion_mv`

### MV Inference Criteria (Q2.14-Q2.17)
*What criteria did authors **cite** to infer whether MV is or is not a problem? (Distinct from which tests they ran.)*

- [ ] Q2.14: Did authors state explicit criteria for inferring MV status? (Boolean — `mv_inference_criteria_used`)
- [ ] Q2.15: Which criteria did authors cite? (Semicolon-separated standardized terms — `mv_inference_criteria_list`)
  - Standard terms: ULMC method variance below threshold; Harman single factor below 50%; no improvement in model fit with ULMC; marker variable nonsignificant; procedural remedies employed; longitudinal/temporal separation; multisource data; CMV not a concern (unspecified); fit indices acceptable without ULMC; factor loadings unchanged; discriminant validity supported; none
- [ ] Criteria detail for non-standard reasons (Text — `mv_inference_criteria_detail`)
- [ ] Q2.16: Do authors conclude MV is NOT a threat? (Boolean — `mv_inferred_not_problem`)
- [ ] Q2.17: Verbatim/near-verbatim MV inference rationale (Text — `mv_inference_rationale_text`)

### Q2.6: ULMC in Final Analysis
- [ ] Was ULMC included in final analysis? (Boolean)

---

## ENHANCED EXTRACTION FIELDS

### Procedural Remedies (Q2.7-Q2.8)
- [ ] Q2.7: Were procedural remedies used? (Boolean — `procedural_remedies_used`)
- [ ] Q2.8: Which procedural remedies? (Semicolon-separated list — `procedural_remedies_list`; use "none" if absent)
  - Standard terms: anonymity, confidentiality, temporal separation, source separation / multisource data, methodological separation, separation between measures, counterbalancing, item pretesting, cover story, objective measures, fact-based unambiguous questions, on-the-spot questionnaire collection

### Statistical Methods (Q2.9)
- [ ] Q2.9: What specific statistical methods were used for MV? (Text: ULMC, Harman's single factor, CFA marker, correlational marker, Lindell & Whitney, MTMM, hybrid, etc.)
- [ ] Q2.9a: Harman's single-factor test deployed? (Boolean — `harman_deployed`; see codebook for coding rules)
- [ ] Statistical method detail (Text)

### PLS-SEM Analysis (Q2.10)
- [ ] Q2.10: PLS-SEM variant used (if applicable) (Text: PLS, PLSc, consistent PLS, etc.) — `pls_variant`
- [ ] PLS-SEM used? (Boolean — `pls_sem_used`; **always code**; excluded from CB-SEM synthesis but retained for misuse documentation)
- [ ] Study does NOT use PLS? (Boolean — `not_pls`; inverse of PLS for Level 1)

### Richardson et al. (2009) Citation (Q2.11-Q2.13)
- [ ] Q2.11: Was Richardson et al. (2009) cited? (Boolean)
- [ ] Q2.12: How was Richardson et al. (2009) cited? (Text: supportive, critical, neutral, misuse)
- [ ] Q2.13: Did authors acknowledge Richardson's critique of ULMC? (Boolean)
- [ ] Richardson citation text (Text: exact context)

---

## THREE-STEP ULMC ANALYSIS (Williams & McGonagle 2016)

| Step | Test | Purpose |
|------|------|---------|
| **1** | Trait-only vs trait+ULMC nested Δχ² | CMV **presence** |
| **2** | Trait/method-R vs trait/method (Method-R) | Substantive **bias** (R model fixes substantive r to baseline) |
| **3** | Indicator/construct MV decomposition | **Contamination** reporting — required even if Step 2 shows no bias |

### Step 1 — CMV presence (nested Δχ²)
- [ ] Step 1 nested Δχ² reported? (`step1_presence_delta_chisq_reported`; legacy: `step1_baseline_reported`)
- [ ] Step 1 nested Δχ² value — trait-only vs trait+ULMC (`step1_presence_delta_chisq`)
- [ ] Step 1 p-value for presence nested test (`step1_presence_pvalue`)
- [ ] Step 1 indicates CMV present? (`step1_cmv_indicated`)

**Note**: Step 1 is the **CMV presence** test (nested χ²/p-value when ULMC is added). Do **not** extract standalone CFI/RMSEA/SRMR/TLI fit indices.

### Step 2 — Method-R bias test
- [ ] Trait/method-R model reported? (`step2_method_r_model_reported`)
- [ ] Trait/method-R vs trait/method comparison reported? (`step2_method_r_bias_test_reported`; legacy: `step2_ulmc_reported`)
- [ ] Method-R test indicates substantive bias? (`step2_bias_indicated`)
- [ ] Optional: Method-R Δχ² / p-value (Numeric)

### Step 3 — Contamination reporting
- [ ] Indicator or construct MV/contamination reported? (`step3_contamination_reported`)
- [ ] Indicator-level decomposition/loadings? (`step3_indicator_level_mv_reported`)
- [ ] Construct-level MV percentages? (`step3_construct_level_mv_reported`)
- [ ] MV reported despite no bias on Step 2? (`method_variance_reported_despite_no_bias`)

### Three-step compliance
- [ ] Three-step approach used/claimed? (`three_step_approach_used`)
- [ ] Three-step complete per codebook? (`three_step_complete`)
- [ ] Legacy `step3_chisq_diff_reported` — **do not use** for Step 3; deprecated misnomer

---

## MODEL COMPLEXITY & CONTENT DOMAIN

**Priority**: Content domain and model complexity over industry/sector classification.

- [ ] **`content_domain`** — Substantive topic/phenomenon (Text — e.g., leadership, turnover, safety climate)
- [ ] **`construct_names`** — Latent construct names in tested ULMC model (semicolon-separated)
- [ ] **`num_constructs`** — Latent constructs in the tested structural/measurement model (Integer; exclude ULMC method factor unless authors count it)
- [ ] **`num_indicators`** — Total items/indicators across all substantive scales in that CFA (Integer)
- [ ] **`complexity_ratio`** — `num_indicators / num_constructs` (Numeric; record or calculate; same as items per construct)

**Where to look**: Title, hypotheses, measurement model section, CFA table footnotes, "X constructs measured with Y items".

**Power heuristic (coding note, not a statistical test)**: Flag likely underpowered ULMC contexts when *any* of: indicators < 15, ratio < 3, constructs > 10 (see `VARIABLE_CODEBOOK.md` §`underpowered_heuristic`).

**Deprecated (do not code)**: `country`, `industry_sector` — use `content_domain` for substantive topic/setting; legacy CSV columns may still exist.

---

## SAMPLE CHARACTERISTICS

- [ ] Sample size (N) (Integer)
- [ ] Study design (Text: cross-sectional, longitudinal, experimental)
- [ ] Data collection method (Text: survey, interview, archival, etc.)

**Deprecated (do not code)**: Response rate, power analysis, missing-data handling, reliability coefficients — Quality Indicators section removed.

---

## ESTIMATOR & METHODOLOGY

- [ ] Estimator type (Text: CB-SEM, PLS, PLSc, Mixed, Unknown)
- [ ] Software used (Text: AMOS, Mplus, LISREL, R, etc.)
- [ ] Model variant (Text)

---

## ADDITIONAL FIELDS

- [ ] Remedy claims (Text)
- [ ] Honesty language (Text - language acknowledging limitations)
- [ ] Limitations discussed (Boolean)
- [ ] Design features (Text)
- [ ] Number of method factors (Integer)

---

## PLS FOLLOW-UP (if PLS study)

- [ ] PLS follow-up study conducted? (Boolean)
- [ ] PLS follow-up method (Text: CB-SEM, etc.)
- [ ] PLS findings confirmed? (Boolean)

---

## NOTES & VERIFICATION

- [ ] Extraction date
- [ ] Extractor name/ID
- [ ] Verification status (Text: pending, verified, needs review)
- [ ] Notes/Additional findings (Text)

---

**Usage**: Check off each field as extracted for each study. This ensures systematic, complete extraction.

