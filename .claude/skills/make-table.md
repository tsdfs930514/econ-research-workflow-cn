---
description: "Generate publication-quality LaTeX regression tables"
user_invocable: true
---

# /make-table - Generate Publication-Quality LaTeX Tables

When the user invokes `/make-table`, follow these steps:

## Step 1: Gather Information

Ask the user for:

1. **Source data** (required) - One of:
   - Stata estimates (stored via `eststo`) or a .log file path
   - Python regression output (pyfixest summary or saved results)
   - Raw data to be formatted (e.g., a CSV of coefficients)
2. **Table type** (required) - One of:
   - `main` - Main regression results table
   - `first_stage` - First stage IV regression table
   - `robustness` - Robustness summary table
   - `descriptive` - Descriptive statistics table
   - `balance` - Balance / summary statistics by group table
   - `event_study` - Event study coefficients table
   - `comparison` - Multi-estimator comparison (e.g., CS-DiD vs TWFE vs BJS)
3. **Target journal language** (required) - `CN` (Chinese) or `EN` (English)
4. **Target journal style** (optional) - e.g., "经济研究", "管理世界", "AER", "QJE"
5. **Additional options** (optional):
   - Number of panels (Panel A, Panel B, etc.)
   - Column group headers
   - Whether to include dependent variable mean
   - Whether to include 95% CIs (in brackets, third row)
   - Custom notes

## Step 2: Parse Source Data

### From Stata .log file
Parse the regression output tables from the log file, extracting:
- Variable names and labels
- Coefficients with significance stars
- Standard errors (in parentheses)
- Number of observations
- R-squared (and adjusted/within R-squared)
- Fixed effects indicators
- F-statistics (first-stage F, KP F)
- Number of clusters

### From Python output
Parse pyfixest `.summary()` output or extract from model objects:
- Coefficients, standard errors, p-values
- Model fit statistics
- Add significance stars based on p-values: *** p<0.01, ** p<0.05, * p<0.10

## Step 3: Generate LaTeX Table

### Chinese Journal Format (三线表 / Three-Line Table)

For Chinese journals like 经济研究 (Economic Research Journal) or 管理世界 (Management World):

```latex
\begin{table}[htbp]
\centering
\caption{<表格标题>}
\label{tab:<label>}
\begin{threeparttable}
\begin{tabular}{l<column alignment specs>}
\toprule
 & \multicolumn{<n>}{c}{<列组标题>} \\
 \cmidrule(lr){<start>-<end>}
 & (1) & (2) & (3) & (4) \\
 & <因变量1> & <因变量2> & <因变量3> & <因变量4> \\
\midrule
% Panel A: <面板标题> (if multiple panels)
\multicolumn{<n>}{l}{\textit{Panel A: <面板标题>}} \\[3pt]
<核心解释变量> & <coef>*** & <coef>** & <coef>*** & <coef>* \\
 & (<se>) & (<se>) & (<se>) & (<se>) \\[3pt]
<控制变量1> & <coef> & <coef> & <coef> & <coef> \\
 & (<se>) & (<se>) & (<se>) & (<se>) \\
\midrule
% Footer rows
控制变量 & 是 & 是 & 是 & 是 \\
个体固定效应 & 是 & 是 & 是 & 是 \\
时间固定效应 & 否 & 是 & 是 & 是 \\
因变量均值 & <mean> & <mean> & <mean> & <mean> \\
观测值 & <N> & <N> & <N> & <N> \\
R$^2$ & <r2> & <r2> & <r2> & <r2> \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\small
\item 注：括号内为聚类稳健标准误。***、**、*分别表示在1\%、5\%、10\%水平上显著。
<附加注释>
\end{tablenotes}
\end{threeparttable}
\end{table}
```

Key formatting rules for Chinese journals:
- Use `\toprule`, `\midrule`, `\bottomrule` (三线表 format, requires `booktabs` package)
- Column headers in Chinese
- "是/否" for Yes/No indicators
- Fixed effects rows: 个体固定效应, 时间固定效应, 行业固定效应, etc.
- Controls row: 控制变量
- Observations: 观测值
- Notes in Chinese with standard significance disclaimer
- Use `threeparttable` for proper note alignment
- Numbers formatted with commas for thousands: 10,000

