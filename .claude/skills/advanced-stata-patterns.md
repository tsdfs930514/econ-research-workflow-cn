---
description: "Reference document for advanced Stata patterns from published replication packages"
user_invocable: false
---

# Advanced Stata Patterns from Published Papers

> **Reference document** — Claude should consult this when encountering advanced Stata patterns from published papers. This is not a standalone skill and should not be invoked directly.

These patterns were extracted from published replication packages (Acemoglu et al. 2019 JPE, and others) during code analysis. They cover advanced estimation techniques beyond standard FE/RE/GMM/IV pipelines.

---

## Panel Data Patterns

### Multi-way Clustering

Some papers cluster SEs on two dimensions (e.g., firm + time):
```stata
reghdfe Y X CONTROLS, absorb(UNIT TIME) vce(cluster CLUSTER1 CLUSTER2)
```

### Custom Ado Programs

Published replication packages often define custom programs (e.g., `program define vareffects`, `program define helm` for Helmert transformation). These must be included in the do-file before calling them. Common patterns:
- **Impulse response computation**: Iteratively computing cumulative effects via `nlcom` (Acemoglu et al. 2019)
- **Forward orthogonal deviations**: Custom Helmert transformation `h_var = w * (var - forward_mean)` where `w = sqrt(n/(n+1))`
- **Minimum distance estimator**: Year-by-year k-class estimation with bootstrapped SEs (HHK estimator)

### Dynamic Panel with Multiple Lags

When using `L(1/N).var` syntax for N > 1 lags:
- Always test joint significance of higher-order lags: `test l5.y l6.y l7.y l8.y`
- Compare models with 1, 2, 4, and 8 lags to check sensitivity of the main coefficient
- Report long-run effect: `shortrun / (1 - sum_of_lag_coefficients)`

### Impulse Response Functions via nlcom Chain (Acemoglu et al. 2019)

In dynamic panel models with lagged dependent variables (`y_t = a*y_{t-1} + ... + b*X_t + e_t`), the short-run effect is `b`, but the cumulative effect after `T` years propagates through the lag structure. Published papers compute these via chained `nlcom` calls.

**Pattern**: After estimation, rename coefficients, then iteratively compute cumulative effects:

```stata
* --- After FE or GMM estimation with 4 lags ---
* First: post the short-run coefficient and lag coefficients as named scalars
nlcom (shortrun: _b[dem]) ///
     (lag1: _b[L.y]) (lag2: _b[L2.y]) (lag3: _b[L3.y]) (lag4: _b[L4.y]), post

* Then call the vareffects program to compute cumulative effects
vareffects
estimates store e3_add   // stores: effect25, longrun, persistence
```

**Program `vareffects`** (define at top of do-file):
```stata
global limit = 25  // evaluate effects N years after transition

capture program drop vareffects
program define vareffects, eclass
* Recursion: effect_j = sum_{k=1}^{4} effect_{j-k} * lag_k + shortrun
* effect_1 = shortrun
* effect_2 = effect_1 * lag1 + shortrun
* effect_3 = effect_2 * lag1 + effect_1 * lag2 + shortrun
* effect_4 = effect_3 * lag1 + effect_2 * lag2 + effect_1 * lag3 + shortrun
* effect_j (j>=5) = effect_{j-1}*lag1 + effect_{j-2}*lag2 + effect_{j-3}*lag3 + effect_{j-4}*lag4 + shortrun

quietly: nlcom (effect1: _b[shortrun]) ///
      (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

quietly: nlcom (effect2: _b[effect1]*_b[lag1]+_b[shortrun]) ///
      (effect1: _b[effect1]) (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

quietly: nlcom (effect3: _b[effect2]*_b[lag1]+_b[effect1]*_b[lag2]+_b[shortrun]) ///
      (effect2: _b[effect2]) (effect1: _b[effect1]) (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

quietly: nlcom (effect4: _b[effect3]*_b[lag1]+_b[effect2]*_b[lag2]+_b[effect1]*_b[lag3]+_b[shortrun]) ///
      (effect3: _b[effect3]) (effect2: _b[effect2]) (effect1: _b[effect1]) ///
      (shortrun: _b[shortrun]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post

forvalues j=5(1)$limit {
    local j1=`j'-1
    local j2=`j'-2
    local j3=`j'-3
    local j4=`j'-4
    quietly: nlcom ///
        (effect`j': _b[effect`j1']*_b[lag1]+_b[effect`j2']*_b[lag2]+_b[effect`j3']*_b[lag3]+_b[effect`j4']*_b[lag4]+_b[shortrun]) ///
        (effect`j1': _b[effect`j1']) (effect`j2': _b[effect`j2']) ///
        (effect`j3': _b[effect`j3']) (shortrun: _b[shortrun]) ///
        (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post
}

