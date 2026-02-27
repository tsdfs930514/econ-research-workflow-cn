---
description: "Run LASSO, post-double-selection, and regularized regression pipeline for variable selection and causal inference"
user_invocable: true
---

# /run-lasso — LASSO & Regularized Regression Pipeline

When the user invokes `/run-lasso`, execute a complete regularized regression pipeline covering standard LASSO for prediction, cross-validated penalty selection, post-LASSO OLS, post-double-selection for causal inference (Belloni, Chernozhukov, Hansen 2014), rigorous LASSO with valid inference, and Python cross-validation.

## Stata Execution Command

Run .do files via the auto-approved wrapper: `bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`. The wrapper handles `cd`, Stata execution (`-e` flag), and automatic log error checking. See `CLAUDE.md` for details.

## When to Use LASSO / Regularization

- **Many candidate controls**: When you have dozens/hundreds of potential controls and need principled selection
- **Causal inference with high-dimensional covariates**: Post-double-selection selects controls for BOTH outcome and treatment models, avoiding omitted variable bias while preventing overfitting
- **Prediction tasks**: When the goal is forecasting rather than inference
- **Variable selection for robustness**: Complement hand-picked controls with data-driven selection
- **Avoiding cherry-picking**: Reviewer concern about which controls were included — LASSO provides a principled answer

**Important**: Standard LASSO does NOT provide valid inference on selected coefficients. For causal inference, use post-double-selection (Step 4) or rigorous LASSO (Step 5).

## Step 0: Gather Inputs

Ask the user for:

- **Dataset**: path to .dta file
- **Outcome variable**: dependent variable Y
- **Treatment variable** (if causal inference): the key variable whose effect is of interest
- **Candidate regressors**: full list of potential controls (can be large)
- **Fixed effects** (optional): FE to absorb before LASSO
- **Cluster variable**: for clustered standard errors in post-selection inference
- **Purpose**: prediction, variable selection, or causal inference via post-double-selection
- **Model type**: linear, logit, or poisson (Stata 16+ `lasso` supports all). **Note**: `lasso logit` may fail with r(430) convergence error when the binary outcome has near-perfect separation with some predictors. Wrap in `cap noisily` and fall back to `rlasso` if needed (Issue #18).

Determine Stata version: LASSO built-ins (`lasso`, `dsregress`) require Stata 16+. For earlier versions, use community packages (`lassopack`: `cvlasso`, `rlasso`, `pdslasso`).

## Step 1: Standard LASSO for Variable Selection (Stata .do file)

```stata
/*==============================================================================
  LASSO Analysis — Step 1: Standard LASSO & Cross-Validation
  Stata 16+ built-in lasso command
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_01_selection.log", replace

use "DATASET_PATH", clear

* --- Check Stata version for built-in lasso ---
if c(stata_version) >= 16 {

    * Standard LASSO with cross-validation
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345)
    estimates store lasso_cv

    * Report selected variables
    lassocoef, display(coef, penalized)
    di "Number of selected variables: " e(k_nonzero_sel)

    * Cross-validation function (lambda path)
    cvplot
    graph export "output/figures/fig_lasso_cvplot.pdf", replace

    * Lambda values
    di "Lambda (CV min):     " e(lambda_sel)
    di "Lambda (CV 1se):     " // use selection(cv, serule) for 1-SE rule

    * --- LASSO with 1-SE rule (more parsimonious) ---
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv, serule) folds(10) rseed(12345)
    estimates store lasso_1se
    lassocoef, display(coef, penalized)
    di "Number of selected (1-SE rule): " e(k_nonzero_sel)

}
else {
    * --- Community package: cvlasso (lassopack) ---
    cap which cvlasso
    if _rc != 0 {
        ssc install lassopack, replace
    }

    cvlasso OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        lopt seed(12345) nfolds(10)
    local lambda_opt = e(lopt)

    * LASSO at optimal lambda
    lasso2 OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        lambda(`lambda_opt')
    di "Selected variables: " e(selected)
}

