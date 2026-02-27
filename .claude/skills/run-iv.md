---
description: "Run complete IV/2SLS analysis pipeline with diagnostics"
user_invocable: true
---

# /run-iv — Instrumental Variables / 2SLS Analysis Pipeline

When the user invokes `/run-iv`, execute a complete IV analysis pipeline covering first stage, reduced form, 2SLS/LIML estimation, comprehensive diagnostics (KP F, AR CIs, DWH, Hansen J), distance-credibility analysis, and Python cross-validation.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## Required Stata Packages (install in this order)

The dependency order matters — `ranktest` must be installed before `ivreg2`, and `ivreg2` before `ivreghdfe`. Missing `ranktest` causes the `struct ms_vcvorthog undefined` error.

```stata
ssc install ranktest, replace      // MUST be first
ssc install ivreg2, replace        // depends on ranktest
ssc install reghdfe, replace
ssc install ftools, replace
ssc install ivreghdfe, replace     // depends on ivreg2 + reghdfe
ssc install estout, replace
ssc install coefplot, replace
ssc install weakiv, replace
ssc install boottest, replace
```

## Step 0: Gather Inputs

Ask the user for the following before proceeding:

- **Dataset**: path to .dta file
- **Endogenous variable(s)**: variable(s) suspected of being endogenous
- **Instrument(s)**: excluded instrument(s) for the endogenous variable(s)
- **Outcome variable**: dependent variable Y
- **Control variables**: exogenous covariates included in all stages
- **Fixed effects**: FE to absorb (e.g., unit FE, time FE, unit x time FE)
- **Cluster variable**: variable for clustered standard errors
- **Alternative outcomes** (optional): for multi-outcome panels (Panel A/B)