### English Journal Format (AER/QJE Style)

For English journals like AER, QJE, Econometrica:

```latex
\begin{table}[htbp]
\centering
\caption{<Table Title>}
\label{tab:<label>}
\begin{threeparttable}
\begin{tabular}{l<column alignment specs>}
\toprule\toprule
 & \multicolumn{<n>}{c}{<Column Group Header>} \\
 \cmidrule(lr){<start>-<end>}
 & (1) & (2) & (3) & (4) \\
 & <Dep Var 1> & <Dep Var 2> & <Dep Var 3> & <Dep Var 4> \\
\midrule
% Panel A: <Panel Title> (if multiple panels)
\multicolumn{<n>}{l}{\textit{Panel A: <Panel Title>}} \\[5pt]
<Key Variable> & <coef>$^{***}$ & <coef>$^{**}$ & <coef>$^{***}$ & <coef>$^{*}$ \\
 & (<se>) & (<se>) & (<se>) & (<se>) \\
 & [<ci_lo>, <ci_hi>] & [<ci_lo>, <ci_hi>] & [<ci_lo>, <ci_hi>] & [<ci_lo>, <ci_hi>] \\[3pt]
\midrule\midrule
% Panel B: <Panel Title> (if applicable)
\multicolumn{<n>}{l}{\textit{Panel B: <Panel Title>}} \\[5pt]
...
\midrule
% Footer rows
Controls & Yes & Yes & Yes & Yes \\
Entity FE & \checkmark & \checkmark & \checkmark & \checkmark \\
Time FE &  & \checkmark & \checkmark & \checkmark \\
Dep.\ var.\ mean & <mean> & <mean> & <mean> & <mean> \\
Observations & <N> & <N> & <N> & <N> \\
$R^2$ & <r2> & <r2> & <r2> & <r2> \\
\bottomrule\bottomrule
\end{tabular}
\begin{figurenotes}
<Notes text>. Standard errors clustered at <cluster var> level in parentheses.
95\% confidence intervals in brackets. *** p$<$0.01, ** p$<$0.05, * p$<$0.10.
\end{figurenotes}
\end{threeparttable}
\end{table}
```

Key formatting rules for English TOP5 journals:
- AER style: clean, minimal formatting, double `\toprule\toprule` and `\bottomrule\bottomrule`
- Use `booktabs` package (no vertical lines)
- Significance stars as superscripts: $^{***}$, $^{**}$, $^{*}$
- Checkmarks (`\checkmark`) for FE indicators (preferred over "Yes/No" in AER)
- 95% CIs in brackets on third row when space permits
- `\begin{figurenotes}` environment for notes (AER house style)
- Panel A/B separated by `\midrule\midrule`
- Numbers with commas: 10,000
- Column alignment: typically `c` for all result columns
- 4 decimal places for coefficients (matching APE/TOP5 standard)

### Stata `esttab` Command Template (AER Style)

For generating tables directly from Stata stored estimates:

```stata
esttab m1 m2 m3 m4 m5 using "output/tables/tab_<name>.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    mtitles("OLS" "2SLS" "LIML" "CS-DiD" "Alt.") ///
    keep(<key variable>) ///
    scalars("widstat KP F-stat" "N_clust Clusters" ///
            "r2_within Within R$^2$") ///
    addnotes("Standard errors clustered at <cluster var> level in parentheses." ///
             "Instrument(s): <instruments>." ///
             "*** p$<$0.01, ** p$<$0.05, * p$<$0.10.") ///
    title("Effect of <Treatment> on <Outcome>") ///
    substitute(\_ _)
```

## Step 4: Table Type-Specific Formatting

### Main Regression Table (`main`)
- Show key independent variables with coefficients and SEs
- Include control variable indicators (not coefficients)
- Show FE indicators, N, R², cluster count
- Show dependent variable mean
- Panel A/B format if multiple outcome families

### First Stage Table (`first_stage`)

