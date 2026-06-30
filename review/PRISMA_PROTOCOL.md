# PRISMA 2020 SYSTEMATIC REVIEW PROTOCOL
## Unmeasured Latent Method Construct (ULMC) Usage in Organizational Research

### **REGISTRATION INFORMATION**
- **OSF Preregistration**: https://osf.io/3kmyc/ (submitted 2026-06-26; public)
- **Protocol Registration**: [To be registered with PROSPERO]
- **Review Title**: "A Systematic Review of Unmeasured Latent Method Construct Usage in Organizational Research: Patterns of Implementation and Reporting Practices"
- **Authors**: Christopher C. Castille (Nicholls State University), Larry J. Williams (Texas Tech University)
- **Contact**: christopher.castille@nicholls.edu

---

## **PROTOCOL HISTORY AND RELATION TO PRIOR WORK**

This review was initiated several years ago with manual screening (DistillerSR) and an initial included set (~182 studies). The authors are **restarting and prospectively registering** an updated protocol to evaluate a **semi-automated systematic review workflow** (structured metadata merge, rule-based and LLM-assisted Level 1 screening, scripted extraction with human verification).

**Published prior work (same authors):**

- Castille, C., & Williams, L. J. (2022). To partial or not? Re-examining the unmeasured latent method construct (ULMC). *Academy of Management Proceedings*, *2022*(1), Article 10998. https://doi.org/10.5465/ambpp.2022.10998abstract
- Castille, C. M., & Williams, L. J. (2024). Shedding light on invisible influences: Reviewing HROB scholars' use of unmeasured latent method factors. In M. R. Buckley, A. R. Wheeler, J. E. Baur, & J. R. B. Halbesleben (Eds.), *Research in Personnel and Human Resources Management* (Vol. 42, pp. 215–250). Emerald Publishing Limited. https://doi.org/10.1108/s0742-730120240000042007

The RPHRM (2024) chapter systematic review (~185 coded studies) provides the **pilot/training corpus** and informs expected prevalence ranges. The **legacy 182-study holdout** is retained for replication validation and is **not** the primary analytic sample under this registration. The **2025–2026 EBSCO identification strand** (narrow PROSPERO query; 570-pool) is the live cohort for pre-registered screening and extraction.

