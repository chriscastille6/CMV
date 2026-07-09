# TMGT Effects Under Common Method Variance: Monte Carlo Simulation

This folder extends the CMV simulation logic described in Siemsen, Roth, and Oliveira (2010) to **Too-Much-of-a-Good-Thing (TMGT)** hypotheses—nonlinear (quadratic) and moderated-quadratic effects such as the ambivert advantage in sales (Grant, 2013).

## Motivation

Siemsen et al. (2010) demonstrated that CMV cannot *create* quadratic or interaction effects, but it can **deflate** them—making true effects harder to detect (Type II error). Our manuscript (`Blinded Manuscript.Rmd`) cites this finding for linear interaction effects. **Moderated TMGT effects under CMV have not been studied.**

This simulation quantifies:

| Error type | Question |
|------------|----------|
| **Type I** | When no true quadratic / moderated-quadratic effect exists, how often does CMV-contaminated same-source data produce spurious significant TMGT terms? |
| **Type II** | When a true inverted-U (or W-shifted peak) exists, how often does CMV cause failure to detect it? |

## Conceptual model

### Substantive (latent) TMGT model

```
Y* = β₀ + β₁X* + β₂(X*)² + β₃W* + β₄X*W* + β₅(X*)²W* + ε
```

- **X*** = focal predictor (e.g., extraversion)
- **W*** = moderator shifting the optimal level (e.g., autonomy, social demand of the role)
- **β₂ < 0** with **β₁ > 0** = inverted-U (ambivert advantage)
- **β₅ ≠ 0** = the "ideal" peak of X* depends on W*

### CMV contamination (Siemsen-style)

Each construct is measured by `k` indicators sharing a common method factor **M**:

```
item_ij = λ_trait · F* + λ_method · M + ε_ij
```

Manipulated conditions:

- `cmv_prop` — proportion of indicator variance due to M (0, .25, .50; review mean ≈ .48)
- `rho_m_x`, `rho_m_y`, `rho_m_w` — correlations between M and latent constructs (symmetry vs. asymmetry)
- `same_source` — whether X, W, and Y share M (same-source) or Y is method-free (split-source benchmark)

## Files

| File | Purpose |
|------|---------|
| `R/tmgt_cmv_dgp.R` | Data-generating process (latent TMGT + CMV indicators) |
| `R/tmgt_cmv_analysis.R` | Fit and test regression models on scale scores |
| `run_tmgt_cmv_simulation.R` | Monte Carlo driver; produces CSV results |
| `config/tmgt_scenarios.R` | Named scenarios (null, simple TMGT, moderated TMGT) |

## Ambiversion power study (large N × measurement approaches)

```bash
Rscript simulations/run_ambiversion_power_study.R          # full (N = 340–5000)
Rscript simulations/run_ambiversion_power_study.R --pilot  # quick test
Rscript simulations/summarize_ambiversion_power.R
```

### Measurement approaches compared

| Approach | Description |
|----------|-------------|
| `grant` | Standard cumulative Likert (Grant 4-item) |
| `unfolding_midrange` | Ideal-point items peaking at ambivert level (τ = 0) |
| `unfolding_spread` | Ideal-point items spread around midrange |
| `unfolding_extremes` | Ideal-point items at intro/extreme poles |
| `unfolding_mixed` | Half cumulative + half unfolding midrange |
| `facet_cumulative` | Assertiveness + enthusiasm summed (Big Five style) |
| `facet_balance` | Facet score penalizing assertiveness–enthusiasm imbalance |

**Note:** Unfolding items are scored via item means for comparability with typical TMGT regression practice. Ideal-point IRT scoring would be the next extension.

## Usage (TMGT-CMV study)

```r
# From repository root
source("simulations/run_tmgt_cmv_simulation.R")

# Quick pilot (100 replications)
results <- run_tmgt_cmv_study(
  n_reps = 100,
  n = 200,
  scenarios = c("null_tmgt", "simple_tmgt", "moderated_tmgt"),
  cmv_conditions = expand.grid(cmv_prop = c(0, 0.25, 0.5), same_source = c(TRUE, FALSE))
)
```

Full study defaults to 1,000 replications per cell. Results are written to `simulations/output/`.

## Scenarios

| Scenario | β₂ | β₅ | Interpretation |
|----------|----|----|----------------|
| `null_tmgt` | 0 | 0 | Linear-only world; tests Type I for spurious curvature |
| `simple_tmgt` | −0.15 | 0 | Ambivert advantage without moderation |
| `moderated_tmgt` | −0.15 | −0.05 | Peak extraversion shifts with W |
| `ideal_tmgt` | −0.25 | 0 | Strong, easily detectable inverted-U (upper bound) |

## References

- Siemsen, E., Roth, A. V., & Oliveira, P. (2010). Common method bias in regression models with linear, quadratic, and interaction effects. *Organizational Research Methods*, 13(3), 456–476.
- Grant, A. M. (2013). Rethinking the extraverted sales rep: The ambivert advantage. *Psychological Science*, 24(6), 1024–1030.
