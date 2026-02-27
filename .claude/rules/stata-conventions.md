---
paths:
  - "**/*.do"
---

# Stata Code Conventions

These conventions apply to ALL Stata .do files in this project.

## Header Template

Every .do file MUST start with this header block:

```stata
/*==============================================================================
Project:    [Project Name]
Version:    [vN]
Script:     [filename.do]
Purpose:    [Brief description]
Author:     [Name]
Created:    [Date]
Modified:   [Date]
Input:      [Input files]
Output:     [Output files]
==============================================================================*/
```

## Standard Settings

Every .do file must include these settings immediately after the header:

```stata
version 18
clear all
set more off
set maxvar 32767
set matsize 11000
set seed 12345
```

## Logging

Every .do file must:
1. Close any existing log first (with `cap log close` to avoid error if no log open)
2. Start a new log
3. End with `log close`

```stata
cap log close
log using "output/logs/XX_script_name.log", replace
* ... all code ...
log close
```

## Cluster Standard Errors

Always use `vce(cluster var)` as the default for ALL regressions. Never report non-clustered standard errors unless explicitly justified.

```stata
reghdfe y x1 x2, absorb(fe) vce(cluster firmid)
```

## Fixed Effects

Use `reghdfe` for multi-way fixed effects, with `absorb()` syntax:

```stata
reghdfe y x1 x2, absorb(firmid year) vce(cluster firmid)
```

For single-dimension FE, `reghdfe` is still preferred for consistency.

## Table Output

Use `esttab`/`estout` for LaTeX table generation. Store estimates with `estimates store`:

```stata
eststo clear
reghdfe y x1 x2, absorb(fe) vce(cluster firmid)
estimates store m1
reghdfe y x1 x2 x3, absorb(fe) vce(cluster firmid)
estimates store m2
esttab m1 m2 using "output/tables/results.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace
```

Note: Use 4 decimal places for coefficients (TOP5 standard for causal inference).

## Variable Labels

All variables MUST have labels. Apply `label variable` immediately after `gen` or `rename`:

```stata
gen log_wage = ln(wage)
label variable log_wage "Log of hourly wage"
```

## Data Safety

- NEVER write to `data/raw/` -- raw data is read-only.
- All modifications go to `data/clean/` or `data/temp/`.
- Save cleaned datasets with descriptive names and version suffixes if needed.

```stata
* CORRECT
save "data/clean/panel_cleaned.dta", replace

* WRONG -- never do this
save "data/raw/original_data.dta", replace
```

## Path Convention

Use relative paths from the project root. Define globals for base paths at the top of each .do file or in a master .do file:

```stata
global root    "."
global data    "$root/data"
global raw     "$data/raw"
global clean   "$data/clean"
global temp    "$data/temp"
global output  "$root/output"
global tables  "$output/tables"
global figures "$output/figures"
global logs    "$output/logs"
```

## Reproducibility

Set `set seed 12345` before ANY randomization, bootstrapping, or simulation:

```stata
set seed 12345
bootstrap, reps(1000) cluster(firmid): reg y x1 x2
```

Always save intermediate datasets so that each script can be run independently.

## Defensive Programming

Use `isid` and `assert` to validate data integrity:

```stata
* Verify unique identifier
isid panel_id year

* Verify expected values
assert treatment >= 0 & treatment <= 1
assert !missing(outcome, treatment, running_var)

* Verify panel structure
xtset panel_id year
assert r(balanced) == "strongly balanced"
```

### Community Package Guards (from Issues #1-#25)

