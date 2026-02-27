/*==============================================================================
  Test 5: Full Pipeline - 02 Descriptive Statistics
  Summary statistics and treatment balance tables
==============================================================================*/
version 18
clear all
set more off

cap log close _all
log using "$logs/02_desc_stats.log", replace name(desc)

di "============================================================"
di "02_desc_stats.do: Started at $S_DATE $S_TIME"
di "============================================================"

* --------------------------------------------------------------------------
* Load cleaned data
* --------------------------------------------------------------------------
use "$clean/panel_cleaned.dta", clear
di "Loaded `c(N)' observations"

* --------------------------------------------------------------------------
* Panel A: Overall summary statistics
* --------------------------------------------------------------------------
di _n "=== Panel A: Summary Statistics ==="

eststo clear

estpost summarize consumption pop income unemployment ln_consumption ///
    ln_pop ln_income, detail

esttab using "$tables/tab_desc_stats.tex", replace ///
    cells("count(fmt(%9.0fc)) mean(fmt(%9.2fc)) sd(fmt(%9.2fc)) min(fmt(%9.2fc)) max(fmt(%9.2fc)) p50(fmt(%9.2fc))") ///
    noobs nonumber nomtitle label ///
    title("Panel A: Summary Statistics") ///
    booktabs ///
    addnotes("Source: Generated panel data. N = 300 (30 states x 10 years).")

di "Panel A exported"

* --------------------------------------------------------------------------
* Panel B: Treatment balance table (covariates by treatment status)
* --------------------------------------------------------------------------
di _n "=== Panel B: Treatment Balance ==="

* Use pre-treatment observations only for balance check
preserve
keep if year < 2013  // before any treatment begins

eststo clear

* Never-treated group
eststo never: estpost summarize consumption pop income unemployment ///
    if ever_treated == 0

* Ever-treated group (pre-treatment)
eststo ever: estpost summarize consumption pop income unemployment ///
    if ever_treated == 1

esttab never ever using "$tables/tab_balance.tex", replace ///
    cells("mean(fmt(%9.2fc)) sd(fmt(%9.2fc) par)") ///
    label nonumber ///
    mtitles("Never Treated" "Ever Treated (Pre)") ///
    title("Panel B: Pre-Treatment Balance") ///
    booktabs ///
    addnotes("Pre-treatment period: 2010--2012, before any cohort adopts policy.")

restore

di "Panel B exported"

* --------------------------------------------------------------------------
* Panel C: Outcome means by cohort and period
* --------------------------------------------------------------------------
di _n "=== Panel C: Cohort Means ==="

table cohort post, statistic(mean consumption) statistic(sd consumption) ///
    statistic(freq) nototals

* --------------------------------------------------------------------------
* Summary statistics to screen
* --------------------------------------------------------------------------
di _n "--- Quick Summary ---"
tabstat consumption pop income unemployment, ///
    by(ever_treated) statistics(mean sd n) format(%9.2f)

di "02_desc_stats.do: Completed at $S_DATE $S_TIME"

log close desc
