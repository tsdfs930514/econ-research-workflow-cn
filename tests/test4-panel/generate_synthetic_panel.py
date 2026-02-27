"""
Generate Synthetic Panel Data for Panel Analysis Testing
=========================================================
DGP: 200 firms x 15 years (2005-2019) = 3,000 observations

Key features baked into the DGP:
- Firm FE correlated with regressors (Hausman should reject RE)
- AR(1) serial correlation rho=0.5 (Wooldridge test should detect)
- Heteroskedasticity across firms proportional to firm size (Modified Wald detects)
- Lagged DV included for GMM testing

True coefficients:
    productivity = 10 + firm_fe + 0.8*rd_spending + 0.3*capital
                   + 0.2*labor + 0.1*export_share + ar1_error
"""

import numpy as np
import pandas as pd
import os

# ==============================================================================
# Settings
# ==============================================================================
np.random.seed(42)

n_firms = 200
years = list(range(2005, 2020))  # 15 years
n_years = len(years)
n_obs = n_firms * n_years

# True parameters
BETA_0 = 10.0
BETA_RD = 0.8
BETA_CAPITAL = 0.3
BETA_LABOR = 0.2
BETA_EXPORT = 0.1
RHO = 0.5  # AR(1) coefficient for serial correlation

# ==============================================================================
# Generate firm-level characteristics (time-invariant)
# ==============================================================================

# Firm fixed effects
firm_fe = np.random.normal(0, 5, n_firms)

# Industry assignment: firms 1-40 = industry 1, 41-80 = industry 2, etc.
industry_ids = np.repeat(np.arange(1, 6), n_firms // 5)

# Firm size (used to generate heteroskedasticity) - drawn once per firm
firm_size = np.random.lognormal(4, 0.8, n_firms)

# ==============================================================================
# Build panel structure
# ==============================================================================

firm_id_col = np.repeat(np.arange(1, n_firms + 1), n_years)
year_col = np.tile(years, n_firms)
industry_col = np.repeat(industry_ids, n_years)
firm_fe_col = np.repeat(firm_fe, n_years)
firm_size_col = np.repeat(firm_size, n_years)

# ==============================================================================
# Generate time-varying regressors
# ==============================================================================

# R&D spending: correlated with firm_fe (ensures Hausman rejects RE)
rd_base = np.repeat(
    2.0 + 0.5 * firm_fe + np.random.normal(0, 1, n_firms),
    n_years
)
rd_spending = rd_base + np.random.normal(0, 1, n_obs)
rd_spending = np.maximum(rd_spending, 0.1)  # floor at 0.1

# Capital
capital = np.random.lognormal(3, 0.5, n_obs)

# Labor
labor = np.random.lognormal(5, 0.3, n_obs)

# Export share
export_share = np.random.beta(2, 5, n_obs)

# ==============================================================================
# Generate AR(1) error term with heteroskedasticity
# ==============================================================================

# Error variance proportional to firm size (generates heteroskedasticity)
sigma_firm = np.sqrt(firm_size_col / np.median(firm_size))  # scale by median

errors = np.zeros(n_obs)
for i in range(n_firms):
    start = i * n_years
    # First period: draw from unconditional distribution
    errors[start] = np.random.normal(0, sigma_firm[start])
    # Subsequent periods: AR(1)
    for t in range(1, n_years):
        errors[start + t] = (
            RHO * errors[start + t - 1]
            + np.random.normal(0, sigma_firm[start + t])
        )

# ==============================================================================
# Generate dependent variable
# ==============================================================================

productivity = (
    BETA_0
    + firm_fe_col
    + BETA_RD * rd_spending
    + BETA_CAPITAL * capital
    + BETA_LABOR * labor
    + BETA_EXPORT * export_share
    + errors
)

# ==============================================================================
# Assemble DataFrame
# ==============================================================================

df = pd.DataFrame({
    "firm_id": firm_id_col,
    "year": year_col,
    "industry_id": industry_col,
    "productivity": productivity,
    "rd_spending": rd_spending,
    "capital": capital,
    "labor": labor,
    "export_share": export_share,
})

# Sort for proper panel structure
df = df.sort_values(["firm_id", "year"]).reset_index(drop=True)

# Create lagged productivity (L_productivity) for GMM
df["L_productivity"] = df.groupby("firm_id")["productivity"].shift(1)

# ==============================================================================
# Export
# ==============================================================================

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_panel.dta")
df.to_stata(out_path, write_index=False, version=118)
print(f"Data saved to: {out_path}")

# ==============================================================================
# Summary statistics
# ==============================================================================

print("\n" + "=" * 70)
print("SYNTHETIC PANEL DATA - SUMMARY STATISTICS")
print("=" * 70)
print(f"\nDimensions: {n_firms} firms x {n_years} years = {len(df)} observations")
print(f"Years: {years[0]}-{years[-1]}")
print(f"Industries: {df['industry_id'].nunique()}")
print(f"Missing L_productivity (first year per firm): {df['L_productivity'].isna().sum()}")

print("\n--- Variable Summary ---")
summary_vars = ["productivity", "rd_spending", "capital", "labor",
                 "export_share", "L_productivity"]
print(df[summary_vars].describe().round(4).to_string())

print("\n--- True DGP Parameters ---")
print(f"  Intercept:      {BETA_0}")
print(f"  rd_spending:    {BETA_RD}")
print(f"  capital:        {BETA_CAPITAL}")
print(f"  labor:          {BETA_LABOR}")
print(f"  export_share:   {BETA_EXPORT}")
print(f"  AR(1) rho:      {RHO}")
print(f"  Firm FE std:    {np.std(firm_fe):.4f}")

print("\n--- Correlation: firm_fe and rd_spending (firm means) ---")
firm_means = df.groupby("firm_id")["rd_spending"].mean().values
corr = np.corrcoef(firm_fe, firm_means)[0, 1]
print(f"  Corr(firm_fe, mean_rd): {corr:.4f}")
print("  (High correlation => Hausman should reject RE)\n")
