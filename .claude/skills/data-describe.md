---
description: "Generate descriptive statistics and variable distributions using Stata and Python"
user_invocable: true
---

# /data-describe - Generate Descriptive Statistics

When the user invokes `/data-describe`, follow these steps:

## Step 1: Gather Information

Ask the user for:

1. **Dataset path** (required) - Path to the data file (.dta, .csv, or other format)
2. **Key variables** (required) - List of variables to describe (comma-separated)
3. **Grouping variable** (optional) - Variable for subgroup analysis / balance table (e.g., treatment indicator)
4. **Output directory** (optional) - Where to save results (default: `output/tables/` and `output/figures/`)

## Step 2: Generate Stata .do File

Create a Stata .do file (e.g., `code/stata/00_descriptive_stats.do`) that does the following:

```stata
/*==============================================================================
  Descriptive Statistics
  Dataset: <dataset path>
  Generated: <current date>
==============================================================================*/

clear all
set more off
cap log close

log using "output/logs/descriptive_stats.log", replace

* --- Load Data ---
use "<dataset path>", clear

* --- Summary Statistics ---
* Produce: N, Mean, SD, Min, P25, P50, P75, Max for each key variable
estpost summarize <key variables>, detail
esttab using "output/tables/tab_summary_stats.tex", ///
    cells("count mean(fmt(3)) sd(fmt(3)) min(fmt(3)) p25(fmt(3)) p50(fmt(3)) p75(fmt(3)) max(fmt(3))") ///
    label nomtitle nonumber replace booktabs ///
    title("Summary Statistics")

* --- Correlation Matrix ---
correlate <key variables>
* Export correlation matrix to LaTeX
estpost correlate <key variables>, matrix
esttab using "output/tables/tab_correlation.tex", ///
    unstack not noobs compress label replace booktabs ///
    title("Correlation Matrix")

* --- Distribution Histograms ---
foreach var of varlist <key variables> {
    histogram `var', ///
        frequency normal ///
        title("Distribution of `var'") ///
        scheme(s2color)
    graph export "output/figures/fig_dist_`var'.pdf", replace
}
```

If a **grouping variable** is provided, also add:

```stata
* --- Balance Table ---
* Compare means across groups
estpost ttest <key variables>, by(<grouping variable>)
esttab using "output/tables/tab_balance.tex", ///
    cells("mu_1(fmt(3)) mu_2(fmt(3)) b(fmt(3) star)") ///
    label nomtitle nonumber replace booktabs ///
    collabels("Control Mean" "Treatment Mean" "Difference") ///
    title("Balance Table") ///
    addnotes("* p<0.10, ** p<0.05, *** p<0.01")
```

End with:

```stata
log close
```

## Step 3: Generate Python .py File

Create a Python script (e.g., `code/python/00_descriptive_stats.py`) that replicates the same analysis:

```python
"""
Descriptive Statistics
Dataset: <dataset path>
Generated: <current date>
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# --- Load Data ---
# Support .dta and .csv
file_path = "<dataset path>"
if file_path.endswith(".dta"):
    df = pd.read_stata(file_path)
elif file_path.endswith(".csv"):
    df = pd.read_csv(file_path)
else:
    raise ValueError(f"Unsupported file format: {file_path}")

key_vars = [<list of key variables as strings>]

# --- Summary Statistics ---
summary = df[key_vars].describe(percentiles=[0.25, 0.5, 0.75]).T
summary = summary.rename(columns={
    "count": "N", "mean": "Mean", "std": "SD",
    "min": "Min", "25%": "P25", "50%": "P50", "75%": "P75", "max": "Max"
})
summary = summary[["N", "Mean", "SD", "Min", "P25", "P50", "P75", "Max"]]
print("=== Summary Statistics ===")
print(summary.to_string())
summary.to_latex("output/tables/tab_summary_stats_py.tex",
                 float_format="%.3f", caption="Summary Statistics (Python)")

# --- Correlation Matrix ---
corr = df[key_vars].corr()
print("\n=== Correlation Matrix ===")
print(corr.to_string())
corr.to_latex("output/tables/tab_correlation_py.tex",
              float_format="%.3f", caption="Correlation Matrix (Python)")

# --- Distribution Histograms ---
for var in key_vars:
    fig, ax = plt.subplots(figsize=(8, 5))
    df[var].dropna().hist(bins=50, ax=ax, density=True, alpha=0.7)
    df[var].dropna().plot.kde(ax=ax)
    ax.set_title(f"Distribution of {var}")
    ax.set_xlabel(var)
    ax.set_ylabel("Density")
    fig.savefig(f"output/figures/fig_dist_{var}_py.pdf", bbox_inches="tight")
    plt.close(fig)
```

If a **grouping variable** is provided, also add:

```python
# --- Balance Table ---
group_var = "<grouping variable>"
groups = df[group_var].unique()
balance = pd.DataFrame()
for var in key_vars:
    g0 = df.loc[df[group_var] == groups[0], var]
    g1 = df.loc[df[group_var] == groups[1], var]
    from scipy import stats
    t_stat, p_val = stats.ttest_ind(g0.dropna(), g1.dropna())
    balance = pd.concat([balance, pd.DataFrame({
        "Variable": [var],
        "Group 0 Mean": [g0.mean()],
        "Group 1 Mean": [g1.mean()],
        "Difference": [g1.mean() - g0.mean()],
        "t-stat": [t_stat],
        "p-value": [p_val]
    })], ignore_index=True)
print("\n=== Balance Table ===")
print(balance.to_string(index=False))
balance.to_latex("output/tables/tab_balance_py.tex",
                 float_format="%.3f", index=False, caption="Balance Table (Python)")
```

## Step 4: Execute and Cross-Check

1. Run the Stata .do file (if Stata is available on the system)
2. Run the Python .py file
3. Compare summary statistics between Stata and Python outputs:
   - Check that N, Mean, SD match within floating-point tolerance
   - Report any discrepancies

## Step 5: Report Results

Print a summary of all generated outputs:

```
Descriptive statistics generated successfully!

Stata outputs:
  - output/tables/tab_summary_stats.tex
  - output/tables/tab_correlation.tex
  - output/figures/fig_dist_<var>.pdf (for each variable)
  - output/tables/tab_balance.tex (if grouping variable provided)
  - output/logs/descriptive_stats.log

Python outputs:
  - output/tables/tab_summary_stats_py.tex
  - output/tables/tab_correlation_py.tex
  - output/figures/fig_dist_<var>_py.pdf (for each variable)
  - output/tables/tab_balance_py.tex (if grouping variable provided)

Cross-check: <PASS/FAIL with details>
```

## Additional Data Format Support

### SAS Datasets (.sas7bdat)

Some replication packages (especially in accounting/finance) provide data in SAS format. Load in Python via:
```python
df = pd.read_sas("data/raw/filename.sas7bdat", format="sas7bdat", encoding="latin-1")
```
Note: `pd.read_sas()` may be slow for large files. Consider converting to .dta or .parquet first.

### Large Dataset Guidance (N > 1M observations)

For datasets exceeding 1 million observations:
- **Subsample for histograms**: Use `if mod(_n, 100) == 0` in Stata or `df.sample(frac=0.01)` in Python
- **Use `summarize` instead of `estpost summarize`** for basic stats (faster, lower memory)
- **Skip correlation matrix** if > 50 key variables (produces very large table)
- **Consider `polars`** instead of `pandas` for faster data loading:
  ```python
  import polars as pl
  df = pl.read_ipc("data/raw/large_file.arrow")  # or scan_csv for lazy evaluation
  ```
