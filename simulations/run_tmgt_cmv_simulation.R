#!/usr/bin/env Rscript

# Monte Carlo study: Type I and Type II error rates for TMGT effects under CMV
# Usage: Rscript simulations/run_tmgt_cmv_simulation.R [--pilot]

args <- commandArgs(trailingOnly = TRUE)
pilot_mode <- "--pilot" %in% args

repo_root <- if (file.exists("simulations/R/tmgt_cmv_dgp.R")) {
  "."
} else if (file.exists("../simulations/R/tmgt_cmv_dgp.R")) {
  ".."
} else {
  stop("Run from repository root or simulations/ directory.")
}

source(file.path(repo_root, "simulations/R/tmgt_cmv_dgp.R"))
source(file.path(repo_root, "simulations/R/tmgt_cmv_analysis.R"))
source(file.path(repo_root, "simulations/config/tmgt_scenarios.R"))

run_tmgt_cmv_study <- function(
    n_reps = if (pilot_mode) 200 else 1000,
    n = 200,
    scenarios = names(TMGT_SCENARIOS),
    cmv_conditions = NULL,
    n_items = 4,
    seed = 20260709,
    output_dir = file.path(repo_root, "simulations/output")) {

  if (is.null(cmv_conditions)) {
    # Core grid: CMV proportion x same-source; symmetric method-trait correlations
    cmv_conditions <- expand.grid(
      cmv_prop = c(0.00, 0.25, 0.50),
      same_source = c(TRUE, FALSE),
      rho_m_x = c(0.00, 0.30),
      rho_m_y = c(0.00, 0.30),
      rho_m_w = c(0.00, 0.30),
      stringsAsFactors = FALSE
    )
    # Keep symmetric and null-correlation cells for primary analysis
    cmv_conditions <- cmv_conditions[
      (cmv_conditions$rho_m_x == cmv_conditions$rho_m_y &
         cmv_conditions$rho_m_y == cmv_conditions$rho_m_w) |
        (cmv_conditions$rho_m_x == 0 &
           cmv_conditions$rho_m_y == 0 &
           cmv_conditions$rho_m_w == 0),
    ]
  }

  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

  results <- list()
  idx <- 1L
  set.seed(seed)

  cat(sprintf("TMGT-CMV Monte Carlo (%d reps/cell, N=%d)\n", n_reps, n))

  for (sc_name in scenarios) {
    scenario <- TMGT_SCENARIOS[[sc_name]]
    cat(sprintf("\nScenario: %s (%s)\n", sc_name, scenario$label))

    for (i in seq_len(nrow(cmv_conditions))) {
      cmv <- cmv_conditions[i, , drop = FALSE]
      cat(sprintf(
        "  CMV=%.2f, same_source=%s, rho=(%.2f,%.2f,%.2f) ... ",
        cmv$cmv_prop, cmv$same_source,
        cmv$rho_m_x, cmv$rho_m_y, cmv$rho_m_w
      ))

      rep_results <- matrix(NA_real_, n_reps, 16)
      colnames(rep_results) <- c(
        "sig_X2_tmgt", "sig_X2W_tmgt", "sig_X2_quadratic", "sig_XW_tmgt",
        "p_X2_tmgt_model", "p_X2W_tmgt_model", "b_X2_tmgt", "b_X2W_tmgt",
        "type1_X2", "type2_X2", "type1_X2W", "type2_X2W",
        "r2_tmgt", "r2_linear", "b_X_tmgt", "b_X2_quadratic"
      )

      for (r in seq_len(n_reps)) {
        out <- run_one_replication(n, scenario, cmv, n_items = n_items)
        errs <- classify_errors(out, scenario)
        row <- c(
          sig_X2_tmgt = out[["sig_X2_tmgt"]],
          sig_X2W_tmgt = out[["sig_X2W_tmgt"]],
          sig_X2_quadratic = out[["sig_X2_quadratic"]],
          sig_XW_tmgt = out[["sig_XW_tmgt"]],
          p_X2_tmgt_model = out[["p_X2_tmgt_model"]],
          p_X2W_tmgt_model = out[["p_X2W_tmgt_model"]],
          b_X2_tmgt = out[["b_X2_tmgt"]],
          b_X2W_tmgt = out[["b_X2W_tmgt"]],
          type1_X2 = errs[["type1_X2"]],
          type2_X2 = errs[["type2_X2"]],
          type1_X2W = errs[["type1_X2W"]],
          type2_X2W = errs[["type2_X2W"]],
          r2_tmgt = out[["r2_tmgt"]],
          r2_linear = out[["r2_linear"]],
        b_X_tmgt = out[["b_X_tmgt"]],
        b_X2_quadratic = NA_real_
        )
        rep_results[r, ] <- row
      }

      # Aggregate
      agg <- data.frame(
        scenario = sc_name,
        scenario_label = scenario$label,
        true_b2 = scenario$b2,
        true_b5 = scenario$b5,
        optimal_x = tmgt_optimal_x(scenario),
        n = n,
        n_reps = n_reps,
        cmv_prop = cmv$cmv_prop,
        same_source = cmv$same_source,
        rho_m_x = cmv$rho_m_x,
        rho_m_y = cmv$rho_m_y,
        rho_m_w = cmv$rho_m_w,
        prop_sig_X2_tmgt = mean(rep_results[, "sig_X2_tmgt"], na.rm = TRUE),
        prop_sig_X2W_tmgt = mean(rep_results[, "sig_X2W_tmgt"], na.rm = TRUE),
        prop_sig_X2_quadratic = mean(rep_results[, "sig_X2_quadratic"], na.rm = TRUE),
        mean_b_X2_tmgt = mean(rep_results[, "b_X2_tmgt"], na.rm = TRUE),
        mean_b_X2W_tmgt = mean(rep_results[, "b_X2W_tmgt"], na.rm = TRUE),
        type1_rate_X2 = mean(rep_results[, "type1_X2"], na.rm = TRUE),
        type2_rate_X2 = mean(rep_results[, "type2_X2"], na.rm = TRUE),
        type1_rate_X2W = mean(rep_results[, "type1_X2W"], na.rm = TRUE),
        type2_rate_X2W = mean(rep_results[, "type2_X2W"], na.rm = TRUE),
        power_X2 = if (scenario$b2 != 0) {
          mean(rep_results[, "sig_X2_tmgt"], na.rm = TRUE)
        } else {
          NA_real_
        },
        mean_r2_tmgt = mean(rep_results[, "r2_tmgt"], na.rm = TRUE),
        mean_r2_linear = mean(rep_results[, "r2_linear"], na.rm = TRUE),
        stringsAsFactors = FALSE
      )

      results[[idx]] <- agg
      idx <- idx + 1L

      cat(sprintf(
        "Type I X2=%.3f, Type II X2=%.3f, Power X2=%.3f\n",
        agg$type1_rate_X2, agg$type2_rate_X2, agg$power_X2
      ))
    }
  }

  out_df <- do.call(rbind, results)
  rownames(out_df) <- NULL

  stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
  mode_tag <- if (pilot_mode) "pilot" else "full"
  out_file <- file.path(output_dir, sprintf("tmgt_cmv_results_%s_%s.csv", mode_tag, stamp))
  write.csv(out_df, out_file, row.names = FALSE)

  cat(sprintf("\nResults written to: %s\n", out_file))
  invisible(out_df)
}

if (sys.nframe() == 0) {
  run_tmgt_cmv_study()
}