Following APE 0185 tab3 format:

```stata
esttab fs_main using "output/tables/tab_first_stage.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(<instrument(s)>) label booktabs replace ///
    scalars("r2_within Within R$^2$" "N Observations") ///
    addnotes("F-statistic on excluded instrument(s): <F>" ///
             "Dependent variable: <endogenous var>") ///
    title("First Stage: <Instrument> $\rightarrow$ <Endogenous Var>")
```

Key first-stage table elements:
- Instrument coefficients prominently displayed
- F-statistic on excluded instruments in footer row
- KP rk Wald F-statistic for heteroskedastic/clustered errors
- Stock-Yogo (2005) / Lee et al. (2022) critical values in notes
- Partial R-squared of excluded instruments

### Robustness Summary Table (`robustness`)
- One column per robustness specification
- Show only the key treatment coefficient
- Compact format with many columns
- Group columns by robustness type with `\cmidrule`
- Column headers: brief specification descriptions

### Descriptive Statistics Table (`descriptive`)
- Rows: variables
- Columns: N, Mean, SD, Min, P25, Median, P75, Max
- No significance stars
- Clean number formatting

### Balance Table (`balance`)
- Rows: variables
- Columns: Group 1 Mean, Group 2 Mean, Difference, t-stat or p-value
- Stars on the difference column
- Show N per group

### Multi-Estimator Comparison Table (`comparison`)

Following APE 0119 tab2 format:

```latex
\toprule\toprule
 & (1) & (2) & (3) & (4) & (5) \\
 & CS-DiD & TWFE & CS-DiD NYT & BJS & Sun-Abraham \\
\midrule
Treatment & <coef> & <coef> & <coef> & <coef> & <coef> \\
 & (<se>) & (<se>) & (<se>) & (<se>) & (<se>) \\
 & [<ci_lo>, <ci_hi>] & ... \\[5pt]
\midrule
Estimator & CS-DiD & TWFE & CS-DiD & BJS & SA \\
Control Group & Never-treated & All & Not-yet-treated & Never-treated & Never-treated \\
Controls & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
Unit FE & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
Time FE & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
Observations & <N> & <N> & <N> & <N> & <N> \\
\bottomrule\bottomrule
```

## Step 5: Number Formatting

Apply consistent formatting:
- Coefficients: 4 decimal places (TOP5 standard for causal inference)
- Standard errors: 4 decimal places (same as coefficients)
- R-squared: 3 decimal places
- Observations: integer with comma separators
- Percentages: 1-2 decimal places
- Large coefficients (>100): 2 decimal places
- Small coefficients (<0.001): scientific notation or more decimal places
- F-statistics: 2 decimal places

## Nested LaTeX Tables via `\input{}` (Multi-Panel Published Paper Pattern)

Published papers often construct complex tables by nesting separate `.tex` files. The main table contains the core regression output, while a subsidiary `_Add.tex` file contains derived statistics (impulse responses, long-run effects) that are `\input{}`-ed into the main table's footer.

### Pattern: Main table + Add table

**Main table** (`TableMain.tex`) — generated by `estout`:
```stata
#delimit ;
estout e1 e2 e3 e4 e1gmm e2gmm e3gmm e4gmm e1md e2md e3md e4md
    using "${project}/results/TableMain.tex", style(tex)
    varlabels(L.y "log GDP first lag" L2.y "log GDP second lag"
              L3.y "log GDP third lag" L4.y "log GDP fourth lag"
              dem "Democracy")
    cells(b(star fmt(%9.3f)) se(par))
    stats(ar2p N N_g,
        fmt(%7.2f %7.0f %7.0f)
        labels("\input{results/TableMain_Add} AR2 test p-value"
               "Observations" "Countries in sample"))
    keep(L.y L2.y L3.y L4.y dem)
    order(dem L.y L2.y L3.y L4.y)
    stardrop(dem L.y L2.y L3.y L4.y)
    nolabel replace mlabels(none) collabels(none);
#delimit cr
```

