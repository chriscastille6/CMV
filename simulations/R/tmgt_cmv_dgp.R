# Data-generating process for TMGT effects with CMV contamination
# Extends Siemsen et al. (2010) to quadratic and moderated-quadratic models

#' Transform latent X to simulate measurement that loses midrange discrimination
apply_x_transform <- function(x, transform = "none") {
  switch(
    transform,
    none = x,
    compressed = tanh(x * 1.5) / 1.5,
    skewed = x + 0.30 * x^2,
    x
  )
}

#' Generate latent TMGT data
#'
#' Population model:
#' Y = b0 + b1*X + b2*X^2 + b3*W + b4*X*W + b5*X^2*W + error
generate_latent_tmgt <- function(n, scenario, measurement = NULL) {
  X <- stats::rnorm(n)
  W <- stats::rnorm(n)

  if (!is.null(scenario$rho_xw) && scenario$rho_xw != 0) {
    W <- scenario$rho_xw * X + sqrt(1 - scenario$rho_xw^2) * W
  }

  x_transform <- "none"
  if (!is.null(measurement) && !is.null(measurement$x_transform)) {
    x_transform <- measurement$x_transform
  }
  X_observed <- apply_x_transform(X, x_transform)

  Y <- scenario$b0 +
    scenario$b1 * X +
    scenario$b2 * X^2 +
    scenario$b3 * W +
    scenario$b4 * X * W +
    scenario$b5 * X^2 * W +
    stats::rnorm(n, sd = scenario$sd_y)

  list(X = X_observed, W = W, Y = Y, X_latent = X)
}

#' Build a method factor optionally correlated with latent constructs
generate_method_factor <- function(n, rho_m_x, rho_m_y, rho_m_w) {
  M <- stats::rnorm(n)
  e_x <- stats::rnorm(n)
  e_y <- stats::rnorm(n)
  e_w <- stats::rnorm(n)

  M_x <- rho_m_x * M + sqrt(pmax(0, 1 - rho_m_x^2)) * e_x
  M_y <- rho_m_y * M + sqrt(pmax(0, 1 - rho_m_y^2)) * e_y
  M_w <- rho_m_w * M + sqrt(pmax(0, 1 - rho_m_w^2)) * e_w

  list(
    M = M,
    M_x = M_x,
    M_y = M_y,
    M_w = M_w
  )
}

#' Create k indicators for a latent construct with CMV contamination
make_indicators <- function(latent, method_component, cmv_prop, n_items = 4,
                            substantive_loading = NULL) {
  n <- length(latent)
  if (is.null(substantive_loading)) {
    substantive_loading <- sqrt(pmax(0.05, 1 - cmv_prop) * 0.75)
  }

  method_loading <- sqrt(cmv_prop)
  residual_sd <- sqrt(pmax(0.01, 1 - substantive_loading^2 - method_loading^2))

  items <- matrix(NA_real_, n, n_items)
  for (j in seq_len(n_items)) {
    items[, j] <- substantive_loading * latent +
      method_loading * method_component +
      stats::rnorm(n, sd = residual_sd)
  }

  items
}

#' Full DGP: latent TMGT + CMV-contaminated indicators
generate_tmgt_cmv_data <- function(n, scenario, cmv_prop = 0,
                                   same_source = TRUE,
                                   rho_m_x = 0, rho_m_y = 0, rho_m_w = 0,
                                   n_items = 4, substantive_loading = NULL,
                                   measurement = NULL) {
  latents <- generate_latent_tmgt(n, scenario, measurement = measurement)

  if (!is.null(measurement)) {
    if (!is.null(measurement$n_items)) {
      n_items <- measurement$n_items
    }
    if (!is.null(measurement$substantive_loading)) {
      substantive_loading <- measurement$substantive_loading
    }
  }
  method <- generate_method_factor(n, rho_m_x, rho_m_y, rho_m_w)

  m_x <- if (same_source) method$M_x else stats::rnorm(n)
  m_w <- if (same_source) method$M_w else stats::rnorm(n)
  m_y <- if (same_source) method$M_y else stats::rnorm(n)

  x_items <- make_indicators(
    latents$X, m_x, cmv_prop, n_items, substantive_loading
  )
  w_items <- make_indicators(
    latents$W, m_w, cmv_prop, n_items, substantive_loading
  )
  y_items <- make_indicators(
    latents$Y, m_y, cmv_prop, n_items, substantive_loading
  )

  list(
    latents = latents,
    X_items = x_items,
    W_items = w_items,
    Y_items = y_items,
    settings = list(
      n = n,
      cmv_prop = cmv_prop,
      same_source = same_source,
      rho_m_x = rho_m_x,
      rho_m_y = rho_m_y,
      rho_m_w = rho_m_w,
      n_items = n_items
    )
  )
}

#' Collapse indicators to scale scores (mean of standardized items)
scale_scores_from_items <- function(items) {
  z_items <- scale(items)
  rowMeans(z_items, na.rm = TRUE)
}

#' Prepare analysis-ready data frame from simulated indicators
prepare_analysis_data <- function(sim_data) {
  X <- scale_scores_from_items(sim_data$X_items)
  W <- scale_scores_from_items(sim_data$W_items)
  Y <- scale_scores_from_items(sim_data$Y_items)

  X_c <- scale(X, center = TRUE, scale = FALSE)[, 1]
  W_c <- scale(W, center = TRUE, scale = FALSE)[, 1]
  X2_c <- X_c^2
  XW_c <- X_c * W_c
  X2W_c <- X2_c * W_c

  data.frame(
    Y = Y,
    X = X_c,
    X2 = X2_c,
    W = W_c,
    XW = XW_c,
    X2W = X2W_c
  )
}

#' Optimal X level for simple TMGT (when b4 = b5 = 0 and b2 != 0)
tmgt_optimal_x <- function(scenario) {
  if (scenario$b2 == 0) {
    return(NA_real_)
  }
  -scenario$b1 / (2 * scenario$b2)
}

#' Optimal X level as function of W for moderated TMGT
tmgt_optimal_x_given_w <- function(scenario, w = 0) {
  denom <- 2 * scenario$b2 + 2 * scenario$b5 * w
  if (denom == 0) {
    return(NA_real_)
  }
  -(scenario$b1 + scenario$b4 * w) / denom
}
