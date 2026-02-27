"""
Generate synthetic IV data with panel structure and strong first stage
Mimics network IV structure: endogenous treatment with instrument (SCI)

DGP Design (REVISED v2 - county-specific slopes):
  - 500 counties in 50 states (~10 counties per state), 10 years = 5000 obs
  - County-specific SCI slopes create within-state, within-year variation
  - After absorbing state_id + year FE, county-slope × time variation survives
  - Treatment (continuous) responds to SCI strongly: partial F > 23
  - True treatment effect on employment: -2.0
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm

np.random.seed(42)

# =============================================================================
# Panel structure
# =============================================================================
n_counties = 500
n_states = 50
counties_per_state = n_counties // n_states  # 10
years = list(range(2010, 2020))
n_years = len(years)
year_mean = np.mean(years)  # 2014.5

records = []
for c in range(1, n_counties + 1):
    state = (c - 1) // counties_per_state + 1
    for y in years:
        records.append({'county_id': c, 'state_id': state, 'year': y})

df = pd.DataFrame(records)
n = len(df)

county_id = df['county_id'].values
state_id = df['state_id'].values
year = df['year'].values
year_centered = year - year_mean  # [-4.5, ..., 4.5]

# =============================================================================
# State-level characteristics (absorbed by state FE)
# =============================================================================
state_sci_base = np.random.uniform(1.0, 5.0, n_states)
state_emp_base = np.random.normal(0, 3, n_states)

# =============================================================================
# County-level SCI slopes: vary WITHIN states, survive state+year FE absorption
# county_slope_i * (year - year_mean) is not captured by any single FE
# =============================================================================
county_slope = np.random.normal(0, 0.8, n_counties)

# County-level omitted confound (drawn independently of slope -> IV validity)
county_confound = np.random.normal(0, 2.0, n_counties)

# Map to obs
sci_base_mapped = state_sci_base[state_id - 1]
emp_base_mapped = state_emp_base[state_id - 1]
county_slope_mapped = county_slope[county_id - 1]
county_confound_mapped = county_confound[county_id - 1]

# =============================================================================
# SCI instrument:
#   sci_it = state_base_s + county_slope_i * (year - year_mean) + noise_it
#   After state + year FE absorption:
#     demeaned_sci ≈ county_slope_i * year_dev + noise  (strong residual variation)
# =============================================================================
sci_noise = np.random.normal(0, 0.3, n)
sci = sci_base_mapped + county_slope_mapped * year_centered + sci_noise

# =============================================================================
# Exogenous controls (county-year level)
# =============================================================================
pop = np.random.lognormal(10, 0.8, n)
manufacturing = np.random.beta(2, 5, n)

# =============================================================================
# Endogenous treatment (continuous):
#   treatment_it = 0.5 * sci_it + county_confound_i + noise_it
#   county_confound makes OLS biased (correlated with employment error)
# =============================================================================
treatment_noise = np.random.normal(0, 1.0, n)
treatment = 0.5 * sci + county_confound_mapped + treatment_noise

# =============================================================================
# Outcome: employment
#   employment_it = 60 + emp_base_s + 0.001*pop + 5*mfg - 2.0*treatment
#                    + 0.5 * county_confound + year_trend + noise
#   True IV treatment effect: -2.0
# =============================================================================
year_trend = 0.5 * (year - 2010)  # common time trend (absorbed by year FE)
employment_noise = np.random.normal(0, 2, n)
employment = (60
              + emp_base_mapped
              + 0.001 * pop
              + 5 * manufacturing
              - 2.0 * treatment
              + 0.5 * county_confound_mapped
              + year_trend
              + employment_noise)

# =============================================================================
# Assemble and save
# =============================================================================
df['sci'] = sci
df['treatment'] = treatment
df['employment'] = employment
df['pop'] = pop
df['manufacturing'] = manufacturing

df.to_stata('synthetic_iv.dta', write_index=False)

# =============================================================================
# Summary statistics
# =============================================================================
print(f"Generated synthetic IV data: {n} observations")
print(f"Counties: {n_counties}, States: {df['state_id'].nunique()}, Years: {n_years}")
print(f"\nTreatment (continuous): mean={treatment.mean():.2f}, sd={treatment.std():.2f}")
print(f"Employment: mean={employment.mean():.2f}, sd={employment.std():.2f}")
print(f"SCI correlation with treatment: {np.corrcoef(sci, treatment)[0,1]:.3f}")

# =============================================================================
# First-stage diagnostics (two-way FE demeaned via within transformation)
# =============================================================================
print(f"\n=== First Stage After State + Year FE (within transformation) ===")

df_temp = df[['county_id', 'state_id', 'year', 'sci', 'treatment', 'pop', 'manufacturing']].copy()

for var in ['sci', 'treatment', 'pop', 'manufacturing']:
    state_mean_v = df_temp.groupby('state_id')[var].transform('mean')
    year_mean_v = df_temp.groupby('year')[var].transform('mean')
    grand_mean_v = df_temp[var].mean()
    df_temp[f'{var}_demean'] = df_temp[var] - state_mean_v - year_mean_v + grand_mean_v

X_demean = sm.add_constant(np.column_stack([
    df_temp['sci_demean'].values,
    df_temp['pop_demean'].values,
    df_temp['manufacturing_demean'].values
]))
model_fe = sm.OLS(df_temp['treatment_demean'].values, X_demean).fit()

print(f"SCI coef (demeaned): {model_fe.params[1]:.4f}")
print(f"SCI t-stat (demeaned): {model_fe.tvalues[1]:.2f}")
print(f"R-squared (demeaned): {model_fe.rsquared:.4f}")

# Partial F-stat for SCI (excluded instrument)
X_restricted = sm.add_constant(np.column_stack([
    df_temp['pop_demean'].values,
    df_temp['manufacturing_demean'].values
]))
model_restricted = sm.OLS(df_temp['treatment_demean'].values, X_restricted).fit()

rss_r = model_restricted.ssr
rss_u = model_fe.ssr
q = 1
k_u = X_demean.shape[1]
partial_f = ((rss_r - rss_u) / q) / (rss_u / (n - k_u))
print(f"Partial F-stat for SCI (excluded instrument): {partial_f:.2f}")
print(f"\nTarget: partial F > 23 for strong instrument after FE absorption")
if partial_f > 23:
    print(f"PASS: Instrument is strong after absorbing state + year FE (F={partial_f:.2f})")
else:
    print(f"WARNING: Instrument is weak after FE absorption (F={partial_f:.2f})")
