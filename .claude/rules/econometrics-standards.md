---
paths:
  - "**/code/**"
  - "**/output/**"
---

# Econometrics Standards

These standards govern all empirical analysis in this project. Every regression, test, and output must comply.

---

## Difference-in-Differences (DID) Standards

1. **Parallel trends assumption**: Check BEFORE estimation. Plot pre-treatment trends for treatment and control groups.
2. **Event study plot**: Report event study with pre-treatment coefficients. All pre-treatment coefficients should be statistically insignificant and close to zero.
3. **Joint pre-trend test**: Conduct formal joint F-test on all pre-treatment leads. Report F-statistic and p-value in figure notes.
4. **Heterogeneous treatment effects**: Test using robust DID estimators:
   - `csdid` (Callaway & Sant'Anna, 2021) for group-time average treatment effects
   - `did_multiplegt` (de Chaisemartin & D'Haultfoeuille, 2020) for heterogeneity-robust estimation
   - `did_imputation` (Borusyak, Jaravel & Spiess, 2024) for imputation-based estimation
   - `eventstudyinteract` (Sun & Abraham, 2021) for interaction-weighted event study
5. **TWFE and robust estimators**: Report BOTH traditional TWFE and at least one robust DID estimator. Discuss discrepancies.
6. **Goodman-Bacon decomposition**: Run `bacondecomp` to diagnose TWFE bias from heterogeneous treatment effects.
7. **Staggered adoption**: If treatment timing varies across units, explicitly discuss staggered adoption and use appropriate estimators (never rely solely on TWFE).
8. **HonestDiD sensitivity**: Apply Rambachan-Roth sensitivity analysis to test how much parallel trends violations could affect results.

---

## Synthetic Difference-in-Differences (SDID) Standards

1. **When to use**: Preferred when few treated units, many control units, and parallel trends are questionable.
2. **Comparison table**: Report SDID alongside traditional DiD and pure Synthetic Control in a comparison table.
3. **Unit weights**: Analyze whether weights are concentrated on a few control units (fragility concern) or diffuse.
4. **Time weights**: Check if time weights emphasize pre-treatment periods close to treatment onset (expected).
5. **Inference**: Report jackknife standard errors, bootstrap standard errors, and placebo p-values. Note if they disagree.
6. **Leave-one-unit-out**: Check sensitivity when individual control units are dropped.

---

## Instrumental Variables / 2SLS Standards

1. **First stage**: Report the first stage regression separately in a dedicated table.
2. **First stage F-statistic**: Must exceed 10 (rule of thumb).
3. **Lee et al. (2022) tF**: Prefer F > 23 when using tF critical values for weak instrument testing.
4. **Kleibergen-Paap rk Wald F-statistic**: Report for non-i.i.d. errors (heteroskedasticity or clustering).
5. **Partial R-squared**: Report partial R-squared of excluded instruments in first stage table.
6. **Overidentification test**: Report Hansen J-statistic if the number of instruments exceeds the number of endogenous variables. Discuss implications of rejection.
7. **Exclusion restriction**: Provide a narrative discussion of instrument validity. Explain why the instrument affects the outcome ONLY through the endogenous variable.
8. **Weak instrument robust inference**: Consider Anderson-Rubin (AR) test for inference robust to weak instruments, especially when F-stat is marginal (10-23).
9. **LIML comparison**: Report LIML estimate alongside 2SLS. Large divergence indicates weak instrument concern.
10. **Leave-one-state/group-out (LOSO)**: Check if any single cluster is driving the result.
11. **Oster bounds**: Report Oster (2019) delta to assess selection on unobservables.

---

## Regression Discontinuity Design (RDD) Standards

1. **Optimal bandwidth**: Report MSE-optimal (`bwselect(mserd)`) and CER-optimal (`bwselect(cerrd)`) bandwidths.
2. **Bandwidth sensitivity**: Show results for at least 6 bandwidths: 0.5x, 0.75x, 1x, 1.25x, 1.5x, and 2x the optimal bandwidth.
3. **Polynomial order**: Test p=1, 2, and 3. Local linear (p=1) is default. Report sensitivity to higher-order polynomials.
4. **Kernel sensitivity**: Report results with triangular (default), uniform, and Epanechnikov kernels.
5. **Manipulation test**: Cattaneo-Jansson-Ma (CJM, 2020) density test for sorting at the cutoff. Report p-value and discuss implications.
6. **Placebo cutoff tests**: Test at alternative (fake) thresholds where no effect should exist (e.g., 25th and 75th percentiles).
7. **Covariate balance**: Test for balance of predetermined covariates at the cutoff using `rdrobust` on each covariate.
8. **RD plot**: Provide binned scatter plot with fitted polynomial on each side of the cutoff using `rdplot`.
9. **Donut hole RDD**: Exclude observations very close to cutoff (e.g., ±0.5, ±1, ±2 units) to test for manipulation.
10. **With and without covariates**: Report main specification with and without covariates for precision.

---

## Panel Data Standards

1. **Hausman test**: Conduct Hausman test to justify FE vs RE. Report test statistic and p-value.
2. **Serial correlation**: Test using Wooldridge (2002) test for autocorrelation in panel data (`xtserial` in Stata).
3. **Cross-sectional dependence**: Test using Pesaran (2004) CD test if T is large relative to N. Consider Driscoll-Kraay standard errors if CD test rejects.
4. **Within R-squared**: Report within R-squared for FE models (not overall R-squared).
5. **Dynamic panels**: If a lagged dependent variable is included, consider system GMM (Blundell-Bond) or difference GMM (Arellano-Bond). Report AR(1) and AR(2) tests and Hansen J test.
6. **Clustering**: Cluster standard errors at the appropriate level (firm, industry, state). Justify the clustering level. When in doubt, cluster at the higher level.
7. **Wild cluster bootstrap**: Use when number of clusters < 50 (Roodman et al.).

---

## Universal Standards (Apply to ALL Regressions)

### Standard Errors
- Cluster standard errors by default. Always specify the clustering variable.
- Report the number of clusters in table notes.
- Use heteroskedasticity-robust SEs only when clustering is not appropriate (rare).

### Multiple Hypothesis Testing
- When testing multiple hypotheses (e.g., multiple outcomes), consider Bonferroni or FDR corrections.
- Report both uncorrected and corrected p-values when applying multiple testing corrections.

### Coefficient Formatting
- Coefficients: 4 decimal places (TOP5 standard for causal inference)
- Standard errors: 4 decimal places, in parentheses below coefficients
- Stars: `*** p<0.01`, `** p<0.05`, `* p<0.10`

### Required Table Statistics
Every regression table MUST report:
- N (number of observations)
- R-squared (within R-squared for FE models)
- Number of clusters or groups
- Mean of dependent variable (in table notes or footer)
- First-stage F-statistic (for IV tables)
- Control variable indicator row
- Fixed effects indicator rows

### Stata Example
```stata
esttab m1 m2 m3 using "output/tables/main_results.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    scalars("N_clust Number of clusters" "r2_within Within R²") ///
    addnotes("Standard errors clustered at firm level in parentheses." ///
             "Mean of dep. var: X.XXXX." ///
             "*** p<0.01, ** p<0.05, * p<0.10.") ///
    label booktabs replace
```

---

## Method-Specific Required Packages

### DID
```stata
ssc install reghdfe
ssc install csdid
ssc install did_multiplegt
ssc install did_imputation
ssc install bacondecomp
ssc install eventstudyinteract
ssc install honestdid
ssc install boottest
```

### SDID
```stata
ssc install sdid
ssc install reghdfe
```

### IV
```stata
ssc install reghdfe
ssc install ivreghdfe
ssc install ivreg2
ssc install ranktest
ssc install weakiv
ssc install boottest
ssc install psacalc
```

### RDD
```stata
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace
net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace
net install rdlocrand, from(https://raw.githubusercontent.com/rdpackages/rdlocrand/master/stata) replace
net install rdmulti, from(https://raw.githubusercontent.com/rdpackages/rdmulti/master/stata) replace
```

### Panel
```stata
ssc install reghdfe
ssc install xtabond2
ssc install xtscc
ssc install xtserial
```
