---
description: "运行安慰剂检验与随机化推断管道（时间、结果、工具变量、置换检验）"
user_invocable: true
---

# /run-placebo — 安慰剂检验与随机化推断管道

当用户调用 `/run-placebo` 时，执行全面的安慰剂检验和随机化推断管道，涵盖安慰剂处理时间、安慰剂因变量、安慰剂工具变量（排除性约束验证）、Fisher 精确置换检验、地理/个体安慰剂以及 Python 交叉验证。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 何时使用安慰剂检验

- **始终需要**：安慰剂检验是应用微观计量的标准做法。审稿人有此预期。
- **DID/事件研究**：安慰剂处理时间比视觉检查更严格地检验平行趋势
- **IV**：安慰剂工具变量验证排除性约束（应为零简约式）
- **RDD**：安慰剂断点检验非处理阈值处是否存在不连续
- **任何因果设计**：置换/随机化推断提供不依赖分布假设的非参数 p 值

## 第 0 步：收集输入信息

向用户询问以下信息：

- **数据集**：.dta 文件路径
- **基准回归命令**：主设定
- **关注的系数**：处理变量或关键变量
- **方法类型**：DID、IV、RDD、面板或 OLS（决定适用哪些安慰剂类型）
- **聚类变量**：用于聚类和置换结构
- **组别变量**（如为面板）：个体标识符
- **时间变量**（如为面板/DID）：时期标识符
- **处理时间**（如为 DID）：处理组的首次处理时期
- **安慰剂因变量**（可选）：不应受处理影响的因变量
- **安慰剂工具变量**（可选）：基于无关冲击构建的工具变量（用于 IV 排除性约束检验）
- **置换检验重复次数**：探索性分析 500 次，发表使用 1000+ 次（默认：1000）

## 第 1 步：安慰剂处理时间（Stata .do 文件）

将处理时间移至处理前时期，在这些时期不应存在效应。显著的"效应"提示存在前趋势或模型误设。

```stata
/*==============================================================================
  安慰剂分析 — 第 1 步：安慰剂处理时间
  将处理时间移至处理前的虚假日期。应得到零效应。
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_01_timing.log", replace

use "DATASET_PATH", clear

* --- 实际处理（基准，供参考）---
eststo clear
eststo actual: BASELINE_COMMAND
local b_actual = _b[COEF_VAR]
local se_actual = _se[COEF_VAR]

* --- 安慰剂时间：将处理提前 N 期 ---
* 将样本限制在处理前时期
preserve
keep if TIME_VAR < FIRST_TREAT_PERIOD

* 在不同处理前日期创建虚假处理指标
local placebo_dates "DATE1 DATE2 DATE3"  // 如实际处理前 3、5、7 期
foreach t of local placebo_dates {
    gen placebo_treat_`t' = (GROUP_IS_TREATED) * (TIME_VAR >= `t')
    eststo placebo_t`t': reghdfe OUTCOME_VAR placebo_treat_`t' CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    local b_p`t' = _b[placebo_treat_`t']
    local p_p`t' = 2 * ttail(e(df_r), abs(_b[placebo_treat_`t'] / _se[placebo_treat_`t']))
    di "Placebo (t=`t'): b = `b_p`t'', p = `p_p`t''"
    drop placebo_treat_`t'
}
restore

* --- 安慰剂时间表格 ---
esttab actual placebo_* using "output/tables/tab_placebo_timing.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    title("Placebo Treatment Timing Tests") ///
    note("Column (1) = actual treatment. Remaining columns = false treatment dates." ///
         "Placebo samples restricted to pre-treatment period." ///
         "Significant placebo effects suggest pre-trend violations.")

log close
```

## 第 2 步：安慰剂因变量（Stata .do 文件）

对不应受处理影响的因变量运行基准模型。

```stata
/*==============================================================================
  安慰剂分析 — 第 2 步：安慰剂因变量
  对不受处理因果影响的因变量运行模型。应得到零效应。
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_02_outcome.log", replace

use "DATASET_PATH", clear

* --- 实际因变量（基准）---
eststo clear
eststo actual: BASELINE_COMMAND

* --- 安慰剂因变量 ---
* 这些应为不受处理因果影响的变量
foreach pvar in PLACEBO_OUTCOME1 PLACEBO_OUTCOME2 PLACEBO_OUTCOME3 {
    eststo placebo_`pvar': reghdfe `pvar' TREATMENT_VAR CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    local b_p = _b[TREATMENT_VAR]
    local p_p = 2 * ttail(e(df_r), abs(_b[TREATMENT_VAR] / _se[TREATMENT_VAR]))
    di "Placebo outcome `pvar': b = `b_p', p = `p_p'"
}