**Add table** (`TableMain_Add.tex`) — impulse response results:
```stata
#delimit ;
estout e1_add e2_add e3_add e4_add e1gmm_add e2gmm_add e3gmm_add e4gmm_add
       e1md_add e2md_add e3md_add e4md_add
    using "${project}/results/TableMain_Add.tex", style(tex)
    varlabels(longrun "Long-run effect of democracy"
              effect${limit} "Effect of democracy after ${limit} years"
              persistence "Persistence of GDP process")
    cells(b(star fmt(%9.3f)) se(par))
    keep(longrun effect${limit} persistence)
    order(longrun effect${limit} persistence)
    stardrop(longrun effect${limit} persistence)
    nolabel replace mlabels(none) collabels(none);
#delimit cr
```

**How it works**: The `\input{results/TableMain_Add}` appears inside the `labels()` of the `stats()` option. When LaTeX compiles, it inserts the subsidiary table rows inline. This separates the core regression output from the derived statistics, making each component independently updatable.

### `#delimit ;` for Complex estout Commands

Long `estout` commands with many options are difficult to read with `///` continuation. Published Stata code uses `#delimit ;` to switch the line delimiter from newline to semicolon:

```stata
#delimit ;
estout m1 m2 m3 m4 m5 m6 m7 m8 m9
    using "output/tables/table.tex", style(tex)
    varlabels(dem "Democracy")
    cells(b(star fmt(%9.3f)) se(par))
    stats(jp N N_g widstat,
        fmt(%7.2f %7.0f %7.0f %7.1f)
        labels("\input{results/Table_Add} Hansen p-value"
               "Observations" "Countries in sample"
               "Exc. Instruments F-stat."))
    keep(dem) order(dem) stardrop(dem)
    nolabel replace mlabels(none) collabels(none);
#delimit cr
```

**Important**: Always end with `#delimit cr` to restore normal newline-delimited mode.

### `stardrop()` Option

The `stardrop()` option in `estout` removes significance stars from specified variables and instead attaches them only to the coefficient (not the standard error row). This gives cleaner output when stars should appear next to the point estimate:

```stata
estout m1 m2 m3, cells(b(star fmt(3)) se(par)) ///
    stardrop(dem L.y L2.y) keep(dem L.y L2.y)
```

### Multi-Estimator Table Layout (FE / GMM / HHK side-by-side)

For papers comparing multiple estimators with multiple lag specifications:

| Columns | FE (1-lag) | FE (2-lag) | FE (4-lag) | FE (8-lag) | GMM (1) | GMM (2) | GMM (4) | GMM (8) | HHK (1) | HHK (2) | HHK (4) | HHK (8) |
|---------|------------|------------|------------|------------|---------|---------|---------|---------|---------|---------|---------|---------|

This requires 12 stored estimates. Use `estout` with all 12 in order, and the LaTeX table header (constructed manually) groups them with `\multicolumn{4}{c}{Within Estimator}` etc.

### Auxiliary p-value File Pattern

Some statistics (e.g., p-values from `test` commands) cannot be stored in `e()` scalars. Write them to a separate `.tex` file:

```stata
file open myfile using "${project}/results/TableMain_lags.tex", write replace
file write myfile "p-value lags 5 to 8"

* After each model:
xtreg y l(1/8).y dem yy*, fe vce(cluster wbcode2)
test l5.y l6.y l7.y l8.y
file write myfile " &&&& [" %7.3f (r(p)) "] "

* Close when done
file write myfile "\\"
file close myfile
```

Then `\input{results/TableMain_lags}` in the main table to include these p-values.

## Step 6: Save Output

Save the generated .tex file:

```
output/tables/tab_<table_type>_<description>.tex
```

Print confirmation:

```
Table generated successfully!

Output: output/tables/tab_<name>.tex
Format: <CN 三线表 / EN AER-style>
Columns: <N>
Panels: <N or "None">

To include in your paper:
  \input{../output/tables/tab_<name>}

Required LaTeX packages:
  \usepackage{booktabs}
  \usepackage{threeparttable}
  \usepackage{multirow}    % if using multirow headers
  \usepackage{amssymb}     % for \checkmark
```
