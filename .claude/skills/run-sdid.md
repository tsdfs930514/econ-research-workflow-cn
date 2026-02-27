---
description: "Run Synthetic Difference-in-Differences (SDID) analysis pipeline"
user_invocable: true
---

# /run-sdid — Synthetic Difference-in-Differences Pipeline

When the user invokes `/run-sdid`, execute a Synthetic DID analysis following Arkhangelsky et al. (2021, AER). SDID combines Synthetic Control unit weights with DiD time weights to produce estimates that are generally more robust than either method alone.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## When to Use SDID vs Other DID Methods

- **SDID preferred when**: Few treated units, many control units, staggered adoption can be handled via cohort-specific SDID, concern about parallel trends
- **CS-DiD preferred when**: Many treated/control groups, staggered adoption is the main design challenge, doubly-robust estimation wanted
- **TWFE preferred when**: Uniform treatment timing, homogeneous treatment effects confirmed

## Step 0: Gather Inputs

Ask the user for:

- **Dataset**: path to .dta file (must be a balanced panel)
- **Outcome variable**: dependent variable Y
- **Unit variable**: entity identifier (state, firm, etc.)
- **Time variable**: period/year identifier
- **Treatment variable**: binary indicator (0 before treatment for all; 1 after treatment for treated only)
- **First treatment period** (for staggered): earliest treatment year if staggered adoption
- **Cluster variable**: for standard error clustering (default: unit variable)

