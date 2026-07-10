#!/usr/bin/env Rscript

# Partial replication of Carter et al. (2017) Study 2
# IRT Scoring and the Detection of Curvilinear Relationships
#
# Compares sum-score vs GRM-EAP for Type I error and power when
# data are generated from a dominance (GRM) process — the case that
# generalizes to Grant (2013) extraversion measures.

args <- commandArgs(trailingOnly = TRUE)
pilot <- "--pilot" %in% args

repo_root <- if (file.exists("simulations/R/carter_grm_irt.R")) "." else ".."
source(file.path(repo_root, "simulations/R/carter_grm_irt.R"))

run_carter_study2_replication <- function(
    n_reps = if (pilot) 100 else 500,
    sample_sizes = if (pilot) c(340, 500) else c(340, 500, 1000, 2000),
    n_items = 20,
    n_cat = 6,
    seed = 2017,
    output_dir = file.path(repo_root, "simulations/output")) {

  set.seed(seed)
  item_params <- carter_study2_item_params(n_items, n_cat)
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  # Carter Study 2 Type I: beta2 = 0, beta1 in {.2,.3,.4}
  # Grant overlay: beta1 = 0, beta2 = -.14 (symmetric inverted-U at mean)
  conditions <- list(
    type1_b1_20 = list(b1 = 0.20, b2 = 0.00, label = "Type I (b1=.20)"),
    type1_b1_30 = list(b1 = 0.30, b2 = 0.00, label = "Type I (b1=.30)"),
    type1_b1_40 = list(b1 = 0.40, b2 = 0.00, label = "Type I (b1=.40)"),
    grant_power = list(b1 = 0.00, b2 = -0.14, label = "Grant TMGT (b2=-.14)"),
    power_inflect_05 = list(b1 = 0.20, b2 = -0.20, label = "Carter inflect=.5SD"),
    power_inflect_10 = list(b1 = 0.20, b2 = -0.10, label = "Carter inflect=1.0SD")
  )

  cat("Carter et al. (2017) Study 2 partial replication\n")
  cat(sprintf("  %d reps/cell, %d items, %d categories\n", n_reps, n_items, n_cat))
  cat("  GRM scoring: latent theta + estimation noise (oracle IRTPRO proxy)\n\n")

  results <- list()
  idx <- 1L

  for (cond_name in names(conditions)) {
    cond <- conditions[[cond_name]]
    cat(sprintf("=== %s ===\n", cond$label))

    for (n in sample_sizes) {
      sum_sig <- grm_sig <- integer(n_reps)

      for (r in seq_len(n_reps)) {
        sim <- simulate_grm_data(n, item_params)
        theta <- sim$theta

        # Criterion from TRUE latent theta (Carter Eq. 2)
        y <- cond$b1 * theta + cond$b2 * theta^2 + stats::rnorm(n)

        # Score methods
        x_sum <- sum_score(sim$responses)
        # Oracle GRM score: latent theta + estimation noise (approximates IRTPRO EAP)
        x_grm <- theta + stats::rnorm(n, sd = 0.25)

        sum_sig[r] <- test_curvilinear(x_sum, y)$sig
        grm_sig[r] <- test_curvilinear(x_grm, y)$sig
      }

      row <- data.frame(
        condition = cond_name,
        condition_label = cond$label,
        true_b1 = cond$b1,
        true_b2 = cond$b2,
        n = n,
        n_reps = n_reps,
        scoring = c("sum_score", "grm_oracle"),
        prop_sig = c(mean(sum_sig), mean(grm_sig)),
        type1_rate = if (cond$b2 == 0) c(mean(sum_sig), mean(grm_sig)) else c(NA, NA),
        power = if (cond$b2 != 0) c(mean(sum_sig), mean(grm_sig)) else c(NA, NA),
        stringsAsFactors = FALSE
      )
      results[[idx]] <- row
      idx <- idx + 1L

      cat(sprintf(
        "  N=%4d: sum-score=%.3f, GRM-oracle=%.3f\n",
        n, mean(sum_sig), mean(grm_sig)
      ))
    }
    cat("\n")
  }

  out_df <- do.call(rbind, results)
  stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
  tag <- if (pilot) "pilot" else "full"
  out_file <- file.path(output_dir, sprintf("carter_study2_replication_%s_%s.csv", tag, stamp))
  write.csv(out_df, out_file, row.names = FALSE)
  cat(sprintf("Results: %s\n", out_file))
  invisible(out_df)
}

if (sys.nframe() == 0) {
  run_carter_study2_replication()
}
