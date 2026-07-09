# Named TMGT population scenarios for Monte Carlo study

TMGT_SCENARIOS <- list(
  # Type I focus: only linear substantive effects; no true curvature
  null_tmgt = list(
    label = "Null TMGT (linear only)",
    b0 = 0,
    b1 = 0.30,
    b2 = 0.00,
    b3 = 0.20,
    b4 = 0.10,
    b5 = 0.00,
    sd_y = 1.0,
    rho_xw = 0.20
  ),

  # Type II focus: inverted-U without moderation (ambivert advantage)
  simple_tmgt = list(
    label = "Simple TMGT (inverted-U)",
    b0 = 0,
    b1 = 0.40,
    b2 = -0.15,
    b3 = 0.00,
    b4 = 0.00,
    b5 = 0.00,
    sd_y = 1.0,
    rho_xw = 0.00
  ),

  # Moderated TMGT: W shifts the optimal level of X
  moderated_tmgt = list(
    label = "Moderated TMGT (peak shifts with W)",
    b0 = 0,
    b1 = 0.40,
    b2 = -0.15,
    b3 = 0.20,
    b4 = 0.00,
    b5 = -0.05,
    sd_y = 1.0,
    rho_xw = 0.20
  ),

  # Benchmark: strong, easily detectable curvature (ideal setting)
  ideal_tmgt = list(
    label = "Ideal TMGT (strong inverted-U)",
    b0 = 0,
    b1 = 0.50,
    b2 = -0.25,
    b3 = 0.00,
    b4 = 0.00,
    b5 = 0.00,
    sd_y = 0.80,
    rho_xw = 0.00
  )
)

# Default CMV manipulation grid (Siemsen-style symmetry conditions)
DEFAULT_CMV_CONDITIONS <- expand.grid(
  cmv_prop = c(0.00, 0.25, 0.50),
  same_source = c(TRUE, FALSE),
  rho_m_x = c(0.00, 0.30),
  rho_m_y = c(0.00, 0.30),
  rho_m_w = c(0.00, 0.30),
  stringsAsFactors = FALSE
)

# Symmetric CMV: method factor correlates equally with X and Y
DEFAULT_CMV_CONDITIONS$symmetric <- with(
  DEFAULT_CMV_CONDITIONS,
  rho_m_x == rho_m_y & rho_m_y == rho_m_w
)
