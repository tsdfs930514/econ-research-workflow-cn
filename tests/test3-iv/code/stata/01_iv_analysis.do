/*==============================================================================
  IV Analysis Test - Synthetic Data
  Test of /run-iv skill
  Reference: APE 0185 (Social Networks & Labor Markets)

  Fallback strategy: ivreghdfe -> ivreg2 (with FE dummies) -> manual Wald
==============================================================================*/

version 18
clear all
set more off
set seed 12345

cap log close
log using "output/logs/01_iv_analysis.log", replace

*===============================================================================
* 0. LOAD DATA
*===============================================================================
use "synthetic_iv.dta", clear

* Verify panel structure
isid county_id year
xtset county_id year

di "=== Data Loaded: " _N " observations ==="
summarize treatment, detail

*===============================================================================
* 1. FIRST STAGE & REDUCED FORM
*===============================================================================
eststo clear

* First Stage: SCI -> Treatment
eststo fs_main: reghdfe treatment sci pop manufacturing, ///
    absorb(state_id year) vce(cluster state_id)

* First-stage F-statistic on excluded instrument
test sci
local fs_F = r(F)
local fs_p = r(p)
local fs_coef = _b[sci]
local fs_se = _se[sci]
di "=== First-Stage F-statistic: `fs_F' (p = `fs_p') ==="
di "SCI coefficient: `fs_coef' (SE: `fs_se')"

* Reduced Form: SCI -> Outcome
eststo rf_main: reghdfe employment sci pop manufacturing, ///
    absorb(state_id year) vce(cluster state_id)
local rf_coef = _b[sci]
di "Reduced form SCI coef: `rf_coef'"

*===============================================================================
* 2. OLS BASELINE
*===============================================================================
eststo ols_base: reghdfe employment treatment pop manufacturing, ///
    absorb(state_id year) vce(cluster state_id)
local ols_coef = _b[treatment]
di "OLS treatment coef: `ols_coef'"

*===============================================================================
* 3. 2SLS WITH FALLBACK CHAIN
*===============================================================================
local iv_method = "none"
local iv_coef = .
local kp_f = .

* --- Attempt 1: ivreghdfe (preferred) ---
di "=== Attempting ivreghdfe ==="
cap noisily ivreghdfe employment pop manufacturing ///
    (treatment = sci), ///
    absorb(state_id year) cluster(state_id) first
if _rc == 0 {
    local iv_method = "ivreghdfe"
    local iv_coef = _b[treatment]
    local kp_f = e(widstat)
    eststo iv_2sls
    di "ivreghdfe SUCCESS: coef = `iv_coef', KP F = `kp_f'"
}
else {
    di "ivreghdfe FAILED (rc = " _rc "). Trying ivreg2 fallback..."

    * --- Attempt 2: ivreg2 with manually generated FE dummies ---
    cap which ivreg2
    if _rc == 0 {
        * Generate FE dummies
        quietly: tab state_id, gen(_state_fe)
        quietly: tab year, gen(_year_fe)

        cap noisily ivreg2 employment pop manufacturing _state_fe* _year_fe* ///
            (treatment = sci), cluster(state_id) first ffirst
        if _rc == 0 {
            local iv_method = "ivreg2"
            local iv_coef = _b[treatment]
            local kp_f = e(widstat)
            eststo iv_2sls
            di "ivreg2 SUCCESS: coef = `iv_coef', KP F = `kp_f'"
        }
        else {
            di "ivreg2 FAILED (rc = " _rc "). Falling back to manual Wald."
        }

        * Clean up FE dummies
        cap drop _state_fe*
        cap drop _year_fe*
    }
    else {
        di "ivreg2 not installed. Falling back to manual Wald."
    }
}

* --- Attempt 3: Manual Wald estimator ---
if "`iv_method'" == "none" {
    * Wald ratio = Reduced Form / First Stage
    local wald = `rf_coef' / `fs_coef'
    local iv_method = "wald"
    local iv_coef = `wald'
    di "Manual Wald 2SLS: `wald'"
}

di ""
di "=== 2SLS Method Used: `iv_method' ==="
di "2SLS treatment coef: `iv_coef'"

*===============================================================================
* 4. LIML WITH FALLBACK CHAIN
*===============================================================================
local liml_coef = .
local liml_method = "none"

* --- Attempt 1: ivreghdfe LIML ---
cap noisily ivreghdfe employment pop manufacturing ///
    (treatment = sci), ///
    absorb(state_id year) cluster(state_id) liml
