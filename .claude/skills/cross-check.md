---
description: "Cross-validate regression results between Stata, Python pyfixest, and R fixest"
user_invocable: true
---

# /cross-check - Cross-Validate Regression Results

When the user invokes `/cross-check`, follow these steps:

## Step 1: Gather Information

Ask the user for:

1. **Stata .log file path** (optional) - Path to the Stata log file containing regression output
2. **Python output file path** (optional) - Path to Python output or script that produces regression results
3. **R output file path** (optional) - Path to R output or script (for APE paper cross-validation)
4. **If none provided**: Ask for the regression specification and dataset, then generate both Stata and Python scripts to produce comparable output
5. **Comparison mode**:
   - `stata-python` (default) — Compare Stata reghdfe vs Python pyfixest
   - `stata-r` — Compare Stata reghdfe vs R fixest (when validating APE papers)
   - `triple` — Compare all three: Stata vs Python vs R

## Step 2: Parse Stata Output

Read the Stata .log file and extract the following from each regression table:

- **Coefficients**: Point estimates for each independent variable
- **Standard errors**: Values in parentheses beneath coefficients
- **R-squared**: R², adjusted R², within-R² as applicable
- **Number of observations (N)**
- **F-statistic** (if reported)
- **Fixed effects** included (if any)
- **Clustering** level (if any)
- **Dependent variable** name
- **KP F-statistic** (for IV models)
- **First-stage F** (for IV models)

Parsing tips:
- Stata regression output follows a standard tabular format
- Look for lines with variable names followed by coefficient and standard error
- R² is typically reported at the bottom of the regression table
- N is reported as "Number of obs"
- Standard errors may be labeled as "Robust", "Cluster", etc.

## Step 3: Parse Python Output

If a Python script/output is provided, extract the same statistics. If generating a new Python script, use `pyfixest`:

```python
import pyfixest as pf
import pandas as pd

# Load data
df = pd.read_stata("<dataset path>")

# --- OLS / Panel FE ---
model = pf.feols("<formula>", data=df, vcov=<vcov specification>)
print(model.summary())

# --- IV / 2SLS ---
# Syntax: Y ~ exog | FEs | endog ~ instrument
model_iv = pf.feols("Y ~ controls | fe1 + fe2 | endog ~ instrument",
                     data=df, vcov={"CRV1": "cluster_var"})
print(model_iv.summary())

# --- DID event study ---
model_es = pf.feols("Y ~ i(rel_time, ref=-1) | unit + time",
                     data=df, vcov={"CRV1": "cluster_var"})
print(model_es.summary())

# Extract key statistics
coefs = model.coef()
se = model.se()
r2 = model._r2 if hasattr(model, '_r2') else None
r2_within = model._r2_within if hasattr(model, '_r2_within') else None
n = model._N
```

## Step 4: Parse R Output (for APE paper validation)

If R output is provided (from APE papers using `fixest`), extract equivalent statistics:

```
# R fixest output format:
# Coefficient table with Estimate, Std. Error, t value, Pr(>|t|)
# Fixed-effects listed at bottom
# Signif. codes at bottom
```

Key R-to-Stata mapping for `fixest`:
| R fixest | Stata reghdfe | Python pyfixest |
|----------|---------------|-----------------|
| `feols(y ~ x \| fe1 + fe2, cluster = ~cl)` | `reghdfe y x, absorb(fe1 fe2) vce(cluster cl)` | `pf.feols("y ~ x \| fe1 + fe2", vcov={"CRV1": "cl"})` |
| `feols(y ~ x \| fe1 + fe2 \| endog ~ inst, cluster = ~cl)` | `ivreghdfe y (endog = inst), absorb(fe1 fe2) cluster(cl)` | `pf.feols("y ~ x \| fe1 + fe2 \| endog ~ inst", vcov={"CRV1": "cl"})` |
| `sunab(first_treat, time)` | `eventstudyinteract` / `csdid` | `pf.feols("y ~ sunab(g, t) \| ...")` |
| `etable()` | `esttab` | `pf.etable()` |

