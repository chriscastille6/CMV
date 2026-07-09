# Summarize TMGT-CMV simulation results

summarize_tmgt_cmv_results <- function(results_file) {
  df <- read.csv(results_file, stringsAsFactors = FALSE)

  cat("=== TMGT-CMV Simulation Summary ===\n\n")

  # Type I: null scenario only
  null_df <- df[df$scenario == "null_tmgt", ]
  if (nrow(null_df) > 0) {
    cat("Type I error rates (null TMGT; target alpha = 0.05):\n")
    print(null_df[, c(
      "cmv_prop", "same_source", "rho_m_x",
      "type1_rate_X2", "type1_rate_X2W", "prop_sig_X2_tmgt"
    )])
    cat("\n")
  }

  # Type II / power: scenarios with true curvature
  tmgt_df <- df[df$true_b2 != 0, ]
  if (nrow(tmgt_df) > 0) {
    cat("Type II error / power for quadratic term (true b2 != 0):\n")
    print(tmgt_df[, c(
      "scenario", "cmv_prop", "same_source", "rho_m_x",
      "type2_rate_X2", "power_X2", "mean_b_X2_tmgt", "true_b2"
    )])
    cat("\n")
  }

  # Moderated quadratic
  mod_df <- df[df$scenario == "moderated_tmgt", ]
  if (nrow(mod_df) > 0) {
    cat("Moderated TMGT (X2W term, true b5 = -0.05):\n")
    print(mod_df[, c(
      "cmv_prop", "same_source", "rho_m_x",
      "type2_rate_X2W", "prop_sig_X2W_tmgt", "mean_b_X2W_tmgt"
    )])
  }

  invisible(df)
}

if (sys.nframe() == 0) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) == 0) {
    files <- sort(
      list.files("simulations/output", pattern = "tmgt_cmv_results_.*\\.csv", full.names = TRUE),
      decreasing = TRUE
    )
    if (length(files) == 0) {
      stop("No results files found in simulations/output/")
    }
    results_file <- files[1]
  } else {
    results_file <- args[1]
  }
  summarize_tmgt_cmv_results(results_file)
}
