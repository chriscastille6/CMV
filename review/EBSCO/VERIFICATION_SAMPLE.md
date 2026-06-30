# EBSCO 1–150 verification sample (3 papers)

Use this sample to sanity-check Level 1 screening before clearing the manual queue. Reply in chat (`M0183 include`) or edit `classification_feedback.csv` and run `apply_classification_feedback.py`.

Each row in `ebsco_150_screening_evidence.csv` now includes structured **`decision_reason_code`** and **`decision_reason_text`** (plus per-criterion `q1_*_reason_code` columns) so you can verify *why* each decision was made.

| Role | ID | EBSCO # | Auto decision | Confidence | decision_reason_code |
|------|-----|--------:|---------------|------------|----------------------|
| **Certain include** | M0183 | 1 | included | high | `INCLUDE_ALL_CRITERIA_PASS` |
| **Uncertain** | M0244 | 63 | manual_review | low | `MANUAL_REVIEW_DOMAIN_BORDERLINE_PUBLIC_HEALTH` |
| **Uncertain** | M0282 | 102 | manual_review | low | `MANUAL_REVIEW_DOMAIN_BORDERLINE_CLINICAL_PATIENTS` |

> **Note:** M0244 and M0282 are **manual_review**, not hard rejected. Automation passes Q1.1–Q1.3 but flags borderline domain/sample for human verification.

---

## 1. M0183 — high-confidence **include** (EBSCO #1)

**Title:** How Workplace Fun Promotes Employees' Innovative Behavior: A Dual Mediation Model.

**Codified reasons:**

| Criterion | Pass? | Code | Text |
|-----------|-------|------|------|
| Q1.1 Domain | ✓ | `DOMAIN_PASS_KEYWORDS_METADATA` | management-domain keywords in metadata |
| Q1.2 ULMC | ✓ | `ULMC_PASS_EMPIRICAL` | empirical ULMC detected |
| Q1.3 Not PLS | ✓ | `PLS_PASS_NOT_DETECTED` | no PLS-SEM detected |
| **Decision** | included | `INCLUDE_ALL_CRITERIA_PASS` | All Level 1 criteria pass |

**PDF evidence (ULMC):**

> Lastly, adopting the unmeasured latent method factor approach, we added a latent common method factor into the hypothesized seven-factor model. Although the model's fit was slightly improved … the changes in these values were not particularly significant … Consequently, common method bias in our study does not appear to be a serious concern.

**Your check:** Confirm include, or reply `M0183 exclude` / `M0183 exclude_pls` with a note if you disagree.

---

## 2. M0244 — low-confidence **manual_review** (EBSCO #63)

**Title:** Beyond coexistence: the asymmetric interplay of health risk and promotion pathways driven by communication legacies across emerging and recurring epidemics.

**Codified reasons:**

| Criterion | Pass? | Code | Text |
|-----------|-------|------|------|
| Q1.1 Domain | ✓ (borderline) | `DOMAIN_BORDERLINE_PUBLIC_HEALTH` | Public health / epidemics framing — verify management-domain scope |
| Q1.2 ULMC | ✓ | `ULMC_PASS_EMPIRICAL` | empirical ULMC detected |
| Q1.3 Not PLS | ✓ | `PLS_PASS_NOT_DETECTED` | no PLS-SEM detected |
| **Decision** | manual_review | `MANUAL_REVIEW_DOMAIN_BORDERLINE_PUBLIC_HEALTH` | Q1.1–Q1.3 auto-pass but public-health domain borderline — **not excluded** |

**Why flagged (not rejected):** Frontiers in Public Health; epidemic/communication framing. Automation passes all criteria at low confidence; human must confirm whether public-health communication studies belong in scope.

**PDF evidence (ULMC):**

> … an unmeasured latent factor (ULF) was added to the measurement model. The results showed that including this method factor did not substantially improve model fit indices (Δ RMSEA < 0.01) … these findings suggest that common method bias is not a serious concern in this study.