**Interim progress reporting (to date):** Native EBSCO export positions **1–150** are the primary dashboard strand: 145 in-pool PDFs with Level 1 decisions and PDF evidence (`review/EBSCO/ebsco_150_screening_evidence.csv`). Five off-pool export rows (#21, #89, #148–#150) are logged separately. PRISMA and Summary tabs on `review/PROGRESS_DASHBOARD.html` report this interim L1 strand; the full 570-pool / legacy-182 publication PRISMA is deferred until screening continues past position 150.

**Secondary methodological aim:** Assess feasibility, reproducibility, and accuracy of the semi-automated pipeline relative to the prior manual review.

Source files: `paper/jap-ulmc-esem/prior-work/README.md`

---

## **1. REVIEW OBJECTIVES**

### **Primary Research Question**
How is the Unmeasured Latent Method Construct (ULMC) being implemented in organizational research, and what evidence exists for methodological misuse?

### **Secondary Research Questions**
1. What percentage of studies retain ULMC in final models after detection?
2. How frequently do studies implement procedural remedies alongside ULMC testing?
3. What is the distribution of method variance percentages detected across studies?

### **Review Rationale**
The ULMC technique is widely used to detect common method variance but may be subject to "checkbox mentality" where scholars test for method variance without proper remediation. This review aims to document patterns of ULMC misuse and provide evidence for improved methodological practices.

---

## **2. ELIGIBILITY CRITERIA**

### **Inclusion Criteria (PICOS Framework)**

**Population (P)**: 
- Empirical studies in management, organizational behavior, human resources, applied psychology
- Studies using survey-based or archival data with multiple constructs

**Intervention/Exposure (I)**:
- Studies implementing Unmeasured Latent Method Construct (ULMC) technique
- Studies testing for common method variance using single method factor approaches

**Comparator (C)**:
- Not applicable (descriptive systematic review)

**Outcomes (O)**:
- Method variance percentage detected
- ULMC model fit improvement
- ULMC retention in final models
- Procedural remedies implementation

**Study Design (S)**:
- Empirical quantitative studies
- Cross-sectional and longitudinal designs
- Published peer-reviewed articles

### **Exclusion Criteria**
- Conceptual/theoretical papers without empirical data
- Studies using PLS-SEM methodology (separate analysis track)
- Studies formally retracted by the publisher (regardless of other eligibility criteria)
- Non-English publications
- Dissertations, conference proceedings, book chapters
- Studies not reporting ULMC implementation details

**Publisher outlet policy**: Studies from predatory or questionable publishers (e.g., MDPI per Beall-style lists) are **not excluded**. They are included in the main analysis, coded via `publisher_outlet` and `predatory_journal_flag`, and re-analyzed in a **sensitivity analysis** excluding flagged outlets.

### **Time Frame**
- **Primary Search**: 2010 to date (2026) (17-year window)
- **Rationale**: ULMC technique gained prominence post-2009 (Richardson et al.)

---

## **3. INFORMATION SOURCES**

### **Electronic Databases (Primary Identification)**
- **Institutional Discovery Service / EBSCO** (PsycINFO + Business Source Complete) ONLY

**Standard limiters on primary search**: English; peer-reviewed journal articles; full text when available; date range 2010–2026.

### **Supplementary / Sensitivity Sources (Not Primary Identification)**
- **OpenAlex** (optional programmatic search — disabled in current config)
- **Crossref** (optional DOI-based search — disabled in current config)
- Reference lists of included studies (backward citation; optional)
- Studies citing key ULMC papers (forward citation; optional)
- Author correspondence for unpublished data

Expanded Boolean queries (ULMC + CMV term combinations) and OpenAlex/Crossref harvests are documented for reproducibility but are **not** the primary identification strategy. Primary PRISMA identification counts derive from the narrow PROSPERO query (see Section 4).

### **Search Date Range**
- **Initial Search**: October 2025
- **Search Updates**: Quarterly through submission
- **Final Search**: Prior to manuscript submission

---

## **4. SEARCH STRATEGY**

### **Primary Search (PROSPERO-Registered Narrow Query)**

**Core query** (identification):
```
"unmeasured latent method construct" OR "unmeasured latent method factor"
```

**Standard limiters**: Full text (when available); scholarly (peer-reviewed) journal articles; English; date range January 1, 2010 to December 31, 2026.

**Rationale**: These two phrases capture scholars' in-text ULMC usage with high specificity. Domain (management/OB/psychology), empirical design, and PLS exclusion are applied at **screening**, not embedded in the search string (aligned with `PROSPERO_DRAFT_REGISTRATION_FINAL.md`).

### **Supplementary / Sensitivity Searches (Optional)**

The following are **not** used for primary PRISMA identification counts but may be run for sensitivity analysis or gap-filling:

**Expanded Boolean** (optional):
```
(("unmeasured latent method construct" OR "unmeasured latent method factor" OR "ULMC" OR "single method factor") 
AND 
("common method variance" OR "common method bias" OR "method variance"))
AND
(management OR organizational OR "human resource" OR psychology OR "applied psychology")
AND 
(empirical OR survey OR questionnaire OR "structural equation")
```

**Programmatic harvest** (optional): OpenAlex and Crossref via `review/01_search_harvest.R` + `config.yaml` (`search.supplementary.programmatic`).

**Additional CMV-related terms** (for expanded searches only): `"common method variance"`, `"common method bias"`, `"Harman single factor"`, `"Harman test"`, `"marker variable"`, `"procedural remedy"`, `"separation of measurement"`.

### **Database-Specific Adaptations (Primary Search)**
- **Discovery Service / EBSCO**: Subject headings + keyword search with standard limiters (PsycINFO thesaurus terms + free text; Business Source Complete field codes)

OpenAlex/Crossref: see supplementary programmatic search in `SEARCH_STRATEGY_REPRODUCIBILITY.md` (optional; disabled in current config).

---

## **5. STUDY SELECTION PROCESS**

### **Screening Workflow**

This is a **methodological systematic review** (descriptive synthesis of ULMC implementation and reporting), not a traditional PICOS outcome review (Aguinis et al., 2020). Eligibility turns on **methods reporting**, not intervention/outcome findings.

```
Stage 1: Automated Filtering
├── Duplicate removal (DOI + title matching)
├── Language filtering (English only)
├── Publication type filtering (peer-reviewed articles)
└── Date range filtering (2010 to date (2026))

Stage 2: Title/Abstract — minimal pass
├── Narrow search already limits ULMC/CMV terminology
├── Flag obvious exclusions (non-empirical, wrong language, clear domain mismatch)
└── Route PLS-SEM hits to separate excluded_pls track

Stage 3: Full-Text Assessment (definitive eligibility)
├── Empirical ULMC / single method-factor implementation verified
├── Organizational / work-related applied psychology domain (Q1.1)
├── PLS estimation excluded (Q1.3)
├── Sufficient methodological detail for extraction
└── Final inclusion decision
```

### **Screening Criteria Application**

**Level 1 Screening (full-text first for on-hand PDFs; title/abstract when full text unavailable)**:
- Q1.4: "Has the study been formally retracted by the publisher?" (Yes = exclude; `screening_status`: `level1_fail`; `decision_reason_code`: `EXCLUDE_RETRACTED`)
- Q1.1: "Is the study published in management/HRM/OB/Applied Psychology domain?"
- Q1.2: "Is the study empirical and mentions ULMC or CMV testing?"
- Q1.3: "Does the study use PLS estimation?" (Yes = separate track)

Q1.4 is evaluated first when title/metadata/PDF indicates retraction (e.g., title prefix `RETRACTED:`, EBSCO `retracted` flag, publisher retraction notice). Example cut from corpus: Fernández-Fernández et al. (2023), *Heliyon* e17201 — teleworking technostress (publisher-retracted).

**Level 2 Screening (Full-Text)**:
- Q2.1: "Does the study implement ULMC technique?"
- Q2.2: "Are method variance results reported?"
- Q2.3: "Is sufficient detail provided for extraction?"

### **Inter-Rater Reliability**
- **Lead reviewer** (CC) with structured rules and PDF evidence snippets
- **Verification sample** and manual-review queue for borderline domain decisions
- **Legacy holdout** (182 studies) retained for replication checks, not merged into live cohort

---

## **6. DATA EXTRACTION PROCESS**

### **Extraction Categories**

#### **Study Characteristics**
- Authors, year, journal, DOI
- **Content domain** (substantive topic/setting — e.g., leadership, turnover, safety climate)
- **Construct names** and **model complexity** (`num_constructs`, `num_indicators`, `complexity_ratio`)
- Study design, sample size

#### **ULMC Implementation**
- Statistical software used
- ULMC model specification
- Method variance percentage detected
- **Step 1 CMV presence evidence**: nested Δχ² (trait-only vs trait+ULMC) and p-value
- Statistical significance of method factor (via presence/bias nested tests, not fit-index extraction)

#### **Procedural Remedies**
- Temporal separation implementation
- Source separation (multi-source data)
- Methodological separation techniques
- Anonymity/confidentiality measures
- Scale design improvements

#### **Study Outcomes**
- ULMC model fit improvement claims
- ULMC retention in final models
- Author conclusions about method bias
- Remedial actions taken post-detection

### **Extraction Validation**
- **Dual Extraction**: 10% random sample
- **Automated Extraction**: AI-assisted with human verification
- **Quality Control**: Standardized extraction forms
- **Pilot Testing**: 5 studies for form refinement

### **AI-Assisted Workflow and Transparency**
Consistent with growing use of AI in literature synthesis (Gibney, 2026), we used AI-assisted tools to pre-screen records and pre-fill extraction fields; all inclusion decisions and extracted values were verified by the authors. We report this use explicitly because general-purpose language models can mis-cite sources, whereas purpose-built, retrieval-grounded tools and human verification remain the appropriate standard for systematic reviews.

---

## **7. DATA SYNTHESIS PLAN**

### **Descriptive Analysis**
- **Study Characteristics**: Frequency tables, descriptive statistics
- **Temporal Trends**: Year-over-year ULMC usage patterns
- **Journal Distribution**: Venue analysis with impact factors

### **Primary Outcome Analysis**
- **Method Variance Distribution**: Histogram, summary statistics
- **ULMC Retention Rates**: Proportion retained in final models
- **Procedural Remedy Usage**: Frequency and type analysis
- **Three-Step Compliance**: Step 1 presence test reporting, Method-R bias tests, Step 3 contamination reporting
- **Model Complexity**: Distribution of constructs, indicators, and complexity ratio

### **Subgroup Analysis (exploratory, descriptive)**
- **By content_domain**: Substantive topic (leadership, turnover, safety climate, etc.) — not industry/sector
- **By Study Design**: Cross-sectional vs Longitudinal
- **By Year / Journal Tier / Estimation Method**: Descriptive cross-tabulations only
- **By Publisher Outlet (sensitivity)**: Main analysis includes all outlets; sensitivity analysis excludes studies with `predatory_journal_flag` = TRUE (e.g., MDPI)

No pre-specified directional hypotheses; inferential tests (chi-square, ANOVA) optional and exploratory only.

---

## **8. REPORTING STANDARDS**

### **PRISMA 2020 Compliance**
- **PRISMA Checklist**: All 27 items addressed
- **PRISMA Flow Diagram**: Study selection visualization
- **Search Strategy**: Complete reproducible documentation

### **Additional Reporting**
- **Search Strategy**: Full database queries in appendix
- **Excluded Studies**: List with exclusion reasons
- **Data Extraction**: Sample extraction forms

---

## **9. TIMELINE**

### **Phase 1: Foundation (Weeks 1-2)**
- [ ] Protocol finalization and registration
- [ ] Search strategy testing and refinement
- [ ] Extraction form development and pilot testing

### **Phase 2: Search and Screening (Weeks 3-6)**
- [ ] Database searches and result compilation
- [ ] Duplicate removal and initial filtering
- [ ] Title/abstract screening (target: 1000+ records)
- [ ] Full-text assessment (target: 100+ studies)

### **Phase 3: Data Extraction (Weeks 7-10)**
- [ ] Systematic data extraction
- [ ] Inter-rater reliability testing
- [ ] Data validation and cleaning

### **Phase 4: Analysis and Reporting (Weeks 11-14)**
- [ ] Descriptive and subgroup analyses
- [ ] PRISMA flow diagram creation
- [ ] Manuscript drafting
- [ ] Supplementary material preparation

---

## **10. POTENTIAL LIMITATIONS**

### **Search Limitations**
- **Language Bias**: English-only publications
- **Database Coverage**: Potential gaps in non-indexed journals
- **Grey Literature**: Limited conference/dissertation coverage

### **Selection Limitations**
- **Publication Bias**: Positive results more likely published
- **Reporting Bias**: Incomplete ULMC implementation details
- **Time Lag**: Recent studies may not yet be indexed

### **Extraction Limitations**
- **Information Availability**: Inconsistent reporting across studies
- **Missing Data**: Incomplete study characteristics

### **Analysis Limitations**
- **Heterogeneity**: Diverse methodologies and contexts
- **Causality**: Cannot establish causal relationships
- **Generalizability**: Limited to included study characteristics

---

**Protocol Version**: 1.0  
**Date**: October 2025  
**Status**: OSF preregistration **submitted** 2026-06-26 — https://osf.io/3kmyc/ (project https://osf.io/x9643/overview). PROSPERO submission pending.

---

## **References (protocol)**

Gibney, E. (2026, February 4). Open-source AI tool beats giant LLMs in literature reviews—and gets citations right. *Nature*. https://doi.org/10.1038/d41586-026-00347-9





