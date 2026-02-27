---
description: "Run a comprehensive robustness test suite for regression results"
user_invocable: true
---

# /robustness - Comprehensive Robustness Test Suite

When the user invokes `/robustness`, follow these steps:

## Step 1: Gather Information

Ask the user for:

1. **Baseline regression specification** (required) - The main regression equation, e.g.:
   - Dependent variable
   - Key independent variable(s) of interest
   - Control variables
   - Fixed effects
   - Clustering level
   - Example: `Y = beta * Treatment + Controls + FE_firm + FE_year, cluster(firm)`
2. **Dataset path** (required) - Path to the dataset (.dta or .csv)
3. **Method type** (required) - One of: DID, IV, RDD, Panel, OLS
4. **Alternative dependent variables** (optional) - List of alternative outcome variables
5. **Additional info for method-specific tests** (optional):
   - DID: Treatment time variable, pre/post periods, first-treatment variable
   - IV: Instrument variable(s), endogenous variable
   - RDD: Running variable, cutoff value
   - Panel: Entity and time variables, lag structure
6. **Number of clusters** (important) - Needed to decide whether wild cluster bootstrap is required

## Step 1b: Identify Missing Robustness Checks via Agent

After gathering information (Step 1), use the Task tool to invoke the `robustness-checker` agent. Provide it with:
- The baseline specification from Step 1
- The method type (DID / IV / RDD / Panel / OLS)
- Any robustness checks the user has already performed

The agent will return a prioritized list of missing robustness checks (High / Medium / Low priority). Merge its suggestions into the test suite generated in Step 2 — add any High-priority checks the template does not already cover.

## Step 2: Generate Stata .do File — Universal Robustness Checks

Create a comprehensive Stata .do file (e.g., `code/stata/XX_robustness.do`) with the following sections.

**Execute via:**
```bash
"D:\Stata18\StataMP-64.exe" -e do "code/stata/XX_robustness.do"
```

```stata
/*==============================================================================
  Robustness Tests
  Baseline: <specification>
  Method: <method type>
  Generated: <current date>
==============================================================================*/

clear all
set more off
set seed 12345

cap log close
log using "output/logs/robustness.log", replace

use "<dataset path>", clear

* Store baseline results for comparison
eststo clear

*===============================================================================
* 0. BASELINE SPECIFICATION
*===============================================================================
eststo baseline: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

local baseline_b = _b[<treatment>]
local baseline_se = _se[<treatment>]
local baseline_N = e(N)

*===============================================================================
* 1. ALTERNATIVE DEPENDENT VARIABLES
*===============================================================================
/* If alternative dependent variables are provided */
foreach alt_y in <alternative dep vars> {
    eststo alt_`alt_y': reghdfe `alt_y' <treatment> <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
}

*===============================================================================
* 2. CONTROL VARIABLE SENSITIVITY
*===============================================================================
* Minimal controls (only key variable)
eststo min_ctrl: reghdfe <depvar> <treatment>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* Add controls one by one to show stability
local controls "<list of control variables>"
local cumulative ""
local i = 1
foreach ctrl of local controls {
    local cumulative "`cumulative' `ctrl'"
    eststo add_ctrl_`i': reghdfe <depvar> <treatment> `cumulative', ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
    local i = `i' + 1
}

*===============================================================================
* 3. SUBSAMPLE REGRESSIONS
*===============================================================================
* By time period (split sample in half)
summarize <time var>, meanonly
local med = r(mean)
eststo sub_early: reghdfe <depvar> <treatment> <controls> if <time var> <= `med', ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
eststo sub_late: reghdfe <depvar> <treatment> <controls> if <time var> > `med', ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* Dropping outliers (top/bottom 1%)
foreach var in <depvar> <key independent vars> {
    _pctile `var', p(1 99)
    local p1 = r(r1)
    local p99 = r(r2)
    gen byte outlier_`var' = (`var' < `p1' | `var' > `p99')
}
eststo no_outlier: reghdfe <depvar> <treatment> <controls> if outlier_<depvar> == 0, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

*===============================================================================
* 4. ALTERNATIVE FIXED EFFECTS
*===============================================================================
* No fixed effects
eststo no_fe: reg <depvar> <treatment> <controls>, vce(cluster <cluster var>)

* Only entity FE
eststo fe_entity: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<entity fe>) vce(cluster <cluster var>)

* Only time FE
eststo fe_time: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<time fe>) vce(cluster <cluster var>)

