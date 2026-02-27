---
description: "Run logit/probit, propensity score, treatment effects (RA/IPW/AIPW), and conditional logit pipeline"
user_invocable: true
---

# /run-logit-probit — Logit/Probit & Discrete Choice Pipeline

When the user invokes `/run-logit-probit`, execute a complete discrete choice and treatment effects pipeline covering standard logit/probit estimation with marginal effects, propensity score estimation, treatment effects via RA/IPW/AIPW, conditional logit for discrete choice, diagnostics (overlap, ROC, Hosmer-Lemeshow), and Python cross-validation.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## When to Use This Pipeline

- **Binary outcome**: Y is 0/1 — use logit or probit
- **Propensity score matching/weighting**: Estimating P(Treatment=1|X) for causal inference
- **Treatment effects**: ATET via regression adjustment, IPW, or doubly robust (AIPW)
- **Discrete choice**: Consumer/firm choice among alternatives — use conditional logit (clogit)
- **Ordered outcome**: Likert scale, rating categories — use ologit/oprobit
- **Multinomial outcome**: Unordered categories (occupation, transport mode) — use mlogit

## Step 0: Gather Inputs

Ask the user for:

- **Dataset**: path to .dta file
- **Outcome type**: binary (0/1), ordered, multinomial, or conditional choice
- **Dependent variable**: outcome variable
- **Treatment variable** (if propensity score / treatment effects): binary treatment indicator
- **Covariates**: control variables for the model
- **Choice group variable** (if conditional logit): group identifier (e.g., household-year)
- **Alternative-specific variables** (if conditional logit): variables that vary across alternatives
- **Cluster variable**: for clustered standard errors
- **Fixed effects** (if applicable): for absorbed FE
- **Weight variable** (optional): sampling weights (e.g., `[pw=weight]`)
- **Purpose**: estimation only, propensity score for matching/weighting, or full treatment effects

## Step 1: Standard Logit/Probit Estimation (Stata .do file)

```stata
/*==============================================================================
  Logit/Probit Analysis — Step 1: Standard Estimation & Marginal Effects
  Reports AME (Average Marginal Effects) and MEM (Marginal Effects at Means)
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_01_estimation.log", replace

use "DATASET_PATH", clear

eststo clear

* --- Probit ---
eststo probit_main: probit OUTCOME_VAR TREATMENT_VAR COVARIATES, ///
    vce(cluster CLUSTER_VAR)

* Average Marginal Effects (AME) — preferred for most applications
margins, dydx(*) post
eststo probit_ame
* AME: average of individual marginal effects across all observations

* Re-run probit for MEM
probit OUTCOME_VAR TREATMENT_VAR COVARIATES, vce(cluster CLUSTER_VAR)
* Marginal Effects at Means (MEM) — effect evaluated at mean of all X
margins, dydx(*) atmeans post
eststo probit_mem

* --- Logit ---
eststo logit_main: logit OUTCOME_VAR TREATMENT_VAR COVARIATES, ///
    vce(cluster CLUSTER_VAR)

* AME for logit
margins, dydx(*) post
eststo logit_ame

* --- Comparison: LPM (Linear Probability Model) ---
eststo lpm: reghdfe OUTCOME_VAR TREATMENT_VAR COVARIATES, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- Table: Coefficients + AME ---
esttab probit_main logit_main probit_ame logit_ame lpm ///
    using "output/tables/tab_logit_probit.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    mtitles("Probit" "Logit" "Probit AME" "Logit AME" "LPM") ///
    title("Binary Outcome: Logit, Probit, and LPM") ///
    note("Columns (1)-(2): coefficient estimates." ///
         "Columns (3)-(4): average marginal effects." ///
         "Column (5): linear probability model with FE." ///
         "Standard errors clustered at CLUSTER_VAR level.")

* --- AME vs MEM comparison ---
di "============================================="
di "MARGINAL EFFECTS COMPARISON"
di "============================================="
di "  Probit AME (treatment): " _b[TREATMENT_VAR]  // from margins, dydx post
di "  Probit MEM (treatment): [from MEM estimation]"
di "  Logit AME (treatment):  [from logit margins]"
di "  LPM coefficient:        [from reghdfe]"
di "  If AME ≈ MEM ≈ LPM: effects are approximately linear"
di "  If they diverge: nonlinearity matters"
di "============================================="

log close
```

