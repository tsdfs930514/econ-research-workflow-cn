"""
Cross-Validation: Compare Python (pyfixest) vs Stata Panel Estimates
=====================================================================
Loads synthetic_panel.dta, estimates multi-way FE model in Python,
and compares against Stata coefficients.

Threshold: PASS if all coefficient differences < 0.1%
"""

import numpy as np
import pandas as pd
import pyfixest as pf
import os

# ==============================================================================
# Paths
# ==============================================================================
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT, "synthetic_panel.dta")

# ==============================================================================
# 1. Load data
# ==============================================================================
print("=" * 70)
print("CROSS-VALIDATION: Python (pyfixest) vs Stata")
print("=" * 70)

df = pd.read_stata(DATA_PATH)
print(f"\nLoaded {len(df)} observations, {df['firm_id'].nunique()} firms, "
      f"{df['year'].nunique()} years")

# ==============================================================================
# 2. Estimate multi-way FE in Python
# ==============================================================================
print("\n--- Python: Multi-way FE (firm + year) with clustered SEs ---")

model = pf.feols(
    "productivity ~ rd_spending + capital + labor + export_share | firm_id + year",
    data=df,
    vcov={"CRV1": "firm_id"}
)

print(model.summary())

# Extract Python coefficients
py_coefs = {
    "rd_spending": model.coef()["rd_spending"],
    "capital": model.coef()["capital"],
    "labor": model.coef()["labor"],
    "export_share": model.coef()["export_share"],
}

print("\nPython coefficients:")
for var, coef in py_coefs.items():
    print(f"  {var:15s}: {coef:.6f}")

# ==============================================================================
# 3. Stata coefficients (placeholder - fill after running Stata)
# ==============================================================================
# After running 01_panel_analysis.do, paste the reghdfe multi-way FE
# coefficients here for comparison.

stata_coefs = {
    "rd_spending": 0.8010303,
    "capital": 0.2991179,
    "labor": 0.2006687,
    "export_share": 0.0912504,
}

# ==============================================================================
# 4. Compare and report PASS/FAIL
# ==============================================================================
print("\n" + "=" * 70)
print("COMPARISON: Python vs Stata")
print("=" * 70)

THRESHOLD = 0.001  # 0.1%

if any(v is None for v in stata_coefs.values()):
    print("\n[SKIP] Stata coefficients not yet filled in.")
    print("Run 01_panel_analysis.do first, then update stata_coefs dict above.")
    print("Python estimates (for reference):")
    for var, coef in py_coefs.items():
        print(f"  {var:15s}: {coef:.6f}")
else:
    all_pass = True
    for var in py_coefs:
        py_val = py_coefs[var]
        st_val = stata_coefs[var]
        if st_val == 0:
            pct_diff = abs(py_val)
        else:
            pct_diff = abs((py_val - st_val) / st_val)
        status = "PASS" if pct_diff < THRESHOLD else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {var:15s}: Python={py_val:.6f}  Stata={st_val:.6f}  "
              f"diff={pct_diff:.6%}  [{status}]")

    print("\n" + "-" * 70)
    if all_pass:
        print("OVERALL: PASS - All coefficients within 0.1% tolerance")
    else:
        print("OVERALL: FAIL - Some coefficients exceed 0.1% tolerance")
    print("-" * 70)