log close
```

## Step 2: Variable Selection Path & Diagnostics (Stata .do file)

```stata
/*==============================================================================
  LASSO Analysis — Step 2: Selection Path & Model Comparison
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_02_path.log", replace

use "DATASET_PATH", clear

* --- LASSO path (coefficient evolution across lambda) ---
if c(stata_version) >= 16 {
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, selection(cv) rseed(12345)

    * Coefficient path plot
    lassoknots, display(nonzero penalized)
    coefpath
    graph export "output/figures/fig_lasso_coefpath.pdf", replace
}
else {
    * lassopack path
    lasso2 OUTCOME_VAR CANDIDATE_REGRESSORS, long
    lasso2, lic(ebic)  // Extended BIC for selection
}

* --- Compare: LASSO-selected vs Hand-picked controls ---
eststo clear

* Full model (all candidates)
eststo full_ols: reghdfe OUTCOME_VAR CANDIDATE_REGRESSORS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* LASSO-selected model
eststo lasso_ols: reghdfe OUTCOME_VAR LASSO_SELECTED_VARS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* Hand-picked controls (researcher's choice)
eststo hand_ols: reghdfe OUTCOME_VAR HANDPICKED_CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* Minimal model (treatment only)
eststo min_ols: reghdfe OUTCOME_VAR TREATMENT_VAR, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

esttab full_ols lasso_ols hand_ols min_ols ///
    using "output/tables/tab_lasso_comparison.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    mtitles("Full" "LASSO" "Hand-Picked" "Minimal") ///
    scalars("N Observations" "r2_within Within R$^2$") ///
    title("Treatment Effect: LASSO vs Alternative Control Sets") ///
    note("LASSO-selected controls chosen by 10-fold CV." ///
         "Treatment coefficient stability across control sets supports robustness.")

log close
```

## Step 3: Post-LASSO OLS (Stata .do file)

Run OLS on the LASSO-selected variables for unbiased coefficient estimates.

```stata
/*==============================================================================
  LASSO Analysis — Step 3: Post-LASSO OLS
  LASSO selects variables; OLS estimates coefficients on selected set.
  This removes the regularization bias from LASSO coefficients.
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_03_postlasso.log", replace

use "DATASET_PATH", clear

if c(stata_version) >= 16 {
    * LASSO selection
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345)

    * Post-LASSO OLS: extract selected variables and run OLS
    * lassocoef stores selected variable names
    * NOTE: CV LASSO may select 0 variables in small samples or when signal
    * is weak. Check e(k_nonzero_sel) before proceeding (Issues #16-17).
    local selected_vars ""
    if e(k_nonzero_sel) > 0 {
        matrix b = e(b_postselection)
        local names : colnames b
        foreach v of local names {
            if "`v'" != "_cons" {
                local selected_vars "`selected_vars' `v'"
            }
        }
        eststo postlasso: reghdfe OUTCOME_VAR `selected_vars', ///
            absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    }
    else {
        di "WARNING: LASSO selected 0 variables. Skipping post-LASSO OLS."
        di "This can happen with small samples or low signal-to-noise ratio."
        di "Consider using rlasso (rigorous LASSO) from lassopack instead."
    }
}
else {
    * lassopack: post-LASSO built into rlasso
    rlasso OUTCOME_VAR CANDIDATE_REGRESSORS, cluster(CLUSTER_VAR)
    local selected = e(selected)
    reghdfe OUTCOME_VAR `selected', absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
}

di "============================================="
di "POST-LASSO OLS"
di "============================================="
di "  Selected variables: `selected_vars'"
di "  N selected: " wordcount("`selected_vars'")
di "  N candidates: " wordcount("CANDIDATE_REGRESSORS")
di "============================================="

log close
```

## Step 4: Post-Double-Selection for Causal Inference (Stata .do file)

The key method for using LASSO in causal inference. Selects controls for BOTH the outcome equation AND the treatment equation, then estimates the treatment effect on the union of selected controls. This avoids omitted variable bias that arises from selecting controls based on the outcome equation alone.

```stata
/*==============================================================================
  LASSO Analysis — Step 4: Post-Double-Selection (PDS)
  Reference: Belloni, Chernozhukov & Hansen (2014, REStud)
  Key insight: Select controls for BOTH Y and D equations
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_04_pds.log", replace

use "DATASET_PATH", clear

* --- Method 1: Stata 16+ dsregress (recommended) ---
if c(stata_version) >= 16 {
    * dsregress: double-selection built-in
    * Syntax: dsregress Y D, controls(candidate_controls) [options]
    dsregress OUTCOME_VAR TREATMENT_VAR, ///
        controls(CANDIDATE_REGRESSORS) ///
        selection(cv) folds(10) rseed(12345) ///
        vce(cluster CLUSTER_VAR)
    estimates store pds_main

    * Report selected controls from each stage
    lassoinfo
    di "Controls selected for outcome equation: " e(k_nonzero_sel_o)
    di "Controls selected for treatment equation: " e(k_nonzero_sel_d)
}

* --- Method 2: pdslasso (community, any Stata version) ---
cap which pdslasso
if _rc != 0 {
    net install pdslasso, from("https://raw.githubusercontent.com/statalasso/pdslasso/master")
}

pdslasso OUTCOME_VAR TREATMENT_VAR (CANDIDATE_REGRESSORS), ///
    cluster(CLUSTER_VAR)
estimates store pds_community

* --- Method 3: Manual double selection ---
* Step A: LASSO for outcome equation (Y on candidates)
* Step B: LASSO for treatment equation (D on candidates)
* Step C: OLS of Y on D + union of (A-selected ∪ B-selected)

* Step A
rlasso OUTCOME_VAR CANDIDATE_REGRESSORS
local selected_y = e(selected)

* Step B
rlasso TREATMENT_VAR CANDIDATE_REGRESSORS
local selected_d = e(selected)

* Step C: Union
local union_controls : list selected_y | selected_d
local union_controls : list uniq union_controls

eststo pds_manual: reghdfe OUTCOME_VAR TREATMENT_VAR `union_controls', ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- Comparison table ---
esttab pds_main pds_community pds_manual ///
    using "output/tables/tab_pds_results.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    mtitles("dsregress" "pdslasso" "Manual PDS") ///
    title("Post-Double-Selection: Treatment Effect") ///
    note("Belloni, Chernozhukov \& Hansen (2014) post-double-selection." ///
         "LASSO selects controls for both outcome and treatment equations." ///
         "Final OLS uses union of selected controls.")

di "============================================="
di "POST-DOUBLE-SELECTION SUMMARY"
di "============================================="
di "  Y-equation selected controls: `selected_y'"
di "  D-equation selected controls: `selected_d'"
di "  Union (final controls):       `union_controls'"
di "  Treatment effect (PDS):       " _b[TREATMENT_VAR]
di "============================================="

log close
```

## Step 5: Rigorous LASSO for Valid Inference (Stata .do file)

```stata
/*==============================================================================
  LASSO Analysis — Step 5: Rigorous LASSO (rlasso)
  Reference: Belloni, Chen, Chernozhukov & Hansen (2012)
  Theory-driven penalty for valid post-selection inference
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_05_rlasso.log", replace

use "DATASET_PATH", clear

* --- Rigorous LASSO ---
* Uses theoretically-justified penalty (not CV) for valid inference
* Penalty accounts for heteroskedasticity and clustering
cap which rlasso
if _rc != 0 {
    ssc install lassopack, replace
}

* rlasso with cluster-robust penalty
rlasso OUTCOME_VAR CANDIDATE_REGRESSORS, ///
    cluster(CLUSTER_VAR) robust

di "Rigorous LASSO selected: " e(selected)
di "N selected: " e(s)

* Post-rlasso OLS
local rlasso_selected = e(selected)
eststo rlasso_post: reghdfe OUTCOME_VAR TREATMENT_VAR `rlasso_selected', ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- Elastic Net (alpha between 0 and 1) ---
* Alpha = 1 is LASSO, alpha = 0 is Ridge
if c(stata_version) >= 16 {
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345) grid(10, ratio(0.001))
    * Elasticnet:
    elasticnet linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345) alphas(0 0.25 0.5 0.75 1)
    estimates store enet
}

log close
```

## Step 6: Python Cross-Validation

```python
"""
LASSO Cross-Validation: Stata vs Python (sklearn, hdm-inspired)
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV, Lasso, ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
import statsmodels.api as sm

df = pd.read_stata("DATASET_PATH")

# --- Prepare data ---
y = df["OUTCOME_VAR"].values
X_candidates = df[CANDIDATE_REGRESSOR_LIST].values
treatment = df["TREATMENT_VAR"].values

# Standardize candidates (LASSO requires standardized inputs)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_candidates)

# --- LASSO with cross-validation ---
lasso_cv = LassoCV(cv=10, random_state=12345, max_iter=10000)
lasso_cv.fit(X_scaled, y)

# Selected variables (nonzero coefficients)
selected_mask = lasso_cv.coef_ != 0
selected_names = [CANDIDATE_REGRESSOR_LIST[i]
                  for i in range(len(CANDIDATE_REGRESSOR_LIST))
                  if selected_mask[i]]
print(f"=== Python LASSO CV ===")
print(f"  Optimal lambda: {lasso_cv.alpha_:.6f}")
print(f"  N selected: {sum(selected_mask)}")
print(f"  Selected: {selected_names}")

# --- Post-LASSO OLS ---
X_selected = df[selected_names]
X_post = sm.add_constant(pd.concat([df[["TREATMENT_VAR"]], X_selected], axis=1))
post_lasso = sm.OLS(y, X_post).fit(cov_type="cluster",
                                    cov_kwds={"groups": df["CLUSTER_VAR"]})
print(f"\n=== Post-LASSO OLS ===")
print(f"  Treatment coef: {post_lasso.params['TREATMENT_VAR']:.6f}")
print(f"  Treatment SE:   {post_lasso.bse['TREATMENT_VAR']:.6f}")

# --- Post-Double-Selection (manual) ---
# Step A: LASSO Y ~ candidates
lasso_y = LassoCV(cv=10, random_state=12345, max_iter=10000)
lasso_y.fit(X_scaled, y)
selected_y = set(np.where(lasso_y.coef_ != 0)[0])

# Step B: LASSO D ~ candidates
lasso_d = LassoCV(cv=10, random_state=12345, max_iter=10000)
lasso_d.fit(X_scaled, treatment)
selected_d = set(np.where(lasso_d.coef_ != 0)[0])

# Step C: OLS Y ~ D + union
union_idx = selected_y | selected_d
union_names = [CANDIDATE_REGRESSOR_LIST[i] for i in union_idx]
X_pds = sm.add_constant(pd.concat([df[["TREATMENT_VAR"]], df[union_names]], axis=1))
pds_model = sm.OLS(y, X_pds).fit(cov_type="cluster",
                                   cov_kwds={"groups": df["CLUSTER_VAR"]})
print(f"\n=== Python Post-Double-Selection ===")
print(f"  Y-selected: {len(selected_y)} vars")
print(f"  D-selected: {len(selected_d)} vars")
print(f"  Union: {len(union_idx)} vars")
print(f"  Treatment coef: {pds_model.params['TREATMENT_VAR']:.6f}")

# --- Cross-validate with Stata ---
stata_pds_coef = STATA_PDS_COEF  # from Step 4 log
python_pds_coef = pds_model.params["TREATMENT_VAR"]
pct_diff = abs(stata_pds_coef - python_pds_coef) / abs(stata_pds_coef) * 100
print(f"\nCross-validation (PDS treatment coef):")
print(f"  Stata:  {stata_pds_coef:.6f}")
print(f"  Python: {python_pds_coef:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 1 else 'CHECK'}")
# Note: PDS comparison uses 1% threshold (different CV splits may select
# different variables, leading to slightly different final estimates)

# --- CV Error Plot ---
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 5))
m_log_alphas = -np.log10(lasso_cv.alphas_)
ax.plot(m_log_alphas, np.mean(lasso_cv.mse_path_, axis=1), color="steelblue")
ax.fill_between(m_log_alphas,
                np.mean(lasso_cv.mse_path_, axis=1) - np.std(lasso_cv.mse_path_, axis=1),
                np.mean(lasso_cv.mse_path_, axis=1) + np.std(lasso_cv.mse_path_, axis=1),
                alpha=0.2, color="steelblue")
ax.axvline(-np.log10(lasso_cv.alpha_), linestyle="--", color="crimson",
           label=f"Optimal lambda = {lasso_cv.alpha_:.4f}")
ax.set_xlabel("-log10(lambda)")
ax.set_ylabel("Mean Squared Error (CV)")
ax.set_title("LASSO Cross-Validation Error")
ax.legend()
fig.savefig("output/figures/fig_lasso_cv_python.pdf", bbox_inches="tight")
plt.close()
```

## Step 7: LASSO Propensity Score Matching in R (Stata .do file + R)

LASSO can estimate propensity scores for matched-sample causal inference. Pattern from Abman, Lundberg & Ruta (JEEA 2024) — RTAs & Environment replication (`jvae023`): logistic LASSO selects which covariates predict treatment, then nearest-neighbor matching on LASSO P-score, then DiD/event study on matched panel.

```r
# ============================================================
# LASSO Propensity Score Matching in R (glmnet)
# Reference: Abman, Lundberg & Ruta (JEEA 2024) jvae023
# ============================================================
library(glmnet)
library(lfe)         # for felm() panel regression
library(data.table)

# --- Step A: Prepare model matrix for LASSO ---
# Outcome: binary treatment indicator (enviro_rta)
# Covariates: everything in rta_cross_section except outcomes and treatment
lasso_data <- data.table(read.csv("rta_cross_section.csv"))

# model.matrix creates dummy variables for factors
X_mat <- model.matrix(
  ~ .,
  lasso_data[, date_signed := as.factor(date_signed)][
    !is.na(avg_biodiver),
    -c("Agreement", "Entry.into.Force", "treatment", "outcome")]
)
y_vec <- lasso_data[!is.na(avg_biodiver), treatment_var]

# --- Step B: Cross-validated logistic LASSO (50 folds) ---
set.seed(12345)
lasso_obj <- cv.glmnet(X_mat, y_vec, family = "binomial", nfolds = 50)

# Two penalty choices:
# lambda.min: minimizes CV error
# lambda.1se: 1 SE above min (more parsimonious, preferred for matching)
cat("Lambda min:", lasso_obj$lambda.min, "\n")
cat("Lambda 1SE:", lasso_obj$lambda.1se, "\n")

# --- Step C: Predict propensity scores ---
panel_data[, prop_score := predict(lasso_obj, newx = X_panel,
                                    s = "lambda.min", type = "response")]

# --- Step D: 1:1 nearest-neighbor matching on P-score ---
# For each treated unit, find closest control by |P-score difference|
treated_ids <- unique(panel_data[treatment == 1, id])
match_key <- data.table(treat_id = treated_ids, match_id = 0L, abs_diff = 99)

for (i in treated_ids) {
  ps_i <- unique(panel_data[id == i, prop_score])
  controls <- panel_data[treatment == 0 & id != i,]
  nearest <- controls[which.min(abs(prop_score - ps_i)), .(id, abs(prop_score - ps_i))]
  match_key[treat_id == i, c("match_id", "abs_diff") := nearest]
}

# --- Step E: Construct matched panel ---
matched_ids <- unique(c(match_key$treat_id, match_key$match_id))
matched_panel <- panel_data[id %in% matched_ids]

# Handle repeated matches (same control matched to multiple treated units)
rep_ids <- match_key[, .N, by = match_id][N > 1]
for (i in rep_ids$match_id) {
  n_extra <- match_key[match_id == i, .N] - 1
  matched_panel <- rbind(matched_panel,
                         rep(list(panel_data[id == i]), n_extra))
}

# --- Step F: DiD/event study on matched panel ---
# Note: areg or lfe::felm for unit + year FE
result <- felm(log(1 + outcome) ~ treatment + enviro_treatment | unit_id + year | 0 | 0,
               data = matched_panel)

# --- Step G: Overlap plot for matched vs unmatched ---
par(mfrow = c(1, 2))
density_ctrl <- density(panel_data[treatment == 0, prop_score], bw = 0.03)
density_trt  <- density(panel_data[treatment == 1, prop_score], bw = 0.03)
plot(density_ctrl, main = "Full Sample P-Score", xlab = "Propensity Score")
lines(density_trt, col = "red")
legend("topright", c("Treated", "Control"), lty = 1, col = c("red", "black"))

density_ctrl_m <- density(matched_panel[treatment == 0, prop_score], bw = 0.03)
density_trt_m  <- density(matched_panel[treatment == 1, prop_score], bw = 0.03)
plot(density_ctrl_m, main = "Matched Sample P-Score", xlab = "Propensity Score")
lines(density_trt_m, col = "red")
```

**IHS transformation for near-zero outcomes** (also from jvae023):
```r
# Inverse hyperbolic sine: better than log(x+1) for small positive values
# IHS(x) ≈ log(2x) for large x; ≈ x for small x
ihs <- function(x) log(x + sqrt(x^2 + 1))
panel_data[, y_ihs := ihs(outcome_var)]
# Use ihs(outcome) as dependent variable in felm()
```

**Stata equivalent** (if switching from R to Stata for matched-sample regression):
```stata
* After matching in R, export matched panel to .dta and run Stata
* areg for absorbed match-pair FE (pairing variable)
eststo m1: areg OUTCOME_VAR TREATMENT_VAR, a(MATCH_PAIR_FE) cluster(CLUSTER_VAR)
* reghdfe equivalent:
eststo m1: reghdfe OUTCOME_VAR TREATMENT_VAR, absorb(MATCH_PAIR_FE) vce(cluster CLUSTER_VAR)
```

## Step 8: Diagnostics Summary

After all steps, provide:

1. **Variable Selection**: How many variables selected by LASSO vs total candidates? Are key theoretical controls included?
2. **CV Error Plot**: Is the minimum well-defined or is the error curve flat (suggesting weak signal)?
3. **Post-LASSO vs Full OLS**: Does the treatment coefficient change substantially when switching from LASSO-selected to full control set? Stability supports robustness.
4. **Post-Double-Selection**: Report controls selected for Y-equation vs D-equation. If the union is much larger than either alone, important confounders were missed by single-equation selection.
5. **PDS vs Hand-Picked**: Compare PDS treatment effect with hand-picked specification. Large divergence suggests the hand-picked set may be misspecified.
6. **Rigorous LASSO**: Compare CV-based and theory-based (rlasso) selected variables. If they agree, selection is stable.
7. **Cross-Validation**: Stata vs Python post-double-selection coefficient comparison.

## Required Stata Packages

```stata
* Stata 16+ built-in: lasso, dsregress, elasticnet (no install needed)

* Community packages (any Stata version):
ssc install lassopack, replace     // cvlasso, rlasso, lasso2
net install pdslasso, from("https://raw.githubusercontent.com/statalasso/pdslasso/master")
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
```

## Key References

- Belloni, A., Chernozhukov, V. & Hansen, C. (2014). "Inference on Treatment Effects after Selection among High-Dimensional Controls." REStud, 81(2), 608-650.
- Belloni, A., Chen, D., Chernozhukov, V. & Hansen, C. (2012). "Sparse Models and Methods for Optimal Instruments with an Application to Eminent Domain." Econometrica, 80(6), 2369-2429.
- Tibshirani, R. (1996). "Regression Shrinkage and Selection via the Lasso." JRSSB. (Original LASSO paper)
- Ahrens, A., Hansen, C.B. & Schaffer, M.E. (2020). "lassopack: Model Selection and Prediction with Regularized Regression in Stata." Stata Journal.
