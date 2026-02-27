---
description: "运行完整的工具变量/两阶段最小二乘法（IV/2SLS）分析管道及诊断检验"
user_invocable: true
---

# /run-iv — 工具变量 / 2SLS 分析管道

当用户调用 `/run-iv` 时，执行完整的 IV 分析管道，涵盖第一阶段、简约式、2SLS/LIML 估计、综合诊断检验（KP F 统计量、AR 置信区间、DWH 检验、Hansen J 检验）、距离-可信度分析以及 Python 交叉验证。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 所需 Stata 包（按此顺序安装）

安装顺序很重要 — `ranktest` 必须在 `ivreg2` 之前安装，`ivreg2` 必须在 `ivreghdfe` 之前。缺少 `ranktest` 会导致 `struct ms_vcvorthog undefined` 错误。

```stata
ssc install ranktest, replace      // 必须首先安装
ssc install ivreg2, replace        // 依赖 ranktest
ssc install reghdfe, replace
ssc install ftools, replace
ssc install ivreghdfe, replace     // 依赖 ivreg2 + reghdfe
ssc install estout, replace
ssc install coefplot, replace
ssc install weakiv, replace
ssc install boottest, replace
```

## 第 0 步：收集输入信息

在开始之前，向用户询问以下信息：

- **数据集**：.dta 文件路径
- **内生变量**：疑似内生的变量
- **工具变量**：内生变量的排除工具变量
- **因变量**：结果变量 Y
- **控制变量**：所有阶段中包含的外生协变量
- **固定效应**：需要吸收的固定效应（如个体固定效应、时间固定效应、个体×时间固定效应）
- **聚类变量**：聚类标准误所用变量
- **替代因变量**（可选）：用于多结果面板（Panel A/B）

注明模型是恰好识别（工具变量数 = 内生变量数）还是过度识别（工具变量数 > 内生变量数）。

**数据探索提示**：使用 `summarize` 和 `codebook` 检查变量 — 不要对连续变量使用 `tab`。对连续变量使用 `tab` 会为每个唯一值生成一行，产生大量输出，对大数据集可能导致崩溃（Issue #5）。仅对取值较少的分类/二值变量使用 `tab`。

## 第 1 步：第一阶段与简约式（Stata .do 文件）

```stata
/*==============================================================================
  IV 分析 — 第 1 步：第一阶段与简约式
  参考文献：APE paper 0185 (Social Networks & Labor Markets)
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/iv_01_firststage.log", replace

use "DATASET_PATH", clear

* --- 第一阶段回归 ---
eststo clear
eststo fs_main: reghdfe ENDOG_VAR INSTRUMENT(S) CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* 排除工具变量的第一阶段 F 统计量
test INSTRUMENT(S)
local fs_F = r(F)
local fs_p = r(p)
di "=== First-Stage F-statistic: `fs_F' (p = `fs_p') ==="
* 经验法则：F > 10 (Stock-Yogo)；F > 23 (Lee et al. 2022 tF)
* 对于异方差/聚类情形：与 Montiel Olea-Pflueger 有效 F 值比较

* 排除工具变量的偏 R 方
reghdfe ENDOG_VAR CONTROLS, absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
local r2_excl = e(r2)
eststo fs_main
local r2_full = e(r2)
local partial_r2 = `r2_full' - `r2_excl'
di "Partial R-squared: `partial_r2'"

* --- 简约式 ---
eststo rf_main: reghdfe OUTCOME_VAR INSTRUMENT(S) CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
di "Reduced form coefficient / FS coefficient ≈ 2SLS (Wald)"

* --- 第一阶段表格（独立表格，遵循 APE 0185 tab3 格式）---
esttab fs_main using "output/tables/tab_first_stage.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(INSTRUMENT(S)) label booktabs replace ///
    scalars("r2_within Within R$^2$" "N Observations") ///
    addnotes("F-statistic on excluded instrument(s): `fs_F'" ///
             "Dependent variable: ENDOG_VAR") ///
    title("First Stage: INSTRUMENT $\rightarrow$ ENDOG\_VAR")

