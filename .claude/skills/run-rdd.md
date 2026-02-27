---
description: "Run complete RDD analysis pipeline with all diagnostics"
user_invocable: true
---

# /run-rdd — Regression Discontinuity Design Analysis Pipeline

When the user invokes `/run-rdd`, execute a complete sharp or fuzzy RDD analysis pipeline covering visualization, manipulation testing, covariate balance, main estimation with rdrobust, bandwidth sensitivity, polynomial order robustness, kernel sensitivity, placebo tests, donut hole RD, and Python cross-validation.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## Step 0: Gather Inputs

Ask the user for:

- **Dataset**: path to .dta file
- **Running variable**: the assignment/forcing variable (e.g., test score, age, vote share)
- **Cutoff value**: the threshold where treatment changes (numeric)
- **Outcome variable**: dependent variable Y
- **Treatment variable**: binary indicator (if not present, will generate from running var)
- **RDD type**: sharp or fuzzy
- **Treatment take-up variable** (fuzzy only): actual treatment receipt variable
- **Covariates** (optional): pre-determined covariates for balance tests and precision
- **Cluster variable** (optional): for clustered standard errors

## Step 1: RD Visualization (Stata .do file)

```stata
/*==============================================================================
  RDD Analysis — Step 1: Visualization
  Reference: Cattaneo, Idrobo & Titiunik (2020) best practices
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_01_visual.log", replace

use "DATASET_PATH", clear

* Generate treatment if needed
cap gen treat = (RUNNING_VAR >= CUTOFF)

* --- RD Plot: binned scatter with local polynomial ---
rdplot OUTCOME_VAR RUNNING_VAR, c(CUTOFF) p(1) ///
    graph_options(title("Regression Discontinuity Plot") ///
    xtitle("RUNNING_VAR") ytitle("OUTCOME_VAR") ///
    xline(CUTOFF, lcolor(cranberry) lpattern(dash)))
graph export "output/figures/fig_rd_plot.pdf", replace

* --- Histogram of running variable ---
histogram RUNNING_VAR, bin(50) ///
    xline(CUTOFF, lcolor(cranberry) lpattern(dash)) ///
    title("Distribution of Running Variable") ///
    xtitle("RUNNING_VAR") ytitle("Frequency")
graph export "output/figures/fig_rd_histogram.pdf", replace

log close
```

## Step 2: Manipulation Test (Stata .do file)

```stata
/*==============================================================================
  RDD — Step 2: Cattaneo-Jansson-Ma Density Test
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_02_density.log", replace

use "DATASET_PATH", clear

* --- CJM (2020) density test (preferred) ---
rddensity RUNNING_VAR, c(CUTOFF) plot ///
    plot_range(PLOT_MIN PLOT_MAX)
graph export "output/figures/fig_rd_density.pdf", replace

* Capture density test p-value (Issue #3: use correct e-class scalar)
* rddensity stores p-value in different scalars across versions:
*   e(pv_q)   — quadratic (preferred)
*   e(pv_p)   — polynomial
* Check which is available:
cap local density_p = e(pv_q)
if "`density_p'" == "" | "`density_p'" == "." {
    cap local density_p = e(pv_p)
}
di "Density test p-value: `density_p'"

* H0: density is continuous at cutoff
* Rejection → evidence of sorting/manipulation

