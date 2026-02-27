---
description: "Run complete DID/TWFE/Callaway-Sant'Anna analysis pipeline"
user_invocable: true
---

# /run-did — Difference-in-Differences Analysis Pipeline

When the user invokes `/run-did`, execute a complete DID analysis pipeline covering standard TWFE, heterogeneity-robust estimators (CS-DiD, dCDH, BJS), Goodman-Bacon decomposition, HonestDiD sensitivity, wild cluster bootstrap, cross-validation in Python, and full diagnostics.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## Step 0: Gather Inputs

Ask the user for the following before proceeding:

- **Dataset**: path to .dta file
- **Treatment variable**: binary treatment indicator (0/1), or the post-treatment indicator
- **Time variable**: period/year identifier
- **Outcome variable**: dependent variable Y (ask if log-transformed is preferred)
- **Group variable**: unit/entity identifier (e.g., state_id, firm_id)
- **First treatment variable**: variable indicating first period of treatment for each unit (needed for Callaway-Sant'Anna); set to 0 for never-treated units. If not available, offer to create it from treatment timing data
- **Control variables**: covariates to include (can be empty)
- **Cluster variable**: variable for clustered standard errors (default: same as group variable)
- **Number of leads/lags** for event study (default: 10 pre, 15 post; calibrate to data span)
- **Control group preference**: never-treated only, or not-yet-treated (default: never-treated)
- **Estimation method for CS-DiD**: doubly robust (`dripw`), inverse probability weighting (`ipw`), or outcome regression (`reg`) (default: `dripw`)

## Step 1: Data Validation & Descriptives (Stata .do file)

Create a .do file that validates data structure before estimation:

```stata
/*==============================================================================
  DID Analysis — Step 1: Data Validation & Descriptives
  Dataset:  DATASET_PATH
  Outcome:  OUTCOME_VAR
  Treatment: TREAT_VAR (first treated: FIRST_TREAT_VAR)
==============================================================================*/
clear all
set more off
set maxvar 32767

log using "output/logs/did_01_validation.log", replace

use "DATASET_PATH", clear

* --- Panel structure check ---
* NOTE: If GROUP_VAR is a string variable, it must be encoded to numeric first.
* This is common when data comes from CSV files (e.g., ISO3 country codes).
* Issue #19 from replication tests.
cap confirm numeric variable GROUP_VAR
if _rc != 0 {
    di "GROUP_VAR is string — encoding to numeric..."
    encode GROUP_VAR, gen(_group_id)
    local GROUP_VAR "_group_id"
}
xtset GROUP_VAR TIME_VAR
xtdescribe

* --- Treatment timing distribution ---
tab FIRST_TREAT_VAR if FIRST_TREAT_VAR > 0
di "Never-treated units: " _N - r(N)

* --- Cohort sizes ---
preserve
  keep if FIRST_TREAT_VAR > 0
  collapse (count) n_units = GROUP_VAR, by(FIRST_TREAT_VAR)
  list, clean
  save "data/temp/cohort_sizes.dta", replace
restore

* --- Pre-treatment outcome trends by group ---
preserve
  gen treated_group = (FIRST_TREAT_VAR > 0)
  collapse (mean) mean_y = OUTCOME_VAR, by(TIME_VAR treated_group)
  twoway (connected mean_y TIME_VAR if treated_group == 1, lcolor(cranberry) mcolor(cranberry)) ///
         (connected mean_y TIME_VAR if treated_group == 0, lcolor(navy) mcolor(navy)), ///
    legend(order(1 "Treated" 2 "Control") rows(1)) ///
    title("Pre-Treatment Outcome Trends") ///
    xtitle("Time") ytitle("Mean OUTCOME_VAR") ///
    xline(EARLIEST_TREAT_YEAR, lpattern(dash) lcolor(gray))
  graph export "output/figures/fig_parallel_trends_raw.pdf", replace
restore

* --- Summary statistics by treatment status ---
estpost tabstat OUTCOME_VAR CONTROLS if TIME_VAR < EARLIEST_TREAT_YEAR, ///
    by(treated_group) stat(mean sd min max n) columns(statistics)
esttab using "output/tables/tab_did_summary.tex", ///
    cells("mean(fmt(3)) sd(fmt(3)) min(fmt(3)) max(fmt(3)) count(fmt(0))") ///
    label booktabs replace noobs

log close
```

Execute via: `"D:\Stata18\StataMP-64.exe" -e do "code/stata/did_01_validation.do"`

Read the .log file to verify panel structure and treatment coding are correct.

## Step 2: Standard TWFE & Event Study (Stata .do file)

```stata
/*==============================================================================
  DID Analysis — Step 2: TWFE & Event Study
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/did_02_twfe.log", replace

use "DATASET_PATH", clear

* --- Canonical TWFE ---
eststo clear
eststo twfe_main: reghdfe OUTCOME_VAR TREAT_VAR CONTROLS, ///
    absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)

* Store key results
local twfe_b    = _b[TREAT_VAR]
local twfe_se   = _se[TREAT_VAR]
local twfe_n    = e(N)
local twfe_r2   = e(r2_within)
local n_clust   = e(N_clust)
di "TWFE: b = `twfe_b', se = `twfe_se', N = `twfe_n', R2w = `twfe_r2', clusters = `n_clust'"

* --- TWFE Event Study (manual leads/lags) ---
gen rel_time = TIME_VAR - FIRST_TREAT_VAR
replace rel_time = . if FIRST_TREAT_VAR == 0  // never-treated: exclude from ES dummies

* Create event-time dummies, omitting rel_time == -1 as reference
forvalues k = K_LEADS(-1)2 {
    gen lead`k' = (rel_time == -`k') if !missing(rel_time)
    replace lead`k' = 0 if missing(lead`k')
}
forvalues k = 0/K_LAGS {
    gen lag`k' = (rel_time == `k') if !missing(rel_time)
    replace lag`k' = 0 if missing(lag`k')
}

eststo twfe_es: reghdfe OUTCOME_VAR lead* lag* CONTROLS, ///
    absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)

