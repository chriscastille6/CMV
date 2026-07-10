# Carter et al. (2017) GRM simulation and scoring utilities
# Psychological Methods, 22(1), 191-203. doi:10.1037/met0000101
#
# Partial R replication of Study 2 (dominance generating model).
# Uses Samejima GRM for data generation and EAP for GRM person scoring.

#' GRM probability of responding in category k or higher
grm_prob_ge_k <- function(theta, a, b_k) {
  1 / (1 + exp(-a * (theta - b_k)))
}

#' Simulate one person's GRM item responses
simulate_grm_person <- function(theta, item_params) {
  n_items <- length(item_params$a)
  n_cat <- item_params$n_cat
  responses <- integer(n_items)

  for (i in seq_len(n_items)) {
    a <- item_params$a[i]
    b <- item_params$b[i, ]
    p_ge <- c(1, vapply(seq_len(n_cat - 1), function(k) {
      grm_prob_ge_k(theta, a, b[k])
    }, numeric(1)), 0)
    probs <- p_ge[seq_len(n_cat)] - p_ge[seq_len(n_cat) + 1]
    probs <- pmax(probs, 1e-10)
    probs <- probs / sum(probs)
    responses[i] <- sample.int(n_cat, 1, prob = probs)
  }

  responses
}

#' Simulate full GRM response matrix
simulate_grm_data <- function(n, item_params, theta = NULL) {
  if (is.null(theta)) {
    theta <- stats::rnorm(n)
  }
  n_items <- length(item_params$a)
  mat <- matrix(NA_integer_, n, n_items)
  for (j in seq_len(n)) {
    mat[j, ] <- simulate_grm_person(theta[j], item_params)
  }
  list(responses = mat, theta = theta)
}

#' Carter Study 2 IPIP-like conscientiousness parameters (approximate)
#' High discrimination + extreme thresholds -> sum-score Type I inflation
#' (Carter et al., 2017, Study 2; cf. Grant, 2013 IPIP extraversion)
carter_study2_item_params <- function(n_items = 20, n_cat = 6,
                                      extreme = TRUE) {
  set.seed(2017)
  a <- stats::runif(n_items, 1.80, 1.95)
  b <- matrix(NA_real_, n_items, n_cat - 1)
  for (i in seq_len(n_items)) {
    if (extreme) {
      # High extremity / low bandwidth (Kang & Waller; Carter Study 2)
      b[i, ] <- sort(stats::runif(n_cat - 1, 0.5, 3.5))
    } else {
      base <- stats::runif(1, -1.5, 2.5)
      b[i, ] <- base + seq(-1.2, 1.2, length.out = n_cat - 1)
    }
  }
  list(a = a, b = b, n_cat = n_cat)
}

#' Carter Study 1 item locations (Table 1) for ideal-point GGUM generation
carter_study1_item_locations <- function(condition = c(
  "strong_dominance", "weak_dominance",
  "weak_ideal_point", "strong_ideal_point"
)) {
  condition <- match.arg(condition)
  locs <- switch(
    condition,
    strong_dominance = c(-3.00, -2.95, -2.90, -2.85, -2.80, -2.75, -2.70,
                         -2.65, -2.60, -2.55, 2.55, 2.60, 2.65, 2.70, 2.75,
                         2.80, 2.85, 2.90, 2.95, 3.00),
    weak_dominance = c(-3.00, -2.90, -2.80, -2.70, -2.60, -2.50, -2.40,
                       -2.30, -2.20, -2.10, 2.10, 2.20, 2.30, 2.40, 2.50,
                       2.60, 2.70, 2.80, 2.90, 3.00),
    weak_ideal_point = c(-3.00, -2.80, -2.60, -2.40, -2.20, -2.00, -1.80,
                         -1.60, -1.40, -1.20, 1.20, 1.40, 1.60, 1.80, 2.00,
                         2.20, 2.40, 2.60, 2.80, 3.00),
    strong_ideal_point = c(-3.00, -2.70, -2.40, -2.10, -1.80, -1.50, -1.20,
                           -0.90, -0.60, -0.30, 0.30, 0.60, 0.90, 1.20, 1.50,
                           1.80, 2.10, 2.40, 2.70, 3.00)
  )
  locs
}

#' Log-likelihood of response pattern under GRM
grm_loglik <- function(theta, responses, item_params) {
  ll <- 0
  for (i in seq_along(responses)) {
    a <- item_params$a[i]
    b <- item_params$b[i, ]
    k <- responses[i]
    n_cat <- item_params$n_cat
    p_ge <- grm_prob_ge_k(theta, a, b)
    p_cat <- numeric(n_cat)
    p_cat[1] <- p_ge[1]
    for (c in 2:(n_cat - 1)) {
      p_cat[c] <- p_ge[c] - p_ge[c - 1]
    }
    p_cat[n_cat] <- 1 - p_ge[n_cat - 1]
    ll <- ll + log(pmax(p_cat[k], 1e-12))
  }
  ll
}

