---
description: "Run bootstrap & resampling inference pipeline (pairs, wild cluster, residual, teffects)"
user_invocable: true
---

# /run-bootstrap — Bootstrap & Resampling Inference Pipeline

When the user invokes `/run-bootstrap`, execute a comprehensive bootstrap inference pipeline covering pairs cluster bootstrap, wild cluster bootstrap (Rademacher/Mammen), residual bootstrap, treatment effects bootstrap (teffects wrapper), and derived quantities via nlcom/parmest. Includes Python cross-validation.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## When to Use Bootstrap Inference

- **Few clusters** (< 50): Wild cluster bootstrap corrects analytical SE bias
- **Complex estimators**: Custom programs, treatment effects, or derived quantities where analytical SEs are unavailable or unreliable
- **Panel data with cluster resampling**: Pairs cluster bootstrap preserves within-unit time series structure
- **Nonlinear estimators**: Bootstrap SEs for marginal effects, nlcom-derived quantities
- **Publication robustness**: Reviewers increasingly expect bootstrap p-values alongside analytical ones

## Step 0: Gather Inputs

Ask the user for:

- **Dataset**: path to .dta file
- **Baseline estimator command**: the regression or estimation command to bootstrap (e.g., `reghdfe Y X CONTROLS, absorb(FE) vce(cluster C)`)
- **Coefficient of interest**: variable whose inference is the focus
- **Cluster variable**: variable for cluster-level resampling
- **Panel variable** (if panel data): unit identifier for pairs cluster bootstrap
- **Time variable** (if panel data): time identifier
- **Bootstrap type(s)** to run: pairs cluster, wild cluster, residual, or all (default: all applicable)
- **Number of replications**: 200 for exploration, 999 for publication (default: 999)
- **Treatment effects model** (optional): if using `teffects`, specify the treatment model (e.g., `probit treatment covars`)
- **Derived quantities** (optional): nlcom expressions to bootstrap (e.g., long-run effect, cumulative impulse response)

## Compact Bootstrap Prefix Syntax

For simple regressions, Stata's `bs` prefix is much more concise than `bootstrap _b, reps(): command`. Both are valid. Pattern from Culture & Development replication (data_programs.zip):

```stata
* Compact prefix — works inside eststo chain
eststo: bs, reps(500): reg OUTCOME_VAR TREATMENT_VAR CONTROLS, cluster(CLUSTER_VAR)

* Multiple specifications
eststo m1: bs, reps(500): reg Y X, cluster(cluster)
eststo m2: bs, reps(500): reg Y X CONTROLS, cluster(cluster)
eststo m3: bs, reps(500): reg Y X CONTROLS EXTRA_CONTROLS, cluster(cluster)
esttab m1 m2 m3, se b star(* 0.10 ** 0.05 *** 0.01)
```

`bs` vs `bootstrap _b, reps():`:
- `bs, reps(N): command` — shorthand, works with `eststo`, simpler syntax
- `bootstrap _b, reps(N) cluster() idcluster() saving():` — full control, required for panel bootstrap with `idcluster()` and for saving draws to file

## Step 1: Pairs Cluster Bootstrap (Stata .do file)

Resamples entire clusters with replacement, preserving within-cluster correlation structure. Standard approach for panel data.

```stata
/*==============================================================================
  Bootstrap Analysis — Step 1: Pairs Cluster Bootstrap
  Reference: Cameron, Gelbach & Miller (2008), bootstrap-t
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_01_pairs.log", replace

use "DATASET_PATH", clear

* --- Baseline estimation (for comparison) ---
eststo clear
eststo baseline: BASELINE_COMMAND
local b_analytic = _b[COEF_VAR]
local se_analytic = _se[COEF_VAR]
local p_analytic = 2 * ttail(e(df_r), abs(_b[COEF_VAR] / _se[COEF_VAR]))
di "Analytical: b = `b_analytic', SE = `se_analytic', p = `p_analytic'"

* --- Pairs cluster bootstrap ---
* idcluster() required for panel data — creates new sequential IDs per draw
gen _cl = CLUSTER_VAR
cap tsset _cl TIME_VAR

bootstrap _b, seed(12345) reps(NREPS) cluster(CLUSTER_VAR) idcluster(_cl) ///
    nodots saving("data/temp/boot_pairs.dta", replace): ///
    BASELINE_COMMAND_WITHOUT_VCE

eststo boot_pairs
local b_boot = _b[COEF_VAR]
local se_boot = _se[COEF_VAR]

* --- Percentile CI ---
* NOTE: BCa requires explicit saving in the bootstrap prefix command.
* Default to percentile + bc only. Add bca only if bootstrap used
* saving(, bca) option. See Issue #11 from replication tests.
cap noisily estat bootstrap, percentile bc
* If BCa is needed, re-run bootstrap with: saving("file.dta", replace) bca

* --- Bootstrap distribution ---
* NOTE: `bootstrap _b` saves variables with `_b_` prefix + variable name,
* NOT `_bs_N` numbering. E.g., for variable `x`, saved as `_b_x`.
* Use `ds` to dynamically identify variable names (Issue #13).
preserve
use "data/temp/boot_pairs.dta", clear
ds
local boot_var : word 1 of `r(varlist)'
hist `boot_var', bin(50) normal ///
    title("Pairs Cluster Bootstrap Distribution") ///
    xtitle("Coefficient Estimate") ytitle("Density") ///
    xline(`b_analytic', lcolor(cranberry) lpattern(dash)) ///
    note("Vertical line = analytical point estimate. N reps = NREPS")