* Joint test of pre-treatment leads
testparm lead*
local pretrend_F = r(F)
local pretrend_p = r(p)
di "Pre-trend joint F-test: F = `pretrend_F', p = `pretrend_p'"

* Event study plot
coefplot twfe_es, keep(lead* lag*) vertical yline(0, lcolor(gs10)) ///
    xline(K_LEADS, lpattern(dash) lcolor(gs10)) ///
    title("TWFE Event Study") ///
    xtitle("Periods Relative to Treatment") ytitle("Coefficient") ///
    ciopts(recast(rcap) lcolor(navy)) mcolor(navy) ///
    note("Joint pre-trend F = `pretrend_F' (p = `: di %5.3f `pretrend_p'')")
graph export "output/figures/fig_event_study_twfe.pdf", replace

log close
```

## Step 3: Robust DID Estimators (Stata .do file)

```stata
/*==============================================================================
  DID Analysis — Step 3: Heterogeneity-Robust Estimators
  Packages required: csdid, did_multiplegt, did_imputation, bacondecomp,
                     eventstudyinteract
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/did_03_robust.log", replace

use "DATASET_PATH", clear

* Ensure first_treat = 0 for never-treated (csdid requirement)
assert FIRST_TREAT_VAR == 0 if TREAT_VAR == 0

* --- 1. Callaway & Sant'Anna (2021) --- [PREFERRED]
* Doubly-robust, group-time ATT with cluster bootstrap
* NOTE: csdid and csdid_stats are version-sensitive. Wrap all calls in
* cap noisily to handle version-specific syntax changes (Issue #20).
cap noisily csdid OUTCOME_VAR CONTROLS, ivar(GROUP_VAR) time(TIME_VAR) gvar(FIRST_TREAT_VAR) ///
    method(dripw) notyet

* Aggregations — wrap in cap noisily (syntax may vary by version, Issue #20)
cap noisily csdid_stats simple, estore(cs_simple)
cap noisily csdid_stats event, estore(cs_event)
cap noisily csdid_stats group, estore(cs_group)
cap noisily csdid_stats calendar, estore(cs_calendar)

* CS Event study plot
cap noisily {
    csdid_plot, style(rcap) title("CS-DiD Event Study") ///
        xtitle("Periods Since Treatment") ytitle("ATT")
    graph export "output/figures/fig_event_study_cs.pdf", replace
}

* --- 2. de Chaisemartin & D'Haultfoeuille (2020) ---
* Wrap in cap noisily — version-sensitive community package (like csdid)
cap noisily did_multiplegt OUTCOME_VAR GROUP_VAR TIME_VAR TREAT_VAR, ///
    robust_dynamic dynamic(K_LAGS) placebo(K_LEADS) ///
    breps(100) cluster(CLUSTER_VAR)
* Note: breps=100 for speed; increase to 500-1000 for final results

* --- 3. Borusyak, Jaravel, Spiess (2024) — Imputation ---
cap noisily did_imputation OUTCOME_VAR GROUP_VAR TIME_VAR FIRST_TREAT_VAR, ///
    allhorizons pretrends(K_LEADS) minn(0)
if _rc == 0 {
    estimates store bjs
}

* --- 4. Sun & Abraham (2021) — Interaction-Weighted ---
gen event_time = TIME_VAR - FIRST_TREAT_VAR
replace event_time = . if FIRST_TREAT_VAR == 0
cap noisily eventstudyinteract OUTCOME_VAR lead* lag* CONTROLS, ///
    absorb(GROUP_VAR TIME_VAR) cohort(FIRST_TREAT_VAR) ///
    control_cohort(FIRST_TREAT_VAR == 0) ///
    vce(cluster CLUSTER_VAR)

* --- 5. Goodman-Bacon Decomposition ---
* Wrap in cap noisily — bacondecomp has version-sensitive dependencies (Issue #2)
cap noisily {
    bacondecomp OUTCOME_VAR TREAT_VAR, id(GROUP_VAR) t(TIME_VAR) ddetail
    graph export "output/figures/fig_bacon_decomp.pdf", replace
}

* --- Comparison Table ---
esttab cs_simple twfe_main bjs using "output/tables/tab_did_comparison.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("CS-DiD" "TWFE" "BJS Imputation") ///
    label booktabs replace ///
    title("DID Estimator Comparison") ///
    note("Standard errors clustered at CLUSTER_VAR level.")

log close
```

## Step 4: Inference Robustness (Stata .do file)

```stata
/*==============================================================================
  DID Analysis — Step 4: Inference Robustness
  HonestDiD (Rambachan-Roth), Wild Cluster Bootstrap
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/did_04_inference.log", replace

use "DATASET_PATH", clear

* --- Wild Cluster Bootstrap (Roodman et al.) ---
* Addresses finite-sample cluster inference (important when N_clusters < 50)
* NOTE: boottest works best after reghdfe. It may fail (r(198)) after
* plain reg, xtreg, or estimators with non-standard VCE. Always wrap
* in cap noisily when using non-reghdfe estimators (Issue #1, #12).
reghdfe OUTCOME_VAR TREAT_VAR CONTROLS, absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
cap noisily boottest TREAT_VAR, cluster(CLUSTER_VAR) boottype(mammen) reps(999) seed(12345)
* Report: WCB p-value and 95% CI

* --- HonestDiD: Sensitivity to Parallel Trends Violations ---
* Requires: honestdid package
* Run event study first, then apply HonestDiD
reghdfe OUTCOME_VAR lead* lag* CONTROLS, absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
honestdid, pre(1/K_LEADS) post(1/K_LAGS) mvec(0(0.01)0.05)
* Interpretation: How much can parallel trends be violated (M parameter)
* before the treatment effect is no longer significant?

log close
```

## Step 5: Python Cross-Validation

> For R `fixest` cross-validation or multi-language comparison, use `/cross-check` after this step.

```python
"""
DID Cross-Validation: Stata vs Python (pyfixest)
"""
import pandas as pd
import pyfixest as pf

df = pd.read_stata("DATASET_PATH")

# TWFE via pyfixest (matches Stata reghdfe)
model = pf.feols("OUTCOME_VAR ~ TREAT_VAR + CONTROLS | GROUP_VAR + TIME_VAR",
                 data=df, vcov={"CRV1": "CLUSTER_VAR"})
print("=== Python TWFE ===")
print(model.summary())

# Cross-validate
stata_coef = STATA_TWFE_COEF  # from Step 2 log
python_coef = model.coef()["TREAT_VAR"]
pct_diff = abs(stata_coef - python_coef) / abs(stata_coef) * 100
print(f"\nCross-validation:")
print(f"  Stata TWFE:  {stata_coef:.6f}")
print(f"  Python TWFE: {python_coef:.6f}")
print(f"  Difference:  {pct_diff:.4f}%")
print(f"  Status:      {'PASS' if pct_diff < 0.1 else 'FAIL'}")

# Event study via pyfixest (if supported)
try:
    es_model = pf.feols(
        "OUTCOME_VAR ~ i(rel_time, ref=-1) + CONTROLS | GROUP_VAR + TIME_VAR",
        data=df, vcov={"CRV1": "CLUSTER_VAR"})
    pf.iplot(es_model)
except Exception as e:
    print(f"Event study in pyfixest failed: {e}")
```

## Step 6: Publication-Quality Output

Generate the main results table matching TOP5 journal format:

```stata
/*==============================================================================
  DID Analysis — Step 6: Final Tables (AER/TOP5 format)
==============================================================================*/
clear all
set more off

