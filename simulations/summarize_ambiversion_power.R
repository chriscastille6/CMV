# Summarize ambiversion power study (N x measurement x CMV)

summarize_ambiversion_power <- function(results_file) {
  df <- read.csv(results_file, stringsAsFactors = FALSE)

  cat("=== Ambiversion Power Study Summary ===\n\n")

  for (cmv in sort(unique(df$cmv_prop))) {
    cat(sprintf("--- CMV = %.0f%% ---\n", cmv * 100))
    sub <- df[df$cmv_prop == cmv, ]
    wide <- reshape(
      sub[, c("measurement_key", "n", "power_X2")],
      idvar = "measurement_key",
      timevar = "n",
      direction = "wide"
    )
    colnames(wide) <- c("approach", paste0("N", sub("^n\\.", "", colnames(wide)[-1])))
    rownames(wide) <- NULL
    print(wide, row.names = FALSE)
    cat("\n")
  }

  cat("--- N needed for 80% power (by approach, CMV=0) ---\n")
  clean <- df[df$cmv_prop == 0, ]
  for (approach in unique(clean$measurement_key)) {
    sub <- clean[clean$measurement_key == approach, ]
    sub <- sub[order(sub$n), ]
    hit <- sub$n[sub$power_X2 >= 0.80]
    n80 <- if (length(hit) > 0) min(hit) else NA
    cat(sprintf("  %-22s  N >= %s\n", approach, n80))
  }

  cat("\n--- N needed for 80% power (by approach, CMV=50%) ---\n")
  dirty <- df[df$cmv_prop == 0.50, ]
  for (approach in unique(dirty$measurement_key)) {
    sub <- dirty[dirty$measurement_key == approach, ]
    sub <- sub[order(sub$n), ]
    hit <- sub$n[sub$power_X2 >= 0.80]
    n80 <- if (length(hit) > 0) min(hit) else ">5000"
    cat(sprintf("  %-22s  N >= %s\n", approach, n80))
  }

  invisible(df)
}

if (sys.nframe() == 0) {
  args <- commandArgs(trailingOnly = TRUE)
  file <- if (length(args) > 0) {
    args[1]
  } else {
    files <- sort(
      list.files("simulations/output", pattern = "ambiversion_power_.*\\.csv", full.names = TRUE),
      decreasing = TRUE
    )
    if (length(files) == 0) stop("No ambiversion power results found.")
    files[1]
  }
  summarize_ambiversion_power(file)
}
