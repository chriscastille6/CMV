# Legacy ULMC Systematic Review Summary

## Overview
This document summarizes the findings from your original systematic review of ULMC usage in management literature (2012-2022).

## Original Methodology

### Search Strategy
- **Database**: Discovery Service (library database)
- **Search Terms**: 
  - "unmeasured latent method construct" OR 
  - "unmeasured latent method factor"
- **Filters**: 
  - Full text only
  - Scholarly (peer reviewed) articles
  - Published in academic journals
- **Initial Results**: 656 records
- **After Deduplication**: 315 records

### Screening Process

#### Level 1: Initial Screening (315 → 182 studies)
**Inclusion Criteria:**
- Management, HRM, organizational behavior, or applied psychology domain
- Business ethics and strategy studies also included
- Empirical studies using ULMC to test CMV as methodological explanation

**Exclusion Criteria:**
- Information systems, advertising, marketing journals
- Data simulations, theoretical papers
- ULMC used to identify substantive effects (not method effects)
- **Partial Least Squares (PLS) estimation studies** (24 studies excluded)

**Results:**
- 315 studies screened
- 219 (69.5%) in management domain
- 216 (68.6%) empirical ULMC studies
- 24 PLS studies excluded
- **182 studies passed to Level 2**

#### Level 2: Data Extraction (185 records)
**Key Extraction Fields:**
1. Exact text regarding authors' conclusions
2. Claims about relative fit of ULMC model
3. Did ULMC improve model fit?
4. Percentage of variance explained by ULMC
5. Author conclusion about method bias
6. Was ULMC included in final analysis?

## Key Findings

### Sample Characteristics
- **Total Included Studies**: 182 (after both screening levels)
- **Unique Journals**: 69
- **Average Sample Size**: ~300 (range: 123-1,795)

### ULMC Performance Patterns

#### Model Fit
- **73 studies** (40%) reported that ULMC improved model fit
- In most cases, inclusion of ULMC resulted in improvement in model fit

#### Method Variance Detection
- **Mean Method Variance**: 14.3%
- **Median Method Variance**: 13.7%
- **Range**: Trivial (~1%) to substantial (>50%)
- **Typical Pattern**: Small amounts of method variance detected

#### Author Conclusions
- **Common Conclusion**: "Method variance not sufficient to cause method bias"
- Authors often noted CMV detected but negligible
- Significance of substantive effects typically unchanged

#### ULMC in Final Analysis
- **0 studies** included ULMC in final reported model
- Authors universally excluded ULMC after testing

### Critical Issues Identified

1. **Power Concerns**
   - Many scholars using ULMC under small sample conditions
   - May lack power to reliably detect method effects when present
   - Risk of Type II errors (failing to detect existing method effects)

2. **Reporting Practices**
   - Tendency to dismiss method variance as "negligible"
   - Inconsistent reporting of model comparison tests
   - Variable transparency about convergence/identification issues

3. **Theoretical Issues**
   - ULMC assumes unidimensional method variance
   - Reality: Method variance typically multifaceted/multidimensional
   - May produce biased results when assumption violated

4. **Bias Risk**
   - If method variance routinely ignored, less accurate estimates may permeate literature
   - Small effects may be inflated without correction
   - Large effects may be over-corrected by ULMC

## Exemplars of Reporting

### Good Example (Ng et al., 2021)
**What They Reported:**
- Specific percentage of variance (7% in Study 1, 2-3% in Study 2)
- Factor loading comparisons with/without ULMC
- Clear conclusion about method bias
- Transparent about sample sizes (900 and 470)

**Quote**: "Our latent factors explained 78% of variance, whereas the latent common method factor explained only 7% of variance. These results suggest that common method variance was not a serious threat to our data analysis."

### Acceptable Example (Thompson et al., 2020)
**What They Reported:**
- Loading change criterion (< .15)
- Replicated across 4 studies (N = 239, 275, 269, 224)
- Clear interpretation

**Missing**: Specific percentage of variance explained

## Best Practices Recommendations

### Planning
1. Use ULMC when meaning of method factor is clear
2. Ensure adequate power to detect method effects
3. Consider whether method variance is truly unidimensional
4. Plan for ULMC usage in design phase (not just post-hoc)

### Reporting
1. Report specific percentage of variance explained by ULMC
2. Provide chi-square difference tests with degrees of freedom
3. Report changes in factor loadings with/without ULMC
4. Report whether ULMC model converged
5. Discuss implications for substantive conclusions
6. **Report results both with and without ULMC**

### Interpretation
1. Small effects may be more accurately estimated with ULMC
2. Large effects may be over-corrected by ULMC
3. Multiple method factors complicate ULMC performance
4. Consider whether to include ULMC in final analysis

## Implications for Updated Review

### What We Learned
- Original manual screening achieved 69.5% inclusion at Level 1
- Mean method variance detection: 14.3%
- Zero studies retained ULMC in final analysis
- Need for improved power and reporting transparency

### What We'll Add (2025 Update)
Based on user request, the updated review will add:

1. **Procedural Remedies**
   - Were procedural remedies used?
   - Which ones? (temporal separation, source separation, anonymity, etc.)
   - Relationship between procedural remedies and detected MV

2. **PLS-SEM Analysis**
   - Include PLS studies (previously excluded)
   - Tag PLS vs. CB-SEM
   - Specific PLS variant used (PLS, PLSc, consistent PLS)
   - Compare MV detection across estimators

3. **Specific Statistical Methods**
   - What statistical methods were used to address MV?
   - ULMC, CFA marker, correlational marker, Harman's test, etc.
   - Combinations of methods
   - Effectiveness of different approaches

### Validation Approach
1. Reproduce legacy screening decisions using AI-assisted automation
2. Calculate agreement metrics (sensitivity, specificity, F1)
3. Identify and resolve disagreements
4. Refine automated screening rules
5. Apply validated approach to updated literature (2012-2025)

## Files Generated
- `legacy_codebook.rds`: Complete codebook from legacy review
- `legacy_extracted_data.rds` / `.csv`: Processed DistillerSR export (182 studies)
- `legacy_summary_stats.rds`: Summary statistics
- `screening_functions.rds`: AI-assisted screening functions for validation

## Next Steps
1. ✅ Extract and document legacy methodology
2. ✅ Process DistillerSR export data
3. ⏳ Validate AI-assisted screening against legacy decisions
4. ⏳ Update automated search for 2012-2026 period (protocol through 2026)
5. ⏳ Add new extraction fields (procedural remedies, PLS, statistical methods)
6. ⏳ Run comprehensive updated review
7. ⏳ Compare legacy vs. updated findings
8. ⏳ Integrate into JAP manuscript






