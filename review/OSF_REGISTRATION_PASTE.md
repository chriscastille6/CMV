# OSF Preregistration — Copy-Paste Blocks

**Project:** https://osf.io/x9643/overview  
**Purpose:** Paste each block below into the corresponding OSF preregistration wizard field. OSF registration only (not PROSPERO).  
**Version:** Derived from protocol v3.2 (June 2026)

---

## Title

```
A Systematic Review of Unmeasured Latent Method Construct Usage in Organizational Research: Patterns of Implementation and Reporting Practices
```

---

## Authors

```
Christopher C. Castille, PhD — Nicholls State University (lead; screening, extraction, analysis)
Larry J. Williams, PhD — Texas Tech University (methodological oversight, manuscript review)

Contact: Christopher C. Castille — christopher.castille@nicholls.edu
Department of Management, Nicholls State University, P.O. Box 2015, Thibodaux, LA 70310, USA
```

---

## Description / Research questions

```
We will conduct a descriptive systematic review of methodological practices (Aguinis et al., 2020), not a traditional PICOS outcome review or meta-analysis of treatment effects. The review documents how organizational researchers implement and report the Unmeasured Latent Method Construct (ULMC) technique for detecting common method variance in survey-based studies.

Primary research question:
How is the Unmeasured Latent Method Construct (ULMC) being implemented in organizational research, and what patterns exist in reporting practices and methodological implementation?

Secondary research questions:
1. What proportion of studies follow the recommended three-step ULMC approach with appropriate statistical reporting?
2. What proportion of studies retain ULMC in final models after detection of method variance?
3. How frequently do studies implement procedural remedies alongside ULMC testing?
4. What is the distribution of method variance percentages detected across organizational studies?
5. How does model complexity (number of indicators and constructs) relate to ULMC implementation and reporting?
6. For PLS-SEM studies (analyzed separately), what proportion conduct confirmatory follow-up using more robust methods?
7. How do ULMC implementation and reporting practices vary by journal tier and over time?

Context and restart note:
Review work began in prior years with manual screening (~182 included studies). We are restarting under this prospectively registered protocol before full-scale re-screening and extraction on the 2025–2026 EBSCO identification strand. A pilot/training corpus (~185 studies) from Castille & Williams (2024, RPHRM) informs codebooks and reviewer training; a legacy holdout supports replication. Full extraction on the expanded live cohort has not begun under this registered protocol.

Secondary methodological aim:
Evaluate feasibility, reproducibility, and accuracy of a semi-automated systematic review workflow (structured metadata merge, rule-based and LLM-assisted Level 1 screening, scripted extraction with human verification) relative to the prior manual review.

Prior related work (same authors):
Castille & Williams (2022, AOM proceedings); Castille & Williams (2024, Research in Personnel and Human Resources Management, Vol. 42). The present review is a prospectively registered, PRISMA-compliant expansion with an updated narrow search (2010–2026), pre-specified three-step ULMC outcomes, model-complexity variables, and open-science dissemination via OSF.

Keywords: unmeasured latent method construct, ULMC, common method variance, systematic review, organizational research, structural equation modeling, methodological practices, three-step approach, model complexity
```

---

## Hypotheses

```
This review is descriptive and exploratory. We do not pre-register directional hypotheses (no H1–H5) about researcher compliance, intent, or prevalence. Pilot work (RPHRM 2024; ~185-study training corpus) informs expected prevalence ranges only.

We will summarize observed patterns, including:
- ULMC detection and method-variance reporting rates
- ULMC retention in final models vs. drop-after-test
- Procedural remedy documentation (proposed and/or used)
- Three-step ULMC compliance (Step 1 nested Δχ²/p-value; Step 2 Method-R bias test; Step 3 indicator- or construct-level contamination reporting)
- Variation by content_domain (substantive topic, e.g., leadership, turnover), publication year, journal tier, estimation method, and model complexity

Any inferential statistics (e.g., chi-square, Fisher's exact, one-way ANOVA) are optional, supplementary, and labeled exploratory—not confirmatory tests of pre-specified hypotheses.
```

---

## Design / Study type

