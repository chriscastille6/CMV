# PROSPERO + OSF preregistration — manual next steps

**Draft ready:** [`PROSPERO_DRAFT_REGISTRATION_FINAL.md`](PROSPERO_DRAFT_REGISTRATION_FINAL.md) (v3.1)  
**OSF project:** https://osf.io/x9643/overview  
**OSA config:** [`open_science_config.yml`](open_science_config.yml)

---

## What you must do (in order)

### A. PROSPERO submission (required — not automated)

1. **Create account / log in:** https://www.crd.york.ac.uk/prospero/
2. **Start new registration** → systematic review of interventions / methods (select review type that fits methodological practices review).
3. **Copy-paste** from `PROSPERO_DRAFT_REGISTRATION_FINAL.md` field by field. Pay special attention to:
   - **Field 5** — restart narrative (DistillerSR ~182 → prospective EBSCO re-screen)
   - **Field 12** — narrow ULMC search string (2010–2026; English; peer-reviewed)
   - **Field 22** — risk of bias: **not used** (dropped per protocol)
   - **Fields 29–33** — OSF link `https://osf.io/x9643/overview`; prior RPHRM (2024) pilot; novelty vs. Castille & Williams (2024)
4. **Submit** for editorial review (typically 5–10 business days).
5. **When PROSPERO assigns CRD… number:** add to `open_science_config.yml` under `registries:` and to `PRISMA_PROTOCOL.md` Protocol History.

### B. OSF backup preregistration (recommended)

1. **OSF personal access token (OSF_PAT):** https://osf.io/settings/tokens — create if needed.
2. **Upload to project x9643:**
   - `PROSPERO_DRAFT_REGISTRATION_FINAL.md`
   - `PRISMA_PROTOCOL.md`
   - `SEARCH_STRATEGY_REPRODUCIBILITY.md`
   - `config.yaml`
3. **Optional — Open Science Agents prereg draft:**
   ```bash
   # OPENAI_API_KEY must be in ~/.Renviron AND reticulate Python needs: pip install openai
   cd "/Users/ccastille/Documents/GitHub/Open Science Agents"
   Rscript scripts/run_orchestrator.R \
     --config "/Users/ccastille/Documents/GitHub/CMV/review/open_science_config.yml" \
     --agent prereg
   ```
   **Last run (2026-06-26):** filled preregistration generated locally (no LLM/API required):
   ```bash
   python3 review/scripts/build_preregistration_json.py
   ```
   Outputs: `review/artifacts/reports/preregistration_filled.json`, `prereg_agent_filled.json`. Paste source: `OSF_REGISTRATION_PASTE.md`. OSA LLM fill optional (`openai` installed in OSA venv; API hung in test). **OSF_PAT not required** for local draft generation.

### C. Pre-submit reconciliation checklist

| Item | Action |
|------|--------|
| Date range | Confirm **2010–2026** in PROSPERO Field 12 matches `SEARCH_STRATEGY_REPRODUCIBILITY.md` |
| `content_domain` | Use `content_domain` (not legacy `industry_sector`) in extraction wording — §20 updated |
| Pilot N | ~185 RPHRM training vs 182 legacy holdout — keep Field 5 wording |
| PLS policy | PLS-SEM studies excluded from primary synthesis; tracked separately (Field 14–15) |
| EBSCO L1 pilot | 145 PDFs screened — see `EBSCO/ebsco_150_screening_evidence.csv` |

### D. After PROSPERO approval

1. Add PROSPERO URL to OSF project description and `PRISMA_PROTOCOL.md`.
2. Clear manual L1 queue: `EBSCO/VERIFICATION_SAMPLE.md` → `classification_feedback.csv` → `apply_classification_feedback.py`.
3. Proceed with full extraction on included EBSCO cohort (beyond legacy 182 holdout).

---

## Files referenced

| File | Purpose |
|------|---------|
| `PROSPERO_DRAFT_REGISTRATION_FINAL.md` | PROSPERO paste source |
| `PRISMA_PROTOCOL.md` | Full protocol |
| `PREREGISTRATION_PLAN.md` | Pilot-informed hypotheses |
| `EBSCO/VERIFICATION_SAMPLE.md` | 3-paper sanity check before queue clearance |
| `EBSCO/classification_feedback.csv` | Your include/exclude decisions |
