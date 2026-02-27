"""
Test 5: Full Pipeline - Cross-Validation
==========================================
Load cleaned panel data, run TWFE via pyfixest matching the Stata specification,
compare coefficients with Stata output, and report PASS/FAIL.

Stata specification (Model 2):
    reghdfe consumption treated pop income unemployment,
        absorb(state_id year) vce(cluster state_id)
"""

import sys
import os
import numpy as np
import pandas as pd

try:
    import pyfixest as pf
except ImportError:
    print("ERROR: pyfixest not installed. Run: pip install pyfixest")
    sys.exit(1)


def load_stata_coefficients(temp_dir):
    """Load Stata coefficients from the temp file saved by 03_did_main.do."""
    coef_path = os.path.join(temp_dir, "stata_coefs.dta")
    if os.path.exists(coef_path):
        df_coef = pd.read_stata(coef_path)
        return df_coef["coef_treated"].iloc[0], df_coef["se_treated"].iloc[0]
    else:
        print(f"WARNING: Stata coefficient file not found at {coef_path}")
        print("         Using placeholder values. Re-run after Stata completes.")
        # Placeholder -- update after running Stata pipeline
        return None, None


def main():
    print("=" * 70)
    print("Cross-Validation: Stata vs Python (pyfixest)")
    print("=" * 70)

    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    v1_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    clean_dir = os.path.join(v1_dir, "data", "clean")
    temp_dir = os.path.join(v1_dir, "data", "temp")

    # -----------------------------------------------------------------------
    # Load cleaned data
    # -----------------------------------------------------------------------
    data_path = os.path.join(clean_dir, "panel_cleaned.dta")
    if not os.path.exists(data_path):
        print(f"ERROR: Cleaned data not found at {data_path}")
        print("       Run Stata pipeline first (master.do).")
        sys.exit(1)

    df = pd.read_stata(data_path)
    print(f"\nData loaded: {len(df)} observations, {len(df.columns)} variables")
    print(f"States: {df['state_id'].nunique()}, Years: {df['year'].min()}-{df['year'].max()}")

    # -----------------------------------------------------------------------
    # Python TWFE estimation (matching Stata Model 2)
    # -----------------------------------------------------------------------
    print("\n--- Python TWFE Estimation ---")

    # Ensure correct types for pyfixest
    df["state_id"] = df["state_id"].astype(int)
    df["year"] = df["year"].astype(int)

    model = pf.feols(
        "consumption ~ treated + pop + income + unemployment | state_id + year",
        data=df,
        vcov={"CRV1": "state_id"},
    )

    print(model.summary())

    py_coef = model.coef()["treated"]
    py_se = model.se()["treated"]

    print(f"\nPython coefficient (treated): {py_coef:.6f}")
    print(f"Python std. error  (treated): {py_se:.6f}")

    # -----------------------------------------------------------------------
    # Load Stata coefficients
    # -----------------------------------------------------------------------
    print("\n--- Stata Coefficients ---")
    stata_coef, stata_se = load_stata_coefficients(temp_dir)

    if stata_coef is not None:
        print(f"Stata coefficient (treated): {stata_coef:.6f}")
        print(f"Stata std. error  (treated): {stata_se:.6f}")
    else:
        print("Stata coefficients not available. Skipping comparison.")
        print("\nTo complete cross-validation:")
        print("  1. Run master.do in Stata")
        print("  2. Re-run this script")
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Compare coefficients
    # -----------------------------------------------------------------------
    print("\n--- Comparison ---")
    print(f"{'':30s} {'Stata':>12s} {'Python':>12s} {'Diff':>12s}")
    print("-" * 70)

    coef_diff = abs(py_coef - stata_coef)
    se_diff = abs(py_se - stata_se)

    # Percentage difference relative to Stata estimate
    if stata_coef != 0:
        coef_pct_diff = abs(coef_diff / stata_coef) * 100
    else:
        coef_pct_diff = float("inf")

    if stata_se != 0:
        se_pct_diff = abs(se_diff / stata_se) * 100
    else:
        se_pct_diff = float("inf")

    print(f"{'Coefficient (treated)':30s} {stata_coef:12.6f} {py_coef:12.6f} {coef_diff:12.6f}")
    print(f"{'Std. Error (treated)':30s} {stata_se:12.6f} {py_se:12.6f} {se_diff:12.6f}")
    print(f"{'Coef % difference':30s} {'':12s} {'':12s} {coef_pct_diff:11.4f}%")
    print(f"{'SE % difference':30s} {'':12s} {'':12s} {se_pct_diff:11.4f}%")

    # -----------------------------------------------------------------------
    # PASS/FAIL criteria
    # -----------------------------------------------------------------------
    print("\n--- Results ---")

    COEF_THRESHOLD = 0.001  # 0.1% tolerance for coefficient match
    SE_THRESHOLD = 0.05     # 5% tolerance for SE (clustering differences expected)
    TRUE_EFFECT = -50       # DGP true treatment effect
    EFFECT_TOLERANCE = 30   # how close to true effect (generous for finite sample)

    results = []

    # Test 1: Coefficient match
    if coef_pct_diff < COEF_THRESHOLD * 100:
        results.append(("Coef match (< 0.1%)", "PASS", coef_pct_diff))
    else:
        results.append(("Coef match (< 0.1%)", "FAIL", coef_pct_diff))

    # Test 2: SE match (more lenient due to clustering implementation differences)
    if se_pct_diff < SE_THRESHOLD * 100:
        results.append(("SE match (< 5%)", "PASS", se_pct_diff))
    else:
        results.append(("SE match (< 5%)", "FAIL", se_pct_diff))

    # Test 3: Coefficient near true DGP value
    if abs(py_coef - TRUE_EFFECT) < EFFECT_TOLERANCE:
        results.append(("Near true effect (-50)", "PASS", py_coef))
    else:
        results.append(("Near true effect (-50)", "FAIL", py_coef))

    # Test 4: Coefficient is negative (correct sign)
    if py_coef < 0:
        results.append(("Correct sign (negative)", "PASS", py_coef))
    else:
        results.append(("Correct sign (negative)", "FAIL", py_coef))

    # Print results
    all_pass = True
    for test_name, status, value in results:
        marker = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"  {marker} {test_name}: {value:.6f}")
        if status == "FAIL":
            all_pass = False

    # -----------------------------------------------------------------------
    # Final verdict
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    if all_pass:
        print("OVERALL: PASS -- Stata and Python results match within tolerance")
    else:
        print("OVERALL: FAIL -- Some tests did not pass")
    print("=" * 70)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