Key R-to-Stata mapping for `lfe::felm()` (common in finance/accounting papers):
| R lfe::felm | Stata reghdfe | Python pyfixest |
|-------------|---------------|-----------------|
| `felm(y ~ x \| fe1 + fe2 \| 0 \| cl1 + cl2)` | `reghdfe y x, absorb(fe1 fe2) vce(cluster cl1 cl2)` | `pf.feols("y ~ x \| fe1 + fe2", vcov={"CRV1": "cl1"})` (note: pyfixest only supports single cluster) |
| `felm(y ~ x \| fe1 + fe2 \| endog ~ inst \| cl)` | `ivreghdfe y (endog = inst), absorb(fe1 fe2) cluster(cl)` | Same as fixest IV syntax |

**felm() 4-part formula**: `y ~ X | FEs | IVs | Clusters`
- Part 1: `y ~ X` — dependent variable and exogenous regressors
- Part 2: `| fe1 + fe2 + fe3` — fixed effects to absorb (additive, not interaction)
- Part 3: `| endog ~ inst` or `| 0` — instrumental variables (0 = none)
- Part 4: `| cluster1 + cluster2` — clustering variables for SEs

**Multi-way clustering with lfe/multiwayvcov**:
```r
library(lfe)
# Two-way clustering directly in felm:
model <- felm(y ~ x | fe1 + fe2 | 0 | cusip + date, data=df)

# Alternative with lm + multiwayvcov:
library(multiwayvcov)
lm_model <- lm(y ~ x + factor(fe1), data=df)
vcov_2way <- cluster.vcov(lm_model, cbind(df$cusip, df$date))
```

**Loading .sas7bdat data in Python** (for packages with SAS data):
```python
df = pd.read_sas("data/raw/file.sas7bdat", format="sas7bdat", encoding="latin-1")
```

## Step 5: Compare Results

Create a comparison table with the following structure:

### Two-way comparison (Stata vs Python):

```
============================================================
Cross-Validation Report: Stata vs Python
============================================================
Variable        | Stata      | Python     | Rel. Diff  | Status
----------------|------------|------------|------------|-------
x1 (coef)       | 0.1234     | 0.1234     | 0.000%     | PASS
x1 (se)         | 0.0456     | 0.0457     | 0.022%     | PASS
x2 (coef)       | -0.5678    | -0.5679    | 0.002%     | PASS
x2 (se)         | 0.1234     | 0.1236     | 0.016%     | PASS
R-squared       | 0.4567     | 0.4567     | 0.000      | PASS
N               | 10000      | 10000      | 0          | PASS
F-stat          | 45.67      | 45.65      | 0.044%     | PASS
============================================================
```

### Triple comparison (Stata vs Python vs R):

```
============================================================
Cross-Validation Report: Stata vs Python vs R
============================================================
Variable     | Stata      | Python     | R          | Max Diff | Status
-------------|------------|------------|------------|----------|-------
x1 (coef)    | 0.1234     | 0.1234     | 0.1234     | 0.000%   | PASS
x1 (se)      | 0.0456     | 0.0457     | 0.0456     | 0.022%   | PASS
...
============================================================
```

### Comparison Thresholds

Apply these thresholds to determine PASS/FAIL:

| Statistic         | Threshold                 | Type              |
|-------------------|---------------------------|-------------------|
| Coefficients      | Relative difference < 0.1% | Relative         |
| Standard errors   | Relative difference < 0.5% | Relative         |
| R-squared         | Absolute difference < 0.001 | Absolute         |
| N (observations)  | Must match exactly         | Exact            |
| F-statistic       | Relative difference < 1%   | Relative         |
| KP F-statistic    | Relative difference < 1%   | Relative         |

### Relative Difference Formula

```
rel_diff = |val_a - val_b| / max(|val_a|, |val_b|) * 100
```

For values very close to zero (< 1e-6), use absolute difference instead.

## Step 6: Diagnose Discrepancies via Agent

If any comparison FAILS, use the Task tool to invoke the `cross-checker` agent for independent diagnosis. Provide it with:
- The Stata log file path and parsed statistics
- The Python output file path and parsed statistics
- The comparison table from Step 5 showing FAIL items
- The SE type, FE specification, and clustering used in both platforms