* Final step: compute long-run effect and persistence
quietly: nlcom (effect$limit: _b[effect$limit]) ///
      (longrun: _b[shortrun]/(1-_b[lag1]-_b[lag2]-_b[lag3]-_b[lag4])) ///
      (shortrun: _b[shortrun]) ///
      (persistence: _b[lag1]+_b[lag2]+_b[lag3]+_b[lag4]) ///
      (lag1: _b[lag1]) (lag2: _b[lag2]) (lag3: _b[lag3]) (lag4: _b[lag4]), post
ereturn display
end
```

**Key outputs from `vareffects`**: `effect25` (cumulative 25-year effect), `longrun` (steady-state effect = shortrun / (1 - persistence)), `persistence` (sum of lag coefficients).

**Usage across estimators**: The same `vareffects` program is called after FE, GMM, IV, and HHK estimation — store separate `_add` estimates for each:
```stata
* FE
xtreg y l(1/4).y dem yy*, fe vce(cluster wbcode2)
estimates store e3
nlcom (shortrun: _b[dem]) (lag1: _b[L.y]) (lag2: _b[L2.y]) (lag3: _b[L3.y]) (lag4: _b[L4.y]), post
vareffects
estimates store e3_add

* GMM
xtabond2 y l(1/4).y dem yy*, gmmstyle(y, laglimits(2 .)) gmmstyle(dem, laglimits(1 .)) ///
    ivstyle(yy*, p) noleveleq robust nodiffsargan
estimates store e3gmm
nlcom (shortrun: _b[dem]) (lag1: _b[L.y]) (lag2: _b[L2.y]) (lag3: _b[L3.y]) (lag4: _b[L4.y]), post
vareffects
estimates store e3gmm_add
```

**For 8-lag models**: Define a separate `vareffects8` program that extends the recursion to 8 lags: `effect_j = sum_{k=1}^{8} effect_{j-k} * lag_k + shortrun`. The structure is identical but tracks 8 lag coefficients instead of 4.

### Helmert / Forward Orthogonal Deviations — Full Implementation

The Helmert transformation replaces first-differencing for removing fixed effects. Instead of `y_t - y_{t-1}`, it computes `w * (y_t - forward_mean_t)` where `forward_mean_t` is the mean of all future observations for that unit and `w = sqrt(n/(n+1))`. This preserves orthogonality of transformed errors (important for GMM validity).

**`xtabond2` built-in**: Use the `orthogonal` option:
```stata
xtabond2 y l(1/4).y dem yy*, ///
    gmmstyle(y, laglimits(2 .)) gmmstyle(dem, laglimits(1 .)) ///
    ivstyle(yy*, p) noleveleq robust orthogonal
```

**Custom `helm` program** (when you need Helmert-transformed data explicitly, e.g., for the HHK estimator):
```stata
capture program drop helm
program define helm
* Helmert transformation for a list of variables
* Requires variables named id and year in the dataset
* Usage: helm var1 var2 var3 ...
* Output: h_var1, h_var2, h_var3 ...
qui while "`1'"~="" {
    gsort id -year                      // sort years descending within unit
    tempvar one sum n m w
    gen `one' = 1 if `1' ~= .          // indicator for non-missing
    qui by id: gen `sum' = sum(`1') - `1'  // running sum excluding current
    qui by id: gen `n' = sum(`one') - 1    // count of future obs
    replace `n' = . if `n' <= 0         // last obs has no future values
    gen `m' = `sum' / `n'               // forward mean
    gen `w' = sqrt(`n' / (`n' + 1))     // Helmert weight
    capture gen h_`1' = `w' * (`1' - `m')  // transformed variable
    sort id year
    mac shift                           // move to next variable in list
}
end
```

**Usage in HHK estimator**: The `helm` program is called on residualized variables (after partialing out exogenous covariates):
```stata
* Partial out covariates, then Helmert-transform
quietly: gen id = panel_id
reg y_var covariates if tsample == 1
predict y_res if tsample == 1, resid
helm y_res
rename h_y_res h_y
```

### HHK Minimum Distance Estimator (Hahn-Hausman-Kuersteiner)