**Your check:** `M0244 include` if you accept public-health communication studies; `M0244 exclude` if domain should be management-only.

---

## 3. M0282 — low-confidence **manual_review** (EBSCO #102)

**Title:** Flourishing and its influencing factor in inflammatory bowel disease patients: a latent profile analysis.

**Codified reasons:**

| Criterion | Pass? | Code | Text |
|-----------|-------|------|------|
| Q1.1 Domain | ✓ (borderline) | `DOMAIN_BORDERLINE_CLINICAL_PATIENTS` | Clinical patient sample — verify organizational vs. clinical scope |
| Q1.2 ULMC | ✓ | `ULMC_PASS_EMPIRICAL` | empirical ULMC detected |
| Q1.3 Not PLS | ✓ | `PLS_PASS_NOT_DETECTED` | no PLS-SEM detected |
| **Decision** | manual_review | `MANUAL_REVIEW_DOMAIN_BORDERLINE_CLINICAL_PATIENTS` | Q1.1–Q1.3 auto-pass but clinical-patient sample borderline — **not excluded** |

**Why flagged (not rejected):** IBD patient sample (Frontiers in Psychiatry). ULMC present; domain/sample is borderline vs. organizational research.

**PDF evidence (ULMC):**

> … the Harman single-factor method and the unmeasured latent method factor analysis (ULMC) were employed to assess such biases within the scale items. A variance contribution rate of less than 40% for the first factor indicated that common method bias was not severe.

**Your check:** `M0282 include` if health/work-adjacent samples count; `M0282 exclude` if clinical-only studies are out of scope.

---

## Reason code reference

**Q1.1 domain codes:** `DOMAIN_PASS_JOURNAL_OUTLET`, `DOMAIN_PASS_KEYWORDS_METADATA`, `DOMAIN_PASS_KEYWORDS_INTRO`, `DOMAIN_FAIL_*`, `DOMAIN_BORDERLINE_PUBLIC_HEALTH`, `DOMAIN_BORDERLINE_CLINICAL_PATIENTS`, `DOMAIN_BORDERLINE_STUDENT_SAMPLE`, …

**Q1.2 ULMC codes:** `ULMC_PASS_EMPIRICAL`, `ULMC_FAIL_HARMAN_ONLY`, `ULMC_FAIL_MARKER_ONLY`, `ULMC_FAIL_NOT_MENTIONED`, `ULMC_AMBIGUOUS`, …

**Q1.3 PLS codes:** `PLS_PASS_NOT_DETECTED`, `PLS_FAIL_SEM_DETECTED`

**Q1.4 retraction codes:** `RETRACTION_FAIL_PUBLISHER` (title/metadata/PDF retraction notice)

**Decision codes:** `INCLUDE_ALL_CRITERIA_PASS`, `EXCLUDE_RETRACTED`, `EXCLUDE_Q1_1_DOMAIN`, `EXCLUDE_Q1_2_ULMC`, `EXCLUDE_Q1_3_PLS`, `MANUAL_REVIEW_DOMAIN_BORDERLINE_*`, `MANUAL_REVIEW_LOW_CONFIDENCE_ALL_PASS`, `MANUAL_REVIEW_ULMC_AMBIGUOUS`

---

## Optional high-confidence **exclude** (PLS)

**M0281** (EBSCO #101) — `EXCLUDE_Q1_3_PLS`, high confidence. Machiavellian leadership paper uses ULMC *and* PLS-SEM (Q1.3 fail). Snippet in `ebsco_150_screening_evidence.csv`.

---

## After you decide

```bash
# Chat: e.g. "M0244 exclude"
python3 review/EBSCO/apply_classification_feedback.py
python3 review/master/progress_counter.py
```

Full worklist evidence: `review/EBSCO/ebsco_150_screening_evidence.csv` (145 rows, all with `decision_reason_code` + `decision_reason_text`).