**IMPORTANT**: Always use the exact variable names provided by the user. Never hardcode variable names like `lgdp`, `gdp`, etc. — verify variables exist in the dataset with `ds` or `desc` before using them (Issue #21).

## Step 1: Data Preparation (Stata .do file)

```stata
/*==============================================================================
  SDID Analysis — Step 1: Data Preparation
  Reference: Arkhangelsky, Athey, Hirshberg, Imbens & Wager (AER 2021)
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/sdid_01_prep.log", replace

use "DATASET_PATH", clear

* --- Verify balanced panel ---
xtset UNIT_VAR TIME_VAR
xtdescribe
* SDID requires a balanced panel. Drop units with missing periods if needed.

* --- Identify treatment groups ---
tab TREAT_VAR
bysort UNIT_VAR: egen ever_treated = max(TREAT_VAR)
tab ever_treated

* Pre-treatment periods for weight estimation
sum TIME_VAR if TREAT_VAR == 0 & ever_treated == 1
local T0 = r(max)  // last pre-treatment period
di "Last pre-treatment period: `T0'"

* Summary statistics
estpost tabstat OUTCOME_VAR, by(ever_treated) stat(mean sd n) columns(statistics)

log close
```

## Step 2: SDID Estimation (Stata .do file)

```stata
/*==============================================================================
  SDID Analysis — Step 2: Main Estimation
  Packages required: sdid (Clarke et al. 2023)
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/sdid_02_estimation.log", replace

use "DATASET_PATH", clear

* --- Synthetic DiD ---
* NOTE: jackknife VCE requires >= 2 treated units per treatment period.
* For staggered treatment with singleton periods, it fails with r(451).
* Use bootstrap VCE as fallback (Issue #25).
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(jackknife) method(sdid) graph ///
    g1_opt(xtitle("") ytitle("Unit Weights")) ///
    g2_opt(xtitle("Time") ytitle("Outcome"))
if _rc != 0 {
    di "Jackknife VCE failed. Trying bootstrap VCE..."
    sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
        vce(bootstrap) method(sdid) seed(12345) reps(200)
}
graph export "output/figures/fig_sdid_main.pdf", replace

* Store results as local macros (NOT via ereturn post + estimates store,
* which clears e-class results and fails with r(301) — Issue #24)
local sdid_att = e(ATT)
local sdid_se  = e(se)

* --- Comparison: Traditional DiD ---
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(jackknife) method(did)
if _rc != 0 {
    sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
        vce(bootstrap) method(did) seed(12345) reps(200)
}
local did_att = e(ATT)
local did_se  = e(se)

* --- Comparison: Synthetic Control ---
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(jackknife) method(sc)
if _rc != 0 {
    sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
        vce(bootstrap) method(sc) seed(12345) reps(200)
}
local sc_att = e(ATT)
local sc_se  = e(se)

* --- SDID diagnostic comparison ---
* SDID estimate should fall between SC and DiD bounds
* If DiD and SC agree → high confidence in treatment effect
* If they disagree → SDID provides a compromise

di "============================================="
di "SDID COMPARISON"
di "============================================="
di "  SDID:  ATT = `sdid_att' (SE = `sdid_se')"
di "  DiD:   ATT = `did_att' (SE = `did_se')"
di "  SC:    ATT = `sc_att' (SE = `sc_se')"
di "============================================="

* --- Manual comparison table (since estimates store is unreliable with sdid) ---
* Use file write for a clean LaTeX table
file open _tab using "output/tables/tab_sdid_comparison.tex", write replace
file write _tab "\begin{table}[htbp]" _n
file write _tab "\centering" _n
file write _tab "\caption{Treatment Effect: SDID vs DiD vs SC}" _n
file write _tab "\begin{tabular}{lccc}" _n
file write _tab "\hline\hline" _n
file write _tab " & SDID & DiD & SC \\\\" _n
file write _tab "\hline" _n
file write _tab "ATT & " %9.4f (`sdid_att') " & " %9.4f (`did_att') " & " %9.4f (`sc_att') " \\\\" _n
file write _tab "SE  & (" %9.4f (`sdid_se') ") & (" %9.4f (`did_se') ") & (" %9.4f (`sc_se') ") \\\\" _n
file write _tab "\hline\hline" _n
file write _tab "\multicolumn{4}{p{12cm}}{\small\textit{Note:} " _n
file write _tab "SDID = Arkhangelsky et al. (2021). Bootstrap SEs.} \\\\" _n
file write _tab "\end{tabular}" _n
file write _tab "\end{table}" _n
file close _tab

log close
```

## Step 3: Robustness (Stata .do file)

```stata
/*==============================================================================
  SDID Analysis — Step 3: Robustness Checks
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/sdid_03_robustness.log", replace

use "DATASET_PATH", clear

* --- Alternative VCE: Bootstrap ---
sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(bootstrap) reps(200) method(sdid) seed(12345)
local sdid_boot_att = e(ATT)
local sdid_boot_se  = e(se)

* --- Placebo: Randomize treatment assignment ---
* Permutation inference: shuffle treated/control labels
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(placebo) reps(200) method(sdid)
if _rc == 0 {
    local sdid_plac_att = e(ATT)
    local sdid_plac_se  = e(se)
}

* --- Leave-one-unit-out ---
* Check sensitivity to individual units
* Use bootstrap VCE for LOSO (jackknife may fail, Issue #25)
levelsof UNIT_VAR if ever_treated == 0, local(controls)
foreach u of local controls {
    cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR if UNIT_VAR != `u', ///
        vce(bootstrap) method(sdid) seed(12345) reps(50)
    if _rc == 0 {
        di "LOSO (drop unit `u'): ATT = " e(ATT) " (SE: " e(se) ")"
    }
}

* --- Alternative outcome ---
cap noisily sdid ALT_OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(bootstrap) method(sdid) seed(12345) reps(200)
if _rc == 0 {
    local sdid_alt_att = e(ATT)
    local sdid_alt_se  = e(se)
}

log close
```

## Step 4: Python Cross-Validation

```python
"""
SDID Cross-Validation using synthdid Python package or manual implementation
"""
import pandas as pd
import numpy as np

df = pd.read_stata("DATASET_PATH")

# Option 1: Use synthdid Python package (if available)
try:
    from synthdid.model import SynthDID
    model = SynthDID(df, unit="UNIT_VAR", time="TIME_VAR",
                     outcome="OUTCOME_VAR", treatment="TREAT_VAR")
    model.fit()
    print(f"Python SDID estimate: {model.att:.6f}")
    print(f"Python SDID SE (jackknife): {model.se:.6f}")
except ImportError:
    print("synthdid not available. Using pyfixest for TWFE comparison.")
    import pyfixest as pf
    model = pf.feols("OUTCOME_VAR ~ TREAT_VAR | UNIT_VAR + TIME_VAR",
                     data=df, vcov={"CRV1": "UNIT_VAR"})
    print(model.summary())

# Cross-validate with Stata
stata_sdid = STATA_SDID_COEF
python_coef = model.att if hasattr(model, 'att') else model.coef()["TREAT_VAR"]
pct_diff = abs(stata_sdid - python_coef) / abs(stata_sdid) * 100
print(f"\nCross-validation (SDID):")
print(f"  Stata:  {stata_sdid:.6f}")
print(f"  Python: {python_coef:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
```

## Step 5: Diagnostics Summary

After all steps, provide:

1. **SDID vs DiD vs SC**: Does SDID fall between DiD and SC? If all three agree, high confidence. If DiD and SC disagree substantially, discuss which identifying assumption is more plausible.
2. **Unit Weights**: Are weights concentrated on a few control units or diffuse? Concentrated weights may indicate fragility.
3. **Time Weights**: Do time weights emphasize pre-treatment periods close to treatment onset? This is expected.
4. **Inference**: Report jackknife SE, bootstrap SE, and placebo p-value. Note if they disagree.
5. **LOSO Sensitivity**: Do results change when individual control units are dropped?
6. **Recommendation**: SDID is preferred when SC weights produce a good pre-treatment fit and DiD parallel trends are questionable. If pre-treatment fit is poor for SC and parallel trends are plausible, DiD may be preferred.

## Required Stata Packages

```stata
ssc install sdid
ssc install reghdfe
ssc install ftools
```

## Key References

- Arkhangelsky, D., Athey, S., Hirshberg, D., Imbens, G. & Wager, S. (2021). "Synthetic Difference-in-Differences." AER, 111(12), 4088-4118.
- Clarke, D., Pailañir, D., Athey, S. & Imbens, G. (2023). "Synthetic Difference-in-Differences Estimation." Stata Journal.