#' Fast MAP estimate via Newton-Raphson on GRM log-likelihood
grm_map_score <- function(responses, item_params, start = NULL, max_iter = 15) {
  if (is.null(start)) {
    start <- (mean(responses) - (item_params$n_cat + 1) / 2) / 2
  }
  theta <- start
  for (iter in seq_len(max_iter)) {
    score <- 0
    info <- 0
    for (i in seq_along(responses)) {
      a <- item_params$a[i]
      b <- item_params$b[i, ]
      k <- responses[i]
      n_cat <- item_params$n_cat
      p_ge <- grm_prob_ge_k(theta, a, b)
      p_cat <- numeric(n_cat)
      p_cat[1] <- p_ge[1]
      for (c in 2:(n_cat - 1)) {
        p_cat[c] <- p_ge[c] - p_ge[c - 1]
      }
      p_cat[n_cat] <- 1 - p_ge[n_cat - 1]
      p_cat <- pmax(p_cat, 1e-12)

      # Numerical derivative of log-likelihood w.r.t. theta
      h <- 1e-4
      p_h <- {
        p_ge_h <- grm_prob_ge_k(theta + h, a, b)
        p_cat_h <- numeric(n_cat)
        p_cat_h[1] <- p_ge_h[1]
        for (c in 2:(n_cat - 1)) {
          p_cat_h[c] <- p_ge_h[c] - p_ge_h[c - 1]
        }
        p_cat_h[n_cat] <- 1 - p_ge_h[n_cat - 1]
        p_cat_h[k]
      }
      d1 <- (log(p_h) - log(p_cat[k])) / h
      d2 <- {
        p_ge_m <- grm_prob_ge_k(theta - h, a, b)
        p_cat_m <- numeric(n_cat)
        p_cat_m[1] <- p_ge_m[1]
        for (c in 2:(n_cat - 1)) {
          p_cat_m[c] <- p_ge_m[c] - p_ge_m[c - 1]
        }
        p_cat_m[n_cat] <- 1 - p_ge_m[n_cat - 1]
        (log(p_h) - 2 * log(p_cat[k]) + log(pmax(p_cat_m[k], 1e-12))) / (h^2)
      }
      score <- score + d1
      info <- info - d2
    }
    if (info <= 0) break
    step <- score / info
    theta <- theta + step
    if (abs(step) < 1e-4) break
  }
  theta
}

grm_eap_score <- function(responses, item_params,
                          theta_grid = seq(-4, 4, length.out = 41)) {
  prior <- dnorm(theta_grid, 0, 1)
  ll <- vapply(
    theta_grid,
    function(t) grm_loglik(t, responses, item_params),
    numeric(1)
  )
  post <- exp(ll - max(ll)) * prior
  post <- post / sum(post)
  sum(theta_grid * post)
}

#' Batch IRT scoring (MAP by default — faster; set method="eap" for EAP)
grm_irt_scores <- function(resp_mat, item_params, method = c("map", "eap")) {
  method <- match.arg(method)
  n <- nrow(resp_mat)
  vapply(
    seq_len(n),
    function(i) {
      if (method == "map") {
        grm_map_score(resp_mat[i, ], item_params)
      } else {
        grm_eap_score(resp_mat[i, ], item_params)
      }
    },
    numeric(1)
  )
}

# Backward compatibility alias
grm_eap_scores <- function(resp_mat, item_params, theta_grid = seq(-4, 4, length.out = 41)) {
  grm_irt_scores(resp_mat, item_params, method = "map")
}

#' Sum-score (dominance assumption; Carter reverse-scores negative-keyed items)
sum_score <- function(responses, reverse_items = NULL) {
  mat <- responses
  if (!is.null(reverse_items)) {
    n_cat <- max(mat, na.rm = TRUE)
    for (i in reverse_items) {
      mat[, i] <- (n_cat + 1) - mat[, i]
    }
  }
  rowMeans(mat)
}

#' Test curvilinearity via OLS (Carter's analytic approach)
test_curvilinear <- function(theta_hat, y, alpha = 0.05) {
  x <- scale(theta_hat, center = TRUE, scale = FALSE)[, 1]
  x2 <- x^2
  m <- stats::lm(y ~ x + x2)
  s <- summary(m)$coefficients
  p <- s["x2", "Pr(>|t|)"]
  b2 <- s["x2", "Estimate"]
  list(
    sig = !is.na(p) && p < alpha,
    p = p,
    b2 = b2,
    t = s["x2", "t value"]
  )
}