* Entity x Time FE (if applicable)
eststo fe_interact: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<entity fe>#<time fe>) vce(cluster <cluster var>)

*===============================================================================
* 5. DIFFERENT CLUSTERING LEVELS
*===============================================================================
* Cluster at different levels
eststo clust_1: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster level 1>)
eststo clust_2: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster level 2>)
eststo clust_twoway: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster level 1> <cluster level 2>)

*===============================================================================
* 6. WINSORIZATION
*===============================================================================
* Winsorize at 1%/99%
foreach var in <depvar> <continuous controls> {
    winsor2 `var', cuts(1 99) suffix(_w1)
    winsor2 `var', cuts(5 95) suffix(_w5)
}
eststo win_1_99: reghdfe <depvar>_w1 <treatment> <controls with _w1 suffix>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
eststo win_5_95: reghdfe <depvar>_w5 <treatment> <controls with _w5 suffix>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

*===============================================================================
* 7. PLACEBO / RANDOMIZATION INFERENCE
*===============================================================================
* Single randomization placebo
set seed 12345
gen treatment_placebo = runiform() > 0.5
eststo placebo_random: reghdfe <depvar> treatment_placebo <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
drop treatment_placebo

* Permutation inference (500 iterations)
* Shuffle treatment labels, estimate coefficient each time
* Compare actual coefficient to distribution of placebo coefficients
cap program drop permute_test
program define permute_test, rclass
    * Permute treatment variable within clusters
    tempvar rand
    gen `rand' = runiform()
    sort <cluster var> `rand'
    by <cluster var>: gen treatment_perm = (RUNNING_VAR >= CUTOFF)[1]
    reghdfe <depvar> treatment_perm <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
    return scalar b = _b[treatment_perm]
    drop treatment_perm
end