log close
```

## 第 2 步：OLS 基准与 2SLS 估计（Stata .do 文件）

**回退策略：** 如果 `ivreghdfe` 崩溃（如缺少 `ranktest`），回退到 `ivreg2` 并手动生成固定效应虚拟变量。如果 `ivreg2` 也不可用，则计算手工 Wald 估计量（简约式 / 第一阶段）。

```stata
/*==============================================================================
  IV 分析 — 第 2 步：OLS 基准、2SLS 和 LIML
  回退链：ivreghdfe -> ivreg2（+ 固定效应虚拟变量）-> 手工 Wald
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/iv_02_estimation.log", replace

use "DATASET_PATH", clear

eststo clear

* --- OLS 基准 ---
eststo ols_base: reghdfe OUTCOME_VAR ENDOG_VAR CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- 使用 ivreghdfe 的 2SLS（首选）---
cap noisily ivreghdfe OUTCOME_VAR CONTROLS ///
    (ENDOG_VAR = INSTRUMENT(S)), ///
    absorb(FIXED_EFFECTS) cluster(CLUSTER_VAR) first
if _rc != 0 {
    di "ivreghdfe failed. Trying ivreg2 with FE dummies..."
    * 手动生成固定效应虚拟变量
    quietly: tab UNIT_VAR, gen(_unit_fe)
    quietly: tab TIME_VAR, gen(_time_fe)
    cap which ivreg2
    if _rc == 0 {
        ivreg2 OUTCOME_VAR CONTROLS _unit_fe* _time_fe* ///
            (ENDOG_VAR = INSTRUMENT(S)), cluster(CLUSTER_VAR) first ffirst
    }
    else {
        * 手工 Wald = 简约式系数 / 第一阶段系数
        di "ivreg2 not available. Computing manual Wald estimator."
    }
    cap drop _unit_fe* _time_fe*
}
else {
    eststo iv_2sls
}
local kp_f = e(widstat)
di "Kleibergen-Paap rk Wald F: `kp_f'"

* --- LIML（对弱工具变量稳健）---
cap noisily ivreghdfe OUTCOME_VAR CONTROLS ///
    (ENDOG_VAR = INSTRUMENT(S)), ///
    absorb(FIXED_EFFECTS) cluster(CLUSTER_VAR) liml
if _rc == 0 {
    eststo iv_liml
}
di "LIML estimate: " _b[ENDOG_VAR]
* LIML 与 2SLS 差异较大表明存在弱工具变量问题

* --- 主要结果表（Panel A/B 格式，遵循 APE 0185 tab2）---
esttab ols_base iv_2sls iv_liml using "output/tables/tab_iv_main.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("OLS" "2SLS" "LIML") ///
    keep(ENDOG_VAR) label booktabs replace ///
    scalars("widstat KP F-stat" "N_clust Clusters" "N Observations") ///
    addnotes("Standard errors clustered at CLUSTER_VAR level." ///
             "Instrument(s): INSTRUMENT(S)." ///
             "KP F = Kleibergen-Paap rk Wald F-statistic.") ///
    title("IV/2SLS Estimation Results")

log close
```

## 第 3 步：综合诊断检验（Stata .do 文件）

```stata
/*==============================================================================
  IV 分析 — 第 3 步：诊断检验
  KP F 统计量、DWH 内生性检验、Hansen J 检验、Anderson-Rubin 置信区间
==============================================================================*/
clear all
set more off

cap log close
log using "output/logs/iv_03_diagnostics.log", replace

use "DATASET_PATH", clear

* --- 通过 ivreg2 进行完整诊断（不含多维固定效应）---
* 注意：如需多维固定效应，需先手动去除
ivreg2 OUTCOME_VAR CONTROLS (ENDOG_VAR = INSTRUMENT(S)), ///
    cluster(CLUSTER_VAR) first ffirst endog(ENDOG_VAR)

* ivreg2 自动报告以下诊断：
* - KP rk Wald F（弱工具变量）
* - KP rk LM（不可识别）
* - Hansen J（过度识别，仅当过度识别时）
* - DWH 内生性检验

di "============================================="
di "IV DIAGNOSTICS SUMMARY"
di "============================================="
di "KP rk Wald F:        " e(widstat)
di "KP rk LM (underid):  " e(idstat) " (p=" e(idp) ")"
* 注意：使用 xtivreg2 配合 partial() 选项时，DWH 内生性检验
* p 值 (e(estatp)) 可能缺失。这是已知限制。
* 此时需手动运行 Hausman 型内生性检验（Issue #14）。
if e(estatp) != . {
    di "DWH endogeneity:     " e(estat) " (p=" e(estatp) ")"
}
else {
    di "DWH endogeneity:     unavailable (xtivreg2 + partial() limitation)"
}
di "Hansen J (overid):   " e(j) " (p=" e(jp) ")"
di "============================================="

* --- Anderson-Rubin 置信集（对弱工具变量稳健）---
* 当 F 统计量处于边界值（10-23 范围）时尤为关键
cap weakiv
if _rc == 0 {
    weakiv
}
else {
    * 手动 AR 检验：运行简约式，检验系数 = 0
    reghdfe OUTCOME_VAR INSTRUMENT(S) CONTROLS, ///
        absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    test INSTRUMENT(S)
    local ar_F = r(F)
    local ar_p = r(p)
    di "Anderson-Rubin F: `ar_F' (p = `ar_p')"
}