log close
```

## Step 3: Covariate Balance (Stata .do file)

```stata
/*==============================================================================
  RDD — Step 3: Covariate Balance at Cutoff
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_03_balance.log", replace

use "DATASET_PATH", clear

* --- Test each covariate for discontinuity ---
local covariates "COVAR1 COVAR2 COVAR3"

foreach var of local covariates {
    di "=== Balance test: `var' ==="
    rdrobust `var' RUNNING_VAR, c(CUTOFF) kernel(triangular) bwselect(mserd)
    di ""
}

* --- Balance table within optimal bandwidth ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) bwselect(mserd)
local bw_opt = e(h_l)

gen near_cutoff = abs(RUNNING_VAR - CUTOFF) <= `bw_opt'
gen above = (RUNNING_VAR >= CUTOFF)

tabstat `covariates' if near_cutoff, by(above) ///
    stat(mean sd n) columns(statistics) format(%9.3f)

log close
```

## Step 4: Main RD Estimation (Stata .do file)

```stata
/*==============================================================================
  RDD — Step 4: Main Estimation (rdrobust)
  Reports: Conventional, Bias-Corrected, and Robust estimates
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_04_main.log", replace

use "DATASET_PATH", clear

* --- Sharp RD with MSE-optimal bandwidth ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
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

* --- With CER-optimal bandwidth (for inference) ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
    kernel(triangular) bwselect(cerrd) all

* --- With covariates (for precision) ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
    kernel(triangular) bwselect(mserd) covs(COVARIATES)

* --- Fuzzy RD (if applicable) ---
* rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
*     fuzzy(TREATMENT_TAKEUP_VAR) kernel(triangular) bwselect(mserd) all

log close
```

## Step 5: Bandwidth & Polynomial Sensitivity (Stata .do file)

```stata
/*==============================================================================
  RDD — Step 5: Bandwidth & Polynomial Sensitivity
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_05_sensitivity.log", replace

use "DATASET_PATH", clear

* --- Get MSE-optimal bandwidth ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(triangular) bwselect(mserd)
local bw_opt = e(h_l)

* --- Bandwidth sensitivity ---
local multipliers "0.50 0.75 1.00 1.25 1.50 2.00"

tempfile bw_results
postfile bw_handle str10 spec bw_val coef se pval N_eff using `bw_results', replace

foreach m of local multipliers {
    local bw_test = `bw_opt' * `m'
    rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(triangular) h(`bw_test')
    post bw_handle ("`m'x") (`bw_test') (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (e(N_h_l) + e(N_h_r))
}

* --- Polynomial order sensitivity ---
forvalues p = 1/3 {
    rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(triangular) bwselect(mserd) p(`p')
    post bw_handle ("p=`p'") (e(h_l)) (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (e(N_h_l) + e(N_h_r))
}

* --- Kernel sensitivity ---
foreach kern in triangular uniform epanechnikov {
    rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(`kern') bwselect(mserd)
    post bw_handle ("`kern'") (e(h_l)) (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (e(N_h_l) + e(N_h_r))
}

postclose bw_handle

* --- Display and plot ---
use `bw_results', clear
gen ci_lo = coef - 1.96 * se
gen ci_hi = coef + 1.96 * se
list, clean

log close
```

## Step 6: Placebo & Donut Tests (Stata .do file)

```stata
/*==============================================================================
  RDD — Step 6: Placebo Cutoffs & Donut Hole Tests
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_06_placebo.log", replace

use "DATASET_PATH", clear

* --- Placebo cutoffs ---
* Test at false thresholds away from true cutoff
sum RUNNING_VAR, detail
local p25 = r(p25)
local p75 = r(p75)

* Below cutoff: test at 25th percentile
di "=== Placebo at p25 (`p25') ==="
rdrobust OUTCOME_VAR RUNNING_VAR if RUNNING_VAR < CUTOFF, ///
    c(`p25') kernel(triangular) bwselect(mserd)

* Above cutoff: test at 75th percentile
di "=== Placebo at p75 (`p75') ==="
rdrobust OUTCOME_VAR RUNNING_VAR if RUNNING_VAR > CUTOFF, ///
    c(`p75') kernel(triangular) bwselect(mserd)

* --- Donut hole RD ---
* Exclude observations very close to cutoff
foreach donut in 0.5 1 2 5 {
    di "=== Donut RD: excluding +-`donut' from cutoff ==="
    rdrobust OUTCOME_VAR RUNNING_VAR if abs(RUNNING_VAR - CUTOFF) > `donut', ///
        c(CUTOFF) kernel(triangular) bwselect(mserd)
}

log close
```

## Step 7: Python Cross-Validation

```python
"""
RDD Cross-Validation using rdrobust Python package
"""
import pandas as pd
import numpy as np

df = pd.read_stata("DATASET_PATH")

try:
    from rdrobust import rdrobust, rdplot, rdbwselect
    result = rdrobust(y=df["OUTCOME_VAR"], x=df["RUNNING_VAR"], c=CUTOFF,
                      kernel='triangular', bwselect='mserd')
    print("=== Python RD Results ===")
    print(result)
    python_rd = result.coef.iloc[0]  # conventional estimate
except ImportError:
    print("rdrobust not installed. Install: pip install rdrobust")
    print("Falling back to pyfixest local regression...")
    import pyfixest as pf
    # Local linear within optimal bandwidth (from Stata)
    bw = OPTIMAL_BW_FROM_STATA
    df_local = df[abs(df["RUNNING_VAR"] - CUTOFF) <= bw].copy()
    df_local["above"] = (df_local["RUNNING_VAR"] >= CUTOFF).astype(int)
    df_local["centered"] = df_local["RUNNING_VAR"] - CUTOFF
    df_local["interact"] = df_local["above"] * df_local["centered"]
    model = pf.feols("OUTCOME_VAR ~ above + centered + interact", data=df_local)
    print(model.summary())
    python_rd = model.coef()["above"]

stata_rd = STATA_RD_COEF
pct_diff = abs(stata_rd - python_rd) / abs(stata_rd) * 100
print(f"\nCross-validation:")
print(f"  Stata:  {stata_rd:.6f}")
print(f"  Python: {python_rd:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 0.5 else 'FAIL'}")
```

## Step 8: Diagnostics Summary

After all steps, provide:

1. **Manipulation Test**: CJM density test p-value. If rejected, RDD validity questionable.
2. **Covariate Balance**: Which covariates show discontinuities? Balanced covariates support validity.
3. **Main Estimate**: Report bias-corrected estimate with robust SE and CI.
4. **Bandwidth Sensitivity**: Stable across 0.5x to 2x optimal? Flag instability.
5. **Polynomial Order**: Stable across p=1,2,3? Local linear (p=1) is default.
6. **Kernel Sensitivity**: Triangular vs uniform vs Epanechnikov agreement.
7. **Placebo Tests**: False cutoffs should show null effects.
8. **Donut Hole**: Excluding units near cutoff should preserve the estimate.
9. **Cross-Validation**: Stata vs Python match (tolerance: 0.5%).

## Required Stata Packages

```stata
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace
net install rdlocrand, from(https://raw.githubusercontent.com/rdpackages/rdlocrand/master/stata) replace
net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace
net install rdmulti, from(https://raw.githubusercontent.com/rdpackages/rdmulti/master/stata) replace
ssc install reghdfe
ssc install ftools
ssc install coefplot
```