simulate b_perm = r(b), reps(500) seed(12345): permute_test
* Count how many permuted coefs exceed the baseline
count if abs(b_perm) >= abs(`baseline_b')
local perm_p = r(N) / 500
di "Permutation p-value: `perm_p'"

*===============================================================================
* 8. WILD CLUSTER BOOTSTRAP (Roodman et al.)
*===============================================================================
* Critical when number of clusters < 50
reghdfe <depvar> <treatment> <controls>, absorb(<fixed effects>) vce(cluster <cluster var>)
boottest <treatment>, cluster(<cluster var>) boottype(mammen) reps(999) seed(12345)
* Report: WCB p-value and 95% CI

*===============================================================================
* 9. OSTER (2019) COEFFICIENT STABILITY / SELECTION ON UNOBSERVABLES
*===============================================================================
* psacalc implements Oster (2019) bounding exercise
* Tests how much selection on unobservables (relative to observables)
* is needed to explain away the treatment effect

* Step 1: Uncontrolled regression
reg <depvar> <treatment>, vce(cluster <cluster var>)
local b_uncontrolled = _b[<treatment>]
local r2_uncontrolled = e(r2)

* Step 2: Controlled regression (no FE for psacalc)
reg <depvar> <treatment> <controls>, vce(cluster <cluster var>)
local b_controlled = _b[<treatment>]
local r2_controlled = e(r2)

* Step 3: Oster bound with R_max = 1.3 * R2_full (Oster recommended)
psacalc delta <treatment>, rmax(1.3)
local oster_delta = r(delta)

psacalc beta <treatment>, rmax(1.3) delta(1)
local oster_beta = r(beta)

di "============================================="
di "OSTER (2019) BOUNDS"
di "============================================="
di "  delta (proportional selection):  `oster_delta'"
di "  beta* (bias-adjusted estimate):  `oster_beta'"
di "  Interpretation: delta > 1 means unobservables"
di "  would need to be MORE important than observables"
di "  to explain away the effect."
di "============================================="
```

## Step 3: Method-Specific Tests

Append method-specific robustness tests to the .do file based on the method type:

### DID-Specific Tests

```stata
*===============================================================================
* 10. DID-SPECIFIC ROBUSTNESS
*===============================================================================

* --- Placebo pre-treatment test (false treatment time) ---
forvalues t = <earliest pre-period> / <period before treatment> {
    gen placebo_treat_`t' = (<entity is treated>) * (<time var> >= `t')
    eststo placebo_t`t': reghdfe <depvar> placebo_treat_`t' <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
    drop placebo_treat_`t'
}

* --- Different treatment windows ---
eststo did_narrow: reghdfe <depvar> <treatment> <controls> ///
    if abs(<time var> - <treatment time>) <= <narrow window>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* --- Goodman-Bacon (2021) Decomposition ---
bacondecomp <depvar> <treatment>, id(<group var>) t(<time var>) ddetail
graph export "output/figures/fig_bacon_decomp.pdf", replace

* --- Callaway-Sant'Anna vs TWFE comparison ---
csdid <depvar> <controls>, ivar(<group var>) time(<time var>) gvar(<first treat var>) ///
    method(dripw) notyet
csdid_stats simple, estore(cs_simple)
* Compare CS-DiD ATT(simple) with TWFE coefficient

* --- HonestDiD sensitivity (Rambachan-Roth) ---
* Run event study, then test how much PT violation is needed
* to overturn the result
reghdfe <depvar> lead* lag* <controls>, absorb(<group var> <time var>) vce(cluster <cluster var>)
honestdid, pre(1/<K_LEADS>) post(1/<K_LAGS>) mvec(0(0.01)0.05)
```

### IV-Specific Tests

```stata
*===============================================================================
* 10. IV-SPECIFIC ROBUSTNESS
*===============================================================================

* --- First stage ---
eststo first_stage: reghdfe <endogenous var> <instruments> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
test <instruments>
local fs_F = r(F)

* --- Reduced form ---
eststo reduced_form: reghdfe <depvar> <instruments> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* --- LIML estimation (robust to weak instruments) ---
eststo iv_liml: ivreghdfe <depvar> <controls> ///
    (<endogenous var> = <instruments>), ///
    absorb(<fixed effects>) cluster(<cluster var>) liml
* Large LIML-2SLS gap indicates weak instrument concern

* --- Anderson-Rubin confidence set (weak-instrument robust) ---
ivreg2 <depvar> <controls> (<endogenous var> = <instruments>), ///
    cluster(<cluster var>) first ffirst endog(<endogenous var>)
* AR CI is valid regardless of instrument strength

* --- Alternative instruments (if provided) ---
foreach inst in <alternative instruments> {
    eststo iv_alt_`inst': ivreghdfe <depvar> <controls> ///
        (<endogenous var> = `inst'), ///
        absorb(<fixed effects>) cluster(<cluster var>)
}

* --- LOSO (Leave-One-State/Group-Out) ---
levelsof <cluster var>, local(clusters)
foreach c of local clusters {
    cap ivreghdfe <depvar> <controls> (<endogenous var> = <instruments>) ///
        if <cluster var> != `c', absorb(<fixed effects>) cluster(<cluster var>)
    if _rc == 0 {
        di "LOSO (drop `c'): b = " _b[<endogenous var>] " (SE = " _se[<endogenous var>] ")"
    }
}

* --- Over-identification test (if overidentified) ---
* Hansen J test reported by ivreg2 / ivreghdfe
```

### RDD-Specific Tests

```stata
*===============================================================================
* 10. RDD-SPECIFIC ROBUSTNESS
*===============================================================================

* --- Bandwidth sensitivity ---
rdrobust <depvar> <running var>, c(<cutoff>) kernel(triangular) bwselect(mserd)
local bw_opt = e(h_l)

foreach m in 0.50 0.75 1.00 1.25 1.50 2.00 {
    local bw_test = `bw_opt' * `m'
    rdrobust <depvar> <running var>, c(<cutoff>) kernel(triangular) h(`bw_test')
    di "BW = `m'x optimal: tau = " e(tau_cl) " (SE = " e(se_tau_cl) ")"
}

* --- Polynomial order sensitivity ---
forvalues p = 1/3 {
    rdrobust <depvar> <running var>, c(<cutoff>) kernel(triangular) bwselect(mserd) p(`p')
    di "p=`p': tau = " e(tau_cl) " (SE = " e(se_tau_cl) ")"
}

* --- Kernel sensitivity ---
foreach kern in triangular uniform epanechnikov {
    rdrobust <depvar> <running var>, c(<cutoff>) kernel(`kern') bwselect(mserd)
    di "`kern': tau = " e(tau_cl) " (SE = " e(se_tau_cl) ")"
}

* --- Donut hole RDD ---
foreach hole in 0.5 1 2 5 {
    rdrobust <depvar> <running var> ///
        if abs(<running var> - <cutoff>) > `hole', c(<cutoff>) bwselect(mserd)
    di "Donut +-`hole': tau = " e(tau_cl)
}

* --- Manipulation test (CJM 2020) ---
rddensity <running var>, c(<cutoff>) plot
graph export "output/figures/fig_density_test.pdf", replace

* --- Placebo cutoffs ---
sum <running var>, detail
local p25 = r(p25)
local p75 = r(p75)
rdrobust <depvar> <running var> if <running var> < <cutoff>, c(`p25') bwselect(mserd)
rdrobust <depvar> <running var> if <running var> > <cutoff>, c(`p75') bwselect(mserd)
```

### Panel-Specific Tests

```stata
*===============================================================================
* 10. PANEL-SPECIFIC ROBUSTNESS
*===============================================================================

* --- Alternative lag structures ---
forvalues lag = 1/3 {
    gen L`lag'_<treatment> = L`lag'.<treatment>
    eststo lag_`lag': reghdfe <depvar> <treatment> L`lag'_<treatment> <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
}

* --- Dynamic panel GMM (if applicable) ---
xtabond2 <depvar> L.<depvar> <treatment> <controls>, ///
    gmm(L.<depvar>, lag(2 4)) iv(<treatment> <controls>) ///
    robust twostep small
* Report: AR(1), AR(2), Hansen J

* --- Hausman test: Fixed vs Random effects ---
xtreg <depvar> <treatment> <controls>, fe
estimates store fe_model
xtreg <depvar> <treatment> <controls>, re
estimates store re_model
hausman fe_model re_model

* --- Driscoll-Kraay SEs (robust to cross-sectional dependence) ---
xtscc <depvar> <treatment> <controls>, fe lag(3)
```

## Step 4: Generate Robustness Summary Table

Add code to output a summary table collecting all key results:

```stata
*===============================================================================
* ROBUSTNESS SUMMARY TABLE
*===============================================================================

esttab baseline alt_* min_ctrl add_ctrl_* sub_* no_outlier ///
    no_fe fe_entity fe_time win_* ///
    using "output/tables/tab_robustness_summary.tex", ///
    keep(<treatment variable>) ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label nomtitle replace booktabs ///
    scalars("N Observations" "r2_within Within R$^2$" "N_clust Clusters") ///
    title("Robustness Summary") ///
    mtitles("Baseline" <appropriate titles for each model>) ///
    addnotes("Standard errors clustered at <cluster var> level in parentheses." ///
             "All specifications include <fixed effects> unless noted.")

log close
```

## Step 5: Flag Results

After running the robustness tests, analyze the results:

1. **Check sign consistency**: Does the treatment coefficient maintain the same sign across all specifications?
2. **Check significance**: In how many specifications does the result remain significant at 5%? At 10%?
3. **Check magnitude**: How much does the coefficient vary across specifications? Flag if any specification deviates by more than 50% from baseline.
4. **Oster delta**: Is delta > 1? If so, unobservables would need to be more important than observables to explain away the effect.
5. **Wild cluster bootstrap**: Does WCB p-value agree with analytical p-value? Flag if they diverge substantially.
6. **Permutation p-value**: Is the actual coefficient in the extreme tail of the permutation distribution?

Report:

```
Robustness Test Summary
=======================
Total specifications tested: <N>
Coefficient sign consistent: <Yes/No>
Significant at 5% level: <X out of N specifications>
Significant at 10% level: <X out of N specifications>
Coefficient range: [<min>, <max>] (baseline: <baseline coef>)

Oster (2019) delta: <value> (> 1 is reassuring)
Oster (2019) beta*: <value> (bias-adjusted estimate at delta=1)
Wild cluster bootstrap p-value: <value>
Permutation p-value: <value>

Specifications where main result does NOT hold:
  - <specification name>: coef = <value>, p = <value>
  - ...

Output files:
  - code/stata/XX_robustness.do
  - output/tables/tab_robustness_summary.tex
  - output/logs/robustness.log
  - output/figures/fig_bacon_decomp.pdf (DID only)
  - output/figures/fig_density_test.pdf (RDD only)
```

## Required Stata Packages

```stata
ssc install reghdfe
ssc install ftools
ssc install estout
ssc install winsor2
ssc install boottest
ssc install psacalc
* Method-specific:
ssc install bacondecomp     // DID
ssc install csdid           // DID
ssc install honestdid       // DID
ssc install ivreghdfe       // IV
ssc install ivreg2          // IV
ssc install ranktest        // IV
ssc install weakiv          // IV
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace  // RDD
net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace  // RDD
ssc install xtabond2        // Panel GMM
ssc install xtscc           // Panel Driscoll-Kraay
ssc install coefplot
```