Note whether the model is exactly identified (# instruments = # endogenous) or overidentified (# instruments > # endogenous).

**Data exploration note**: Use `summarize` and `codebook` to inspect variables — NOT `tab` for continuous variables. `tab` on a continuous variable generates one row per unique value, producing massive output and potentially crashing for large datasets (Issue #5). Reserve `tab` for categorical/binary variables with few distinct values.

## Step 1: First Stage & Reduced Form (Stata .do file)

```stata
/*==============================================================================
  IV Analysis — Step 1: First Stage & Reduced Form
  Reference: APE paper 0185 (Social Networks & Labor Markets)
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/iv_01_firststage.log", replace

use "DATASET_PATH", clear

* --- First Stage Regression ---
eststo clear
eststo fs_main: reghdfe ENDOG_VAR INSTRUMENT(S) CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* First-stage F-statistic on excluded instruments
test INSTRUMENT(S)
local fs_F = r(F)
local fs_p = r(p)
di "=== First-Stage F-statistic: `fs_F' (p = `fs_p') ==="
* Rule of thumb: F > 10 (Stock-Yogo); F > 23 (Lee et al. 2022 tF)
* For heteroskedastic/clustered: compare to Montiel Olea-Pflueger effective F

* Partial R-squared of excluded instruments
reghdfe ENDOG_VAR CONTROLS, absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
local r2_excl = e(r2)
eststo fs_main
local r2_full = e(r2)
local partial_r2 = `r2_full' - `r2_excl'
di "Partial R-squared: `partial_r2'"

* --- Reduced Form ---
eststo rf_main: reghdfe OUTCOME_VAR INSTRUMENT(S) CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
di "Reduced form coefficient / FS coefficient ≈ 2SLS (Wald)"

* --- First Stage Table (dedicated, following APE 0185 tab3 format) ---
esttab fs_main using "output/tables/tab_first_stage.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(INSTRUMENT(S)) label booktabs replace ///
    scalars("r2_within Within R$^2$" "N Observations") ///
    addnotes("F-statistic on excluded instrument(s): `fs_F'" ///
             "Dependent variable: ENDOG_VAR") ///
    title("First Stage: INSTRUMENT $\rightarrow$ ENDOG\_VAR")

log close
```

## Step 2: OLS Baseline & 2SLS Estimation (Stata .do file)

**Fallback strategy:** If `ivreghdfe` crashes (e.g., missing `ranktest`), fall back to `ivreg2` with manually generated FE dummies. If `ivreg2` is also unavailable, compute a manual Wald estimator (reduced form / first stage).

```stata
/*==============================================================================
  IV Analysis — Step 2: OLS Baseline, 2SLS, and LIML
  Fallback chain: ivreghdfe -> ivreg2 (+ FE dummies) -> manual Wald
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/iv_02_estimation.log", replace

use "DATASET_PATH", clear

eststo clear

* --- OLS Baseline ---
eststo ols_base: reghdfe OUTCOME_VAR ENDOG_VAR CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- 2SLS with ivreghdfe (preferred) ---
cap noisily ivreghdfe OUTCOME_VAR CONTROLS ///
    (ENDOG_VAR = INSTRUMENT(S)), ///
    absorb(FIXED_EFFECTS) cluster(CLUSTER_VAR) first
if _rc != 0 {
    di "ivreghdfe failed. Trying ivreg2 with FE dummies..."
    * Generate FE dummies manually
    quietly: tab UNIT_VAR, gen(_unit_fe)
    quietly: tab TIME_VAR, gen(_time_fe)
    cap which ivreg2
    if _rc == 0 {
        ivreg2 OUTCOME_VAR CONTROLS _unit_fe* _time_fe* ///
            (ENDOG_VAR = INSTRUMENT(S)), cluster(CLUSTER_VAR) first ffirst
    }
    else {
        * Manual Wald = RF_coef / FS_coef
        di "ivreg2 not available. Computing manual Wald estimator."
    }
    cap drop _unit_fe* _time_fe*
}
else {
    eststo iv_2sls
}
local kp_f = e(widstat)
di "Kleibergen-Paap rk Wald F: `kp_f'"

* --- LIML (robust to weak instruments) ---
cap noisily ivreghdfe OUTCOME_VAR CONTROLS ///
    (ENDOG_VAR = INSTRUMENT(S)), ///
    absorb(FIXED_EFFECTS) cluster(CLUSTER_VAR) liml
if _rc == 0 {
    eststo iv_liml
}
di "LIML estimate: " _b[ENDOG_VAR]
* Large LIML-2SLS gap indicates weak instrument concern

* --- Main Results Table (Panel A/B format, following APE 0185 tab2) ---
esttab ols_base iv_2sls iv_liml using "output/tables/tab_iv_main.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("OLS" "2SLS" "LIML") ///
    keep(ENDOG_VAR) label booktabs replace ///
    scalars("widstat KP F-stat" "N_clust Clusters" "N Observations") ///
    addnotes("Standard errors clustered at CLUSTER_VAR level." ///
             "Instrument(s): INSTRUMENT(S)." ///
             "KP F = Kleibergen-Paap rk Wald F-statistic.") ///
    title("IV/2SLS Estimation Results")

log close
```

## Step 3: Comprehensive Diagnostics (Stata .do file)

```stata
/*==============================================================================
  IV Analysis — Step 3: Diagnostics
  KP F, DWH endogeneity, Hansen J, Anderson-Rubin CIs
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/iv_03_diagnostics.log", replace

use "DATASET_PATH", clear

* --- Full diagnostics via ivreg2 (without multi-way FE) ---
* Note: if multi-way FE needed, partial them out first
ivreg2 OUTCOME_VAR CONTROLS (ENDOG_VAR = INSTRUMENT(S)), ///
    cluster(CLUSTER_VAR) first ffirst endog(ENDOG_VAR)

* Diagnostics are automatically reported by ivreg2:
* - KP rk Wald F (weak instrument)
* - KP rk LM (underidentification)
* - Hansen J (overidentification, if overidentified)
* - DWH endogeneity test

di "============================================="
di "IV DIAGNOSTICS SUMMARY"
di "============================================="
di "KP rk Wald F:        " e(widstat)
di "KP rk LM (underid):  " e(idstat) " (p=" e(idp) ")"
* NOTE: DWH endogeneity test p-value (e(estatp)) may be missing when
* xtivreg2 is used with partial() option. This is a known limitation.
* In that case, run a manual Hausman-type endogeneity test (Issue #14).
if e(estatp) != . {
    di "DWH endogeneity:     " e(estat) " (p=" e(estatp) ")"
}
else {
    di "DWH endogeneity:     unavailable (xtivreg2 + partial() limitation)"
}
di "Hansen J (overid):   " e(j) " (p=" e(jp) ")"
di "============================================="

* --- Anderson-Rubin Confidence Set (weak-instrument robust) ---
* Critical when F-stat is marginal (10-23 range)
cap weakiv
if _rc == 0 {
    weakiv
}
else {
    * Manual AR test: run reduced form, test coefficient = 0
    reghdfe OUTCOME_VAR INSTRUMENT(S) CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    test INSTRUMENT(S)
    local ar_F = r(F)
    local ar_p = r(p)
    di "Anderson-Rubin F: `ar_F' (p = `ar_p')"
}

* --- Shock-robust SEs (Adao et al. 2019) for shift-share IVs ---
* If instrument is Bartik/shift-share, add two-way clustering:
* reghdfe OUTCOME_VAR TREAT CONTROLS, absorb(FE) vce(cluster CLUSTER1 CLUSTER2)

log close
```

## Step 4: Robustness & Distance-Credibility (Stata .do file)

```stata
/*==============================================================================
  IV Analysis — Step 4: Robustness
  Following APE 0185: distance-credibility tradeoff, LOSO, placebos
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/iv_04_robustness.log", replace

use "DATASET_PATH", clear

* --- Leave-One-State/Group-Out (LOSO) ---
* Check if results driven by a single influential unit
levelsof CLUSTER_VAR, local(clusters)
foreach c of local clusters {
    cap ivreghdfe OUTCOME_VAR CONTROLS (ENDOG_VAR = INSTRUMENT(S)) ///
        if CLUSTER_VAR != `c', absorb(FIXED_EFFECTS) cluster(CLUSTER_VAR)
    if _rc == 0 {
        di "LOSO (drop `c'): b = " _b[ENDOG_VAR] " (SE = " _se[ENDOG_VAR] ")"
    }
}

* --- Placebo Instruments ---
* If exclusion restriction is debatable, test alternative instruments
* that should NOT affect the outcome
* eststo placebo: reghdfe OUTCOME_VAR PLACEBO_INSTRUMENT CONTROLS, ...

* --- Reduced-Form Pre-Trend Test ---
* If instrument varies over time, check for pre-trends in reduced form

* --- Wild Cluster Bootstrap ---
reghdfe OUTCOME_VAR ENDOG_VAR CONTROLS, absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
boottest ENDOG_VAR, cluster(CLUSTER_VAR) boottype(mammen) reps(999) seed(12345)

log close
```

## Step 5: Python Cross-Validation

```python
"""
IV Cross-Validation: Stata vs Python (pyfixest)
"""
import pandas as pd
import pyfixest as pf

df = pd.read_stata("DATASET_PATH")

# IV estimation via pyfixest
# Syntax: Y ~ exog | FEs | endog ~ instrument
model_iv = pf.feols("OUTCOME_VAR ~ CONTROLS | FIXED_EFFECTS | ENDOG_VAR ~ INSTRUMENT(S)",
                     data=df, vcov={"CRV1": "CLUSTER_VAR"})
print("=== Python 2SLS ===")
print(model_iv.summary())

# OLS for comparison
model_ols = pf.feols("OUTCOME_VAR ~ ENDOG_VAR + CONTROLS | FIXED_EFFECTS",
                      data=df, vcov={"CRV1": "CLUSTER_VAR"})
print("=== Python OLS ===")
print(model_ols.summary())

# Cross-validate
stata_coef = STATA_IV_COEF
python_coef = model_iv.coef()["ENDOG_VAR"]
pct_diff = abs(stata_coef - python_coef) / abs(stata_coef) * 100
print(f"\nCross-validation (2SLS on ENDOG_VAR):")
print(f"  Stata:  {stata_coef:.6f}")
print(f"  Python: {python_coef:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 0.1 else 'FAIL'}")
```

## Step 6: Diagnostics Summary

After all steps, provide:

1. **Instrument Relevance**: KP F vs Stock-Yogo/Lee et al. critical values. Partial R-squared.
2. **2SLS vs LIML**: If estimates diverge, weak instruments are a concern.
3. **Instrument Validity**: Hansen J (if overidentified). Narrative on exclusion restriction.
4. **Endogeneity**: DWH test result. If not rejected, OLS preferred for efficiency.
5. **Weak Instrument Inference**: AR confidence set (important when F < 23).
6. **LOSO Sensitivity**: Is any single cluster driving the result?
7. **OLS vs IV Direction**: Attenuation bias (IV > OLS) or reverse?
8. **Cross-Validation**: Stata vs Python match.

## Advanced Patterns Reference

For advanced IV patterns from published papers (xtivreg2 panel IV, shift-share/Bartik instruments, k-class estimation, spatial lags via `spmat`, bootstrap with `cluster()`/`idcluster()`, multiple endogenous variables, interaction FE), see `advanced-stata-patterns.md`.