The agent will return a detailed diagnosis of each discrepancy with specific root causes and recommended fixes. Incorporate its findings into the diagnostic guidance below.

If any comparison FAILS, provide diagnostic guidance:

### Common Sources of Discrepancy

1. **Standard Error Type Mismatch**
   - Stata default: conventional OLS SE
   - Stata `robust`: HC1 (Eicker-Huber-White)
   - Stata `cluster`: CRV1 (Cluster-Robust Variance, small-sample corrected)
   - Python `pyfixest` default with `vcov="hetero"`: HC1
   - Python `pyfixest` with `vcov={"CRV1": "var"}`: matches Stata `cluster`
   - R `fixest` with `cluster = ~var`: CRV1 (matches Stata)
   - **Fix**: Ensure all use the same SE type.

2. **Degrees of Freedom Adjustment**
   - Stata applies small-sample correction by default for clustered SE
   - pyfixest CRV1 also applies small-sample correction (should match)
   - R fixest default: small-sample correction applied
   - Check: G/(G-1) * (N-1)/(N-k) adjustment where G = number of clusters

3. **Fixed Effects Handling**
   - Stata `reghdfe`: iterative demeaning via LSMR
   - pyfixest: same algorithm as `reghdfe` (iterative demeaning)
   - R `fixest`: C++ implementation of demeaning
   - **Fix**: Use `reghdfe` in Stata, `feols` in pyfixest and R fixest for consistency

4. **Floating Point Precision**
   - Minor differences (< 0.01%) are expected due to floating-point arithmetic
   - Different convergence criteria in iterative algorithms

5. **Sample Differences**
   - Missing value handling may differ
   - Stata drops observations with any missing value in the regression variables
   - Python may need explicit `dropna()` on the relevant columns
   - R `fixest` drops NAs by default
   - **Fix**: Check N first. If N differs, the samples are different.

6. **Singleton Fixed Effects**
   - `reghdfe` drops singleton groups by default
   - pyfixest also drops singletons by default
   - R `fixest` drops singletons by default (`fixef.rm = "singleton"`)
   - Check if singleton dropping behavior matches

7. **R-specific: `sunab()` vs Stata `csdid`**
   - R `fixest::sunab()` implements Sun-Abraham (2021) interaction-weighted estimator
   - Not directly comparable to `csdid` (Callaway-Sant'Anna)
   - Compare Sun-Abraham to `eventstudyinteract` in Stata instead

### Suggested Diagnostic Steps

If discrepancies exceed thresholds:

1. First check if N matches. If not, investigate sample construction.
2. If N matches but SEs differ, check SE type (robust/cluster/conventional).
3. If coefficients differ, check variable definitions and transformations.
4. Try running both with conventional (non-robust) SEs to isolate the source.
5. Check for collinear variables that may be dropped differently.
6. For IV: check whether first-stage coefficients match before comparing 2SLS.

## Step 7: Generate Report

Save the cross-validation report as a text file and optionally as a LaTeX table:

```
output/tables/tab_cross_check_<timestamp>.tex
output/logs/cross_check_report_<timestamp>.txt
```

Print the overall result:

```
Cross-Validation Result: PASS (all statistics within tolerance)
  Stata log:  output/logs/<stata_log>.log
  Python log: output/logs/<python_log>.log
  Compared:   <N> coefficients, <N> standard errors, R², N
```

or

```
Cross-Validation Result: FAIL
  - x1 standard error: relative difference 2.3% (threshold: 0.5%)
  - Possible cause: SE type mismatch (Stata uses cluster, Python uses robust)
  - Suggested fix: In pyfixest, change vcov to {"CRV1": "cluster_var"}
```

## Batch Cross-Validation Mode

When cross-validating an entire paper (multiple tables), run in batch mode:

```
Cross-Validation Summary
========================
Table 1 (Main Results):     PASS (max diff: 0.003%)
Table 2 (First Stage):      PASS (max diff: 0.012%)
Table 3 (Robustness):       PASS (max diff: 0.008%)
Table 4 (Heterogeneity):    FAIL (SE mismatch in col 3)
Table A1 (Balance):         PASS (max diff: 0.001%)
========================
Overall: 4/5 PASS, 1 FAIL
```