if _rc == 0 {
    local liml_method = "ivreghdfe"
    local liml_coef = _b[treatment]
    eststo iv_liml
    di "LIML (ivreghdfe): `liml_coef'"
}
else {
    * --- Attempt 2: ivreg2 LIML ---
    cap which ivreg2
    if _rc == 0 {
        quietly: tab state_id, gen(_state_fe)
        quietly: tab year, gen(_year_fe)

        cap noisily ivreg2 employment pop manufacturing _state_fe* _year_fe* ///
            (treatment = sci), cluster(state_id) liml
        if _rc == 0 {
            local liml_method = "ivreg2"
            local liml_coef = _b[treatment]
            eststo iv_liml
            di "LIML (ivreg2): `liml_coef'"
        }

        cap drop _state_fe*
        cap drop _year_fe*
    }
}

if "`liml_method'" == "none" {
    di "LIML estimation not available — skipped"
}

*===============================================================================
* 5. ANDERSON-RUBIN TEST (weak-instrument robust)
*===============================================================================
di ""
di "=== Anderson-Rubin Test ==="
reghdfe employment sci pop manufacturing, absorb(state_id year) vce(cluster state_id)
test sci
local ar_F = r(F)
local ar_p = r(p)
di "AR F: `ar_F' (p = `ar_p')"
di "Interpretation: AR test is valid regardless of instrument strength"

*===============================================================================
* 6. LOSO SENSITIVITY (Leave-One-State-Out)
*===============================================================================
di ""
di "=== LOSO Sensitivity (all states) ==="
levelsof state_id, local(states)
foreach s of local states {
    * Use whichever method worked above
    if "`iv_method'" == "ivreghdfe" {
        cap ivreghdfe employment pop manufacturing (treatment = sci) ///
            if state_id != `s', absorb(state_id year) cluster(state_id)
        if _rc == 0 {
            di "Drop state `s': b = " %7.4f _b[treatment]
        }
    }
    else {
        * Use reghdfe for first stage and reduced form, compute Wald
        cap reghdfe treatment sci pop manufacturing if state_id != `s', ///
            absorb(state_id year) vce(cluster state_id)
        if _rc == 0 {
            local loso_fs = _b[sci]
            cap reghdfe employment sci pop manufacturing if state_id != `s', ///
                absorb(state_id year) vce(cluster state_id)
            if _rc == 0 {
                local loso_rf = _b[sci]
                local loso_wald = `loso_rf' / `loso_fs'
                di "Drop state `s': b(Wald) = " %7.4f `loso_wald'
            }
        }
    }
}

*===============================================================================
* 7. TABLES
*===============================================================================
* Main table: OLS vs 2SLS vs LIML
cap esttab ols_base iv_2sls iv_liml using "output/tables/tab_iv_main.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("OLS" "2SLS" "LIML") ///
    keep(treatment) label booktabs replace ///
    scalars("widstat KP F-stat" "N_clust Clusters") ///
    addnotes("SE clustered at state. Instrument: SCI." ///
             "2SLS method: `iv_method'. LIML method: `liml_method'.")

* First stage table
esttab fs_main using "output/tables/tab_first_stage.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(sci) label booktabs replace ///
    addnotes("F-stat on excluded instrument: `fs_F'")

*===============================================================================
* 8. SAVE COEFFICIENTS FOR PYTHON CROSS-VALIDATION
*===============================================================================
clear
set obs 1
gen ols_coef = `ols_coef'
gen iv_coef = `iv_coef'
gen iv_method = "`iv_method'"
gen fs_F = `fs_F'
save "output/stata_iv_coefs.dta", replace

*===============================================================================
* 9. SUMMARY
*===============================================================================
di ""
di "============================================="
di "IV ANALYSIS SUMMARY"
di "============================================="
di "OLS coef:        `ols_coef'"
di "2SLS coef:       `iv_coef' (method: `iv_method')"
di "LIML coef:       `liml_coef' (method: `liml_method')"
di "First-Stage F:   `fs_F'"
di "KP F:            `kp_f'"
di "AR F:            `ar_F' (p = `ar_p')"
di "True effect:     -2.0"
di "============================================="
di "2SLS-OLS gap:    " %7.4f (`iv_coef' - `ols_coef')
if `liml_coef' != . {
    di "LIML-2SLS gap:   " %7.4f (`liml_coef' - `iv_coef')
}
di "============================================="

log close