```
Systematic review of methodological practices (descriptive synthesis).

Review type: Descriptive systematic review per Aguinis et al. (2020); not a meta-analysis of treatment effects.

Domain: Methodological practices in management, organizational behavior, human resource management, and applied psychology—specifically ULMC implementation and reporting in survey-based empirical studies.

Organizational settings include corporate, healthcare, educational, government/public sector, non-profit, and cross-cultural contexts.

Screening workflow (methodological review framing):
- Stage 1 — Identification filtering: automated duplicate removal (DOI + title), English language, peer-reviewed articles, date range 2010–2026.
- Stage 2 — Title/abstract (minimal): narrow search string limits ULMC terminology; flag obvious exclusions and route PLS-SEM to a separate track.
- Stage 3 — Full-text eligibility and extraction: definitive inclusion based on empirical ULMC (or equivalent single method-factor) implementation with sufficient reporting; organizational/work-related applied psychology domain; PLS-SEM excluded from main CB-SEM synthesis (retained for separate descriptive reporting).

Selection process:
Primary reviewer (CC) conducts screening and extraction with training/validation on the ~185-study pilot dataset, justified by extensive ULMC literature experience. Err toward inclusion at early passes; apply formal eligibility at full-text review (Aguinis et al., 2020, Step 3). Legacy ~182-study holdout retained for replication checks, not merged into the live analytic cohort.

Risk of bias / quality scoring: Not used. Early drafts included STROBE-adapted scoring; dropped per author decision. Synthesis uses descriptive extraction fields only.

Reporting standards: PRISMA 2020 (checklist, flow diagram, reproducible search documentation).

Timeline:
- Anticipated start: November 1, 2025
- Anticipated completion: February 28, 2026
- Search updates: quarterly through manuscript submission
```

---

## Sampling plan / Search strategy

```
Primary identification database:
- Institutional Discovery Service / EBSCO (PsycINFO + Business Source Complete) ONLY

Supplementary / sensitivity sources (not primary PRISMA identification counts):
- OpenAlex (optional programmatic search; disabled in current config)
- Crossref (optional DOI-based search; disabled in current config)
- Reference lists of included studies (backward citation; optional)
- Forward citation of key ULMC papers (optional)
- Author correspondence for unpublished data (if needed)

Primary search query (narrow, pre-registered):
("unmeasured latent method construct" OR "unmeasured latent method factor")

Rationale: Captures in-text ULMC usage with high specificity. Domain (management/OB/psychology), empirical design, and PLS exclusion are applied at screening—not embedded in the search string.

Standard limiters (primary search):
- Language: English
- Publication type: peer-reviewed journal articles
- Date range: January 1, 2010 to December 31, 2026
- Full text when available (Discovery Service)
- Geographic: no restrictions
- Publisher: no exclusions (all journals included; predatory/questionable outlets flagged for sensitivity analysis)

Optional expanded Boolean and programmatic harvests (OpenAlex/Crossref) documented for reproducibility but not used for primary identification counts.

Database adaptations:
- Discovery Service/EBSCO: subject headings + keyword with field codes

Expected sample size: approximately 300–500 studies based on preliminary searches.

Live cohort: 2025–2026 EBSCO identification strand under this registration.
```

---

## Inclusion / Exclusion

```
Inclusion criteria:
- Empirical quantitative studies in management, organizational behavior, human resource management, or applied psychology
- Survey-based or archival data with multiple constructs
- ULMC or equivalent single method-factor implementation with sufficient reporting for extraction
- Peer-reviewed journal articles, English language
- Publication date 2010–2026
- Study designs: cross-sectional, longitudinal, field, archival with survey components, multi-source, experimental with survey measures

Exclusion criteria:
- PLS-SEM studies (separate descriptive analysis track; excluded from main CB-SEM synthesis)
- Studies formally retracted by the publisher (regardless of other eligibility criteria)
- Conceptual/theoretical papers without empirical data
- Meta-analyses (unless they also report primary ULMC analysis)
- Case studies without quantitative analysis
- Qualitative studies
- Conference abstracts, dissertations, book chapters
- Non-English publications
- Insufficient methodological detail for extraction

Publisher outlet policy:
Studies from predatory or questionable publishers (e.g., MDPI per Beall-style lists) are NOT excluded from the main analysis. They are coded via publisher_outlet and predatory_journal_flag and re-analyzed in a sensitivity analysis excluding flagged outlets.

Level 1 screening questions (full-text first when PDF available):
- Q1.4: Formally retracted by publisher? (Yes → exclude; screening_status: level1_fail; decision_reason_code: EXCLUDE_RETRACTED)
- Q1.1: Management/HRM/OB/applied psychology domain?
- Q1.2: Empirical study mentioning ULMC or CMV testing?
- Q1.3: PLS estimation? (Yes → separate track)

Level 2 full-text questions:
- Q2.1: ULMC technique implemented?
- Q2.2: Method variance results reported?
- Q2.3: Sufficient detail for extraction?
```

---

## Variables / Outcomes

