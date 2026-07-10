#!/usr/bin/env Rscript

# Ambiversion power study: larger N x unfolding/facet measurement approaches
# Usage: Rscript simulations/run_ambiversion_power_study.R [--pilot]

args <- commandArgs(trailingOnly = TRUE)
pilot_mode <- "--pilot" %in% args

repo_root <- if (file.exists("simulations/R/tmgt_cmv_dgp.R")) {
  "."
} else if (file.exists("../simulations/R/tmgt_cmv_dgp.R")) {
  ".."
} else {
  stop("Run from repository root.")
}

source(file.path(repo_root, "simulations/R/tmgt_cmv_dgp.R"))
source(file.path(repo_root, "simulations/R/tmgt_cmv_analysis.R"))
source(file.path(repo_root, "simulations/config/tmgt_scenarios.R"))

run_ambiversion_power_study <- function(
    n_reps = if (pilot_mode) 200 else 1000,
    sample_sizes = if (pilot_mode) {
      c(340, 1000, 3000)
    } else {
      AMBIVERSION_SAMPLE_SIZES
    },
    cmv_props = c(0.00, 0.25, 0.50),
    measurement_approaches = AMBIVERSION_MEASUREMENT_APPROACHES,
    scenario_name = "grant_ambivert",
    seed = 20260710,
    output_dir = file.path(repo_root, "simulations/output")) {

  scenario <- TMGT_SCENARIOS[[scenario_name]]
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  set.seed(seed)

  cat("Ambiversion Power Study\n")
  cat(sprintf("  Scenario: %s (b2 = %.2f)\n", scenario$label, scenario$b2))
  cat(sprintf("  Reps/cell: %d\n", n_reps))
  cat(sprintf("  N: %s\n", paste(sample_sizes, collapse = ", ")))
  cat(sprintf("  Approaches: %d\n\n", length(measurement_approaches)))

  results <- list()
  idx <- 1L

  cmv_base <- data.frame(
    same_source = TRUE,
    rho_m_x = 0.00,
    rho_m_y = 0.00,
    rho_m_w = 0.00,
    asymmetric = FALSE,
    stringsAsFactors = FALSE
  )

  for (meas_key in measurement_approaches) {
    measurement <- MEASUREMENT_PROFILES[[meas_key]]
    cat(sprintf("=== %s ===\n", measurement$label))

    for (sample_n in sample_sizes) {
      for (cmv_prop in cmv_props) {
        cmv <- cbind(cmv_base, data.frame(cmv_prop = cmv_prop))

        rep_power <- rep_b2 <- rep_type1 <- numeric(n_reps)
        for (r in seq_len(n_reps)) {
          out <- run_one_replication(sample_n, scenario, cmv, measurement = measurement)
          errs <- classify_errors(out, scenario)
          rep_power[r] <- out[["sig_X2_tmgt"]]
          rep_b2[r] <- out[["b_X2_tmgt"]]
          rep_type1[r] <- errs[["type1_X2"]]
        }

        row <- data.frame(
          study = "ambiversion_power",
          scenario = scenario_name,
          true_b2 = scenario$b2,
          n = sample_n,
          n_reps = n_reps,
          cmv_prop = cmv_prop,
          same_source = TRUE,
          measurement_key = meas_key,
          measurement_profile = measurement$label,
          measurement_mode = measurement$mode,
          power_X2 = mean(rep_power),
          type2_rate_X2 = 1 - mean(rep_power),
          type1_rate_X2 = mean(rep_type1, na.rm = TRUE),
          mean_b_X2_tmgt = mean(rep_b2, na.rm = TRUE),
          bias_b_X2 = mean(rep_b2, na.rm = TRUE) - scenario$b2,
          stringsAsFactors = FALSE
        )

        results[[idx]] <- row
        idx <- idx + 1L

        cat(sprintf(
          "  N=%4d, CMV=%.2f -> power=%.3f, mean(b2)=%.3f\n",
          sample_n, cmv_prop, row$power_X2, row$mean_b_X2_tmgt
        ))
      }
    }
    cat("\n")
  }

  out_df <- do.call(rbind, results)
  rownames(out_df) <- NULL

  stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
  tag <- if (pilot_mode) "pilot" else "full"
  out_file <- file.path(
    output_dir,
    sprintf("ambiversion_power_%s_%s.csv", tag, stamp)
  )
  write.csv(out_df, out_file, row.names = FALSE)

  cat(sprintf("Results: %s\n", out_file))
  cat(sprintf("Total cells: %d\n", nrow(out_df)))
  invisible(out_df)
}

if (sys.nframe() == 0) {
  run_ambiversion_power_study()
}
