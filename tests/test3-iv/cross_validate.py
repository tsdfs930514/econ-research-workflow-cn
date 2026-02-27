"""
Cross-validation: Stata vs Python pyfixest for IV analysis
Compare OLS and 2SLS results between Stata and Python
"""
import pandas as pd
import pyfixest as pf
import numpy as np
from pathlib import Path

# Load data
df = pd.read_stata("synthetic_iv.dta")

print("=" * 60)
print("Cross-Validation: Stata vs Python (IV Analysis)")
print("=" * 60)

# =========================================================================
# Python OLS (matches Stata reghdfe)
# =========================================================================
print("\n=== Python OLS ===")
model_ols = pf.feols(
    "employment ~ treatment + pop + manufacturing | state_id + year",
    data=df,
    vcov={"CRV1": "state_id"}
)
print(model_ols.summary())

py_ols_coef = model_ols.coef()["treatment"]
py_ols_se = model_ols.se()["treatment"]
print(f"Python OLS treatment coef: {py_ols_coef:.6f}")
print(f"Python OLS treatment SE:   {py_ols_se:.6f}")

# =========================================================================
# Python 2SLS via pyfixest
# Syntax: Y ~ exog | FEs | endog ~ instrument
# =========================================================================
print("\n=== Python 2SLS ===")
model_iv = pf.feols(
    "employment ~ pop + manufacturing | state_id + year | treatment ~ sci",
    data=df,
    vcov={"CRV1": "state_id"}
)
print(model_iv.summary())

py_iv_coef = model_iv.coef()["treatment"]
py_iv_se = model_iv.se()["treatment"]
print(f"Python 2SLS treatment coef: {py_iv_coef:.6f}")
print(f"Python 2SLS treatment SE:   {py_iv_se:.6f}")

# =========================================================================
# Load Stata coefficients (from saved .dta or hardcoded after first run)
# =========================================================================
print("\n=== Cross-Validation ===")

# Try to load Stata coefficients from saved file
stata_coefs_path = Path("output/stata_iv_coefs.dta")
if stata_coefs_path.exists():
    stata_df = pd.read_stata(str(stata_coefs_path))
    stata_ols_coef = stata_df['ols_coef'].iloc[0]
    stata_iv_coef = stata_df['iv_coef'].iloc[0]
    stata_method = stata_df['iv_method'].iloc[0]
    print(f"Stata OLS coef:  {stata_ols_coef:.6f}")
    print(f"Stata IV coef:   {stata_iv_coef:.6f} (method: {stata_method})")

    # OLS comparison
    ols_diff = abs(stata_ols_coef - py_ols_coef) / abs(stata_ols_coef) * 100
    print(f"\nOLS coefficient diff: {ols_diff:.4f}% (threshold: 0.1%)")
    ols_pass = ols_diff < 0.1
    print(f"OLS: {'PASS' if ols_pass else 'FAIL'}")

    # IV comparison
    iv_diff = abs(stata_iv_coef - py_iv_coef) / abs(stata_iv_coef) * 100
    print(f"\n2SLS coefficient diff: {iv_diff:.4f}% (threshold: 0.1%)")
    iv_pass = iv_diff < 0.1
    print(f"2SLS: {'PASS' if iv_pass else 'FAIL'}")

    overall = "PASS" if (ols_pass and iv_pass) else "FAIL"
    print(f"\nOverall: {overall}")
else:
    print("Stata coefficients file not found at output/stata_iv_coefs.dta")
    print("Run 01_iv_analysis.do in Stata first, then re-run this script.")
    print(f"\nPython-only results:")
    print(f"  OLS treatment coef:  {py_ols_coef:.6f}")
    print(f"  2SLS treatment coef: {py_iv_coef:.6f}")
    print(f"  True effect:         -2.0")

print("=" * 60)
