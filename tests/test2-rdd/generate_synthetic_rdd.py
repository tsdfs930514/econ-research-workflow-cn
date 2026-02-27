"""
Generate synthetic RDD data
Mimics apep_0439 structure: running variable with cutoff at 0
"""
import pandas as pd
import numpy as np

np.random.seed(42)

# Parameters
n = 5000
cutoff = 0

# Generate running variable (centered at cutoff)
# Mix of values below and above cutoff
running = np.random.normal(0, 10, n)

# Treatment: 1 if running >= cutoff
treat = (running >= cutoff).astype(int)

# Generate covariates
age = np.random.normal(40, 10, n)
education = np.random.normal(12, 3, n)

# Outcome with RDD effect
# Base: linear in running var + covariates
# Treatment effect: +2 units jump at cutoff
base_outcome = 50 + 0.5 * running + 0.1 * age + 0.5 * education
treatment_effect = 2.0 * treat  # True effect = 2.0
noise = np.random.normal(0, 5, n)
outcome = base_outcome + treatment_effect + noise

# Create DataFrame
df = pd.DataFrame({
    'id': range(1, n + 1),
    'running': running,
    'treat': treat,
    'outcome': outcome,
    'age': age,
    'education': education
})

# Save as Stata .dta
df.to_stata('synthetic_rdd.dta', write_index=False)

print(f"Generated synthetic RDD data: {n} observations")
print(f"Cutoff: {cutoff}")
print(f"Below cutoff: {sum(running < cutoff)}")
print(f"Above cutoff: {sum(running >= cutoff)}")
print(f"\n=== Outcome by treatment status ===")
print(df.groupby('treat')['outcome'].agg(['mean', 'std', 'count']))
print(f"\n=== Running variable stats ===")
print(df['running'].describe())
