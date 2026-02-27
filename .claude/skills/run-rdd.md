---
description: "运行完整的断点回归设计（RDD）分析管道及全套诊断检验"
user_invocable: true
---

# /run-rdd — 断点回归设计分析管道

当用户调用 `/run-rdd` 时，执行完整的精确断点或模糊断点 RDD 分析管道，涵盖可视化、操纵检验、协变量平衡、rdrobust 主估计、带宽敏感性、多项式阶数稳健性、核函数敏感性、安慰剂检验、环形断点回归以及 Python 交叉验证。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 第 0 步：收集输入信息

向用户询问以下信息：

- **数据集**：.dta 文件路径
- **驱动变量**：赋值/强制变量（如考试分数、年龄、得票率）
- **断点值**：处理状态发生变化的阈值（数值）
- **因变量**：结果变量 Y
- **处理变量**：二值指标（如不存在，将根据驱动变量生成）
- **RDD 类型**：精确断点或模糊断点
- **处理接受变量**（仅模糊断点）：实际接受处理的变量
- **协变量**（可选）：用于平衡检验和提高精度的前定协变量
- **聚类变量**（可选）：聚类标准误所用变量

## 第 1 步：RD 可视化（Stata .do 文件）

```stata
/*==============================================================================
  RDD 分析 — 第 1 步：可视化
  参考：Cattaneo, Idrobo & Titiunik (2020) 最佳实践
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_01_visual.log", replace

use "DATASET_PATH", clear

* 如需生成处理变量
cap gen treat = (RUNNING_VAR >= CUTOFF)

* --- RD 图：分箱散点图与局部多项式 ---
rdplot OUTCOME_VAR RUNNING_VAR, c(CUTOFF) p(1) ///
    graph_options(title("Regression Discontinuity Plot") ///
    xtitle("RUNNING_VAR") ytitle("OUTCOME_VAR") ///
    xline(CUTOFF, lcolor(cranberry) lpattern(dash)))
graph export "output/figures/fig_rd_plot.pdf", replace

* --- 驱动变量的直方图 ---
histogram RUNNING_VAR, bin(50) ///
    xline(CUTOFF, lcolor(cranberry) lpattern(dash)) ///
    title("Distribution of Running Variable") ///
    xtitle("RUNNING_VAR") ytitle("Frequency")
graph export "output/figures/fig_rd_histogram.pdf", replace

log close
```

## 第 2 步：操纵检验（Stata .do 文件）

```stata
/*==============================================================================
  RDD — 第 2 步：Cattaneo-Jansson-Ma 密度检验
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_02_density.log", replace

use "DATASET_PATH", clear

* --- CJM (2020) 密度检验（首选）---
rddensity RUNNING_VAR, c(CUTOFF) plot ///
    plot_range(PLOT_MIN PLOT_MAX)
graph export "output/figures/fig_rd_density.pdf", replace

* 提取密度检验 p 值（Issue #3：使用正确的 e-class 标量）
* rddensity 在不同版本中存储 p 值的标量不同：
*   e(pv_q) — 二次方（首选）
*   e(pv_p) — 多项式
* 检查哪个可用：
cap local density_p = e(pv_q)
if "`density_p'" == "" | "`density_p'" == "." {
    cap local density_p = e(pv_p)
}
di "Density test p-value: `density_p'"

* 原假设：密度在断点处连续
* 拒绝 → 存在分选/操纵的证据

