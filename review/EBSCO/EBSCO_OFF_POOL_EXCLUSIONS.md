# EBSCO export-only rows — now in master

**Updated:** 2026-06-26

Positions **21, 89, 148, 149, 150** (strand 1–150) and **32 off-pool positions in 151–200** from the 06_26_2026 native search-order export were previously absent from `articles_master.csv`. **Option A (2026-06-26):** all are now master rows with Level 1 decisions applied.

## Positions 1–150 (M0720–M0724)

| EBSCO # | master_id | DOI | Decision | Reason | PDF |
|--------:|-----------|-----|----------|--------|-----|
| 21 | M0720 | [10.1155/jonm/2207579](https://doi.org/10.1155/jonm/2207579) | **Included** | Borderline OB/nursing management (OD → stress → depersonalization) | `pdfs/imports/Mollet_2026_jonm_2207579.pdf` |
| 89 | M0721 | [10.1039/d5rp00404g](https://doi.org/10.1039/d5rp00404g) | **Excluded** | Q1.1 domain: K-12 chemistry education | — |
| 148 | M0722 | [10.3389/fpsyg.2025.1662636](https://doi.org/10.3389/fpsyg.2025.1662636) | **Excluded** | Q1.1 domain: adaptive sports/disability | — |
| 149 | M0723 | [10.1186/s40359-025-03570-7](https://doi.org/10.1186/s40359-025-03570-7) | **Excluded (PLS)** | PLS-SEM substantive focus; routine CMV only | `pdfs/imports/Lin_2025_s40359-025-03570-7.pdf` |
| 150 | M0724 | [10.1007/s43621-025-02087-8](https://doi.org/10.1007/s43621-025-02087-8) | **Excluded** | Q1.1 domain: student financial literacy (Tanzania) | — |

Add script: `review/EBSCO/add_export_only_master_rows.py`

## Positions 151–200 (M0725–M0756)

**Canonical source:** `imports/EBSCO-Metadata-06_26_2026-4.csv` (50 rows). All 50 positions now have a master row. PRISMA strand 151–200 reports **50 assessed**, **0 off-pool removed**.

Add script: `review/EBSCO/add_export_only_master_rows_151_200.py`

### L1 summary (32 export-only rows added)

| Decision | Count | Positions |
|----------|------:|-----------|
| **Included** | 21 | 153, 160, 162, 163, 167, 168, 169, 170, 172, 176, 178, 182, 186, 187, 188, 189, 191, 192, 193, 194, 195 |
| **Excluded** | 9 | 151, 152, 155, 171, 173, 174, 190, 196, 199 |
| **Excluded (PLS)** | 2 | 154, 165 |

### Export-only registry (M0725–M0756)

| EBSCO # | master_id | DOI | Decision | Reason |
|--------:|-----------|-----|----------|--------|
| 151 | M0725 | 10.3389/fpubh.2025.1649455 | **Excluded** | Public health (herpes zoster vaccination) |
| 152 | M0726 | 10.3389/fpsyg.2025.1661379 | **Excluded** | Higher-ed teaching effectiveness |
| 153 | M0727 | 10.3389/fpsyg.2025.1646817 | **Included** | Employee narcissism → creativity (OB) |
| 154 | M0728 | 10.3390/systems13100905 | **Excluded (PLS)** | PLS-SEM CSR/compliance |
| 155 | M0729 | 10.3390/bioengineering12101056 | **Excluded** | LLM / academic success (education) |
| 160 | M0730 | 10.1080/24721840.2023.2242391 | **Included** | Air-traffic-controller job satisfaction |
| 162 | M0731 | 10.1080/09585192.2025.2458281 | **Included** | Resilient workforce (IHRM) |
| 163 | M0732 | 10.1007/s10490-024-09956-2 | **Included** | Stretch-goal double-edged sword |
| 165 | M0733 | 10.1080/13527266.2025.2518456 | **Excluded (PLS)** | PLS consumer marketing |
| 167 | M0734 | 10.1111/beer.12659 | **Included** | Moral licensing / work engagement |
| 168 | M0735 | 10.5281/zenodo.15824866 | **Included** | Supplier orientation SME |
| 169 | M0736 | 10.1371/journal.pone.0290849 | **Included** | Lean startup / entrepreneurial performance |
| 170 | M0737 | 10.1080/08959285.2023.2222272 | **Included** | Team effectiveness (configurational) |
| 171 | M0738 | 10.1186/s12888-023-04982-8 | **Excluded** | Clinical adolescent sample (psychiatry) |
| 172 | M0739 | 10.3389/fpsyg.2025.1592148 | **Included** | Leader humility → proactivity |
| 173 | M0740 | 10.3389/fpsyg.2025.1644701 | **Excluded** | Clinical depression profiles |
| 174 | M0741 | 10.1186/s40359-025-03299-3 | **Excluded** | K-12 kindergarten teachers |
| 176 | M0742 | 10.1155/hbe2/8886180 | **Included** | Remote-work e-skill self-efficacy |
| 178 | M0743 | 10.1186/s40359-025-03239-1 | **Included** | Workplace cyberbullying |
| 182 | M0744 | 10.1186/s40359-025-03077-1 | **Included** | Role stress → work engagement |
| 186 | M0745 | 10.1177/21582440251376462 | **Included** | Psychological contract breach / LMX |
| 187 | M0746 | 10.1155/2024/5522654 | **Included** | Borderline OB/nursing presenteeism |
| 188 | M0747 | 10.1111/apps.12408 | **Included** | Team personality / innovation |
| 189 | M0748 | 10.1111/jan.16120 | **Included** | Workplace mistreatment (nursing) |
| 190 | M0749 | 10.15244/pjoes/156789 | **Excluded** | Residents' waste separation (consumer/env) |
| 191 | M0750 | 10.1080/02642069.2023.2270924 | **Included** | Abusive supervision |
| 192 | M0751 | 10.1080/09585192.2025.2492129 | **Included** | Perceived overqualification |
| 193 | M0752 | 10.1111/padm.13011 | **Included** | Leader empowering / public admin |
| 194 | M0753 | 10.1007/s10551-024-05709-9 | **Included** | Mindfulness / unethical behavior |
| 195 | M0754 | 10.1080/13678868.2023.2268488 | **Included** | HPWS / employee performance |
| 196 | M0755 | 10.3389/fpsyt.2025.1554239 | **Excluded** | Clinical bariatric-surgery patients |
| 199 | M0756 | 10.1057/s41270-025-00399-2 | **Excluded** | Marketing analytics / item-level CMV |

**18 pre-existing in-pool rows** (positions 156–200 with master IDs before this batch) remain unchanged; see `missed_in_ebsco_151_200.csv` for in-pool PDF gaps.

## Run order (important)

`merge_sources.py` rebuilds master from registry and **does not** add export-only rows. After merge, re-run both add scripts:

```bash
python3 review/EBSCO/add_export_only_master_rows.py
python3 review/EBSCO/add_export_only_master_rows_151_200.py
python3 review/master/progress_counter.py
```

## Related

- Worklist rule: [`EBSCO_PRIMARY_WORKLIST.md`](EBSCO_PRIMARY_WORKLIST.md)
- Positions 1–150 status: [`MISSED_IN_FIRST_150.md`](MISSED_IN_FIRST_150.md)
- Batch 4 vs batch 5: [`EBSCO_METADATA_06_26_2026_COMPARISON.md`](EBSCO_METADATA_06_26_2026_COMPARISON.md)