```
Primary outcomes:
1. ULMC three-step implementation — proportion following recommended approach:
   - Step 1: nested Δχ² / p-value for CMV presence (trait-only vs trait+ULMC)
   - Step 2: Method-R bias test (trait/method-R vs trait/method)
   - Step 3: indicator- or construct-level method variance / contamination reporting
   Coding: binary per step and for complete three-step implementation (three_step_complete)
2. Method variance detection — percentage of variance attributed to method factor (continuous, 0–100%)
3. ULMC retention — proportion retaining ULMC in final models (binary)
4. Model complexity — number of indicators, number of constructs, indicators-per-construct ratio

Secondary outcomes:
1. Procedural remedies — types and frequency (procedural_remedies_used, procedural_remedies_list; codebook list non-exhaustive; free-text captured in notes)
2. PLS follow-up — for PLS track, presence of confirmatory follow-up (CB-SEM or other robust method) and whether findings confirmed
3. Content domain patterns — variation by substantive topic (content_domain; e.g., leadership, turnover, safety climate; NOT industry/sector)
4. Temporal trends — ULMC practices by year (2010–2026)
5. Journal tier patterns — descriptive variation by publication venue and impact factor tier

Study characteristics extracted:
Authors, year, journal, DOI, content_domain, construct_names, study design, sample size, estimator, software, publisher_outlet, predatory_journal_flag

Extraction management:
Standardized database with automated validation; pilot validation on ~185-study corpus; version-controlled forms; systematic documentation of decisions. AI-assisted pre-screening and pre-fill with human verification on all inclusion decisions and extracted values.

Sample size and response rate are NOT outcomes of interest for this methodological review.
```

---

## Analysis plan

```
Primary synthesis (descriptive only):
- Study characteristics: frequency tables, descriptive statistics
- Three-step implementation: proportions with 95% confidence intervals; breakdown by individual steps
- Method variance distribution: histogram, mean, median, range, SD, quartiles
- ULMC retention: proportion with 95% CI
- Procedural remedy usage: frequency and type analysis
- Model complexity: distributions and descriptive associations with ULMC reporting
- Temporal trends: year-over-year patterns (2010–2026)
- Journal distribution: venue and impact-factor tier summaries

PLS-specific analysis (separate track):
- Proportion using PLS-SEM
- Follow-up study rate and method comparison vs. CB-SEM findings

Pre-specified descriptive subgroup slices (exploratory; no directional hypotheses):
1. content_domain (substantive topic)
2. Model complexity: low (<5 constructs), medium (5–10), high (>10)
3. Study design: cross-sectional vs. longitudinal
4. Publication year: 2010–2015, 2016–2020, 2021–2026
5. Journal tier: high (>3.0), medium (1.5–3.0), low (<1.5) impact factor — descriptive only
6. Estimation method: CB-SEM vs. PLS-SEM (PLS reported separately)

Optional exploratory inferential summaries (supplementary, not hypothesis tests):
Chi-square or Fisher's exact tests and one-way ANOVA may characterize observed associations. No Bonferroni correction or multivariable logistic regression planned. Effect sizes (e.g., Cohen's d, Cramer's V) reported descriptively where helpful.

Sensitivity analyses:
- Recent studies only (2020–2026)
- Exclude vs. include studies with predatory_journal_flag = TRUE

Protocol deviations from this plan will be documented in the final report.
```

---

## Other

```
OSF project and materials:
All protocol documents, extraction codebooks, search reproducibility notes, and analysis materials: https://osf.io/x9643/overview

Funding and conflicts:
No external funding. Conducted as academic research at Nicholls State University. Authors have published on ULMC methodology; no financial conflicts related to this review.

Collaborators:
None at this time.

Dissemination plans:
- Primary manuscript: Journal of Applied Psychology (target)
- Protocol publication and conference presentations (AOM, SIOP)
- Open access data, code, and materials on OSF

Pilot and training:
RPHRM (2024) chapter (~185 coded studies) serves as pilot/training corpus. Legacy ~182-study holdout supports workflow replication. Interim EBSCO screening progress documented in project repository.

AI transparency:
AI-assisted tools used for pre-screening and pre-filling extraction fields; all inclusion decisions and extracted values verified by authors. AI use reported explicitly in methods.

Limitations (anticipated):
English-only search; database coverage gaps; publication and reporting bias; inconsistent ULMC reporting detail across primary studies; heterogeneity limits causal inference.

References (selected):
Aguinis, H., Ramani, R. S., & Alabduljader, N. (2020). Best-practice recommendations for producers and consumers of methodological literature reviews. Organizational Research Methods.
Castille, C. M., & Williams, L. J. (2024). Shedding light on invisible influences: Reviewing HROB scholars' use of unmeasured latent method factors. Research in Personnel and Human Resources Management, Vol. 42.
Richardson, H. A., Simmering, M. J., & Sturman, M. C. (2009). A tale of three perspectives… Organizational Research Methods.
```

---

## Quick checklist before submitting on OSF

- [ ] Title pasted
- [ ] Authors and contact pasted
- [ ] Description / research questions pasted
- [ ] Hypotheses block confirms descriptive/exploratory framing (no H1–H5)
- [ ] Design / study type pasted
- [ ] Sampling / search strategy pasted
- [ ] Inclusion / exclusion pasted
- [ ] Variables / outcomes pasted
- [ ] Analysis plan pasted
- [ ] Other (OSF link, funding, dissemination) pasted
- [ ] Linked to OSF project https://osf.io/x9643/overview