log close
```

## 第 3 步：协变量平衡（Stata .do 文件）

```stata
/*==============================================================================
  RDD — 第 3 步：断点处的协变量平衡
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_03_balance.log", replace

use "DATASET_PATH", clear

* --- 检验每个协变量的断点处不连续性 ---
local covariates "COVAR1 COVAR2 COVAR3"

foreach var of local covariates {
    di "=== Balance test: `var' ==="
    rdrobust `var' RUNNING_VAR, c(CUTOFF) kernel(triangular) bwselect(mserd)
    di ""
}

* --- 最优带宽内的平衡表 ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) bwselect(mserd)
local bw_opt = e(h_l)

gen near_cutoff = abs(RUNNING_VAR - CUTOFF) <= `bw_opt'
gen above = (RUNNING_VAR >= CUTOFF)

tabstat `covariates' if near_cutoff, by(above) ///
    stat(mean sd n) columns(statistics) format(%9.3f)

log close
```

## 第 4 步：主 RD 估计（Stata .do 文件）

```stata
/*==============================================================================
  RDD — 第 4 步：主估计 (rdrobust)
  报告：常规估计、偏差校正估计和稳健估计
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_04_main.log", replace

use "DATASET_PATH", clear

* --- MSE 最优带宽下的精确断点 RD ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
    kernel(triangular) bwselect(mserd) all

* 存储关键结果
local tau_conv  = e(tau_cl)
local tau_bc    = e(tau_bc)
local se_conv   = e(se_tau_cl)
local se_robust = e(se_tau_rb)
local bw_l      = e(h_l)
local bw_r      = e(h_r)
local N_l       = e(N_h_l)
local N_r       = e(N_h_r)

di "============================================="
di "MAIN RD RESULTS"
di "============================================="
di "Conventional:    `tau_conv' (SE = `se_conv')"
di "Bias-corrected:  `tau_bc' (Robust SE = `se_robust')"
di "Bandwidth (L/R): `bw_l' / `bw_r'"
di "Eff. N (L/R):    `N_l' / `N_r'"
di "============================================="

* --- CER 最优带宽（用于推断）---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
    kernel(triangular) bwselect(cerrd) all

* --- 加入协变量（提高精度）---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
    kernel(triangular) bwselect(mserd) covs(COVARIATES)

* --- 模糊断点 RD（如适用）---
* rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) ///
*     fuzzy(TREATMENT_TAKEUP_VAR) kernel(triangular) bwselect(mserd) all

log close
```

## 第 5 步：带宽与多项式阶数敏感性（Stata .do 文件）

```stata
/*==============================================================================
  RDD — 第 5 步：带宽与多项式阶数敏感性
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_05_sensitivity.log", replace

use "DATASET_PATH", clear

* --- 获取 MSE 最优带宽 ---
rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(triangular) bwselect(mserd)
local bw_opt = e(h_l)

* --- 带宽敏感性 ---
local multipliers "0.50 0.75 1.00 1.25 1.50 2.00"

tempfile bw_results
postfile bw_handle str10 spec bw_val coef se pval N_eff using `bw_results', replace

foreach m of local multipliers {
    local bw_test = `bw_opt' * `m'
    rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(triangular) h(`bw_test')
    post bw_handle ("`m'x") (`bw_test') (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (e(N_h_l) + e(N_h_r))
}

* --- 多项式阶数敏感性 ---
forvalues p = 1/3 {
    rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(triangular) bwselect(mserd) p(`p')
    post bw_handle ("p=`p'") (e(h_l)) (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (e(N_h_l) + e(N_h_r))
}

* --- 核函数敏感性 ---
foreach kern in triangular uniform epanechnikov {
    rdrobust OUTCOME_VAR RUNNING_VAR, c(CUTOFF) kernel(`kern') bwselect(mserd)
    post bw_handle ("`kern'") (e(h_l)) (e(tau_cl)) (e(se_tau_cl)) (e(pv_cl)) (e(N_h_l) + e(N_h_r))
}

postclose bw_handle

* --- 显示与绘图 ---
use `bw_results', clear
gen ci_lo = coef - 1.96 * se
gen ci_hi = coef + 1.96 * se
list, clean

log close
```

## 第 6 步：安慰剂检验与环形断点检验（Stata .do 文件）

```stata
/*==============================================================================
  RDD — 第 6 步：安慰剂断点与环形断点检验
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/rdd_06_placebo.log", replace

use "DATASET_PATH", clear

* --- 安慰剂断点 ---
* 在远离真实断点的虚假阈值处检验
sum RUNNING_VAR, detail
local p25 = r(p25)
local p75 = r(p75)

* 断点以下：在第 25 百分位检验
di "=== Placebo at p25 (`p25') ==="
rdrobust OUTCOME_VAR RUNNING_VAR if RUNNING_VAR < CUTOFF, ///
    c(`p25') kernel(triangular) bwselect(mserd)

* 断点以上：在第 75 百分位检验
di "=== Placebo at p75 (`p75') ==="
rdrobust OUTCOME_VAR RUNNING_VAR if RUNNING_VAR > CUTOFF, ///
    c(`p75') kernel(triangular) bwselect(mserd)

* --- 环形断点 RD ---
* 排除非常接近断点的观测值
foreach donut in 0.5 1 2 5 {
    di "=== Donut RD: excluding +-`donut' from cutoff ==="
    rdrobust OUTCOME_VAR RUNNING_VAR if abs(RUNNING_VAR - CUTOFF) > `donut', ///
        c(CUTOFF) kernel(triangular) bwselect(mserd)
}

log close
```

## 第 7 步：Python 交叉验证

```python
"""
RDD 交叉验证：使用 rdrobust Python 包
"""
import pandas as pd
import numpy as np

df = pd.read_stata("DATASET_PATH")

try:
    from rdrobust import rdrobust, rdplot, rdbwselect
    result = rdrobust(y=df["OUTCOME_VAR"], x=df["RUNNING_VAR"], c=CUTOFF,
                      kernel='triangular', bwselect='mserd')
    print("=== Python RD Results ===")
    print(result)
    python_rd = result.coef.iloc[0]  # 常规估计
except ImportError:
    print("rdrobust not installed. Install: pip install rdrobust")
    print("Falling back to pyfixest local regression...")
    import pyfixest as pf
    # 在最优带宽内的局部线性回归（来自 Stata）
    bw = OPTIMAL_BW_FROM_STATA
    df_local = df[abs(df["RUNNING_VAR"] - CUTOFF) <= bw].copy()
    df_local["above"] = (df_local["RUNNING_VAR"] >= CUTOFF).astype(int)
    df_local["centered"] = df_local["RUNNING_VAR"] - CUTOFF
    df_local["interact"] = df_local["above"] * df_local["centered"]
    model = pf.feols("OUTCOME_VAR ~ above + centered + interact", data=df_local)
    print(model.summary())
    python_rd = model.coef()["above"]

stata_rd = STATA_RD_COEF
pct_diff = abs(stata_rd - python_rd) / abs(stata_rd) * 100
print(f"\nCross-validation:")
print(f"  Stata:  {stata_rd:.6f}")
print(f"  Python: {python_rd:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 0.5 else 'FAIL'}")
```

## 第 8 步：诊断总结

所有步骤完成后，提供以下内容：

1. **操纵检验**：CJM 密度检验 p 值。如果拒绝，RDD 有效性存疑。
2. **协变量平衡**：哪些协变量在断点处出现不连续？平衡的协变量支持有效性。
3. **主估计**：报告偏差校正估计值及稳健标准误和置信区间。
4. **带宽敏感性**：在 0.5 倍到 2 倍最优带宽范围内是否稳定？标记不稳定情况。
5. **多项式阶数**：在 p=1,2,3 之间是否稳定？局部线性（p=1）为默认选择。
6. **核函数敏感性**：三角核 vs 均匀核 vs Epanechnikov 核的一致性。
7. **安慰剂检验**：虚假断点应显示零效应。
8. **环形断点**：排除断点附近的个体应保持估计结果。
9. **交叉验证**：Stata vs Python 匹配结果（容差：0.5%）。

## 所需 Stata 包

```stata
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace
net install rdlocrand, from(https://raw.githubusercontent.com/rdpackages/rdlocrand/master/stata) replace
net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace
net install rdmulti, from(https://raw.githubusercontent.com/rdpackages/rdmulti/master/stata) replace
ssc install reghdfe
ssc install ftools
ssc install coefplot
```
