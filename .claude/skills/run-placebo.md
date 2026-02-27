---
description: "Run placebo tests & randomization inference pipeline (timing, outcome, instrument, permutation)"
user_invocable: true
---

# /run-placebo — Placebo & Randomization Inference Pipeline

When the user invokes `/run-placebo`, execute a comprehensive placebo and randomization inference pipeline covering placebo treatment timing, placebo outcomes, placebo instruments (exclusion restriction validation), Fisher exact permutation tests, geographic/unit placebos, and Python cross-validation.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## When to Use Placebo Tests

- **Always**: Placebo tests are standard practice in applied micro. Reviewers expect them.
- **DID/Event Study**: Placebo treatment timing tests parallel trends more rigorously than visual inspection
- **IV**: Placebo instruments validate the exclusion restriction (expect null reduced form)
- **RDD**: Placebo cutoffs test for discontinuities at non-treatment thresholds
- **Any causal design**: Permutation/randomization inference provides non-parametric p-values robust to distributional assumptions

## Step 0: Gather Inputs

Ask the user for:

- **Dataset**: path to .dta file
- **Baseline regression command**: the main specification to test
- **Coefficient of interest**: treatment or key variable
- **Method type**: DID, IV, RDD, Panel, or OLS (determines which placebo types apply)
- **Cluster variable**: for clustering and permutation structure
- **Group variable** (if panel): unit identifier
- **Time variable** (if panel/DID): period identifier
- **Treatment timing** (if DID): first treatment period for treated units
- **Placebo outcome variables** (optional): outcome variables that should NOT be affected by treatment
- **Placebo instrument variables** (optional): instruments constructed from unrelated shocks (for IV exclusion restriction test)
- **Number of permutation replications**: 500 for exploration, 1000+ for publication (default: 1000)

## Step 1: Placebo Treatment Timing (Stata .do file)

Shift treatment to pre-treatment periods where no effect should exist. A significant "effect" suggests pre-trends or model misspecification.

```stata
/*==============================================================================
  Placebo Analysis — Step 1: Placebo Treatment Timing
  Shift treatment to false dates in the pre-period. Expect NULL effects.
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_01_timing.log", replace

use "DATASET_PATH", clear

* --- Baseline (actual treatment) for reference ---
eststo clear
eststo actual: BASELINE_COMMAND
local b_actual = _b[COEF_VAR]
local se_actual = _se[COEF_VAR]

* --- Placebo timing: shift treatment N periods earlier ---
* Restrict sample to pre-treatment period only
preserve
keep if TIME_VAR < FIRST_TREAT_PERIOD

* Create false treatment indicators at various pre-period dates
local placebo_dates "DATE1 DATE2 DATE3"  // e.g., 3, 5, 7 periods before actual
foreach t of local placebo_dates {
    gen placebo_treat_`t' = (GROUP_IS_TREATED) * (TIME_VAR >= `t')
    eststo placebo_t`t': reghdfe OUTCOME_VAR placebo_treat_`t' CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    local b_p`t' = _b[placebo_treat_`t']
    local p_p`t' = 2 * ttail(e(df_r), abs(_b[placebo_treat_`t'] / _se[placebo_treat_`t']))
    di "Placebo (t=`t'): b = `b_p`t'', p = `p_p`t''"
    drop placebo_treat_`t'
}
restore

* --- Placebo timing table ---
esttab actual placebo_* using "output/tables/tab_placebo_timing.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    title("Placebo Treatment Timing Tests") ///
    note("Column (1) = actual treatment. Remaining columns = false treatment dates." ///
         "Placebo samples restricted to pre-treatment period." ///
         "Significant placebo effects suggest pre-trend violations.")

log close
```

## Step 2: Placebo Outcome (Stata .do file)

Run the baseline model on outcomes that should NOT be affected by the treatment.

```stata
/*==============================================================================
  Placebo Analysis — Step 2: Placebo Outcomes
  Run model on outcomes unaffected by treatment. Expect NULL effects.
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_02_outcome.log", replace

use "DATASET_PATH", clear

* --- Actual outcome (baseline) ---
eststo clear
eststo actual: BASELINE_COMMAND

* --- Placebo outcomes ---
* These should be variables not causally affected by the treatment
foreach pvar in PLACEBO_OUTCOME1 PLACEBO_OUTCOME2 PLACEBO_OUTCOME3 {
    eststo placebo_`pvar': reghdfe `pvar' TREATMENT_VAR CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    local b_p = _b[TREATMENT_VAR]
    local p_p = 2 * ttail(e(df_r), abs(_b[TREATMENT_VAR] / _se[TREATMENT_VAR]))
    di "Placebo outcome `pvar': b = `b_p', p = `p_p'"
}