* --- Bartik/份额偏移型 IV 的冲击稳健标准误（Adao et al. 2019）---
* 如果工具变量是 Bartik/份额偏移型，添加双向聚类：
* reghdfe OUTCOME_VAR TREAT CONTROLS, absorb(FE) vce(cluster CLUSTER1 CLUSTER2)

log close
```

## 第 4 步：稳健性与距离-可信度分析（Stata .do 文件）

```stata
/*==============================================================================
  IV 分析 — 第 4 步：稳健性
  遵循 APE 0185：距离-可信度权衡、LOSO、安慰剂检验
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/iv_04_robustness.log", replace

use "DATASET_PATH", clear

* --- 逐一剔除州/组（LOSO）---
* 检查结果是否由某个特定单位驱动
levelsof CLUSTER_VAR, local(clusters)
foreach c of local clusters {
    cap ivreghdfe OUTCOME_VAR CONTROLS (ENDOG_VAR = INSTRUMENT(S)) ///
        if CLUSTER_VAR != `c', absorb(FIXED_EFFECTS) cluster(CLUSTER_VAR)
    if _rc == 0 {
        di "LOSO (drop `c'): b = " _b[ENDOG_VAR] " (SE = " _se[ENDOG_VAR] ")"
    }
}

* --- 安慰剂工具变量 ---
* 如果排除性约束有争议，测试不应影响因变量的替代工具变量
* eststo placebo: reghdfe OUTCOME_VAR PLACEBO_INSTRUMENT CONTROLS, ...

* --- 简约式前趋势检验 ---
* 如果工具变量随时间变化，检查简约式中的前趋势

* --- Wild Cluster Bootstrap ---
reghdfe OUTCOME_VAR ENDOG_VAR CONTROLS, absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
boottest ENDOG_VAR, cluster(CLUSTER_VAR) boottype(mammen) reps(999) seed(12345)

log close
```

## 第 5 步：Python 交叉验证

```python
"""
IV 交叉验证：Stata vs Python (pyfixest)
"""
import pandas as pd
import pyfixest as pf

df = pd.read_stata("DATASET_PATH")

# 通过 pyfixest 进行 IV 估计
# 语法：Y ~ exog | FEs | endog ~ instrument
model_iv = pf.feols("OUTCOME_VAR ~ CONTROLS | FIXED_EFFECTS | ENDOG_VAR ~ INSTRUMENT(S)",
                     data=df, vcov={"CRV1": "CLUSTER_VAR"})
print("=== Python 2SLS ===")
print(model_iv.summary())

# OLS 对比
model_ols = pf.feols("OUTCOME_VAR ~ ENDOG_VAR + CONTROLS | FIXED_EFFECTS",
                      data=df, vcov={"CRV1": "CLUSTER_VAR"})
print("=== Python OLS ===")
print(model_ols.summary())

# 交叉验证
stata_coef = STATA_IV_COEF
python_coef = model_iv.coef()["ENDOG_VAR"]
pct_diff = abs(stata_coef - python_coef) / abs(stata_coef) * 100
print(f"\nCross-validation (2SLS on ENDOG_VAR):")
print(f"  Stata:  {stata_coef:.6f}")
print(f"  Python: {python_coef:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 0.1 else 'FAIL'}")
```

## 第 6 步：诊断总结

所有步骤完成后，提供以下内容：

1. **工具变量相关性**：KP F 值与 Stock-Yogo/Lee et al. 临界值的比较。偏 R 方。
2. **2SLS vs LIML**：如果估计值偏离，说明存在弱工具变量问题。
3. **工具变量有效性**：Hansen J 检验（仅过度识别时）。排除性约束的叙述性论证。
4. **内生性**：DWH 检验结果。如不拒绝，OLS 因效率更高而更优。
5. **弱工具变量推断**：AR 置信集（当 F < 23 时尤为重要）。
6. **LOSO 敏感性**：是否有单个聚类驱动结果？
7. **OLS vs IV 方向**：衰减偏误（IV > OLS）还是反向？
8. **交叉验证**：Stata vs Python 匹配结果。

## 高级模式参考

关于已发表论文中的高级 IV 模式（xtivreg2 面板 IV、份额偏移/Bartik 工具变量、k 类估计、通过 `spmat` 的空间滞后、带 `cluster()`/`idcluster()` 的 Bootstrap、多内生变量、交互固定效应），参见 `advanced-stata-patterns.md`。
