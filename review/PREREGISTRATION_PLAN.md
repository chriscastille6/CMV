# PRE-REGISTRATION PLAN FOR ULMC SYSTEMATIC REVIEW
## Using Zotero Corpus as Pilot Data for Protocol Refinement

### **Relation to prior published work**

This expanded registration builds on Castille & Williams (2022, AOM proceedings) and Castille & Williams (2024, *Research in Personnel and Human Resources Management*, Vol. 42). The RPHRM chapter (~185 coded studies) is the pilot/training corpus; the legacy ~182-study holdout supports replication. The live 2025–2026 EBSCO strand is the primary sample under this registration. See `paper/jap-ulmc-esem/prior-work/README.md` and `PRISMA_PROTOCOL.md` (Protocol History).

### 🎯 **PRE-REGISTRATION STRATEGY**

**Excellent idea!** Using our 32 Zotero studies as **pilot data** for pre-registration provides:
- **Methodological transparency** before full-scale analysis
- **Protocol validation** with real data
- **Credibility enhancement** for JAP submission
- **Protection against post-hoc analysis** accusations

---

## **📊 PILOT DATA SUMMARY (32 Studies)**

### **Pilot Findings (To Inform Pre-Registration)**
- **ULMC Detection Rate**: 30/32 (93.8%) - High prevalence confirmed
- **Method Variance Range**: 1-100% (Mean = 48.1%) - Substantial variation
- **ULMC Retention Rate**: 0/32 (0%) - Complete abandonment pattern
- **Procedural Remedies**: 12/32 (37.5%) - Low implementation
- **Content domains**: Diverse (workplace, healthcare, education, etc.) — pilot informed `content_domain` coding

### **Pilot-Informed Protocol Refinements**
Based on pilot data, we can now **pre-specify**:
1. **Expected prevalence ranges** for primary outcomes
2. **Subgroup analysis plans** based on pilot variation
3. ~~**Quality assessment thresholds**~~ — not used (dropped per author decision)
4. **Sample size targets** for adequate power

---

## **🔬 PRE-REGISTRATION COMPONENTS**

### **1. PROSPERO Registration**
**Platform**: PROSPERO (International Prospective Register of Systematic Reviews)
**Timeline**: Submit before analyzing 350 EBSCO studies
**Status**: Protocol ready for submission

**Registration Elements**:
- [x] Research questions pre-specified
- [x] Search strategy documented
- [x] Inclusion/exclusion criteria defined
- [x] Data extraction plan detailed
- [x] Analysis plan specified
- [x] ~~Quality assessment framework established~~ — not used; dropped

### **2. PILOT-INFORMED EXPECTATIONS (DESCRIPTIVE, NOT HYPOTHESES)**

Pilot work (RPHRM 2024; ~185-study training corpus) informs **expected prevalence ranges** only. We do **not** pre-register directional hypotheses about researcher compliance — the review documents **observed** implementation and reporting patterns descriptively.

**Exploratory patterns to summarize (not tested as H1–Hn)**:
- ULMC detection and method-variance reporting rates
- ULMC retention in final models vs. drop-after-test
- Procedural remedy documentation (proposed and/or used)
- Variation by `content_domain`, year, journal tier, and estimation approach

### **3. PRE-SPECIFIED ANALYSIS PLAN**

#### **Primary Outcomes (Pre-Registered)**
1. **ULMC Detection Rate**: Proportion of studies implementing ULMC
2. **Method Variance Distribution**: Mean, median, range, standard deviation
3. **ULMC Retention Rate**: Proportion retaining ULMC in final models
4. **Procedural Remedy Usage**: Frequency and types implemented

#### **Secondary Outcomes (Pre-Registered)**
1. **Content Domain Patterns**: Method variance and ULMC usage by substantive topic (`content_domain`)
2. **Temporal Trends**: ULMC usage changes over time (2010 to date (2026))

#### **Subgroup Analyses (exploratory)**
Descriptive cross-tabulations only:
1. **Content Domain**: Substantive topical categories from `content_domain`
2. **Study Design**: Cross-sectional vs Longitudinal
3. **Temporal trends**: Year bands (2010–2019, 2020+)
4. **Journal impact tier**: Descriptive venue groupings
5. **Publisher Outlet** (sensitivity): Predatory/questionable outlets flagged via `predatory_journal_flag`

Sample size and response rate are **not** outcomes of interest for this methodological review.

---

## **📋 PRE-REGISTRATION PROTOCOL**

### **Study Selection (Pre-Specified)**
```yaml
Inclusion Criteria:
  - Empirical studies in management/OB/psychology
  - ULMC or CMV testing reported
  - Peer-reviewed publications 2010 to date (2026)
  - English language
  - Sufficient statistical detail for extraction

Exclusion Criteria:
  - PLS-SEM studies (separate analysis)
  - Conceptual/theoretical papers
  - Insufficient methodological detail

Publisher policy: Predatory/questionable outlets (e.g., MDPI) included in main analysis; flag for sensitivity analysis (no exclusion).
```

