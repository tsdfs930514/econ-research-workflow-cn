"""
Cross-validation: Stata vs Python pyfixest
Compare DID results between Stata TWFE and Python
"""
import pandas as pd
import pyfixest as pf

# Load data
df = pd.read_stata("synthetic_panel.dta")

# Create treatment cohort for pyfixest
df['first_treat'] = df['treat_year']
df.loc[df['treat_year'] == 0, 'first_treat'] = 0

print("=" * 60)
print("Cross-Validation: Stata vs Python pyfixest")
print("=" * 60)

# --- Python TWFE (matches Stata reghdfe) ---
print("\n=== Python TWFE ===")
model_py = pf.feols(
    "consumption ~ treated + pop + income + unemployment | state_id + year",
    data=df,
    vcov={"CRV1": "state_id"}
)
print(model_py.summary())

# Extract key stats
py_coef = model_py.coef()["treated"]
py_se = model_py.se()["treated"]
py_r2 = model_py._r2_within
py_n = model_py._N

print(f"\nPython Results:")
print(f"  Treated coef: {py_coef:.6f}")
print(f"  SE:           {py_se:.6f}")
print(f"  Within R²:    {py_r2:.6f}")
print(f"  N:            {py_n}")

# --- Stata results (from log) ---
stata_coef = -48.069306
stata_se = 4.045206
stata_r2 = 0.9997
stata_n = 750

print(f"\nStata Results (from log):")
print(f"  Treated coef: {stata_coef:.6f}")
print(f"  SE:           {stata_se:.6f}")
print(f"  Within R²:    {stata_r2:.6f}")
print(f"  N:            {stata_n}")

# --- Cross-validation ---
print(f"\n=== Cross-Validation ===")
coef_diff = abs(stata_coef - py_coef) / abs(stata_coef) * 100
se_diff = abs(stata_se - py_se) / stata_se * 100
r2_diff = abs(stata_r2 - py_r2)

print(f"Coefficient diff: {coef_diff:.4f}% (threshold: 0.1%)")
print(f"SE diff:          {se_diff:.4f}% (threshold: 0.5%)")
print(f"R² diff:          {r2_diff:.6f} (threshold: 0.001)")

coef_pass = coef_diff < 0.1
se_pass = se_diff < 0.5
r2_pass = r2_diff < 0.001

print(f"\nStatus:")
print(f"  Coefficient: {'PASS' if coef_pass else 'FAIL'}")
print(f"  SE:          {'PASS' if se_pass else 'FAIL'}")
print(f"  R²:          {'PASS' if r2_pass else 'FAIL'}")

overall = "PASS" if (coef_pass and se_pass and r2_pass) else "FAIL"
print(f"\nOverall: {overall}")
print("=" * 60)
