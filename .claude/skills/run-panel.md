---
description: "Run complete Panel FE/RE/GMM analysis pipeline"
user_invocable: true
---

# /run-panel — Panel Data Analysis Pipeline (FE/RE/GMM)

When the user invokes `/run-panel`, execute a complete panel data analysis pipeline covering panel setup and diagnostics, FE vs RE estimation with Hausman test, serial correlation and cross-sectional dependence tests, dynamic panel GMM (if requested), and Python cross-validation.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## Required Stata Packages

```stata
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install xtabond2, replace      // System/Difference GMM
cap ssc install xtserial, replace  // Wooldridge test — may be removed from SSC (Issue #6)
ssc install xtscc, replace         // Driscoll-Kraay standard errors
ssc install coefplot, replace
```

**Note on xtserial**: This package has been removed from SSC in some periods. Stata 18 may have built-in equivalents. Always use `cap ssc install` and wrap `xtserial` calls in `cap noisily` (Issues #6-7).

## Step 0: Gather Inputs

Ask the user for the following before proceeding:

- **Dataset**: path to .dta file
- **Panel unit variable**: entity identifier (e.g., firm_id, state_id, country)
- **Panel time variable**: time identifier (e.g., year, quarter, month)
- **Outcome variable**: dependent variable Y
- **Regressors**: independent variables of interest
- **Control variables**: additional covariates
- **Cluster variable**: variable for clustered standard errors (often same as unit variable)
- **Dynamic panel needed?**: whether to include lagged dependent variable and estimate via GMM (yes/no)
- **Additional fixed effects**: any FE beyond unit and time (e.g., industry, region)

## Step 1: Panel Setup and Description (Stata .do file)

Create a Stata .do file for panel setup and descriptive analysis:

```stata
* =============================================================================
* Panel Data — Setup and Description
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear

* --- Set panel structure ---
xtset UNIT_VAR TIME_VAR

* --- Panel structure description ---
xtdescribe
* Reports: number of panels, time periods, gaps, balance

* --- Between/within variation decomposition ---
xtsum OUTCOME_VAR REGRESSORS CONTROLS
* Reports: overall, between, and within standard deviations
* Key insight: FE exploits within-variation; RE uses both

* --- Tabulate panel balance ---
di "Panel balance check:"
tab TIME_VAR, missing
bysort UNIT_VAR: gen T_i = _N
tab T_i
drop T_i

* --- Summary statistics ---
summarize OUTCOME_VAR REGRESSORS CONTROLS, detail
```

Execute and check the .log file. Report panel structure (balanced vs unbalanced, number of units and time periods, gaps). Highlight the within vs between variation decomposition — if within-variation is small relative to between, FE estimates may be imprecise.

## Step 2: FE vs RE Estimation (Stata .do file)

Create a Stata .do file for the core FE and RE estimations:

```stata
* =============================================================================
* Panel Data — Fixed Effects vs Random Effects
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear
xtset UNIT_VAR TIME_VAR

* --- Pooled OLS (baseline, likely biased) ---
reg OUTCOME_VAR REGRESSORS CONTROLS, vce(cluster CLUSTER_VAR)
estimates store pooled_ols

* --- Fixed Effects ---
xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe vce(cluster CLUSTER_VAR)
estimates store fe_model

* --- Random Effects ---
xtreg OUTCOME_VAR REGRESSORS CONTROLS, re vce(cluster CLUSTER_VAR)
estimates store re_model

* --- Hausman Test ---
* Need to re-estimate without cluster VCE for valid Hausman test
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe
estimates store fe_hausman
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, re
estimates store re_hausman

hausman fe_hausman re_hausman
* H0: RE is consistent and efficient (differences in coefficients are not systematic)
* Rejection => use FE (RE is inconsistent due to correlation between unit effects and regressors)

local hausman_chi2 = r(chi2)
local hausman_p = r(p)
di "Hausman test chi2: `hausman_chi2'"
di "Hausman test p-value: `hausman_p'"
* NOTE: Hausman chi2 can be negative when FE strongly dominates RE
* (variance matrix difference is not positive semi-definite). This is
* known Stata behavior — FE is still the correct choice. See Issue #9.
if `hausman_chi2' < 0 {
    di "Result: Negative chi2 (`hausman_chi2') — FE strongly dominates RE."
    di "  This occurs when V_FE - V_RE is not positive semi-definite."
    di "  Interpretation: FE is the correct model."
}
else if `hausman_p' < 0.05 {
    di "Result: Reject RE in favor of FE (p < 0.05)"
}
else {
    di "Result: Cannot reject RE (p >= 0.05) — RE may be preferred for efficiency"
}

* --- Multi-way FE with reghdfe (preferred for multiple FE) ---
reghdfe OUTCOME_VAR REGRESSORS CONTROLS, absorb(UNIT_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
estimates store fe_reghdfe
```