log using "output/logs/did_06_tables.log", replace

use "DATASET_PATH", clear

* Run all specifications and store
eststo clear
* (1) CS-DiD, never-treated
eststo m1: ... /* CS-DiD specification */
* (2) TWFE
eststo m2: reghdfe OUTCOME_VAR TREAT_VAR CONTROLS, absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
* (3) CS-DiD, not-yet-treated
eststo m3: ... /* CS-DiD not-yet-treated */
* (4) Alternative outcome
eststo m4: ... /* Alternative outcome */
* (5) Alternative outcome 2
eststo m5: ... /* e.g., prices */

* --- AER-style table ---
esttab m1 m2 m3 m4 m5 using "output/tables/tab_did_main.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    mtitles("CS-DiD" "TWFE" "CS-DiD NYT" "Alt. Outcome" "Prices") ///
    scalars("N_clust Clusters" "r2_within Within R$^2$") ///
    addnotes("Standard errors clustered at CLUSTER_VAR level in parentheses." ///
             "CS-DiD: Callaway \& Sant'Anna (2021) doubly-robust estimator." ///
             "Column (1) uses never-treated; column (3) uses not-yet-treated control.") ///
    title("Effect of TREATMENT on OUTCOME") ///
    substitute(\_ _)

log close
```

## Step 7: Diagnostics Summary

After all steps complete, provide a written summary covering:

1. **Panel Structure**: Balanced/unbalanced, N units, T periods, N treated, N never-treated
2. **Parallel Trends**: Are pre-treatment leads jointly insignificant? Visual assessment of pre-trend plot. HonestDiD M-sensitivity result.
3. **Treatment Effect Heterogeneity**: Do CS-DiD, dCDH, BJS give different ATTs vs. TWFE? Bacon decomposition: what share of TWFE weight comes from problematic comparisons?
4. **Inference Robustness**: Wild cluster bootstrap p-value (especially if clusters < 50). HonestDiD: at what M does significance disappear?
5. **Recommended Estimator**: Based on diagnostics:
   - Uniform timing → TWFE is fine
   - Staggered, homogeneous effects → TWFE and robust agree
   - Staggered, heterogeneous effects → CS-DiD or BJS preferred
6. **Cross-Validation**: Stata vs Python coefficient match (target: < 0.1% difference)
7. **Event Study Narrative**: Describe the dynamic treatment effects pattern

## Required Stata Packages

Install before first run:
```stata
ssc install reghdfe
ssc install ftools
ssc install csdid
ssc install drdid
ssc install did_multiplegt
ssc install did_imputation
ssc install bacondecomp
ssc install eventstudyinteract
ssc install event_plot
ssc install boottest
ssc install honestdid
ssc install coefplot
```

## Execution Notes

- Run all Stata .do files via: `"D:\Stata18\StataMP-64.exe" -e do "script.do"`
- Always read the `.log` file after each Stata execution to check for errors
- If a package is not installed, `ssc install PACKAGE` first, then re-run
- Use `set seed 12345` before any bootstrap/permutation for reproducibility
- Export figures as PDF (vector) for publication quality
- All tables use `booktabs` format with 4 decimal places for DID coefficients
