# EBSCO On-Hand PDF Examination Cohort

**Generated**: 2026-06-30
**Cohort size**: 178 articles

## Purpose

Live examination cohort for the EBSCO June 2026 search strand. The original
systematic review (**legacy 182**) is held out for replication and must **not**
be merged into this cohort or `systematic_extraction_ebsco_on_hand.csv`.

## Inclusion rules

1. Row in `review/master/articles_master.csv` with `has_pdf=True` (or non-empty `pdf_path`)
2. PDF file exists on disk under `review/EBSCO/pdfs/`
3. EBSCO 570 pool membership (`ebsco_screening_pool_570.csv`) **or** `ebsco_2026` / `ebsco` in `sources`

## Exclusion rules

1. `legacy_final_include=TRUE`
2. Non-empty `legacy_refid` (original 182 studies)
3. `corpus_tier=legacy_gold` or legacy-only `fully_coded` from prior extraction

## Current status snapshot

| Metric | Count |
|--------|------:|
| Cohort N | 178 |
| screening_status=excluded_pls | 33 |
| screening_status=included | 93 |
| screening_status=level1_fail | 47 |
| screening_status=manual_review | 2 |
| screening_status=pending | 3 |
| examination_status=fully_coded | 80 |
| examination_status=not_read | 91 |
| examination_status=partially_coded | 1 |
| examination_status=pdf_missing | 1 |
| examination_status=read_snippet_only | 5 |

## Output files

- `review/EBSCO/examination_cohort_on_hand.csv` — machine-readable cohort list
- `review/EBSCO/systematic_extraction_ebsco_on_hand.csv` — new extractions (separate from legacy)

## master_id list

Total: **178**

```
M0183, M0184, M0185, M0186, M0187, M0188, M0189, M0190, M0191, M0192, M0193, M0194, M0195, M0196, M0197, M0198, M0199, M0200, M0201, M0202, M0203, M0204, M0205, M0206, M0207, M0208, M0209, M0210, M0211, M0212, M0213, M0214, M0215, M0216, M0217, M0218, M0219, M0220, M0221, M0222, M0223, M0224, M0225, M0226, M0227, M0228, M0229, M0230, M0231, M0232, M0233, M0234, M0235, M0236, M0237, M0238, M0239, M0240, M0241, M0242, M0243, M0244, M0245, M0246, M0247, M0248, M0249, M0250, M0251, M0252, M0253, M0254, M0255, M0256, M0257, M0258, M0259, M0260, M0261, M0262, M0263, M0264, M0265, M0266, M0267, M0268, M0269, M0270, M0271, M0272, M0273, M0274, M0275, M0276, M0277, M0278, M0279, M0280, M0281, M0282, M0283, M0284, M0285, M0286, M0287, M0288, M0289, M0290, M0291, M0292, M0293, M0294, M0295, M0296, M0297, M0298, M0299, M0300, M0301, M0302, M0303, M0304, M0305, M0306, M0307, M0308, M0309, M0310, M0311, M0312, M0313, M0314, M0315, M0316, M0317, M0318, M0319, M0320, M0321, M0322, M0323, M0324, M0325, M0326, M0327, M0353, M0400, M0427, M0428, M0429, M0430, M0431, M0474, M0479, M0613, M0675, M0679, M0720, M0723, M0726, M0727, M0728, M0729, M0730, M0731, M0732, M0733, M0734, M0735, M0736, M0737, M0738, M0739, M0740, M0741, M0743, M0745, M0746
```
