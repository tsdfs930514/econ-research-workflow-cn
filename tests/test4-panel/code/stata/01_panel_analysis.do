/*==============================================================================
  Panel Data Analysis: Firm Productivity and R&D Spending
  =======================================================

  DGP: 200 firms x 15 years, firm FE correlated with regressors,
       AR(1) errors (rho=0.5), heteroskedasticity across firms.

  Estimation strategy:
    1. Pooled OLS (baseline, biased)
    2. Fixed Effects (consistent under correlated FE)
    3. Random Effects (inconsistent if FE correlated with X)
    4. Hausman test (FE vs RE)
    5. Multi-way FE via reghdfe (firm + year FE)
    6. Diagnostics: Wooldridge serial correlation, Pesaran CD, Modified Wald
    7. Dynamic GMM via xtabond2

  Output: output/tables/tab_panel_main.tex
==============================================================================*/

version 18
clear all
set more off
set seed 12345
set matsize 5000

* ==============================================================================
* Paths
* ==============================================================================
local root "`c(pwd)'"
local data "`root'/synthetic_panel.dta"
local logfile "`root'/output/logs/01_panel_analysis.log"
local outtab "`root'/output/tables/tab_panel_main.tex"

cap log close _all
log using "`logfile'", replace text name(panel_log)

di "=============================================================="
di "  Panel Analysis: Firm Productivity and R&D"
di "  Date: `c(current_date)' `c(current_time)'"
di "=============================================================="

timer clear
timer on 1

* ==============================================================================
* 1. Load and set up panel
* ==============================================================================
use "`data'", clear

xtset firm_id year
xtdescribe
xtsum productivity rd_spending capital labor export_share

summarize, detail

* ==============================================================================
* 2. Estimation
* ==============================================================================

* --- 2a. Pooled OLS ---
di _n ">>> Pooled OLS <<<"
eststo pooled: reg productivity rd_spending capital labor export_share, ///
    vce(cluster firm_id)

* --- 2b. Fixed Effects ---
di _n ">>> Fixed Effects <<<"
eststo fe: xtreg productivity rd_spending capital labor export_share, ///
    fe vce(cluster firm_id)

* --- 2c. Random Effects ---
di _n ">>> Random Effects <<<"
eststo re: xtreg productivity rd_spending capital labor export_share, ///
    re vce(cluster firm_id)

* --- 2d. Hausman test ---
* Re-estimate without cluster VCE for valid Hausman test
di _n ">>> Hausman Test (FE vs RE) <<<"
quietly xtreg productivity rd_spending capital labor export_share, fe
estimates store fe_haus

quietly xtreg productivity rd_spending capital labor export_share, re
estimates store re_haus

hausman fe_haus re_haus
local hausman_chi2 = r(chi2)
local hausman_p = r(p)
di "Hausman chi2 = `hausman_chi2', p-value = `hausman_p'"
if `hausman_p' < 0.05 {
    di "=> Reject RE at 5% level. FE preferred."
}
else {
    di "=> Cannot reject RE at 5% level."
}

* --- 2e. Multi-way FE via reghdfe ---
di _n ">>> Multi-way FE (firm + year) via reghdfe <<<"
eststo mwfe: reghdfe productivity rd_spending capital labor export_share, ///
    absorb(firm_id year) vce(cluster firm_id)

* ==============================================================================
* 3. Diagnostics
* ==============================================================================

* --- 3a. Wooldridge test for serial correlation ---
di _n ">>> Wooldridge Test for Serial Correlation <<<"
cap noisily xtserial productivity rd_spending capital labor export_share
if _rc == 0 {
    local wooldridge_F = r(F)
    local wooldridge_p = r(p)
    di "Wooldridge F = `wooldridge_F', p-value = `wooldridge_p'"
    if `wooldridge_p' < 0.05 {
        di "=> Reject no serial correlation at 5%. AR(1) detected."
    }
}
else {
    di "xtserial not available — skipping Wooldridge test"
}

* --- 3b. Pesaran CD test for cross-sectional dependence ---
di _n ">>> Pesaran CD Test <<<"
quietly xtreg productivity rd_spending capital labor export_share, fe
cap noisily xtcsd, pesaran abs
if _rc != 0 di "xtcsd not available — skipping Pesaran CD test"

* --- 3c. Modified Wald test for groupwise heteroskedasticity ---
di _n ">>> Modified Wald Test for Heteroskedasticity <<<"
quietly xtreg productivity rd_spending capital labor export_share, fe
cap noisily xttest3
if _rc != 0 di "xttest3 not available — skipping Modified Wald test"

* ==============================================================================
* 4. Dynamic GMM
* ==============================================================================
di _n ">>> Dynamic GMM (xtabond2) <<<"

cap noisily xtabond2 productivity L.productivity rd_spending capital labor export_share, ///
    gmm(L.productivity, lag(2 4)) iv(rd_spending capital labor export_share) ///
    two robust small
if _rc != 0 {
    di "xtabond2 failed, skipping GMM estimation"
}
else {
    eststo gmm: xtabond2 productivity L.productivity rd_spending capital labor export_share, ///
        gmm(L.productivity, lag(2 4)) iv(rd_spending capital labor export_share) ///
        two robust small
    di "Hansen J p-value: " e(hansenp)
    di "AR(1) p-value: " e(ar1p)
    di "AR(2) p-value: " e(ar2p)
}

* ==============================================================================
* 5. Export results table
* ==============================================================================
di _n ">>> Exporting Results Table <<<"

esttab pooled fe re mwfe using "`outtab'", replace ///
    b(4) se(4) star(* 0.10 ** 0.05 *** 0.01) ///
    title("Panel Estimates: Productivity and R\&D Spending") ///
    mtitles("Pooled OLS" "FE" "RE" "Multi-way FE") ///
    scalars("N_g Number of firms" "r2_w Within R-sq" "r2_b Between R-sq" "r2_o Overall R-sq") ///
    note("Standard errors clustered at firm level in parentheses.") ///
    label booktabs

di "Table saved to: `outtab'"

* ==============================================================================
* Wrap up
* ==============================================================================
timer off 1
timer list

di _n "=============================================================="
di "  Panel analysis complete."
di "=============================================================="

estimates clear
log close panel_log