The HHK estimator is a bias-corrected panel estimator that runs year-by-year k-class IV regressions on Helmert-transformed data, then pools results using inverse-variance weighting. It addresses the Nickell bias problem without requiring GMM-style moment conditions.

**Algorithm**:
1. Partial out exogenous covariates from all variables (including instruments)
2. Apply Helmert transformation to residualized variables
3. Construct GMM-style lagged instruments (replacing missing with 0)
4. For each year `t`:
   a. Run `ivreg2` on Helmert-transformed data for that year only
   b. Compute k-class parameter: `lambda = 1 + e(sargandf) / e(N)`
   c. Re-run `ivreg2` with `k(lambda)` option
   d. Extract coefficients `b` and variance `V`
   e. Accumulate: `Num += N_t * inv(V) * b'`, `Den += N_t * inv(V)`
5. Pool: `b_HHK = inv(Den) * Num`, `V_HHK = inv(Den) * Num2 * inv(Den)`
6. Post results via `ereturn post b V`

### Interaction Heterogeneity with Percentile Centering

To test whether treatment effects vary by a characteristic (e.g., initial GDP), center the interaction at a reference percentile:

```stata
* Center interaction at 25th percentile of initial GDP
summarize gdp1960 if dem == 0, detail
gen inter = dem * (gdp1960 - r(p25))

* IV with interaction heterogeneity (both endogenous)
xtivreg2 y l(1/4).y ///
    (dem inter = l(1/4).demreg l(1/4).intereg) yy*, ///
    fe cluster(wbcode2) r partial(yy*)
```

**Interpretation**: The coefficient on `dem` is the effect at the 25th percentile of GDP. The coefficient on `inter` is the marginal effect of a 1-unit increase in initial GDP on the treatment effect. Centering at a percentile (rather than 0 or the mean) gives the `dem` coefficient a natural interpretation.

### Matrix Operations for Custom Estimators

Advanced Stata programs manipulate matrices directly for custom pooling:

```stata
* Initialize accumulator matrices
matrix def Num1 = J(k, 1, 0)     // k*1 zero vector (numerator for b)
matrix def Num2 = J(k, k, 0)     // k*k zero matrix (numerator for V)
matrix def Den1 = J(k, k, 0)     // k*k zero matrix (denominator)

* Accumulate across years
matrix b = e(b)
matrix V = e(V)
matrix Num1 = Num1 + N_t * inv(V) * b'
matrix Den1 = Den1 + N_t * inv(V)

* Pool results
matrix est = inv(Den1) * Num1
matrix var = inv(Den1) * Num2 * inv(Den1)
matrix b = est'
matrix V = var

* Name and post
mat colnames b = dem L.y L2.y L3.y L4.y
mat colnames V = dem L.y L2.y L3.y L4.y
mat rownames V = dem L.y L2.y L3.y L4.y
ereturn post b V, obs(N_total) depname("Dep var") esample(sample_indicator)
```

This pattern enables any custom estimator to "look like" a standard Stata estimation command, compatible with `eststo`, `esttab`, `nlcom`, etc.

---

## IV-Specific Patterns

### Panel IV with xtivreg2

When `ivreghdfe` is unavailable or you need panel-specific IV features, use `xtivreg2`:
```stata
* Panel IV with built-in FE (no need to generate dummies)
xtivreg2 Y CONTROLS (ENDOG = INSTRUMENTS) YEAR_DUMMIES, ///
    fe cluster(UNIT_VAR) r partial(YEAR_DUMMIES)
```
Key differences from `ivreghdfe`:
- `xtivreg2` has a native `fe` option for panel FE
- Use `partial()` to partial out high-dimensional controls (e.g., year dummies) for speed
- Reports `widstat` (KP F), `jp` (Hansen J p-value) directly
- Install via: `ssc install xtivreg2`

### Interaction Fixed Effects in absorb()

For models with interaction FE (e.g., year x municipality):
```stata
* ivreghdfe syntax
ivreghdfe Y CONTROLS (ENDOG = IV), absorb(FE1 FE2#FE3) cluster(CLUSTER)
* Example: absorb(market_c year#mun_c) for market FE + year*municipality FE

* reghdfe syntax (same pattern)
reghdfe Y CONTROLS, absorb(FE1 i.FE2#i.FE3) vce(cluster CLUSTER)
```

### Shift-Share / Bartik IV

When the instrument is a shift-share (Bartik) construct:
1. Report the effective F-statistic (Montiel Olea-Pflueger) instead of just KP F
2. Consider Adao, Kolesar, Morales (2019) exposure-robust standard errors:
   ```stata
   * Two-way clustering on sector + region for shift-share SEs
   reghdfe Y TREAT CONTROLS, absorb(FE) vce(cluster SECTOR REGION)
   ```
