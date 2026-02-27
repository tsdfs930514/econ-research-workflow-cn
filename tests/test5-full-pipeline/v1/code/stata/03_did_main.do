/*==============================================================================
  Test 5: Full Pipeline - 03 DID Main Analysis
  TWFE estimation and event study with pre-trend test
==============================================================================*/
version 18
clear all
set more off

cap log close _all
log using "$logs/03_did_main.log", replace name(did)

di "============================================================"
di "03_did_main.do: Started at $S_DATE $S_TIME"
di "============================================================"

* --------------------------------------------------------------------------
* Load cleaned data
* --------------------------------------------------------------------------
use "$clean/panel_cleaned.dta", clear
di "Loaded `c(N)' observations"

eststo clear

* ==========================================================================
* Model 1: TWFE - Base specification (no covariates)
* ==========================================================================
di _n "=== Model 1: TWFE Base ==="

reghdfe consumption treated, absorb(state_id year) vce(cluster state_id)

eststo m1_base
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "No"
estadd scalar n_cluster = e(N_clust)

di "Treated coefficient: " _b[treated]
di "Std. error: " _se[treated]

* ==========================================================================
* Model 2: TWFE - With covariates (main specification)
* ==========================================================================
di _n "=== Model 2: TWFE with Controls ==="

reghdfe consumption treated pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)

eststo m2_main
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "Yes"
estadd scalar n_cluster = e(N_clust)

di "Treated coefficient: " _b[treated]
di "Std. error: " _se[treated]

* Save main coefficient for cross-validation
scalar b_treated_main = _b[treated]
scalar se_treated_main = _se[treated]

* Export coefficient to temp file for Python cross-validation
preserve
clear
set obs 1
gen coef_treated = scalar(b_treated_main)
gen se_treated = scalar(se_treated_main)
save "$temp/stata_coefs.dta", replace
restore

di "Main coefficient saved to $temp/stata_coefs.dta"

* ==========================================================================
* Model 3: TWFE - Log outcome
* ==========================================================================
di _n "=== Model 3: TWFE Log Outcome ==="

reghdfe ln_consumption treated pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)

eststo m3_log
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "Yes"
estadd scalar n_cluster = e(N_clust)

* ==========================================================================
* Model 4: Event Study
* ==========================================================================
di _n "=== Model 4: Event Study ==="

* Generate lead/lag indicators from time_to_treat
* Bin endpoints: <= -4 and >= 4
* Omit: -1 (period before treatment)

* Create indicators for each relative period
forvalues k = 4(-1)2 {
    gen lead`k' = (time_to_treat == -`k') if !missing(time_to_treat)
    replace lead`k' = 0 if missing(lead`k')
}
* lag 0 = treatment period
forvalues k = 0/4 {
    gen lag`k' = (time_to_treat == `k') if !missing(time_to_treat)
    replace lag`k' = 0 if missing(lag`k')
}

* Bin endpoints
replace lead4 = 1 if time_to_treat <= -4 & !missing(time_to_treat)
replace lag4 = 1 if time_to_treat >= 4 & !missing(time_to_treat)

* Note: lead1 (time_to_treat == -1) is omitted as reference period
* Never-treated units have all indicators = 0

di "Lead/lag indicators created"
tab time_to_treat, missing

reghdfe consumption lead4 lead3 lead2 lag0 lag1 lag2 lag3 lag4 ///
    pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)

eststo m4_event
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "Yes"
estadd scalar n_cluster = e(N_clust)

* --------------------------------------------------------------------------
* Pre-trend F-test: joint significance of pre-treatment leads
* --------------------------------------------------------------------------
di _n "=== Pre-Trend F-Test ==="
test lead4 lead3 lead2

scalar f_pretrend = r(F)
scalar p_pretrend = r(p)

di "Pre-trend F-statistic: " scalar(f_pretrend)
di "Pre-trend p-value: " scalar(p_pretrend)

if scalar(p_pretrend) > 0.05 {
    di "PASS: Pre-trend test insignificant (p > 0.05) -- parallel trends supported"
}
else {
    di "WARNING: Pre-trend test significant (p <= 0.05) -- parallel trends may be violated"
}

* --------------------------------------------------------------------------
* Event study coefficient plot
* --------------------------------------------------------------------------
coefplot m4_event, ///
    keep(lead4 lead3 lead2 lag0 lag1 lag2 lag3 lag4) ///
    rename(lead4 = "-4+" lead3 = "-3" lead2 = "-2" ///
           lag0 = "0" lag1 = "1" lag2 = "2" lag3 = "3" lag4 = "4+") ///
    vertical ///
    yline(0, lcolor(red) lpattern(dash)) ///
    xline(4.5, lcolor(gray) lpattern(dash)) ///
    xtitle("Periods Relative to Treatment") ///
    ytitle("Effect on Consumption") ///
    title("Event Study: Effect of Policy on Consumption") ///
    note("Reference period: t = -1. Bars show 95% CIs clustered at state level.") ///
    ciopts(recast(rcap)) ///
    msymbol(D) mcolor(navy) ///
    graphregion(color(white))

graph export "$figures/fig_event_study.png", replace width(1200)

di "Event study plot exported"

* --------------------------------------------------------------------------
* Summary of all models
* --------------------------------------------------------------------------
di _n "=== Summary ==="
estimates table m1_base m2_main m3_log, ///
    keep(treated) b(%9.4f) se(%9.4f) stats(N r2_within)

di "03_did_main.do: Completed at $S_DATE $S_TIME"

log close did
