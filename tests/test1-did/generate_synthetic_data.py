"""
Generate synthetic panel data for DID testing
Mimics apep_0119 structure: state-year panel with staggered treatment
"""
import pandas as pd
import numpy as np

np.random.seed(42)

# Parameters
n_states = 50
years = range(2005, 2020)  # 15 years
treatment_years = [2010, 2012, 2014, 2016]  # Staggered adoption

# Generate state-level data
data = []
for state_id in range(1, n_states + 1):
    # Assign treatment cohort (or never-treated)
    if state_id <= 10:
        treat_year = 2010
    elif state_id <= 20:
        treat_year = 2012
    elif state_id <= 30:
        treat_year = 2014
    elif state_id <= 40:
        treat_year = 2016
    else:
        treat_year = 0  # Never treated

    for year in years:
        # Treatment indicator
        treated = 1 if (treat_year > 0 and year >= treat_year) else 0

        # Time to treatment (for event study)
        time_to_treat = year - treat_year if treat_year > 0 else np.nan

        # Covariates
        pop = np.random.lognormal(15, 0.5)  # Population
        income = np.random.normal(50000, 10000)  # Per capita income
        unemployment = np.random.beta(2, 8)  # Unemployment rate

        # Outcome: electricity consumption (with treatment effect)
        base_consumption = 1000 + 10 * (year - 2005) + 0.001 * pop + 0.01 * income
        treatment_effect = -50 * treated if treated else 0  # 50 unit reduction
        noise = np.random.normal(0, 30)
        consumption = base_consumption + treatment_effect + noise

        data.append({
            'state_id': state_id,
            'year': year,
            'treat_year': treat_year,
            'treated': treated,
            'time_to_treat': time_to_treat,
            'consumption': consumption,
            'pop': pop,
            'income': income,
            'unemployment': unemployment
        })

df = pd.DataFrame(data)

# Save as Stata .dta
df.to_stata('synthetic_panel.dta', write_index=False)
print(f"Generated synthetic panel: {len(df)} observations")
print(f"States: {n_states}, Years: {min(years)}-{max(years)}")
print(f"Treated states: {len(df[df['treat_year'] > 0]['state_id'].unique())}")
print(f"Never-treated states: {len(df[df['treat_year'] == 0]['state_id'].unique())}")

# Summary statistics
print("\n=== Treatment Adoption ===")
print(df[df['treat_year'] > 0][['state_id', 'treat_year']].drop_duplicates()['treat_year'].value_counts().sort_index())

print("\n=== Mean Consumption by Treatment Status ===")
summary = df.groupby(['year', 'treated'])['consumption'].mean().unstack()
print(summary)