## Step 2: Propensity Score Estimation (Stata .do file)

Following Acemoglu et al. (2019, JPE) Table A11 pattern.

```stata
/*==============================================================================
  Logit/Probit Analysis — Step 2: Propensity Score Estimation
  Reference: DDCG Table A11 — probit for propensity score, predict _pscore
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_02_pscore.log", replace

use "DATASET_PATH", clear

* --- Propensity score via probit ---
probit TREATMENT_VAR COVARIATES i.YEAR_VAR, vce(cluster CLUSTER_VAR)

* Marginal effects (for reporting)
margins, dydx(COVARIATES) post
eststo pscore_margins

* Predicted propensity score
probit TREATMENT_VAR COVARIATES i.YEAR_VAR, vce(cluster CLUSTER_VAR)
predict _pscore, pr

* --- Propensity score diagnostics ---
* Summary by treatment status
tabstat _pscore, by(TREATMENT_VAR) stat(mean sd min p5 p25 p50 p75 p95 max n)

* --- Overlap / Common Support ---
* Kernel density plot (following DDCG Figure A5/A6)
twoway (kdensity _pscore if TREATMENT_VAR == 1, lcolor(cranberry) lwidth(medthick)) ///
       (kdensity _pscore if TREATMENT_VAR == 0, lcolor(navy) lwidth(medthick)), ///
    legend(order(1 "Treated" 2 "Control") rows(1)) ///
    title("Propensity Score Overlap") ///
    xtitle("Propensity Score") ytitle("Density") ///
    note("Adequate overlap requires substantial density overlap.")
graph export "output/figures/fig_pscore_overlap.pdf", replace

* --- Histogram version ---
twoway (hist _pscore if TREATMENT_VAR == 1, fcolor(cranberry%40) lcolor(cranberry) width(0.02)) ///
       (hist _pscore if TREATMENT_VAR == 0, fcolor(navy%40) lcolor(navy) width(0.02)), ///
    legend(order(1 "Treated" 2 "Control") rows(1)) ///
    title("Propensity Score Distribution") ///
    xtitle("Propensity Score") ytitle("Frequency")
graph export "output/figures/fig_pscore_hist.pdf", replace

* --- Trim to common support ---
sum _pscore if TREATMENT_VAR == 1, detail
local trim_lo = r(min)
sum _pscore if TREATMENT_VAR == 0, detail
local trim_hi = r(max)
gen byte common_support = (_pscore >= `trim_lo' & _pscore <= `trim_hi')
tab common_support TREATMENT_VAR

* --- Covariate balance after weighting ---
* IPW weights
gen _ipw = cond(TREATMENT_VAR == 1, 1/_pscore, 1/(1-_pscore))

foreach var of varlist COVARIATES {
    sum `var' [aw=_ipw] if TREATMENT_VAR == 1
    local mean_t = r(mean)
    sum `var' [aw=_ipw] if TREATMENT_VAR == 0
    local mean_c = r(mean)
    sum `var'
    local sd_pool = r(sd)
    local std_diff = (`mean_t' - `mean_c') / `sd_pool'
    di "Balance `var': std diff = `std_diff' (target: < 0.1)"
}

