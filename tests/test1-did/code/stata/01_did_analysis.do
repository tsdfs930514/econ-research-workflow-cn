/*==============================================================================
  DID Analysis Test - Synthetic Panel Data
  Test of /run-did skill with staggered adoption design
  Reference: Cattaneo, Idrobo & Titiunik (2020) best practices
==============================================================================*/

version 18
clear all
set more off
set seed 42

cap log close
log using "output/logs/01_did_analysis.log", replace

*===============================================================================
* 0. LOAD DATA
*===============================================================================
use "synthetic_panel.dta", clear

* Verify panel structure
isid state_id year
xtset state_id year
xtdescribe

* Generate treatment cohort variable for csdid
gen first_treat = treat_year
replace first_treat = 0 if treat_year == 0  // Never-treated = 0

*===============================================================================
* 1. DATA VALIDATION & DESCRIPTIVES
*===============================================================================
* Treatment timing distribution
tab first_treat if first_treat > 0
di "Never-treated units: " _N - r(N)

* Create treated indicator
gen treated_group = (first_treat > 0)

* Pre-treatment outcome trends by group
preserve
  collapse (mean) mean_cons = consumption, by(year treated_group)
  twoway (connected mean_cons year if treated_group == 1, lcolor(cranberry) mcolor(cranberry)) ///
         (connected mean_cons year if treated_group == 0, lcolor(navy) mcolor(navy)), ///
    legend(order(1 "Treated" 2 "Control") rows(1)) ///
    title("Pre-Treatment Outcome Trends") ///
    xtitle("Year") ytitle("Mean Consumption") ///
    xline(2010, lpattern(dash) lcolor(gray))
  graph export "output/figures/fig_parallel_trends_raw.pdf", replace
restore

* Summary statistics by treatment status
estpost tabstat consumption pop income unemployment if year < 2010, ///
    by(treated_group) stat(mean sd n) columns(statistics)

*===============================================================================
* 2. CANONICAL TWFE
*===============================================================================
eststo clear

* Main TWFE specification
eststo twfe_main: reghdfe consumption treated pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)

local twfe_b = _b[treated]
local twfe_se = _se[treated]
di "TWFE: b = `twfe_b', se = `twfe_se'"

*===============================================================================
* 3. TWFE EVENT STUDY (Manual leads/lags)
*===============================================================================
gen rel_time = year - first_treat
replace rel_time = . if first_treat == 0

* Create event-time dummies (rel_time == -1 is reference)
forvalues k = 5(-1)2 {
    gen lead`k' = (rel_time == -`k') if !missing(rel_time)
    replace lead`k' = 0 if missing(lead`k')
}
forvalues k = 0/5 {
    gen lag`k' = (rel_time == `k') if !missing(rel_time)
    replace lag`k' = 0 if missing(lag`k')
}

eststo twfe_es: reghdfe consumption lead* lag* pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)

* Joint test of pre-treatment leads
testparm lead*
local pretrend_F = r(F)
local pretrend_p = r(p)
di "Pre-trend joint F-test: F = `pretrend_F', p = `pretrend_p'"

* Event study plot
coefplot twfe_es, keep(lead* lag*) vertical yline(0, lcolor(gs10)) ///
    xline(5, lpattern(dash) lcolor(gs10)) ///
    title("TWFE Event Study") ///
    xtitle("Periods Relative to Treatment") ytitle("Coefficient") ///
    ciopts(recast(rcap) lcolor(navy)) mcolor(navy) ///
    note("Joint pre-trend F = `pretrend_F' (p = `: di %5.3f `pretrend_p'')")
graph export "output/figures/fig_event_study_twfe.pdf", replace

*===============================================================================
* 4. CALLAWAY & SANT'ANNA (2021)
*===============================================================================
* Doubly-robust, group-time ATT with never-treated control

cap noisily csdid consumption pop income unemployment, ivar(state_id) time(year) gvar(first_treat) ///
    method(dripw)

* Aggregations
cap noisily csdid_stats simple, estore(cs_simple)
cap noisily csdid_stats event, estore(cs_event)
cap noisily csdid_stats group, estore(cs_group)

* CS Event study plot
cap noisily csdid_plot, style(rcap) title("CS-DiD Event Study") ///
    xtitle("Periods Since Treatment") ytitle("ATT")
cap noisily graph export "output/figures/fig_event_study_cs.pdf", replace

*===============================================================================
* 5. GOODMAN-BACON DECOMPOSITION
*===============================================================================
cap noisily bacondecomp consumption treated, id(state_id) t(year) ddetail
cap noisily graph export "output/figures/fig_bacon_decomp.pdf", replace

*===============================================================================
* 6. COMPARISON TABLE
*===============================================================================
* TWFE only (CS-DiD stored separately)
esttab twfe_main using "output/tables/tab_did_comparison.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("TWFE") ///
    keep(treated) label booktabs replace ///
    scalars("r2_within Within R$^2$" "N_clust Clusters") ///
    addnotes("Standard errors clustered at state level." ///
             "CS-DiD results stored separately in cs_simple.") ///
    title("DID Estimation: TWFE vs CS-DiD")

*===============================================================================
* 7. WILD CLUSTER BOOTSTRAP
*===============================================================================
cap noisily reghdfe consumption treated pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)
cap noisily boottest treated, cluster(state_id) boottype(mammen) reps(999) seed(12345)

*===============================================================================
* 8. DIAGNOSTICS SUMMARY
*===============================================================================
di "============================================="
di "DID DIAGNOSTICS SUMMARY"
di "============================================="
di "Panel: " _N " observations, " e(N_clust) " clusters"
di "TWFE coef: `twfe_b' (SE: `twfe_se')"
di "Pre-trend F: `pretrend_F' (p = `pretrend_p')"
di "============================================="

log close