graph export "output/figures/fig_boot_pairs_dist.pdf", replace
restore

log close
```

## Step 2: Wild Cluster Bootstrap (Stata .do file)

Preferred when the number of clusters is small (< 50). Uses Rademacher or Mammen weight distributions.

```stata
/*==============================================================================
  Bootstrap Analysis — Step 2: Wild Cluster Bootstrap
  Reference: Cameron, Gelbach & Miller (2008); Roodman et al. (2019)
  Package: boottest (Roodman)
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_02_wild.log", replace

use "DATASET_PATH", clear

* --- Run baseline regression ---
BASELINE_COMMAND

* --- Wild cluster bootstrap with Rademacher weights ---
* NOTE: boottest may not work after all estimator types. It works best after
* reghdfe. After plain reg or xtreg, it may fail with r(198). Always wrap
* in cap noisily if using non-reghdfe estimators (Issue #12).
cap noisily boottest COEF_VAR, cluster(CLUSTER_VAR) boottype(rademacher) ///
    reps(NREPS) seed(12345) nograph
local wcb_p_rad = r(p)
local wcb_ci_lo_rad = r(CI)[1,1]
local wcb_ci_hi_rad = r(CI)[1,2]

* --- Wild cluster bootstrap with Mammen weights ---
boottest COEF_VAR, cluster(CLUSTER_VAR) boottype(mammen) ///
    reps(NREPS) seed(12345) graphname(wcb_mammen)
local wcb_p_mam = r(p)
local wcb_ci_lo_mam = r(CI)[1,1]
local wcb_ci_hi_mam = r(CI)[1,2]
graph export "output/figures/fig_boot_wild_mammen.pdf", replace

* --- Wild cluster bootstrap with Webb weights (6-point) ---
* Preferred when clusters < 12
boottest COEF_VAR, cluster(CLUSTER_VAR) boottype(webb) ///
    reps(NREPS) seed(12345) nograph
local wcb_p_webb = r(p)

* --- Comparison ---
di "============================================="
di "WILD CLUSTER BOOTSTRAP RESULTS"
di "============================================="
di "  Rademacher: p = `wcb_p_rad',  CI = [`wcb_ci_lo_rad', `wcb_ci_hi_rad']"
di "  Mammen:     p = `wcb_p_mam',  CI = [`wcb_ci_lo_mam', `wcb_ci_hi_mam']"
di "  Webb:       p = `wcb_p_webb'"
di "============================================="

* --- Joint test (if multiple coefficients) ---
* boottest COEF_VAR1 COEF_VAR2, cluster(CLUSTER_VAR) boottype(mammen) reps(NREPS)

log close
```

## Step 3: Residual Bootstrap (Stata .do file)

Appropriate under homoskedasticity. Resamples residuals and reconstructs outcomes.

```stata
/*==============================================================================
  Bootstrap Analysis — Step 3: Residual Bootstrap
  Appropriate when errors are iid (homoskedastic, no clustering)
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_03_residual.log", replace

use "DATASET_PATH", clear

* --- Fit baseline and save residuals ---
BASELINE_COMMAND
predict double _resid, residuals
predict double _yhat, xb

* --- Residual bootstrap program ---
cap program drop resid_boot
program define resid_boot, rclass
    syntax, yvar(string) xvar(string) controls(string) fe(string) cluster(string)
    tempvar newresid newy
    * Resample residuals with replacement
    bsample
    gen `newresid' = _resid
    gen `newy' = _yhat + `newresid'
    reghdfe `newy' `xvar' `controls', absorb(`fe') vce(cluster `cluster')
    return scalar b = _b[`xvar']
end

simulate b_resid = r(b), reps(NREPS) seed(12345): ///
    resid_boot, yvar(OUTCOME_VAR) xvar(COEF_VAR) ///
    controls(CONTROLS) fe(FIXED_EFFECTS) cluster(CLUSTER_VAR)

* --- Residual bootstrap p-value ---
BASELINE_COMMAND
local b_actual = _b[COEF_VAR]

count if abs(b_resid) >= abs(`b_actual')
local resid_p = r(N) / NREPS
di "Residual bootstrap p-value: `resid_p'"

* --- Residual bootstrap CI (percentile) ---
_pctile b_resid, p(2.5 97.5)
di "Residual bootstrap 95% CI: [" r(r1) ", " r(r2) "]"

log close
```

## Step 4: Bootstrap for Treatment Effects (Stata .do file)

Wraps `teffects` (RA, IPW, AIPW) inside `bootstrap` for cluster-robust inference. Pattern from Acemoglu et al. (2019, JPE) Table 5.

```stata
/*==============================================================================
  Bootstrap Analysis — Step 4: Treatment Effects with Bootstrap
  Reference: Acemoglu, Naidu, Restrepo & Robinson (2019, JPE) Table 5
  Pattern: bootstrap wrapping custom programs that compute ATET
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_04_teffects.log", replace

use "DATASET_PATH", clear

* --- Define custom program for RA-ATET ---
cap program drop tef_ra
program define tef_ra, rclass
    teffects ra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR), atet
    return scalar atet = _b[r1vs0.TREATMENT_VAR]
end

* --- Define custom program for IPW-ATET (probit first stage) ---
cap program drop tef_ipw
program define tef_ipw, rclass
    teffects ipw (OUTCOME_VAR) (TREATMENT_VAR COVARIATES, probit), atet
    return scalar atet = _b[r1vs0.TREATMENT_VAR]
end

* --- Define custom program for AIPW-ATET (doubly robust) ---
cap program drop tef_aipw
program define tef_aipw, rclass
    teffects ipwra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR COVARIATES, probit), atet
    return scalar atet = _b[r1vs0.TREATMENT_VAR]
end

* --- Bootstrap RA ---
bootstrap atet_ra = r(atet), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_tef_ra.dta", replace): tef_ra
eststo tef_ra_boot

* --- Bootstrap IPW ---
bootstrap atet_ipw = r(atet), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_tef_ipw.dta", replace): tef_ipw
eststo tef_ipw_boot

* --- Bootstrap AIPW ---
bootstrap atet_aipw = r(atet), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_tef_aipw.dta", replace): tef_aipw
eststo tef_aipw_boot

* --- Comparison table ---
esttab tef_ra_boot tef_ipw_boot tef_aipw_boot ///
    using "output/tables/tab_teffects_bootstrap.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("RA" "IPW" "AIPW") ///
    label booktabs replace ///
    title("Treatment Effects (ATET) with Cluster Bootstrap") ///
    note("Bootstrap SEs with NREPS replications, clustered at CLUSTER_VAR level." ///
         "IPW and AIPW use probit treatment model.")

log close
```

## Step 5: Saving Bootstrap CIs with parmest & nlcom (Stata .do file)

For derived quantities (e.g., cumulative impulse response, period-averaged effects).

```stata
/*==============================================================================
  Bootstrap Analysis — Step 5: Derived Quantities & parmest
  Reference: DDCG Table 5 — nlcom for period-averaged effects, parmest for CI export
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_05_derived.log", replace

use "DATASET_PATH", clear

* --- Bootstrap the full estimation + derived quantities ---
cap program drop boot_derived
program define boot_derived, rclass
    BASELINE_COMMAND
    * Derived quantity: e.g., period-averaged effect
    * nlcom (avg_effect: (_b[lag0] + _b[lag1] + _b[lag2]) / 3)
    * return scalar avg = r(table)[1,1]
    return scalar b = _b[COEF_VAR]
end

bootstrap b = r(b), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_derived.dta", replace): boot_derived

* --- Export bootstrap CIs via parmest ---
cap which parmest
if _rc != 0 {
    ssc install parmest, replace
}
parmest, saving("data/temp/boot_parmest.dta", replace) ///
    label eform stars(0.10 0.05 0.01)

* --- BCa vs Percentile comparison ---
* NOTE: BCa requires explicit saving with bca option in the bootstrap command.
* Default to percentile + bc only (Issue #11).
cap noisily estat bootstrap, percentile bc

di "============================================="
di "BOOTSTRAP CI COMPARISON"
di "============================================="
di "  Percentile CI:      [reported above]"
di "  Bias-corrected CI:  [reported above]"
di "  BCa CI:             [reported above]"
di "  If CIs differ substantially, the bootstrap"
di "  distribution is skewed — prefer BCa."
di "============================================="

log close
```

## Step 6: Python Cross-Validation

```python
"""
Bootstrap Cross-Validation: Stata vs Python (scipy, pyfixest)
"""
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_stata("DATASET_PATH")

# --- Pairs bootstrap (manual implementation) ---
np.random.seed(12345)
n_reps = 999
clusters = df["CLUSTER_VAR"].unique()
boot_coefs = []

for i in range(n_reps):
    # Resample clusters with replacement
    boot_clusters = np.random.choice(clusters, size=len(clusters), replace=True)
    boot_df = pd.concat([df[df["CLUSTER_VAR"] == c].assign(**{"_boot_cl": j})
                         for j, c in enumerate(boot_clusters)])
    try:
        import pyfixest as pf
        model = pf.feols("OUTCOME_VAR ~ COEF_VAR + CONTROLS | FIXED_EFFECTS",
                         data=boot_df, vcov={"CRV1": "_boot_cl"})
        boot_coefs.append(model.coef()["COEF_VAR"])
    except Exception:
        pass

boot_coefs = np.array(boot_coefs)

# --- Bootstrap statistics ---
b_mean = np.mean(boot_coefs)
b_se = np.std(boot_coefs, ddof=1)
b_ci_pct = np.percentile(boot_coefs, [2.5, 97.5])

print("=== Python Pairs Cluster Bootstrap ===")
print(f"  Mean:          {b_mean:.6f}")
print(f"  SE:            {b_se:.6f}")
print(f"  95% CI (pct):  [{b_ci_pct[0]:.6f}, {b_ci_pct[1]:.6f}]")

# --- Cross-validate with Stata ---
stata_boot_se = STATA_BOOT_SE  # from Step 1 log
pct_diff = abs(b_se - stata_boot_se) / abs(stata_boot_se) * 100
print(f"\nCross-validation (bootstrap SE):")
print(f"  Stata:  {stata_boot_se:.6f}")
print(f"  Python: {b_se:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 5 else 'CHECK'}")
# Note: bootstrap SE comparison uses 5% threshold (not 0.1%)
# because bootstrap SEs have inherent simulation variance

# --- Coverage check ---
# If true coefficient known (e.g., simulation), compute coverage rate
# coverage = np.mean((boot_ci_lo <= true_b) & (true_b <= boot_ci_hi))
```

## Step 7: Diagnostics Summary

After all steps, provide:

1. **Analytical vs Bootstrap**: Compare analytical SE, pairs bootstrap SE, and wild cluster bootstrap p-value. Flag if they diverge substantially.
2. **CI Method Comparison**: Percentile, bias-corrected, and BCa CIs. If BCa differs from percentile, the bootstrap distribution is skewed.
3. **Weight Sensitivity** (wild cluster): Do Rademacher, Mammen, and Webb weights give similar p-values? Divergence suggests sensitivity to few clusters.
4. **Replication Count**: Report effective number of replications (some may fail for bootstrap with complex estimators).
5. **Treatment Effects**: If Step 4 was run, compare RA, IPW, and AIPW ATET estimates. Convergence suggests robustness; divergence suggests model sensitivity.
6. **Cross-Validation**: Python vs Stata bootstrap SE comparison (target: < 5% difference given simulation variance).

## Required Stata Packages

```stata
ssc install boottest, replace    // Wild cluster bootstrap (Roodman)
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install parmest, replace     // Export bootstrap CIs
ssc install coefplot, replace
```

## Key References

- Cameron, A.C., Gelbach, J.B. & Miller, D.L. (2008). "Bootstrap-Based Improvements for Inference with Clustered Errors." REStat.
- Roodman, D., Nielsen, M.O., MacKinnon, J.G. & Webb, M.D. (2019). "Fast and Wild: Bootstrap Inference in Stata Using boottest." Stata Journal.
- Acemoglu, D., Naidu, S., Restrepo, P. & Robinson, J.A. (2019). "Democracy Does Cause Growth." JPE, 127(1), 47-100.