3. Report the Rotemberg weights decomposition to assess which sectors/shocks drive identification

### savefirst Option

To store and inspect first-stage estimates:
```stata
* ivreghdfe
ivreghdfe Y CONTROLS (ENDOG = IV), absorb(FE) cluster(CLUSTER) first savefirst
* Saved estimates accessible via: estimates restore _ivreghdfe_ENDOG

* ivreg2
ivreg2 Y CONTROLS (ENDOG = IV), cluster(CLUSTER) first ffirst savefirst
```

### Multiple Endogenous Variables

When instrumenting multiple endogenous variables (e.g., democracy + spatial lag):
```stata
xtivreg2 Y CONTROLS (ENDOG1 ENDOG2 = IV1 IV2 IV3 IV4), ///
    fe cluster(UNIT) r partial(YEAR_DUMMIES)
```
Requires # instruments >= # endogenous variables.

### Multiple Endogenous with Interaction Terms

When both a treatment and its interaction with a moderator are endogenous, instrument both using the corresponding interacted instruments:
```stata
* Construct instrument interaction (same moderator variable)
gen inter = dem * (gdp1960 - reference_value)
gen intereg = demreg * (gdp1960 - reference_value)

* IV: instrument (dem, inter) with lags of (demreg, intereg)
xtivreg2 y l(1/4).y ///
    (dem inter = l(1/4).demreg l(1/4).intereg) yy*, ///
    fe cluster(wbcode2) r partial(yy*)
```

For spatial lags as additional endogenous variables:
```stata
* Two endogenous: democracy + spatial lag of GDP
xtivreg2 y l(1/4).y (dem y_w = l(1/4).instrument l(1/4).y_w) yy*, ///
    fe cluster(wbcode2) r partial(yy*)

* Four endogenous: democracy + spatial lags of GDP and democracy
xtivreg2 y l(1/4).y ///
    (dem l(0/4).y_w dem_w = l(1/4).instrument l(1/5).y_w l(1/4).dem_w) yy*, ///
    fe cluster(wbcode2) r partial(yy*)
```

---

## Shared Patterns (Panel + IV)

### k-Class Estimation via ivreg2

The k-class estimator nests OLS (k=0), 2SLS (k=1), LIML (k=lambda_min), and the bias-corrected Fuller estimator. The HHK minimum distance estimator uses `k = 1 + (degree_of_overid / N)`:

```stata
* First pass: get degree of overidentification
ivreg2 h_y (h_x = instruments) if year == 2000, noid noconstant
local lambda = 1 + e(sargandf) / e(N)

* Second pass: k-class estimator
ivreg2 h_y (h_x = instruments) if year == 2000, ///
    k(`lambda') nocollin coviv noid noconstant
```

**Key ivreg2 k-class options**:
- `k(scalar)`: the k parameter value
- `nocollin`: skip collinearity check (speed)
- `coviv`: use IV-style variance estimator
- `noid`: suppress underidentification test
- `noconstant`: omit constant (e.g., when data is Helmert-transformed)

### Spatial Lags via spmat

For constructing spatially-lagged variables as instruments or controls:
```stata
cap ssc install spmat
cap ssc install spmack

