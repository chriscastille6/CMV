# TMGT-CMV Simulation Handoff

Branch: `cursor/tmgt-cmv-simulation-9773`  
Repo: https://github.com/chriscastille6/CMV  
PR: https://github.com/chriscastille6/CMV/pull/12

## Get it on your computer

```bash
cd /path/to/CMV   # or clone fresh:
# git clone https://github.com/chriscastille6/CMV.git && cd CMV

git fetch origin
git checkout cursor/tmgt-cmv-simulation-9773
git pull origin cursor/tmgt-cmv-simulation-9773
```

Requires R (base). Optional: `mirt` for full Carter GRM scoring (not required to run main studies).

## Run simulations locally

```bash
# TMGT + CMV Type I/II (extended study, ~15 min)
Rscript simulations/run_tmgt_cmv_simulation.R --extended

# Ambiversion power: large N × unfolding/facet measurement (~15 min)
Rscript simulations/run_ambiversion_power_study.R

# Carter et al. (2017) Study 2 partial replication (~5 min)
Rscript simulations/run_carter_replication.R

# Summaries
Rscript simulations/summarize_results.R
Rscript simulations/summarize_ambiversion_power.R
```

Results CSVs from cloud runs are in `simulations/output/results/` (committed).
Fresh runs still write timestamped files to `simulations/output/` (gitignored).

## What's included

| File | Purpose |
|------|---------|
| `simulations/R/tmgt_cmv_dgp.R` | TMGT + CMV data generation |
| `simulations/R/tmgt_cmv_analysis.R` | Regression tests, Type I/II |
| `simulations/R/carter_grm_irt.R` | Carter GRM replication utilities |
| `simulations/config/tmgt_scenarios.R` | Grant, null, TMGT scenarios |
| `simulations/run_tmgt_cmv_simulation.R` | Main CMV Monte Carlo |
| `simulations/run_ambiversion_power_study.R` | N × measurement power study |
| `simulations/run_carter_replication.R` | Carter Study 2 replication |
| `simulations/README.md` | Full documentation |

## Key findings (cloud run, 1000 reps/cell unless noted)

### Grant power at N = 340
- Post-hoc from published t = 2.71: **~77% power** (α = .05)
- A priori from ΔR² = .02: **~87% power**
- MC with controls + 7pt scale: **~82%**

### TMGT + CMV (Grant b₂ = −0.14, N = 340)
| CMV | Power (cumulative sum-score) |
|-----|------------------------------|
| 0%  | 50% |
| 25% | 25% |
| 50% | 15% |

### Ambiversion measurement (N = 340, CMV = 0%)
| Approach | Power |
|----------|-------|
| Cumulative (Grant 4-item) | 55% |
| Facet cumulative | 50% |
| Unfolding midrange (sum-scored) | 7% |

Unfolding items require IRT scoring (Carter et al., 2017), not sum-scores.

### Carter Study 2 replication (500 reps, extreme IPIP-like items)
| Condition | Sum-score | GRM (oracle θ) |
|-----------|-----------|----------------|
| Type I (linear Y, N = 500) | 18–57% | ~5% |
| Grant TMGT (b₂ = −.14, N = 340) | 45% | 92% |

Carter target Type I for sum-score: **28%**. Mechanism replicates.

## References
- Carter, N. T., et al. (2017). IRT scoring and curvilinearity. *Psychological Methods*, 22(1), 191–203.
- Grant, A. M. (2013). The ambivert advantage. *Psychological Science*, 24(6), 1024–1030.
- Siemsen, E., et al. (2010). CMV in regression with quadratic/interaction effects. *ORM*, 13(3), 456–476.
