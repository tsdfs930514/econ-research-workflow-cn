/*==============================================================================
  RDD Analysis Test - Synthetic Data
  Test of /run-rdd skill
  Reference: Cattaneo, Idrobo & Titiunik (2020) best practices
==============================================================================*/

version 18
clear all
set more off
set seed 42

cap log close
log using "output/logs/01_rdd_analysis.log", replace

*===============================================================================
* 0. LOAD DATA
*===============================================================================
use "synthetic_rdd.dta", clear

* Verify unique IDs
isid id

*===============================================================================
* 1. RD VISUALIZATION
*===============================================================================
* Generate treatment if needed
cap gen treat = (running >= 0)

* RD Plot: binned scatter with local polynomial
rdplot outcome running, c(0) p(1) ///
    graph_options(title("Regression Discontinuity Plot") ///
    xtitle("Running Variable") ytitle("Outcome") ///
    xline(0, lcolor(cranberry) lpattern(dash)))
graph export "output/figures/fig_rd_plot.pdf", replace

* Histogram of running variable
histogram running, bin(50) ///
    xline(0, lcolor(cranberry) lpattern(dash)) ///
    title("Distribution of Running Variable") ///
    xtitle("Running Variable") ytitle("Frequency")
graph export "output/figures/fig_rd_histogram.pdf", replace

*===============================================================================
* 2. MANIPULATION TEST (CJM Density Test)
*===============================================================================
rddensity running, c(0)
graph export "output/figures/fig_rd_density.pdf", replace

* Store test result for summary
local cjm_p = r(pv)
di "CJM density test p-value: `cjm_p'"

*===============================================================================
* 3. COVARIATE BALANCE
*===============================================================================
* Test each covariate for discontinuity
local covariates "age education"

foreach var of local covariates {
    di "=== Balance test: `var' ==="
    rdrobust `var' running, c(0) kernel(triangular) bwselect(mserd)
    di ""
}

*===============================================================================
* 4. MAIN RD ESTIMATION
*===============================================================================
* Sharp RD with MSE-optimal bandwidth
rdrobust outcome running, c(0) ///
    kernel(triangular) bwselect(mserd) all

* Store key results
local tau_conv  = e(tau_cl)
local tau_bc    = e(tau_bc)
local se_conv   = e(se_tau_cl)
local se_robust = e(se_tau_rb)
local bw_l      = e(h_l)
local bw_r      = e(h_r)
local N_l       = e(N_h_l)
local N_r       = e(N_h_r)

di "============================================="
di "MAIN RD RESULTS"
di "============================================="
di "Conventional:    `tau_conv' (SE = `se_conv')"
di "Bias-corrected:  `tau_bc' (Robust SE = `se_robust')"
di "Bandwidth (L/R): `bw_l' / `bw_r'"
di "Eff. N (L/R):    `N_l' / `N_r'"
di "============================================="

* With CER-optimal bandwidth (for inference)
rdrobust outcome running, c(0) ///
    kernel(triangular) bwselect(cerrd) all

* With covariates (for precision)
rdrobust outcome running, c(0) ///
    kernel(triangular) bwselect(mserd) covs(age education)

*===============================================================================
* 5. BANDWIDTH & POLYNOMIAL SENSITIVITY
*===============================================================================
* Get MSE-optimal bandwidth for reference
rdrobust outcome running, c(0) kernel(triangular) bwselect(mserd)
local bw_opt = e(h_l)

* Bandwidth sensitivity
tempfile bw_results
postfile bw_handle str10 spec double bw_val double coef double se double pval double ci_lo double ci_hi double N_eff using `bw_results', replace

foreach m in 0.50 0.75 1.00 1.25 1.50 2.00 {
    local bw_test = `bw_opt' * `m'
    rdrobust outcome running, c(0) kernel(triangular) h(`bw_test')
    local ci_lo = e(tau_cl) - 1.96 * e(se_tau_cl)
    local ci_hi = e(tau_cl) + 1.96 * e(se_tau_cl)
    post bw_handle ("`m'x") (`bw_test') (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (`ci_lo') (`ci_hi') (e(N_h_l) + e(N_h_r))
}

* Polynomial order sensitivity
forvalues p = 1/3 {
    rdrobust outcome running, c(0) kernel(triangular) bwselect(mserd) p(`p')
    local ci_lo = e(tau_cl) - 1.96 * e(se_tau_cl)
    local ci_hi = e(tau_cl) + 1.96 * e(se_tau_cl)
    post bw_handle ("p=`p'") (e(h_l)) (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (`ci_lo') (`ci_hi') (e(N_h_l) + e(N_h_r))
}

* Kernel sensitivity
foreach kern in triangular uniform epanechnikov {
    rdrobust outcome running, c(0) kernel(`kern') bwselect(mserd)
    local ci_lo = e(tau_cl) - 1.96 * e(se_tau_cl)
    local ci_hi = e(tau_cl) + 1.96 * e(se_tau_cl)
    post bw_handle ("`kern'") (e(h_l)) (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (`ci_lo') (`ci_hi') (e(N_h_l) + e(N_h_r))
}

postclose bw_handle

* Display sensitivity results
use `bw_results', clear
list, clean

*===============================================================================
* 6. PLACEBO & DONUT TESTS
*===============================================================================
* Reload main data
use "synthetic_rdd.dta", clear

* Placebo cutoffs
sum running, detail
local p25 = r(p25)
local p75 = r(p75)

di "=== Placebo at p25 (`p25') ==="
rdrobust outcome running if running < 0, c(`p25') kernel(triangular) bwselect(mserd)

di "=== Placebo at p75 (`p75') ==="
rdrobust outcome running if running > 0, c(`p75') kernel(triangular) bwselect(mserd)

* Donut hole RD
foreach donut in 0.5 1 2 5 {
    di "=== Donut RD: excluding +-`donut' from cutoff ==="
    rdrobust outcome running if abs(running) > `donut', ///
        c(0) kernel(triangular) bwselect(mserd)
}

*===============================================================================
* 7. DIAGNOSTICS SUMMARY
*===============================================================================
di "============================================="
di "RDD DIAGNOSTICS SUMMARY"
di "============================================="
di "1. Manipulation Test (CJM): p = `cjm_p'"
di "   H0: No sorting at cutoff"
di "2. Main Estimate (bias-corrected): `tau_bc'"
di "   Robust SE: `se_robust'"
di "3. Bandwidth: `bw_l' (left), `bw_r' (right)"
di "4. Effective sample: `N_l' (left), `N_r' (right)"
di "============================================="

log close
