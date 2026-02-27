---
description: "使用 Stata 和 Python 生成描述性统计和变量分布"
user_invocable: true
---

# /data-describe — 生成描述性统计

当用户调用 `/data-describe` 时，按以下步骤执行：

## 步骤 1：收集信息

向用户询问：

1. **数据集路径**（必填）— 数据文件路径（.dta、.csv 或其他格式）
2. **关键变量**（必填）— 需描述的变量列表（逗号分隔）
3. **分组变量**（可选）— 用于分组分析/平衡性检验的变量（如处理/干预指标）
4. **输出目录**（可选）— 结果保存位置（默认：`output/tables/` 和 `output/figures/`）

## 步骤 2：生成 Stata .do 文件

创建 Stata .do 文件（如 `code/stata/00_descriptive_stats.do`），执行以下操作：

```stata
/*==============================================================================
  描述性统计
  数据集: <dataset path>
  生成日期: <current date>
==============================================================================*/

clear all
set more off
cap log close

log using "output/logs/descriptive_stats.log", replace

* --- 加载数据 ---
use "<dataset path>", clear

* --- 汇总统计 ---
* 输出: N, 均值, 标准差, 最小值, P25, P50, P75, 最大值
estpost summarize <key variables>, detail
esttab using "output/tables/tab_summary_stats.tex", ///
    cells("count mean(fmt(3)) sd(fmt(3)) min(fmt(3)) p25(fmt(3)) p50(fmt(3)) p75(fmt(3)) max(fmt(3))") ///
    label nomtitle nonumber replace booktabs ///
    title("Summary Statistics")

* --- 相关系数矩阵 ---
correlate <key variables>
* 导出相关系数矩阵为 LaTeX
estpost correlate <key variables>, matrix
esttab using "output/tables/tab_correlation.tex", ///
    unstack not noobs compress label replace booktabs ///
    title("Correlation Matrix")

* --- 分布直方图 ---
foreach var of varlist <key variables> {
    histogram `var', ///
        frequency normal ///
        title("Distribution of `var'") ///
        scheme(s2color)
    graph export "output/figures/fig_dist_`var'.pdf", replace
}
```

如提供了**分组变量**，追加以下内容：

```stata
* --- 平衡性检验表 ---
* 比较各组均值
estpost ttest <key variables>, by(<grouping variable>)
esttab using "output/tables/tab_balance.tex", ///
    cells("mu_1(fmt(3)) mu_2(fmt(3)) b(fmt(3) star)") ///
    label nomtitle nonumber replace booktabs ///
    collabels("Control Mean" "Treatment Mean" "Difference") ///
    title("Balance Table") ///
    addnotes("* p<0.10, ** p<0.05, *** p<0.01")
```

以下列命令结束：

```stata
log close
```

## 步骤 3：生成 Python .py 文件

创建 Python 脚本（如 `code/python/00_descriptive_stats.py`），复现相同的分析：

```python
"""
描述性统计
数据集: <dataset path>
生成日期: <current date>
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# --- 加载数据 ---
# 支持 .dta 和 .csv
file_path = "<dataset path>"
if file_path.endswith(".dta"):
    df = pd.read_stata(file_path)
elif file_path.endswith(".csv"):
    df = pd.read_csv(file_path)
else:
    raise ValueError(f"Unsupported file format: {file_path}")

key_vars = [<list of key variables as strings>]

# --- 汇总统计 ---
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

# --- 相关系数矩阵 ---
corr = df[key_vars].corr()
print("\n=== Correlation Matrix ===")
print(corr.to_string())
corr.to_latex("output/tables/tab_correlation_py.tex",
              float_format="%.3f", caption="Correlation Matrix (Python)")

# --- 分布直方图 ---
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

如提供了**分组变量**，追加以下内容：

```python
# --- 平衡性检验表 ---
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

## 步骤 4：执行并交叉验证

1. 运行 Stata .do 文件（若系统中 Stata 可用）
2. 运行 Python .py 文件
3. 比较 Stata 与 Python 输出的汇总统计：
   - 检查 N、均值、标准差是否在浮点误差范围内一致
   - 报告任何差异

## 步骤 5：报告结果

输出所有生成文件的汇总：

```
描述性统计生成成功！

Stata 输出:
  - output/tables/tab_summary_stats.tex
  - output/tables/tab_correlation.tex
  - output/figures/fig_dist_<var>.pdf（每个变量各一张）
  - output/tables/tab_balance.tex（如提供了分组变量）
  - output/logs/descriptive_stats.log

Python 输出:
  - output/tables/tab_summary_stats_py.tex
  - output/tables/tab_correlation_py.tex
  - output/figures/fig_dist_<var>_py.pdf（每个变量各一张）
  - output/tables/tab_balance_py.tex（如提供了分组变量）

交叉验证: <通过/未通过及详情>
```

## 附加数据格式支持

### SAS 数据集 (.sas7bdat)

部分复现包（特别是会计/金融领域）以 SAS 格式提供数据。在 Python 中加载：
```python
df = pd.read_sas("data/raw/filename.sas7bdat", format="sas7bdat", encoding="latin-1")
```
注意：`pd.read_sas()` 处理大文件时可能较慢。建议先转换为 .dta 或 .parquet 格式。

### 大数据集处理指南（N > 100 万观测）

当数据集超过 100 万条观测时：
- **直方图使用子样本**：Stata 中用 `if mod(_n, 100) == 0`，Python 中用 `df.sample(frac=0.01)`
- **使用 `summarize` 替代 `estpost summarize`** 获取基本统计量（更快、更省内存）
- **变量超过 50 个时跳过相关系数矩阵**（表格过大）
- **考虑使用 `polars`** 替代 `pandas` 以加快数据加载速度：
  ```python
  import polars as pl
  df = pl.read_ipc("data/raw/large_file.arrow")  # 或用 scan_csv 进行惰性求值
  ```