* Construct inverse-distance spatial weight matrix (year by year)
forvalues j = 1960(1)2010 {
    preserve
    keep if year == `j'
    keep if cen_lon != . & cen_lat != . & y != . & dem != .
    keep wbcode2 cen_lon cen_lat y dem year
    sort wbcode2

    * Create spatial weight matrix from coordinates
    spmat idistance dmat cen_lon cen_lat, id(wbcode2) dfunction(dhaversine) norm(row) replace

    * Compute spatial lags
    spmat lag y_w dmat y        // spatially-lagged GDP
    spmat lag dem_w dmat dem    // spatially-lagged democracy

    keep y_w dem_w wbcode2 year
    tempfile m
    save `m', replace
    restore
    merge 1:1 wbcode2 year using `m', update
    drop _m
}
```

### Bootstrap Inference with Panel Structure

For IV or custom estimators where analytical SEs are complex, use cluster bootstrap:

```stata
* Generate bootstrap panel ID variable
gen newcl = wbcode2
tsset newcl year

* Bootstrap the entire estimation procedure
bootstrap _b, seed(12345) reps(100) cluster(wbcode2) idcluster(newcl): ///
    custom_estimator y (dem L1.y L2.y L3.y L4.y) (y dem) (demreg) (yy*)

estimates store e_boot
```

**Critical bootstrap options for panel data**:
- `cluster(panelvar)`: resample entire panels (preserving within-unit time series)
- `idcluster(newvar)`: required for panel bootstrap — creates new sequential IDs for each bootstrap draw (because resampling with replacement duplicates panel IDs)
- `reps(N)`: 100 for exploration, 500-1000 for publication
- `seed(N)`: always set for reproducibility

**HHK-specific bootstrap**:
```stata
gen newcl = wbcode2
tsset newcl year

bootstrap _b, seed(12345) reps(100) cluster(wbcode2) idcluster(newcl): ///
    hhkBS y (dem L1.y L2.y L3.y L4.y) (y dem) (demreg) (yy*), ///
    ydeep(1960) ystart(1964) yfinal(2009) truncate(4)
estimates store e3md
```

**`hhkBS` program arguments** (parenthesized groups):
```
hhkBS yvar (sequentially_exogenous) (gmm_instruments) (gmm_truncated) (exogenous_covariates), options
```
- Group 1 `(dem L1.y ... L4.y)`: sequentially exogenous regressors (treatment + lagged DV)
- Group 2 `(y dem)`: variables used as GMM-style instruments (levels lagged by 2+)
- Group 3 `(demreg)`: truncated GMM instruments (lagged up to `truncate` periods)
- Group 4 `(yy*)`: exogenous covariates (partialed out before transformation)

After bootstrap, use `nlcom` to derive impulse response functions from the bootstrapped coefficients (standard errors will propagate through the delta method correctly).

### Consistent Sample Pattern: `gen samp = e(sample)`

Ensure consistent samples across specifications by saving estimation samples:

```stata
* Specification 1 -- save its sample indicator
xtivreg2 y l(1/4).y (dem = l.instrument) yy*, fe cluster(wbcode2) r partial(yy*)
gen samp1 = e(sample)

* Specification 2 -- save its sample
xtivreg2 y l(1/4).y (dem = l(1/4).instrument) yy*, fe cluster(wbcode2) r partial(yy*)
gen samp2 = e(sample)

* First stage for spec 1 -- restrict to same sample
xtreg dem l(1/4).y l.instrument yy* if samp1 == 1, fe cluster(wbcode2)
```

This is essential when different instrument sets create different estimation samples (different lags -> different missing patterns). Always report first-stage results on the exact sample used for 2SLS. Use `gen sampN = e(sample)` after each specification when samples may differ.

---

## SDID Results Capture via Local Macros (Issue #24)

The `sdid` command (Clarke et al. 2023) stores results in `e(ATT)` and `e(se)`, but these are NOT compatible with `ereturn post` + `estimates store`. The `ereturn post b V` pattern clears the e-class environment and fails with r(301). Instead, capture results immediately into local macros after `sdid` succeeds:

```stata
* Initialize result locals
local sdid_att = .
local sdid_se  = .
local sdid_ok  = 0

* Run SDID with bootstrap VCE (jackknife fails on staggered treatment, Issue #25)
cap noisily sdid Y unit time treat, vce(bootstrap) method(sdid) seed(12345) reps(200)

* Capture results IMMEDIATELY after successful run (before any ereturn/estimates command)
if _rc == 0 {
    local sdid_att = e(ATT)
    local sdid_se  = e(se)
    local sdid_N   = e(N)
    local sdid_ok  = 1
}

* Repeat for DID and SC methods
cap noisily sdid Y unit time treat, vce(bootstrap) method(did) seed(12345) reps(200)
if _rc == 0 {
    local did_att = e(ATT)
    local did_se  = e(se)
    local did_ok  = 1
}

* Build LaTeX table from locals (NOT from estimates store)
file open _tab using "output/tables/tab_sdid.tex", write replace
file write _tab "\begin{tabular}{lccc}" _n
file write _tab " & SDID & DID & SC \\\\" _n
if `sdid_ok' {
    file write _tab "ATT & " %9.4f (`sdid_att') " & ... \\\\" _n
}
file close _tab
```

**Key rules for SDID:**
1. Always use `cap noisily` around `sdid` calls
2. Capture `e(ATT)` and `e(se)` into locals BEFORE any other command
3. Never use `ereturn post` or `estimates store` after `sdid`
4. Build tables via `file write` using local macros
5. Use `vce(bootstrap)` as default; `vce(jackknife)` requires >= 2 treated units per period