* --- 表格 ---
esttab actual placebo_* using "output/tables/tab_placebo_outcomes.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    title("Placebo Outcome Tests") ///
    note("Column (1) = actual outcome. Remaining columns = placebo outcomes." ///
         "Significant effects on placebo outcomes suggest confounding.")

log close
```

## 第 3 步：安慰剂工具变量 / 排除性约束检验（Stata .do 文件）

基于无关冲击构建工具变量并检验简约式。安慰剂工具变量的显著简约式将削弱排除性约束。模式来自 APE 0185 (Social Networks & Minimum Wage)。

```stata
/*==============================================================================
  安慰剂分析 — 第 3 步：安慰剂工具变量
  参考：APE 0185 — 04c_placebo_shocks.R 模式
  基于无关冲击构建工具变量；应得到零简约式。
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_03_instrument.log", replace

use "DATASET_PATH", clear

* --- 实际简约式（工具变量 -> 因变量）---
eststo clear
eststo actual_rf: reghdfe OUTCOME_VAR ACTUAL_INSTRUMENT CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- 安慰剂工具变量 ---
* 方案 A：使用无关部门/地区的工具变量
* 方案 B：在个体间随机重排工具变量取值
* 方案 C：使用工具变量生效前时期的滞后工具变量

* 安慰剂工具变量 1：无关部门冲击
eststo placebo_rf1: reghdfe OUTCOME_VAR PLACEBO_INSTRUMENT1 CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* 安慰剂工具变量 2：随机置换的工具变量
preserve
    bsample, cluster(CLUSTER_VAR)
    rename ACTUAL_INSTRUMENT placebo_perm_iv
    tempfile perm
    keep UNIT_VAR TIME_VAR placebo_perm_iv
    save `perm', replace
restore
merge 1:1 UNIT_VAR TIME_VAR using `perm', nogenerate

eststo placebo_rf2: reghdfe OUTCOME_VAR placebo_perm_iv CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- 表格 ---
esttab actual_rf placebo_rf* using "output/tables/tab_placebo_instruments.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    title("Placebo Instrument Tests (Reduced Form)") ///
    note("Column (1) = actual instrument reduced form." ///
         "Remaining columns = placebo instruments. Expect NULL effects." ///
         "Significant placebo RF undermines the exclusion restriction.")

log close
```

## 第 4 步：置换 / 随机化推断（Stata .do 文件）

Fisher 精确检验：打乱处理标签，重新估计模型 N 次，计算实际系数在零分布中的秩作为 p 值。

```stata
/*==============================================================================
  安慰剂分析 — 第 4 步：置换 / 随机化推断
  Fisher 精确检验：打乱处理标签，计算零分布
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_04_permutation.log", replace

use "DATASET_PATH", clear

* --- 实际估计 ---
BASELINE_COMMAND
local b_actual = _b[COEF_VAR]
di "Actual coefficient: `b_actual'"

* --- 定义置换程序 ---
cap program drop permute_test
program define permute_test, rclass
    * 在聚类间（而非聚类内）置换处理标签
    tempvar rand
    gen `rand' = runiform()
    * 随机排序聚类，然后重新分配处理状态
    bysort CLUSTER_VAR (`rand'): gen byte _treat_perm = TREATMENT_VAR[1]
    * 替代方案：在个体层面纯随机打乱
    * sort `rand'
    * gen _treat_perm = TREATMENT_VAR[_n]

    reghdfe OUTCOME_VAR _treat_perm CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    return scalar b = _b[_treat_perm]
    drop _treat_perm
end

* --- 运行置换检验 ---
simulate b_perm = r(b), reps(NREPS) seed(12345) nodots: permute_test

* --- 计算 p 值 ---
count if abs(b_perm) >= abs(`b_actual')
local perm_p = r(N) / NREPS
di "============================================="
di "PERMUTATION INFERENCE"
di "============================================="
di "  Actual coefficient:   `b_actual'"
di "  Permutation p-value:  `perm_p'"
di "  (fraction of |permuted b| >= |actual b|)"
di "============================================="

* --- 置换分布图 ---
hist b_perm, bin(50) ///
    title("Randomization Inference: Null Distribution") ///
    xtitle("Permuted Coefficient") ytitle("Density") ///
    xline(`b_actual', lcolor(cranberry) lpattern(dash) lwidth(medthick)) ///
    note("Vertical line = actual estimate. p = `perm_p'. N perms = NREPS")
graph export "output/figures/fig_permutation_dist.pdf", replace

log close
```

## 第 5 步：地理 / 个体安慰剂（Stata .do 文件）

将处理分配给未处理的个体（或地区）并重新估计。

```stata
/*==============================================================================
  安慰剂分析 — 第 5 步：地理 / 个体安慰剂
  将处理分配给未处理个体。应得到零效应。
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/placebo_05_geographic.log", replace

use "DATASET_PATH", clear

* --- 识别处理/对照组 ---
bysort GROUP_VAR: egen ever_treated = max(TREATMENT_VAR)

* --- 方案 1：仅在对照组个体中随机分配处理 ---
preserve
keep if ever_treated == 0

* 将"安慰剂处理"随机分配给一半对照组个体
bysort GROUP_VAR: gen _tag = (_n == 1)
gen _rand = runiform() if _tag == 1
bysort GROUP_VAR: replace _rand = _rand[1]
egen _med = median(_rand) if _tag == 1
gen placebo_treat = (TREATMENT_VAR == 0) & (_rand >= _med) & (TIME_VAR >= FIRST_TREAT_PERIOD)

eststo geo_placebo: reghdfe OUTCOME_VAR placebo_treat CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
di "Geographic placebo: b = " _b[placebo_treat] ", p = " ///
    2 * ttail(e(df_r), abs(_b[placebo_treat] / _se[placebo_treat]))
restore

* --- 方案 2：逐一剔除组别 (LOGO) 敏感性 ---
levelsof GROUP_VAR if ever_treated == 1, local(treated_units)
foreach u of local treated_units {
    cap BASELINE_COMMAND_IF GROUP_VAR != `u'
    if _rc == 0 {
        di "LOGO (drop `u'): b = " _b[COEF_VAR] " (SE = " _se[COEF_VAR] ")"
    }
}

log close
```

## 第 6 步：Python 交叉验证

```python
"""
安慰剂检验与置换推断交叉验证：Stata vs Python
"""
import pandas as pd
import numpy as np
import pyfixest as pf

df = pd.read_stata("DATASET_PATH")

# --- Python 中的置换推断 ---
np.random.seed(12345)
n_perms = 1000

# 实际估计
model = pf.feols("OUTCOME_VAR ~ TREATMENT_VAR + CONTROLS | FIXED_EFFECTS",
                 data=df, vcov={"CRV1": "CLUSTER_VAR"})
b_actual = model.coef()["TREATMENT_VAR"]
print(f"Actual coefficient: {b_actual:.6f}")

# 在聚类间置换处理
clusters = df["CLUSTER_VAR"].unique()
perm_coefs = []
for i in range(n_perms):
    df_perm = df.copy()
    # 在聚类层面打乱处理
    perm_map = dict(zip(clusters, np.random.permutation(clusters)))
    df_perm["_perm_cl"] = df_perm["CLUSTER_VAR"].map(perm_map)
    # 基于置换后的聚类重新分配处理
    treat_map = df.groupby("CLUSTER_VAR")["TREATMENT_VAR"].first().to_dict()
    df_perm["_treat_perm"] = df_perm["_perm_cl"].map(treat_map)
    try:
        m = pf.feols("OUTCOME_VAR ~ _treat_perm + CONTROLS | FIXED_EFFECTS",
                     data=df_perm, vcov={"CRV1": "CLUSTER_VAR"})
        perm_coefs.append(m.coef()["_treat_perm"])
    except Exception:
        pass

perm_coefs = np.array(perm_coefs)
perm_p = np.mean(np.abs(perm_coefs) >= abs(b_actual))

print(f"\n=== Python Permutation Inference ===")
print(f"  Permutation p-value: {perm_p:.4f}")
print(f"  Null distribution mean: {np.mean(perm_coefs):.6f}")
print(f"  Null distribution SD:   {np.std(perm_coefs):.6f}")

# --- 与 Stata 交叉验证 ---
stata_perm_p = STATA_PERM_P  # 来自第 4 步日志
print(f"\nCross-validation (permutation p):")
print(f"  Stata:  {stata_perm_p:.4f}")
print(f"  Python: {perm_p:.4f}")
print(f"  Status: {'PASS' if abs(stata_perm_p - perm_p) < 0.05 else 'CHECK'}")
# 注意：置换 p 值可能因模拟方差而略有不同

# --- 可视化 ---
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(perm_coefs, bins=50, density=True, alpha=0.7, color="steelblue",
        edgecolor="white", label="Null distribution")
ax.axvline(b_actual, color="crimson", linestyle="--", linewidth=2,
           label=f"Actual = {b_actual:.4f}")
ax.set_xlabel("Coefficient")
ax.set_ylabel("Density")
ax.set_title(f"Randomization Inference (p = {perm_p:.3f})")
ax.legend()
fig.savefig("output/figures/fig_permutation_python.pdf", bbox_inches="tight")
plt.close()
```

## 第 7 步：诊断总结

所有步骤完成后，提供以下内容：

1. **安慰剂时间**：所有处理前安慰剂处理系数是否均不显著？任何显著结果都标记前趋势问题。**重要提示**：显著的时间安慰剂**不一定**意味着设计无效 — 它可能反映**预期效应**（个体在正式政策变更前作出反应）。需区分预期效应（对有提前期的政策如民主化是预期的）和混淆因素（Issue #22）。
2. **安慰剂因变量**：对无关因变量的效应是否不显著？显著效应提示混淆或数据问题。
3. **安慰剂工具变量**（仅 IV）：安慰剂工具变量的简约式是否为零？显著结果削弱排除性约束。
4. **置换 p 值**：与解析 p 值一并报告。差异较大提示分布假设有影响。
5. **地理安慰剂**：将处理分配给对照组个体时是否确认零效应？
6. **LOGO 敏感性**：是否有单个处理组个体驱动结果？
7. **交叉验证**：Stata vs Python 置换 p 值比较。

以表格形式报告：

```
安慰剂检验与随机化推断总结
================================
检验                    | 实际系数 | 安慰剂系数 | p 值   | 通过?
安慰剂时间 (t-3)        |   X.XXX  |    X.XXX   | X.XXX  | 是/否
安慰剂时间 (t-5)        |   X.XXX  |    X.XXX   | X.XXX  | 是/否
安慰剂因变量 1          |   X.XXX  |    X.XXX   | X.XXX  | 是/否
置换推断                |   X.XXX  |    ---     | X.XXX  | ---
地理安慰剂              |   X.XXX  |    X.XXX   | X.XXX  | 是/否
```

## 所需 Stata 包

```stata
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install coefplot, replace
```

## 核心参考文献

- Fisher, R.A. (1935). *The Design of Experiments*.（随机化推断基础）
- Bertrand, M., Duflo, E. & Mullainathan, S. (2004). "How Much Should We Trust Differences-in-Differences Estimates?" QJE.
- Abman, R., Lundberg, C. & Ruta, M. — APE 0185 安慰剂冲击构建模式。