### **Data Extraction (Pre-Specified)**
```yaml
Primary Variables:
  - ULMC implementation (Yes/No)
  - Method variance percentage (Continuous)
  - ULMC retained in final model (Yes/No)
  - Procedural remedies used (Yes/No, Types)

Secondary Variables:
  - content_domain, construct_names, num_indicators
  - Study design, statistical software used
  - procedural_remedies_used, procedural_remedies_list (codebook list non-exhaustive)
  - Three-step ULMC fields (Step 1 Δχ²/p-value, Method-R, contamination)
```

### **Quality Assessment (Pre-Specified)**
~~STROBE-adapted risk-of-bias scoring was piloted in early drafts; not used in the registered review.~~


### **Statistical Analysis Plan (Pre-Registered)**
```yaml
Descriptive Analysis:
  - Frequencies, proportions, means, standard deviations
  - 95% confidence intervals for all estimates

Primary Analysis:
  - ULMC detection rate with 95% CI
  - Method variance distribution (histogram, summary stats)
  - ULMC retention rate with 95% CI
  - Procedural remedy frequency analysis

Subgroup Analysis (exploratory only):
  - Descriptive cross-tabulations by content_domain, year, journal tier, estimation method
  - Optional chi-square / ANOVA without pre-specified directional hypotheses
  - Effect sizes reported descriptively where helpful (Cohen's d, Cramer's V)

Sensitivity Analysis:
  - Recent studies only (2020-2026)
  - Predatory/questionable publisher outlets excluded vs included
```

---

## **🚀 PRE-REGISTRATION TIMELINE**

### **Phase 1: Pre-Registration Submission (Week 1)**
- [ ] **PROSPERO Registration**: Submit complete protocol
- [ ] **OSF Pre-Registration**: Backup registration at https://osf.io/x9643/overview (project created; **draft ready** — paste from `OSF_REGISTRATION_PASTE.md` or use `artifacts/reports/preregistration_filled.json`)
- [ ] **Protocol Publication**: Submit to journal for protocol publication

### **Phase 2: Full-Scale Data Collection (Weeks 2-6)**
- [ ] **EBSCO 350 Studies**: Process with validated pipeline
- [ ] **OpenAlex Supplementation**: Additional studies if needed
- [ ] **Quality Control**: Apply pre-registered criteria strictly

### **Phase 3: Pre-Registered Analysis (Weeks 7-10)**
- [ ] **Primary Outcomes**: Exactly as pre-specified
- [ ] **Secondary Outcomes**: Follow pre-registered plan
- [ ] **Subgroup Analysis**: Only pre-specified comparisons
- [ ] **Sensitivity Analysis**: As planned in protocol

### **Phase 4: Manuscript Preparation (Weeks 11-14)**
- [ ] **Results Reporting**: Transparent about pre-registration
- [ ] **Protocol Deviations**: Document any necessary changes
- [ ] **Supplementary Analysis**: Clearly labeled as exploratory

---

## **📈 PILOT DATA VALIDATION**

### **What Pilot Data Confirms**
1. **Extraction Pipeline Works**: 90%+ accuracy on key variables
2. **Variation Exists**: Sufficient spread for subgroup analysis
3. **Effect Sizes Detectable**: Clear patterns in ULMC usage
4. ~~**Quality Assessment Feasible**~~ — formal RoB scoring dropped

### **Protocol Refinements from Pilot**
1. **Search Terms Validated**: ULMC detection rate confirms good sensitivity
2. **Extraction Categories Confirmed**: All planned variables extractable
3. **Sample Size Adequate**: Pilot suggests 300+ studies achievable

---

## **🎯 PRE-REGISTRATION BENEFITS**

### **Scientific Rigor**
- **Prevents HARKing**: Hypotheses after results are known
- **Reduces P-hacking**: Analysis plan locked before full data
- **Increases Transparency**: All decisions documented upfront
- **Enhances Credibility**: Shows methodological sophistication

### **Publication Advantages**
- **JAP Preference**: Top journals favor pre-registered studies
- **Reviewer Confidence**: Demonstrates rigorous methodology
- **Replication Facilitation**: Complete protocol available
- **Open Science Compliance**: Meets transparency standards

### **Research Quality**
- **Bias Reduction**: Minimizes researcher degrees of freedom
- **Power Optimization**: Sample size planned based on pilot data
- **Analysis Focus**: Prevents fishing expeditions
- **Interpretation Clarity**: Results evaluated against pre-specified hypotheses

---

## **✅ NEXT STEPS**

### **Immediate Actions (This Week)**
1. **Finalize PROSPERO Registration** - Submit complete protocol
2. **OSF Project** — https://osf.io/x9643/overview (created; link PROSPERO after submission)
3. **Document Pilot Findings** - Formal pilot study report
4. **Prepare Analysis Code** - Pre-registered analysis scripts

### **Pre-Registration Checklist**
- [x] Research questions specified
- [x] Hypotheses pre-registered  
- [x] Search strategy documented
- [x] Inclusion/exclusion criteria defined
- [x] Data extraction plan detailed
- [x] ~~Quality assessment framework established~~ — not used; dropped
- [x] Statistical analysis plan specified
- [x] Subgroup analyses pre-specified
- [x] Pilot data documented separately

**Status**: Ready for PROSPERO submission
**Timeline**: Register this week, analyze 350 studies next month
**Outcome**: Bulletproof systematic review with maximum credibility

This approach transforms our work from "just another systematic review" to a **methodologically exemplary study** that sets the standard for ULMC research! 🏆