All SSC/community commands must be wrapped in `cap noisily` because:
- They may be uninstalled, renamed, or have version-breaking API changes
- Their `e()` scalars may differ across versions
- Some are removed from SSC entirely (e.g., `xtserial` — Issue #6-7)

```stata
* CORRECT: defensive install + defensive call
cap ssc install xtserial, replace        // cap: may fail if removed from SSC
cap noisily xtserial y x1 x2            // cap noisily: fail gracefully
if _rc != 0 {
    di "xtserial unavailable. Skipping."
}

* WRONG: bare call that halts the script on error
ssc install xtserial, replace
xtserial y x1 x2
```

**Commands that MUST always be wrapped in `cap noisily`:**

| Command | Package | Risk |
|---------|---------|------|
| `csdid` / `csdid_stats` | csdid | Version-sensitive syntax (Issue #20) |
| `bacondecomp` | bacondecomp | Dependency issues (Issue #2) |
| `did_multiplegt` | did_multiplegt | Version-sensitive |
| `did_imputation` | did_imputation | Version-sensitive |
| `eventstudyinteract` | eventstudyinteract | Version-sensitive |
| `sdid` | sdid | jackknife fails on staggered treatment (Issue #25) |
| `boottest` | boottest | Fails after non-reghdfe estimators (Issue #1, #12) |
| `xtserial` | xtserial | Removed from SSC (Issue #6-7) |
| `xtcsd` | xtcsd | May be unavailable (Issue #8) |
| `xttest3` | xttest3 | May be unavailable (Issue #8) |
| `teffects` (all) | built-in | Fails on panel data with repeated obs (Issue #15) |
| `lasso logit` | built-in | Convergence failure with near-separation (Issue #18) |
| `weakiv` | weakiv | May not be installed |
| `rddensity` | rddensity | p-value scalar varies by version (Issue #3) |

### String Panel ID Check

Before `xtset`, always check if the panel ID variable is string. `xtset` requires numeric IDs:

```stata
* Check if unit variable is string and encode if needed (Issue #19)
cap confirm string variable UNIT_VAR
if _rc == 0 {
    encode UNIT_VAR, gen(_unit_num)
    local UNIT_VAR _unit_num
}
xtset `UNIT_VAR' TIME_VAR
```

### e-class Result Availability

Always check if e-class scalars exist before using them. Some commands leave certain scalars missing:

```stata
* CORRECT: check before use (Issue #14 — DWH may be missing with xtivreg2)
if e(estatp) != . {
    di "DWH p-value: " e(estatp)
}
else {
    di "DWH p-value unavailable for this estimator."
}

* WRONG: assume scalar exists
di "DWH p-value: " e(estatp)   // crashes if missing
```

### Results Storage Pattern for Non-Standard Estimators

For commands whose `e()` results are not compatible with `estimates store` (e.g., `sdid`), store results in local macros and build tables manually:

```stata
* CORRECT: local macros + file write (Issue #24)
cap noisily sdid Y unit time treat, vce(bootstrap) method(sdid) seed(12345)
if _rc == 0 {
    local att = e(ATT)
    local se  = e(se)
}
* Then build LaTeX table via file write using locals

* WRONG: ereturn post + estimates store after sdid
ereturn post b V       // clears e-class, fails with r(301)
estimates store m1      // not reached
```

### Continuous vs Categorical Variable Inspection

Use `summarize` for continuous variables and `tab` only for low-cardinality categoricals:

```stata
* CORRECT
summarize wage, detail      // continuous variable
tab industry, missing       // categorical with few levels

* WRONG: tab on continuous variable (Issue #5)
tab wage                    // generates 1 row per unique value, huge output
```

### Negative Hausman Chi-Squared

The Hausman test can produce negative chi2 when FE strongly dominates RE. This is known behavior, not an error:

```stata
hausman fe_model re_model
if r(chi2) < 0 {
    di "Negative chi2: FE strongly dominates RE (Issue #9)."
    di "Interpretation: V_FE - V_RE is not positive semi-definite. Choose FE."
}
```

### Old Stata Syntax Handling

Published replication packages may contain deprecated commands (Issue #23):

| Old Command | Action | Modern Equivalent |
|-------------|--------|-------------------|
| `set mem 250m` | Omit entirely | Stata 18 memory is dynamic |
| `set memory 500m` | Omit entirely | Stata 18 memory is dynamic |
| `clear matrix` | Replace | `matrix drop _all` or `clear all` |
| `set matsize 800` | Omit (default 11000) | Only set if explicitly needed |

When adapting old replication code, omit deprecated commands. Do not include them in new `.do` files.

## Memory Management

Use `compress` before saving large datasets:

```stata
compress
save "data/clean/panel_cleaned.dta", replace
```

## Required Packages

List all required packages in a comment block at the top of each .do file or in master.do:

```stata
* Required packages:
*   ssc install reghdfe
*   ssc install ftools
*   ssc install estout
*   ssc install coefplot
```

## Master.do Pattern

Organize projects with a master.do file that:
1. Sets all globals
2. Creates output directories
3. Runs all analysis scripts in order
4. Verifies outputs

See `init-project.md` for the full master.do template.