* --- Table ---
esttab actual placebo_* using "output/tables/tab_placebo_outcomes.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    title("Placebo Outcome Tests") ///
    note("Column (1) = actual outcome. Remaining columns = placebo outcomes." ///
         "Significant effects on placebo outcomes suggest confounding.")

log close
```

## Step 3: Placebo Instrument / Exclusion Restriction Test (Stata .do file)

Construct instruments from unrelated shocks and test the reduced form. A significant reduced form with placebo instruments undermines the exclusion restriction. Pattern from APE 0185 (Social Networks & Minimum Wage).

```stata
/*==============================================================================
  Placebo Analysis — Step 3: Placebo Instruments
  Reference: APE 0185 — 04c_placebo_shocks.R pattern
  Construct instruments from unrelated shocks; expect NULL reduced form.
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_03_instrument.log", replace

use "DATASET_PATH", clear

* --- Actual reduced form (instrument -> outcome) ---
eststo clear
eststo actual_rf: reghdfe OUTCOME_VAR ACTUAL_INSTRUMENT CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- Placebo instruments ---
* Option A: Use instruments from unrelated sectors/geographies
* Option B: Randomly reassign instrument values across units
* Option C: Use lagged instruments from periods before instrument should matter

* Placebo instrument 1: unrelated sector shocks
eststo placebo_rf1: reghdfe OUTCOME_VAR PLACEBO_INSTRUMENT1 CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* Placebo instrument 2: randomly permuted instrument
preserve
    bsample, cluster(CLUSTER_VAR)
    rename ACTUAL_INSTRUMENT placebo_perm_iv
    tempfile perm
    keep UNIT_VAR TIME_VAR placebo_perm_iv
    save `perm', replace
restore
merge 1:1 UNIT_VAR TIME_VAR using `perm', nogenerate

eststo placebo_rf2: reghdfe OUTCOME_VAR placebo_perm_iv CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- Table ---
esttab actual_rf placebo_rf* using "output/tables/tab_placebo_instruments.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    title("Placebo Instrument Tests (Reduced Form)") ///
    note("Column (1) = actual instrument reduced form." ///
         "Remaining columns = placebo instruments. Expect NULL effects." ///
         "Significant placebo RF undermines the exclusion restriction.")

log close
```

## Step 4: Permutation / Randomization Inference (Stata .do file)

Fisher exact test: shuffle treatment labels, re-estimate the model N times, compute the p-value as the rank of the actual coefficient in the null distribution.

```stata
/*==============================================================================
  Placebo Analysis — Step 4: Permutation / Randomization Inference
  Fisher exact test: shuffle treatment, compute null distribution
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_04_permutation.log", replace

use "DATASET_PATH", clear

* --- Actual estimate ---
BASELINE_COMMAND
local b_actual = _b[COEF_VAR]
di "Actual coefficient: `b_actual'"

* --- Define permutation program ---
cap program drop permute_test
program define permute_test, rclass
    * Permute treatment labels across clusters (not within)
    tempvar rand
    gen `rand' = runiform()
    * Sort clusters randomly, then reassign treatment status
    bysort CLUSTER_VAR (`rand'): gen byte _treat_perm = TREATMENT_VAR[1]
    * Alternative: pure random shuffle at unit level
    * sort `rand'
    * gen _treat_perm = TREATMENT_VAR[_n]

    reghdfe OUTCOME_VAR _treat_perm CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    return scalar b = _b[_treat_perm]
    drop _treat_perm
end

* --- Run permutation test ---
simulate b_perm = r(b), reps(NREPS) seed(12345) nodots: permute_test

* --- Compute p-value ---
count if abs(b_perm) >= abs(`b_actual')
local perm_p = r(N) / NREPS
di "============================================="
di "PERMUTATION INFERENCE"
di "============================================="
di "  Actual coefficient:   `b_actual'"
di "  Permutation p-value:  `perm_p'"
di "  (fraction of |permuted b| >= |actual b|)"
di "============================================="

* --- Permutation distribution plot ---
hist b_perm, bin(50) ///
    title("Randomization Inference: Null Distribution") ///
    xtitle("Permuted Coefficient") ytitle("Density") ///
    xline(`b_actual', lcolor(cranberry) lpattern(dash) lwidth(medthick)) ///
    note("Vertical line = actual estimate. p = `perm_p'. N perms = NREPS")
graph export "output/figures/fig_permutation_dist.pdf", replace

log close
```

## Step 5: Geographic / Unit Placebo (Stata .do file)

Assign treatment to untreated units (or regions) and re-estimate.

```stata
/*==============================================================================
  Placebo Analysis — Step 5: Geographic / Unit Placebo
  Assign treatment to untreated units. Expect NULL effects.
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_05_geographic.log", replace

use "DATASET_PATH", clear

* --- Identify treatment/control groups ---
bysort GROUP_VAR: egen ever_treated = max(TREATMENT_VAR)

* --- Approach 1: Randomly assign treatment among control units only ---
preserve
keep if ever_treated == 0

* Randomly assign "placebo treatment" to half of control units
bysort GROUP_VAR: gen _tag = (_n == 1)
gen _rand = runiform() if _tag == 1
bysort GROUP_VAR: replace _rand = _rand[1]
egen _med = median(_rand) if _tag == 1
gen placebo_treat = (TREATMENT_VAR == 0) & (_rand >= _med) & (TIME_VAR >= FIRST_TREAT_PERIOD)

eststo geo_placebo: reghdfe OUTCOME_VAR placebo_treat CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
di "Geographic placebo: b = " _b[placebo_treat] ", p = " ///
    2 * ttail(e(df_r), abs(_b[placebo_treat] / _se[placebo_treat]))
restore

* --- Approach 2: Leave-one-group-out (LOGO) sensitivity ---
levelsof GROUP_VAR if ever_treated == 1, local(treated_units)
foreach u of local treated_units {
    cap BASELINE_COMMAND_IF GROUP_VAR != `u'
    if _rc == 0 {
        di "LOGO (drop `u'): b = " _b[COEF_VAR] " (SE = " _se[COEF_VAR] ")"
    }
}

log close
```

## Step 6: Python Cross-Validation

```python
"""
Placebo & Permutation Cross-Validation: Stata vs Python
"""
import pandas as pd
import numpy as np
import pyfixest as pf

df = pd.read_stata("DATASET_PATH")

# --- Permutation inference in Python ---
np.random.seed(12345)
n_perms = 1000

# Actual estimate
model = pf.feols("OUTCOME_VAR ~ TREATMENT_VAR + CONTROLS | FIXED_EFFECTS",
                 data=df, vcov={"CRV1": "CLUSTER_VAR"})
b_actual = model.coef()["TREATMENT_VAR"]
print(f"Actual coefficient: {b_actual:.6f}")

# Permute treatment across clusters
clusters = df["CLUSTER_VAR"].unique()
perm_coefs = []
for i in range(n_perms):
    df_perm = df.copy()
    # Shuffle treatment at cluster level
    perm_map = dict(zip(clusters, np.random.permutation(clusters)))
    df_perm["_perm_cl"] = df_perm["CLUSTER_VAR"].map(perm_map)
    # Reassign treatment based on permuted clusters
    treat_map = df.groupby("CLUSTER_VAR")["TREATMENT_VAR"].first().to_dict()
    df_perm["_treat_perm"] = df_perm["_perm_cl"].map(treat_map)
    try:
        m = pf.feols("OUTCOME_VAR ~ _treat_perm + CONTROLS | FIXED_EFFECTS",
                     data=df_perm, vcov={"CRV1": "CLUSTER_VAR"})
        perm_coefs.append(m.coef()["_treat_perm"])
    except Exception:
        pass

perm_coefs = np.array(perm_coefs)
perm_p = np.mean(np.abs(perm_coefs) >= abs(b_actual))

print(f"\n=== Python Permutation Inference ===")
print(f"  Permutation p-value: {perm_p:.4f}")
print(f"  Null distribution mean: {np.mean(perm_coefs):.6f}")
print(f"  Null distribution SD:   {np.std(perm_coefs):.6f}")

# --- Cross-validate with Stata ---
stata_perm_p = STATA_PERM_P  # from Step 4 log
print(f"\nCross-validation (permutation p):")
print(f"  Stata:  {stata_perm_p:.4f}")
print(f"  Python: {perm_p:.4f}")
print(f"  Status: {'PASS' if abs(stata_perm_p - perm_p) < 0.05 else 'CHECK'}")
# Note: permutation p-values may differ slightly due to simulation variance

# --- Visualization ---
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(perm_coefs, bins=50, density=True, alpha=0.7, color="steelblue",
        edgecolor="white", label="Null distribution")
ax.axvline(b_actual, color="crimson", linestyle="--", linewidth=2,
           label=f"Actual = {b_actual:.4f}")
ax.set_xlabel("Coefficient")
ax.set_ylabel("Density")
ax.set_title(f"Randomization Inference (p = {perm_p:.3f})")
ax.legend()
fig.savefig("output/figures/fig_permutation_python.pdf", bbox_inches="tight")
plt.close()
```

## Step 7: Diagnostics Summary

After all steps, provide:

1. **Placebo Timing**: Are all pre-period placebo treatment coefficients insignificant? Any significant result flags a pre-trend concern. **Important**: A significant timing placebo does NOT necessarily invalidate the design — it may reflect **anticipation effects** (agents respond before the formal policy change). Distinguish between anticipation (expected for policies with lead-up periods like democratization) and confounding (Issue #22).
2. **Placebo Outcomes**: Are effects on unrelated outcomes insignificant? Significant effects suggest confounding or data issues.
3. **Placebo Instruments** (IV only): Is the reduced form null for placebo instruments? A significant result undermines the exclusion restriction.
4. **Permutation p-value**: Report alongside the analytical p-value. Large discrepancy suggests distributional assumptions matter.
5. **Geographic Placebo**: Is the null effect confirmed when treatment is assigned to control units?
6. **LOGO Sensitivity**: Does any single treated unit drive the result?
7. **Cross-Validation**: Stata vs Python permutation p-value comparison.

Report in table format:

```
Placebo & Randomization Summary
================================
Test                    | Actual Coef | Placebo Coef | p-value | Pass?
Placebo timing (t-3)    |   X.XXX     |    X.XXX     |  X.XXX  | Yes/No
Placebo timing (t-5)    |   X.XXX     |    X.XXX     |  X.XXX  | Yes/No
Placebo outcome 1       |   X.XXX     |    X.XXX     |  X.XXX  | Yes/No
Permutation inference   |   X.XXX     |    ---        |  X.XXX  | ---
Geographic placebo      |   X.XXX     |    X.XXX     |  X.XXX  | Yes/No
```

## Required Stata Packages

```stata
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install coefplot, replace
```

## Key References

- Fisher, R.A. (1935). *The Design of Experiments*. (Randomization inference foundation)
- Bertrand, M., Duflo, E. & Mullainathan, S. (2004). "How Much Should We Trust Differences-in-Differences Estimates?" QJE.
- Abman, R., Lundberg, C. & Ruta, M. — APE 0185 placebo shock construction pattern.