Execute and check the .log file. Report Hausman test results and the recommended model (FE or RE).

## Step 3: Diagnostic Tests (Stata .do file)

Create a Stata .do file for panel diagnostic tests:

```stata
* =============================================================================
* Panel Data — Diagnostic Tests
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear
xtset UNIT_VAR TIME_VAR

* --- 1. Serial Correlation: Wooldridge Test ---
* H0: No first-order autocorrelation in panel data
* NOTE: xtserial may be unavailable (removed from SSC). Wrap in cap noisily.
cap noisily xtserial OUTCOME_VAR REGRESSORS CONTROLS
if _rc != 0 {
    di "xtserial not available. Skipping Wooldridge serial correlation test."
    di "Alternative: check AR(1) via xtabond2 diagnostics or estat abond."
}
* If rejected: use clustered SEs or Newey-West, or AR(1) correction

* --- 2. Cross-Sectional Dependence: Pesaran CD Test ---
* H0: No cross-sectional dependence
* First run FE model
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe
cap noisily xtcsd, pesaran abs
if _rc != 0 {
    di "xtcsd not available. Skipping Pesaran CD test."
}
* If rejected: consider Driscoll-Kraay standard errors

* --- 3. Heteroskedasticity: Modified Wald Test ---
* H0: Homoskedastic errors across panels
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe
cap noisily xttest3
if _rc != 0 {
    di "xttest3 not available. Skipping Modified Wald test."
}
* If rejected: use robust/clustered SEs (already doing this)

* --- 4. Unit Root Tests (if T is large) ---
* Only meaningful for macro panels with large T
* xtunitroot llc OUTCOME_VAR, trend lags(aic 10)   // Levin-Lin-Chu
* xtunitroot ips OUTCOME_VAR, trend lags(aic 10)    // Im-Pesaran-Shin
* xtunitroot fisher OUTCOME_VAR, dfuller lags(4)     // Fisher-type ADF

* --- Summary ---
di "============================================="
di "Panel Diagnostics Summary"
di "============================================="
di "Run serial correlation, CD, and heteroskedasticity"
di "tests above. Use results to choose appropriate SEs."
di "============================================="
```

Execute and check the .log file. Summarize which diagnostics reject and what implications they have for standard error computation:
- Serial correlation => cluster at unit level or use Newey-West
- Cross-sectional dependence => consider Driscoll-Kraay SEs
- Heteroskedasticity => use robust/clustered SEs

## Step 4: Dynamic Panel GMM (if requested) (Stata .do file)

Only create this if the user requested dynamic panel analysis:

