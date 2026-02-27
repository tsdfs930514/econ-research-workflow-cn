"""
Test 5: Full Pipeline - Data Generation
========================================
Generates a staggered DID panel dataset with 30 states x 10 years.

DGP:
    consumption = 1000 + 10*(year-2010) + 0.001*pop + 0.01*income
                  - 50*treated + noise(0,30)

Staggered adoption:
    States  1-8:  adopt in 2013
    States  9-16: adopt in 2015
    States 17-24: adopt in 2017
    States 25-30: never treated

Covariates:
    pop:          lognormal
    income:       normal
    unemployment: beta
"""

import numpy as np
import pandas as pd
import os

def main():
    np.random.seed(42)

    # Panel dimensions
    n_states = 30
    years = list(range(2010, 2020))  # 2010-2019
    n_years = len(years)

    # Build panel skeleton
    state_ids = np.repeat(np.arange(1, n_states + 1), n_years)
    year_vals = np.tile(years, n_states)
    n_obs = len(state_ids)

    # Assign treatment cohorts (staggered adoption)
    treat_year_map = {}
    for s in range(1, n_states + 1):
        if 1 <= s <= 8:
            treat_year_map[s] = 2013
        elif 9 <= s <= 16:
            treat_year_map[s] = 2015
        elif 17 <= s <= 24:
            treat_year_map[s] = 2017
        else:  # 25-30
            treat_year_map[s] = 0  # never treated

    treat_year = np.array([treat_year_map[s] for s in state_ids])

    # Treatment indicator: 1 if year >= adoption year (and adopted)
    treated = np.where(
        (treat_year > 0) & (year_vals >= treat_year), 1, 0
    )

    # Covariates
    pop = np.random.lognormal(mean=12, sigma=0.5, size=n_obs)
    pop = np.round(pop).astype(int)

    income = np.random.normal(loc=50000, scale=10000, size=n_obs)
    income = np.round(income, 2)

    unemployment = np.random.beta(a=2, b=20, size=n_obs)
    unemployment = np.round(unemployment, 4)

    # State fixed effects (persistent differences across states)
    state_fe = np.random.normal(0, 50, size=n_states)
    state_fe_expanded = np.array([state_fe[s - 1] for s in state_ids])

    # Outcome variable
    noise = np.random.normal(0, 30, size=n_obs)
    consumption = (
        1000
        + 10 * (year_vals - 2010)
        + 0.001 * pop
        + 0.01 * income
        + state_fe_expanded
        - 50 * treated
        + noise
    )
    consumption = np.round(consumption, 2)

    # State names
    state_names = [f"State_{s:02d}" for s in range(1, n_states + 1)]
    state_name_arr = np.array([state_names[s - 1] for s in state_ids])

    # Build DataFrame
    df = pd.DataFrame({
        "state_id": state_ids,
        "state_name": state_name_arr,
        "year": year_vals,
        "consumption": consumption,
        "pop": pop,
        "income": income,
        "unemployment": unemployment,
        "treat_year": treat_year,
        "treated": treated,
    })

    # Sort
    df = df.sort_values(["state_id", "year"]).reset_index(drop=True)

    # Validate
    assert len(df) == 300, f"Expected 300 obs, got {len(df)}"
    assert df.groupby(["state_id", "year"]).size().max() == 1, "Duplicate state-year"
    assert df["treated"].sum() > 0, "No treated observations"
    assert (df.loc[df["treat_year"] == 0, "treated"] == 0).all(), "Never-treated error"

    # Save to Stata format
    out_dir = os.path.join("v1", "data", "raw")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "policy_panel.dta")
    df.to_stata(out_path, write_index=False, version=118)

    print(f"Dataset saved: {out_path}")
    print(f"Observations: {len(df)}")
    print(f"States: {df['state_id'].nunique()}")
    print(f"Years: {df['year'].min()}-{df['year'].max()}")
    print(f"Treated obs: {df['treated'].sum()}")
    print(f"Never-treated states: {(df.groupby('state_id')['treat_year'].first() == 0).sum()}")
    print(f"\nConsumption summary:")
    print(df["consumption"].describe())
    print(f"\nTreatment cohorts:")
    cohorts = df.groupby("state_id")["treat_year"].first()
    for yr in sorted(cohorts.unique()):
        label = "Never" if yr == 0 else str(yr)
        count = (cohorts == yr).sum()
        print(f"  {label}: {count} states")


if __name__ == "__main__":
    main()
