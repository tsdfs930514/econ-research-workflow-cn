/*==============================================================================
  Test 5: Full Pipeline - 04 Tables Export
  Export formatted regression tables in AER style
==============================================================================*/
version 18
clear all
set more off

cap log close _all
log using "$logs/04_tables_export.log", replace name(tables)

di "============================================================"
di "04_tables_export.do: Started at $S_DATE $S_TIME"
di "============================================================"

* --------------------------------------------------------------------------
* Reload data and re-run models to populate estimates
* (Estimates are lost after clear all; re-run for export)
* --------------------------------------------------------------------------
use "$clean/panel_cleaned.dta", clear

eststo clear

* Model 1: TWFE Base
reghdfe consumption treated, absorb(state_id year) vce(cluster state_id)
eststo m1_base
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "No"
estadd scalar n_cluster = e(N_clust)

* Model 2: TWFE with Controls
reghdfe consumption treated pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)
eststo m2_main
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "Yes"
estadd scalar n_cluster = e(N_clust)

* Model 3: Log outcome
reghdfe ln_consumption treated pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)
eststo m3_log
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "Yes"
estadd scalar n_cluster = e(N_clust)

* --------------------------------------------------------------------------
* Table 1: Main DID results (AER style)
* --------------------------------------------------------------------------
di _n "=== Table 1: Main DID Results ==="

esttab m1_base m2_main m3_log using "$tables/tab_did_main.tex", replace ///
    keep(treated) ///
    b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    label ///
    nomtitles ///
    mgroups("Consumption" "Consumption" "Log Consumption", ///
        pattern(1 1 1) ///
        prefix(\multicolumn{@span}{c}{) suffix(}) span ///
        erepeat(\cmidrule(lr){@span})) ///
    scalars("fe_state State FE" ///
            "fe_year Year FE" ///
            "controls Controls" ///
            "n_cluster Clusters" ///
            "r2_within Within R\$^2\$") ///
    sfmt(%~9s %~9s %~9s %9.0f %9.4f) ///
    booktabs ///
    title("Effect of Policy Adoption on Consumption") ///
    addnotes("Standard errors clustered at the state level in parentheses." ///
             "\sym{*} \(p<0.10\), \sym{**} \(p<0.05\), \sym{***} \(p<0.01\)") ///
    substitute(\_ _)

di "Table 1 exported to $tables/tab_did_main.tex"

* --------------------------------------------------------------------------
* Table 2: Full coefficient table (all covariates shown)
* --------------------------------------------------------------------------
di _n "=== Table 2: Full Coefficients ==="

esttab m2_main using "$tables/tab_did_full.tex", replace ///
    b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    label ///
    nomtitles ///
    scalars("fe_state State FE" ///
            "fe_year Year FE" ///
            "n_cluster Clusters" ///
            "r2_within Within R\$^2\$") ///
    sfmt(%~9s %~9s %9.0f %9.4f) ///
    booktabs ///
    title("Full Regression Results: Effect of Policy on Consumption") ///
    addnotes("Standard errors clustered at the state level in parentheses." ///
             "State and year fixed effects absorbed via \texttt{reghdfe}." ///
             "\sym{*} \(p<0.10\), \sym{**} \(p<0.05\), \sym{***} \(p<0.01\)")

di "Table 2 exported to $tables/tab_did_full.tex"

* --------------------------------------------------------------------------
* Event study table
* --------------------------------------------------------------------------
di _n "=== Table 3: Event Study Coefficients ==="

* Need to re-create lead/lag indicators
forvalues k = 4(-1)2 {
    gen lead`k' = (time_to_treat == -`k') if !missing(time_to_treat)
    replace lead`k' = 0 if missing(lead`k')
}
forvalues k = 0/4 {
    gen lag`k' = (time_to_treat == `k') if !missing(time_to_treat)
    replace lag`k' = 0 if missing(lag`k')
}
replace lead4 = 1 if time_to_treat <= -4 & !missing(time_to_treat)
replace lag4 = 1 if time_to_treat >= 4 & !missing(time_to_treat)

* Label for nice output
label var lead4 "$\tau \leq -4$"
label var lead3 "$\tau = -3$"
label var lead2 "$\tau = -2$"
label var lag0  "$\tau = 0$"
label var lag1  "$\tau = 1$"
label var lag2  "$\tau = 2$"
label var lag3  "$\tau = 3$"
label var lag4  "$\tau \geq 4$"

reghdfe consumption lead4 lead3 lead2 lag0 lag1 lag2 lag3 lag4 ///
    pop income unemployment, ///
    absorb(state_id year) vce(cluster state_id)

eststo m4_event
estadd local fe_state "Yes"
estadd local fe_year "Yes"
estadd local controls "Yes"
estadd scalar n_cluster = e(N_clust)

* Pre-trend test
test lead4 lead3 lead2
estadd scalar f_pre = r(F)
estadd scalar p_pre = r(p)

esttab m4_event using "$tables/tab_event_study.tex", replace ///
    keep(lead4 lead3 lead2 lag0 lag1 lag2 lag3 lag4) ///
    order(lead4 lead3 lead2 lag0 lag1 lag2 lag3 lag4) ///
    b(%9.4f) se(%9.4f) ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    label ///
    nomtitles ///
    scalars("fe_state State FE" ///
            "fe_year Year FE" ///
            "controls Controls" ///
            "n_cluster Clusters" ///
            "r2_within Within R\$^2\$" ///
            "f_pre Pre-trend F-stat" ///
            "p_pre Pre-trend p-value") ///
    sfmt(%~9s %~9s %~9s %9.0f %9.4f %9.3f %9.3f) ///
    booktabs ///
    title("Event Study: Dynamic Treatment Effects") ///
    addnotes("Reference period: $\tau = -1$ (omitted)." ///
             "Endpoints binned: $\tau \leq -4$ and $\tau \geq 4$." ///
             "Standard errors clustered at the state level in parentheses." ///
             "\sym{*} \(p<0.10\), \sym{**} \(p<0.05\), \sym{***} \(p<0.01\)")

di "Table 3 exported to $tables/tab_event_study.tex"

* --------------------------------------------------------------------------
* Verify all table files
* --------------------------------------------------------------------------
di _n "=== Verify Outputs ==="

foreach f in tab_desc_stats tab_did_main tab_did_full tab_event_study {
    cap confirm file "$tables/`f'.tex"
    if _rc == 0 di "  OK: `f'.tex"
    else di "  MISSING: `f'.tex"
}

di _n "04_tables_export.do: Completed at $S_DATE $S_TIME"

log close tables