```stata
* =============================================================================
* Panel Data — Dynamic Panel GMM (Arellano-Bond / Blundell-Bond)
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear
xtset UNIT_VAR TIME_VAR

* --- System GMM (Blundell-Bond) via xtabond2 ---
* Requires: ssc install xtabond2
* NOTE: Use cap noisily as xtabond2 can fail with certain panel structures
*
* DYNAMIC LAG SYNTAX: Published papers often use L(1/N).var for N lags:
*   L(1/4).y  = l.y l2.y l3.y l4.y   (4 lags of dependent variable)
*   L(1/8).y  = l.y ... l8.y          (8 lags)
* When N > 4 lags, test whether higher-order lags are jointly significant:
*   test l5.y l6.y l7.y l8.y
*
* HELMERT / FORWARD ORTHOGONAL DEVIATIONS:
* Some papers (e.g., Acemoglu et al. 2019 JPE) use Helmert-transformed data
* instead of first-differencing. xtabond2 supports this natively:
*   xtabond2 ... , orthogonal ...
* Alternatively, authors define custom programs for Helmert transformation
* (see "program define helm" pattern in published replication code).
*
* DIFFERENCE-ONLY GMM (noleveleq):
* Some papers estimate difference GMM only (not system GMM) by adding:
*   xtabond2 ... , noleveleq ...
* This drops the level equation, estimating only from first differences.
*
cap noisily xtabond2 OUTCOME_VAR L.OUTCOME_VAR REGRESSORS CONTROLS, ///
    gmm(L.OUTCOME_VAR, lag(2 4)) ///
    iv(REGRESSORS CONTROLS) ///
    two robust small

if _rc != 0 {
    di "xtabond2 failed (rc = " _rc "). Skipping GMM estimation."
    di "Common causes: too few time periods, singular matrix, or panel gaps."
}
else {
    estimates store gmm_sys
}

* --- Key Diagnostics ---
* 1. Hansen J test of overidentifying restrictions
*    H0: instruments are valid. Do NOT want to reject.
di "Hansen J test p-value: " e(hansenp)

* 2. AR(1) and AR(2) tests
*    AR(1): expected to reject (by construction)
*    AR(2): should NOT reject for GMM consistency
di "AR(1) test p-value: " e(ar1p)
di "AR(2) test p-value: " e(ar2p)

* 3. Instrument proliferation check
*    Rule of thumb: # instruments should be <= # groups
di "Number of instruments: " e(j)
di "Number of groups: " e(g)
if e(j) > e(g) {
    di "WARNING: Too many instruments relative to groups — consider collapsing"
    * Re-estimate with collapse option
    xtabond2 OUTCOME_VAR L.OUTCOME_VAR REGRESSORS CONTROLS, ///
        gmm(L.OUTCOME_VAR, lag(2 4) collapse) ///
        iv(REGRESSORS CONTROLS) ///
        two robust small
    estimates store gmm_sys_collapse
}

* --- Difference GMM (Arellano-Bond) for comparison ---
xtabond2 OUTCOME_VAR L.OUTCOME_VAR REGRESSORS CONTROLS, ///
    gmm(L.OUTCOME_VAR, lag(2 4)) ///
    iv(REGRESSORS CONTROLS) ///
    two robust small nodiffsargan
estimates store gmm_diff
```

Execute and check the .log file. Report:
- AR(2) test: must fail to reject for GMM to be valid
- Hansen J: must fail to reject for instruments to be valid
- Instrument count vs group count

## Step 5: Python Cross-Validation

Create a Python script for cross-validation:

```python
import pandas as pd
import pyfixest as pf

# Load data
df = pd.read_stata("DATASET_PATH")

# FE estimation via pyfixest
model_fe = pf.feols("OUTCOME_VAR ~ REGRESSORS + CONTROLS | UNIT_VAR + TIME_VAR",
                     data=df,
                     vcov={"CRV1": "CLUSTER_VAR"})
print("=== Fixed Effects (pyfixest) ===")
print(model_fe.summary())

# Pooled OLS
model_ols = pf.feols("OUTCOME_VAR ~ REGRESSORS + CONTROLS",
                      data=df,
                      vcov={"CRV1": "CLUSTER_VAR"})
print("\n=== Pooled OLS (pyfixest) ===")
print(model_ols.summary())

# Cross-validate FE coefficient with Stata
stata_fe_coef = STATA_FE_COEF  # from Step 2 log (reghdfe)
python_fe_coef = model_fe.coef()["MAIN_REGRESSOR"]
pct_diff = abs(stata_fe_coef - python_fe_coef) / abs(stata_fe_coef) * 100
print(f"\nCross-validation (FE coefficient on MAIN_REGRESSOR):")
print(f"  Stata FE:  {stata_fe_coef:.6f}")
print(f"  Python FE: {python_fe_coef:.6f}")
print(f"  Pct diff:  {pct_diff:.4f}%")
if pct_diff < 0.01:
    print("  PASS: Coefficients match within tolerance")
else:
    print("  WARNING: Coefficients diverge — investigate specification")
```

