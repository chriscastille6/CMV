# Analysis and hypothesis testing for TMGT models under CMV

ALPHA <- 0.05

#' Fit TMGT regression models on observed scale scores
fit_tmgt_models <- function(df) {
  m_linear <- stats::lm(Y ~ X + W + XW, data = df)
  m_quadratic <- stats::lm(Y ~ X + X2 + W + XW, data = df)
  m_tmgt <- stats::lm(Y ~ X + X2 + W + XW + X2W, data = df)

  list(
    linear = m_linear,
    quadratic = m_quadratic,
    tmgt = m_tmgt
  )
}

#' Extract coefficient p-values for key TMGT terms
extract_tmgt_pvalues <- function(models) {
  p_quadratic <- function(m) {
    s <- summary(m)$coefficients
    if (!"X2" %in% rownames(s)) {
      return(NA_real_)
    }
    s["X2", "Pr(>|t|)"]
  }

  p_mod_quad <- function(m) {
    s <- summary(m)$coefficients
    if (!"X2W" %in% rownames(s)) {
      return(NA_real_)
    }
    s["X2W", "Pr(>|t|)"]
  }

  list(
    p_X2_linear_model = p_quadratic(models$linear),
    p_X2_quadratic_model = p_quadratic(models$quadratic),
    p_X2_tmgt_model = p_quadratic(models$tmgt),
    p_X2W_tmgt_model = p_mod_quad(models$tmgt),
    p_XW_linear_model = summary(models$linear)$coefficients["XW", "Pr(>|t|)"],
    p_XW_tmgt_model = summary(models$tmgt)$coefficients["XW", "Pr(>|t|)"]
  )
}

#' Extract standardized-ish effect estimates for bias tracking
extract_tmgt_estimates <- function(models) {
  coef_safe <- function(m, term) {
    cf <- coef(m)
    if (!term %in% names(cf)) {
      return(NA_real_)
    }
    cf[[term]]
  }

  list(
    b_X2_tmgt = coef_safe(models$tmgt, "X2"),
    b_X2W_tmgt = coef_safe(models$tmgt, "X2W"),
    b_X_tmgt = coef_safe(models$tmgt, "X"),
    r2_tmgt = summary(models$tmgt)$r.squared,
    r2_linear = summary(models$linear)$r.squared
  )
}

#' Run one replication: generate data, fit models, return test outcomes
run_one_replication <- function(n, scenario, cmv_settings, n_items = 4) {
  sim <- generate_tmgt_cmv_data(
    n = n,
    scenario = scenario,
    cmv_prop = cmv_settings$cmv_prop,
    same_source = cmv_settings$same_source,
    rho_m_x = cmv_settings$rho_m_x,
    rho_m_y = cmv_settings$rho_m_y,
    rho_m_w = cmv_settings$rho_m_w,
    n_items = n_items
  )

  df <- prepare_analysis_data(sim)
  models <- fit_tmgt_models(df)
  pvals <- extract_tmgt_pvalues(models)
  ests <- extract_tmgt_estimates(models)

  c(
    sig_X2_tmgt = as.integer(!is.na(pvals$p_X2_tmgt_model) && pvals$p_X2_tmgt_model < ALPHA),
    sig_X2W_tmgt = as.integer(!is.na(pvals$p_X2W_tmgt_model) && pvals$p_X2W_tmgt_model < ALPHA),
    sig_X2_quadratic = as.integer(!is.na(pvals$p_X2_quadratic_model) && pvals$p_X2_quadratic_model < ALPHA),
    sig_XW_tmgt = as.integer(!is.na(pvals$p_XW_tmgt_model) && pvals$p_XW_tmgt_model < ALPHA),
    pvals,
    ests
  )
}

#' Classify replication outcome relative to population truth
classify_errors <- function(row, scenario) {
  true_quadratic <- scenario$b2 != 0
  true_mod_quad <- scenario$b5 != 0

  type1_X2 <- if (!true_quadratic) row[["sig_X2_tmgt"]] else NA
  type2_X2 <- if (true_quadratic) 1 - row[["sig_X2_tmgt"]] else NA

  type1_X2W <- if (!true_mod_quad) row[["sig_X2W_tmgt"]] else NA
  type2_X2W <- if (true_mod_quad) 1 - row[["sig_X2W_tmgt"]] else NA

  c(
    type1_X2 = type1_X2,
    type2_X2 = type2_X2,
    type1_X2W = type1_X2W,
    type2_X2W = type2_X2W
  )
}
