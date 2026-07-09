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
  ),

  # Grant (2013): standardized coefficients from Table 1 (Step 5)
  # Linear extraversion ns; quadratic beta = -0.14, p < .01; N = 340
  grant_ambivert = list(
    label = "Grant (2013) ambivert advantage",
    b0 = 0,
    b1 = 0.00,
    b2 = -0.14,
    b3 = 0.00,
    b4 = 0.00,
    b5 = 0.00,
    sd_y = 1.00,
    rho_xw = 0.00,
    n_default = 340,
    measurement = "grant"
  ),

  # Grant-style null: linear effect only (no true curvature)
  grant_null = list(
    label = "Grant-style null (linear extraversion only)",
    b0 = 0,
    b1 = 0.30,
    b2 = 0.00,
    b3 = 0.00,
    b4 = 0.00,
    b5 = 0.00,
    sd_y = 1.00,
    rho_xw = 0.00,
    n_default = 340,
    measurement = "grant"
  )
)

# Measurement profiles for ambiversion sensitivity
MEASUREMENT_PROFILES <- list(
  grant = list(
    label = "Grant (4-item, alpha ~ .85)",
    n_items = 4,
    substantive_loading = 0.61,
    x_transform = "none"
  ),
  coarse = list(
    label = "Coarse (2-item, low reliability)",
    n_items = 2,
    substantive_loading = 0.55,
    x_transform = "none"
  ),
  compressed = list(
    label = "Compressed midrange (poor ambiversion sensitivity)",
    n_items = 4,
    substantive_loading = 0.61,
    x_transform = "compressed"
  )
)

# Asymmetric CMV: method factor more correlated with X than Y
ASYMMETRIC_CMV_CONDITIONS <- data.frame(
  cmv_prop = c(0.25, 0.25, 0.50),
  same_source = c(TRUE, TRUE, TRUE),
  rho_m_x = c(0.30, 0.30, 0.30),
  rho_m_y = c(0.00, 0.10, 0.00),
  rho_m_w = c(0.00, 0.00, 0.00),
  asymmetric = c(TRUE, TRUE, TRUE),
  stringsAsFactors = FALSE
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