Execute and report results.

## Step 6: Output Generation

Create a combined LaTeX table:

```stata
* --- Combined Output Table ---
esttab pooled_ols fe_model re_model fe_reghdfe using "output/tables/panel_results.tex", ///
    mtitles("Pooled OLS" "FE (xtreg)" "RE (xtreg)" "FE (reghdfe)") ///
    cells(b(star fmt(3)) se(par fmt(3))) ///
    starlevels(* 0.10 ** 0.05 *** 0.01) ///
    stats(N r2_w r2_b r2_o, labels("Observations" "R2 (within)" "R2 (between)" "R2 (overall)")) ///
    addnotes("Hausman test p-value: [from Step 2]" ///
             "Wooldridge serial corr test p-value: [from Step 3]" ///
             "Pesaran CD test p-value: [from Step 3]" ///
             "Cluster: CLUSTER_VAR") ///
    title("Panel Estimation Results") replace

* If GMM was estimated, add a separate table
* esttab fe_reghdfe gmm_sys gmm_diff using "output/tables/panel_gmm_results.tex", ///
*     mtitles("FE" "System GMM" "Difference GMM") ...
```

Ensure all outputs are saved:

- `output/tables/panel_results.tex` — Main panel results (Pooled OLS, FE, RE)
- `output/tables/panel_gmm_results.tex` — GMM results (if applicable)
- Cross-validation report (printed in console)

## Interpretation Guide

After all steps, provide a written summary:

1. **Panel Structure**: Balanced or unbalanced? How many units and time periods? Any gaps?
2. **Within vs Between Variation**: Is there sufficient within-unit variation for FE? If within-variation is tiny, FE estimates will be noisy.
3. **FE vs RE (Hausman)**: Which model does the Hausman test favor? If FE is selected, there is evidence that unit effects correlate with regressors.
4. **Diagnostic Tests**:
   - Serial correlation: present? Impact on inference.
   - Cross-sectional dependence: present? May need Driscoll-Kraay SEs.
   - Heteroskedasticity: present? Clustered SEs address this.
5. **GMM (if applicable)**:
   - Is AR(2) insignificant? (required for validity)
   - Does Hansen J fail to reject? (required for instrument validity)
   - Is instrument count reasonable relative to groups?
   - How does the GMM coefficient on the lagged DV compare to the OLS upper bound and FE lower bound? (Nickell bias check)
6. **Cross-Validation**: Do Stata and Python FE coefficients match?
7. **Recommended Specification**: Based on diagnostics, which model and SE specification to use.

## Execution Notes

- Run all Stata .do files via: `"D:\Stata18\StataMP-64.exe" -e do "script.do"` (必须用 `-e` 自动退出)
- Always read the `.log` file after each Stata execution to check for errors
- Required Stata packages: `reghdfe`, `ftools`, `estout`, `xtabond2`, `xtserial`, `xtscc`, `coefplot` (install via `ssc install PACKAGE, replace`)
- Create `output/tables/` and `output/figures/` directories if they don't exist
- Generate both Stata and Python code for every pipeline
- For the Hausman test, models must be estimated without robust/clustered SEs first, then re-estimate with clustered SEs for reporting

## Handling Old Stata Syntax in Replication Code

Published replication packages may contain deprecated Stata commands (Issue #23):
- `set mem 250m` / `set memory` — not needed in Stata 18 (memory is dynamic)
- `clear matrix` — replaced by `clear all` or `matrix drop _all`
- `set matsize 800` — Stata 18 default is 11000, usually sufficient

When adapting old replication code, simply omit these commands. Do not include them in new .do files.

## Advanced Patterns Reference

For advanced patterns from published papers (impulse responses via `nlcom` chain, Helmert/forward orthogonal deviations, HHK minimum distance estimator, k-class estimation, bootstrap with `cluster()`/`idcluster()`, multi-way clustering, interaction heterogeneity, matrix operations), see `advanced-stata-patterns.md`.