log close
```

## Step 3: Treatment Effects — RA, IPW, AIPW (Stata .do file)

Following Acemoglu et al. (2019, JPE) Table 5 pattern.

**IMPORTANT: `teffects` commands (ra, ipw, ipwra, nnmatch) only work with cross-sectional data.** They will fail on panel data with repeated observations per unit (r(459) or similar). For panel data, either: (1) collapse to a cross-section first (e.g., pre/post means), (2) use manual IPW weighting with `reghdfe`, or (3) use `bootstrap` wrapping a custom program that computes ATET on a cross-sectional snapshot. All `teffects` calls below should be wrapped in `cap noisily` when data structure is uncertain (Issue #15).

```stata
/*==============================================================================
  Logit/Probit Analysis — Step 3: Treatment Effects via teffects
  Reference: DDCG Table 5 — RA, IPW, AIPW with probit treatment model
  NOTE: teffects requires cross-sectional data (no repeated observations).
  For panel data, collapse to cross-section first or use manual IPW.
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_03_teffects.log", replace

use "DATASET_PATH", clear

eststo clear

* --- 1. Regression Adjustment (RA) ---
* Outcome model: OUTCOME ~ COVARIATES, separately for treated and control
* Wrap in cap noisily — fails on panel data with repeated obs (Issue #15)
cap noisily teffects ra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR), atet
if _rc == 0 {
    eststo tef_ra
    local atet_ra = _b[r1vs0.TREATMENT_VAR]
    di "RA-ATET: `atet_ra'"
}
else {
    di "teffects ra failed (likely panel data with repeated obs). Skipping."
}

* --- 2. Inverse Probability Weighting (IPW) with probit ---
* Treatment model: probit(TREATMENT ~ COVARIATES)
cap noisily teffects ipw (OUTCOME_VAR) (TREATMENT_VAR COVARIATES, probit), atet
if _rc == 0 {
    eststo tef_ipw
    local atet_ipw = _b[r1vs0.TREATMENT_VAR]
    di "IPW-ATET: `atet_ipw'"
}
else {
    di "teffects ipw failed (likely panel data). Skipping."
}

* --- 3. Doubly Robust: AIPW (Augmented IPW) ---
* Outcome model + treatment model — consistent if EITHER model is correct
cap noisily teffects ipwra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR COVARIATES, probit), atet
if _rc == 0 {
    eststo tef_aipw
    local atet_aipw = _b[r1vs0.TREATMENT_VAR]
    di "AIPW-ATET: `atet_aipw'"
}
else {
    di "teffects ipwra failed (likely panel data). Skipping."
}

* --- 4. Nearest Neighbor Matching ---
cap noisily teffects nnmatch (OUTCOME_VAR COVARIATES) (TREATMENT_VAR), ///
    atet nneighbor(5) metric(mahalanobis)
if _rc == 0 {
    eststo tef_nn
    local atet_nn = _b[r1vs0.TREATMENT_VAR]
    di "NN-Match ATET: `atet_nn'"
}
else {
    di "teffects nnmatch failed (likely panel data). Skipping."
}

* --- Comparison table ---
esttab tef_ra tef_ipw tef_aipw tef_nn ///
    using "output/tables/tab_treatment_effects.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("RA" "IPW" "AIPW" "NN-Match") ///
    label booktabs replace ///
    title("Average Treatment Effect on the Treated (ATET)") ///
    note("RA = regression adjustment. IPW = inverse probability weighting (probit)." ///
         "AIPW = augmented IPW (doubly robust). NN = nearest-neighbor matching." ///
         "AIPW is preferred: consistent if either outcome or treatment model correct.")

* --- Summary ---
di "============================================="
di "TREATMENT EFFECTS COMPARISON"
di "============================================="
di "  RA-ATET:      `atet_ra'"
di "  IPW-ATET:     `atet_ipw'"
di "  AIPW-ATET:    `atet_aipw'"
di "  NN-ATET:      `atet_nn'"
di "  Convergence of RA and IPW supports AIPW."
di "  Large divergence suggests model sensitivity."
di "============================================="

log close
```

## Step 4: Conditional Logit for Discrete Choice (Stata .do file)

Following Mexico Retail Table 5 pattern.

```stata
/*==============================================================================
  Logit/Probit Analysis — Step 4: Conditional Logit (Discrete Choice)
  Reference: Mexico Retail Table 5 — clogit for household store choice
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_04_clogit.log", replace

use "DATASET_PATH", clear

* --- Conditional logit (McFadden's choice model) ---
* Data must be in long format: one row per alternative per choice occasion
* GROUP_VAR identifies the choice group (e.g., household-year)
* CHOICE_VAR is 1 for the chosen alternative, 0 otherwise
* X variables can be alternative-specific or interacted with alternative dummies

eststo clear
eststo clogit_main: clogit CHOICE_VAR ALT_SPECIFIC_VARS ///
    [pw=WEIGHT_VAR], group(GROUP_VAR) vce(cluster CLUSTER_VAR)

* Marginal effects (average over choice groups)
margins, dydx(*) post
eststo clogit_ame

* --- Alternative specifications ---
* Specification with additional controls
eststo clogit_full: clogit CHOICE_VAR ALT_SPECIFIC_VARS ADDITIONAL_CONTROLS ///
    [pw=WEIGHT_VAR], group(GROUP_VAR) vce(cluster CLUSTER_VAR)

* --- Table ---
esttab clogit_main clogit_full clogit_ame ///
    using "output/tables/tab_conditional_logit.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("Baseline" "Full Controls" "AME") ///
    label booktabs replace ///
    title("Conditional Logit: Discrete Choice") ///
    note("Conditional logit estimated via clogit." ///
         "Choice groups defined by GROUP_VAR." ///
         "Standard errors clustered at CLUSTER_VAR level.")

log close
```

## Step 5: Diagnostics (Stata .do file)

```stata
/*==============================================================================
  Logit/Probit Analysis — Step 5: Model Diagnostics
  ROC, Hosmer-Lemeshow, link test, classification
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_05_diagnostics.log", replace

use "DATASET_PATH", clear

* --- Fit main model ---
logit OUTCOME_VAR TREATMENT_VAR COVARIATES, vce(cluster CLUSTER_VAR)

* --- ROC Curve and AUC ---
lroc, title("ROC Curve") note("AUC = area under curve; 0.5 = random, 1.0 = perfect")
graph export "output/figures/fig_roc_curve.pdf", replace
lstat
* AUC > 0.7 is acceptable; > 0.8 is good; > 0.9 is excellent

* --- Hosmer-Lemeshow Goodness of Fit ---
* Re-fit without vce(cluster) for estat gof compatibility
logit OUTCOME_VAR TREATMENT_VAR COVARIATES
estat gof, group(10)
* Null: model fits well. Reject (p < 0.05) → poor fit

* --- Link Test (Pregibon) ---
linktest
* _hat should be significant, _hatsq should NOT be significant
* Significant _hatsq suggests misspecification (wrong functional form)

* --- Classification Table ---
estat classification
* Reports sensitivity, specificity, and overall correct classification rate

* --- Pseudo R-squared comparison ---
di "============================================="
di "MODEL FIT DIAGNOSTICS"
di "============================================="
logit OUTCOME_VAR TREATMENT_VAR COVARIATES
di "  Pseudo R2 (logit):   " e(r2_p)
probit OUTCOME_VAR TREATMENT_VAR COVARIATES
di "  Pseudo R2 (probit):  " e(r2_p)
di "  AIC (logit):         [from estat ic]"
di "  BIC (logit):         [from estat ic]"
estat ic
di "============================================="

log close
```

## Step 6: Extensions (Stata .do file)

```stata
/*==============================================================================
  Logit/Probit Analysis — Step 6: Extensions
  Multinomial logit, ordered logit/probit, IV probit
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_06_extensions.log", replace

use "DATASET_PATH", clear

* --- Multinomial Logit (unordered categories) ---
* Use when outcome has 3+ unordered categories
eststo mlogit_main: mlogit MULTI_OUTCOME COVARIATES, ///
    vce(cluster CLUSTER_VAR) baseoutcome(BASE_CATEGORY)
margins, dydx(TREATMENT_VAR) predict(outcome(CATEGORY_1)) post
* Repeat for each outcome category

* --- Ordered Logit ---
* Use when outcome is ordinal (Likert scale, rating)
eststo ologit_main: ologit ORDERED_OUTCOME COVARIATES, ///
    vce(cluster CLUSTER_VAR)
margins, dydx(TREATMENT_VAR) predict(outcome(CATEGORY_1)) post

* --- Ordered Probit ---
eststo oprobit_main: oprobit ORDERED_OUTCOME COVARIATES, ///
    vce(cluster CLUSTER_VAR)

* --- IV Probit (endogenous binary treatment) ---
* When treatment is binary and endogenous
eststo ivprobit_main: ivprobit OUTCOME_VAR COVARIATES ///
    (TREATMENT_VAR = INSTRUMENT), vce(cluster CLUSTER_VAR)
margins, dydx(TREATMENT_VAR) post

log close
```

## Step 7: Python Cross-Validation

```python
"""
Logit/Probit Cross-Validation: Stata vs Python (statsmodels, sklearn)
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report

df = pd.read_stata("DATASET_PATH")

# --- Logit via statsmodels ---
X = df[["TREATMENT_VAR"] + COVARIATES_LIST]
X = sm.add_constant(X)
y = df["OUTCOME_VAR"]

logit_model = sm.Logit(y, X).fit(cov_type="cluster",
                                  cov_kwds={"groups": df["CLUSTER_VAR"]})
print("=== Python Logit (statsmodels) ===")
print(logit_model.summary())

# --- Marginal effects (AME) ---
ame = logit_model.get_margeff(at="overall")
print("\n=== Average Marginal Effects ===")
print(ame.summary())

# --- Probit via statsmodels ---
probit_model = sm.Probit(y, X).fit(cov_type="cluster",
                                    cov_kwds={"groups": df["CLUSTER_VAR"]})
print("\n=== Python Probit (statsmodels) ===")
print(probit_model.summary())

# --- Cross-validate with Stata ---
stata_logit_ame = STATA_LOGIT_AME  # AME from Step 1
python_logit_ame = ame.margeff[0]  # treatment variable AME
pct_diff = abs(stata_logit_ame - python_logit_ame) / abs(stata_logit_ame) * 100
print(f"\nCross-validation (Logit AME on treatment):")
print(f"  Stata:  {stata_logit_ame:.6f}")
print(f"  Python: {python_logit_ame:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 0.5 else 'CHECK'}")
# Note: AME comparison uses 0.5% threshold (numerical integration differences)

# --- ROC/AUC ---
y_pred_prob = logit_model.predict(X)
auc = roc_auc_score(y, y_pred_prob)
print(f"\nPython AUC: {auc:.4f}")

# --- sklearn for comparison ---
lr = LogisticRegression(penalty=None, max_iter=10000)
X_sk = df[["TREATMENT_VAR"] + COVARIATES_LIST]
lr.fit(X_sk, y)
print(f"sklearn Logit coef (treatment): {lr.coef_[0][0]:.6f}")
```

## Step 8: Diagnostics Summary

After all steps, provide:

1. **Model Selection**: Logit vs probit — coefficients differ but AME should be similar. If AME diverges, report both and note which is preferred.
2. **LPM Comparison**: LPM coefficient vs logit/probit AME. If similar, nonlinearity is minimal.
3. **Propensity Score**: Overlap quality (visual + numeric). Flag if common support excludes > 10% of observations.
4. **Treatment Effects**: RA, IPW, AIPW convergence. If all three agree, result is robust. If IPW diverges from RA, treatment model may be misspecified.
5. **Diagnostics**: ROC/AUC, Hosmer-Lemeshow, link test results. Flag poor fit (AUC < 0.7 or H-L rejection).
6. **Conditional Logit** (if applicable): IIA assumption discussion, marginal effects interpretation.
7. **Cross-Validation**: Stata vs Python AME comparison.

## Required Stata Packages

```stata
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install coefplot, replace
```

## Key References

- Acemoglu, D., Naidu, S., Restrepo, P. & Robinson, J.A. (2019). "Democracy Does Cause Growth." JPE, 127(1), 47-100. (Propensity score, teffects, bootstrap)
- Imbens, G.W. (2004). "Nonparametric Estimation of Average Treatment Effects Under Exogeneity." REStat. (IPW, overlap)
- McFadden, D. (1974). "Conditional Logit Analysis of Qualitative Choice Behavior." (Conditional logit foundation)
- Cattaneo, M.D. (2010). "Efficient Semiparametric Estimation of Multi-Valued Treatment Effects." JoE. (Treatment effects)
