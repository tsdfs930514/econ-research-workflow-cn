---
description: "对基准回归结果运行稳健性检验套件——替代规范、子样本、聚类、Oster 界、野蛮聚类自助法"
user_invocable: true
---

# /robustness — 全面稳健性检验套件

当用户调用 `/robustness` 时，按以下步骤执行：

## 步骤 1：收集信息

向用户询问：

1. **基准回归设定**（必填）— 主回归方程，例如：
   - 因变量
   - 核心自变量
   - 控制变量
   - 固定效应
   - 聚类标准误层级
   - 示例：`Y = beta * Treatment + Controls + FE_firm + FE_year, cluster(firm)`
2. **数据集路径**（必填）— 数据集路径（.dta 或 .csv）
3. **方法类型**（必填）— DID、IV、RDD、Panel、OLS 之一
4. **替代因变量**（可选）— 替代结果变量列表
5. **方法专属检验所需的额外信息**（可选）：
   - DID：处理时间变量、处理前/后期数、首次处理变量
   - IV：工具变量、内生变量
   - RDD：驱动变量、断点值
   - Panel：个体和时间变量、滞后结构
6. **聚类数量**（重要）— 用于判断是否需要野蛮聚类自助法

## 步骤 1b：通过代理识别遗漏的稳健性检验

收集信息（步骤 1）后，使用 Task 工具调用 `robustness-checker` 代理，提供：
- 步骤 1 中的基准设定
- 方法类型（DID / IV / RDD / Panel / OLS）
- 用户已经执行的稳健性检验

该代理将返回一份按优先级排列的遗漏检验清单（高/中/低优先级）。将其建议合并到步骤 2 生成的检验套件中——添加模板尚未涵盖的所有高优先级检验。

## 步骤 2：生成 Stata .do 文件 — 通用稳健性检验

创建一个全面的 Stata .do 文件（例如 `code/stata/XX_robustness.do`），包含以下各部分。

**执行方式：**
```bash
"D:\Stata18\StataMP-64.exe" -e do "code/stata/XX_robustness.do"
```

```stata
/*==============================================================================
  稳健性检验
  基准设定: <specification>
  方法: <method type>
  生成日期: <current date>
==============================================================================*/

clear all
set more off
set seed 12345

cap log close
log using "output/logs/robustness.log", replace

use "<dataset path>", clear

* 存储基准结果以便比较
eststo clear

*===============================================================================
* 0. 基准设定
*===============================================================================
eststo baseline: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

local baseline_b = _b[<treatment>]
local baseline_se = _se[<treatment>]
local baseline_N = e(N)

*===============================================================================
* 1. 替代因变量
*===============================================================================
/* 如果提供了替代因变量 */
foreach alt_y in <alternative dep vars> {
    eststo alt_`alt_y': reghdfe `alt_y' <treatment> <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
}

*===============================================================================
* 2. 控制变量敏感性
*===============================================================================
* 最小控制变量（仅核心变量）
eststo min_ctrl: reghdfe <depvar> <treatment>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* 逐步添加控制变量以展示稳定性
local controls "<list of control variables>"
local cumulative ""
local i = 1
foreach ctrl of local controls {
    local cumulative "`cumulative' `ctrl'"
    eststo add_ctrl_`i': reghdfe <depvar> <treatment> `cumulative', ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
    local i = `i' + 1
}

*===============================================================================
* 3. 子样本回归
*===============================================================================
* 按时间段（样本对半分）
summarize <time var>, meanonly
local med = r(mean)
eststo sub_early: reghdfe <depvar> <treatment> <controls> if <time var> <= `med', ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
eststo sub_late: reghdfe <depvar> <treatment> <controls> if <time var> > `med', ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* 剔除极端值（上下 1%）
foreach var in <depvar> <key independent vars> {
    _pctile `var', p(1 99)
    local p1 = r(r1)
    local p99 = r(r2)
    gen byte outlier_`var' = (`var' < `p1' | `var' > `p99')
}
eststo no_outlier: reghdfe <depvar> <treatment> <controls> if outlier_<depvar> == 0, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

*===============================================================================
* 4. 替代固定效应
*===============================================================================
* 无固定效应
eststo no_fe: reg <depvar> <treatment> <controls>, vce(cluster <cluster var>)

* 仅个体固定效应
eststo fe_entity: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<entity fe>) vce(cluster <cluster var>)

* 仅时间固定效应
eststo fe_time: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<time fe>) vce(cluster <cluster var>)

* 个体 x 时间交互固定效应（如适用）
eststo fe_interact: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<entity fe>#<time fe>) vce(cluster <cluster var>)

*===============================================================================
* 5. 不同聚类标准误层级
*===============================================================================
* 在不同层级聚类
eststo clust_1: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster level 1>)
eststo clust_2: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster level 2>)
eststo clust_twoway: reghdfe <depvar> <treatment> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster level 1> <cluster level 2>)

*===============================================================================
* 6. 缩尾处理
*===============================================================================
* 在 1%/99% 缩尾
foreach var in <depvar> <continuous controls> {
    winsor2 `var', cuts(1 99) suffix(_w1)
    winsor2 `var', cuts(5 95) suffix(_w5)
}
eststo win_1_99: reghdfe <depvar>_w1 <treatment> <controls with _w1 suffix>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
eststo win_5_95: reghdfe <depvar>_w5 <treatment> <controls with _w5 suffix>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

*===============================================================================
* 7. 安慰剂检验 / 随机化推断
*===============================================================================
* 单次随机安慰剂
set seed 12345
gen treatment_placebo = runiform() > 0.5
eststo placebo_random: reghdfe <depvar> treatment_placebo <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
drop treatment_placebo

* 置换推断（500 次迭代）
* 随机打乱处理标签，每次估计系数
* 将实际系数与安慰剂系数分布进行比较
cap program drop permute_test
program define permute_test, rclass
    * 在聚类内置换处理变量
    tempvar rand
    gen `rand' = runiform()
    sort <cluster var> `rand'
    by <cluster var>: gen treatment_perm = (RUNNING_VAR >= CUTOFF)[1]
    reghdfe <depvar> treatment_perm <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
    return scalar b = _b[treatment_perm]
    drop treatment_perm
end

simulate b_perm = r(b), reps(500) seed(12345): permute_test
* 计算有多少置换系数超过基准系数
count if abs(b_perm) >= abs(`baseline_b')
local perm_p = r(N) / 500
di "Permutation p-value: `perm_p'"

*===============================================================================
* 8. 野蛮聚类自助法 (Roodman et al.)
*===============================================================================
* 聚类数 < 50 时尤为重要
reghdfe <depvar> <treatment> <controls>, absorb(<fixed effects>) vce(cluster <cluster var>)
boottest <treatment>, cluster(<cluster var>) boottype(mammen) reps(999) seed(12345)
* 报告: WCB p 值和 95% 置信区间

*===============================================================================
* 9. OSTER (2019) 系数稳定性 / 不可观测变量选择性
*===============================================================================
* psacalc 实现 Oster (2019) 的边界分析
* 检验需要多大程度的不可观测变量选择性（相对于可观测变量）
* 才能解释掉处理效应

* 第 1 步：无控制变量回归
reg <depvar> <treatment>, vce(cluster <cluster var>)
local b_uncontrolled = _b[<treatment>]
local r2_uncontrolled = e(r2)

* 第 2 步：有控制变量回归（psacalc 不加 FE）
reg <depvar> <treatment> <controls>, vce(cluster <cluster var>)
local b_controlled = _b[<treatment>]
local r2_controlled = e(r2)

* 第 3 步：Oster 边界，R_max = 1.3 * R2_full（Oster 建议值）
psacalc delta <treatment>, rmax(1.3)
local oster_delta = r(delta)

psacalc beta <treatment>, rmax(1.3) delta(1)
local oster_beta = r(beta)

di "============================================="
di "OSTER (2019) BOUNDS"
di "============================================="
di "  delta (proportional selection):  `oster_delta'"
di "  beta* (bias-adjusted estimate):  `oster_beta'"
di "  Interpretation: delta > 1 means unobservables"
di "  would need to be MORE important than observables"
di "  to explain away the effect."
di "============================================="
```

## 步骤 3：方法专属检验

根据方法类型，将方法专属稳健性检验追加到 .do 文件中：

### DID 专属检验

```stata
*===============================================================================
* 10. DID 专属稳健性检验
*===============================================================================

* --- 安慰剂处理前检验（虚假处理时间） ---
forvalues t = <earliest pre-period> / <period before treatment> {
    gen placebo_treat_`t' = (<entity is treated>) * (<time var> >= `t')
    eststo placebo_t`t': reghdfe <depvar> placebo_treat_`t' <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
    drop placebo_treat_`t'
}

* --- 不同处理窗口 ---
eststo did_narrow: reghdfe <depvar> <treatment> <controls> ///
    if abs(<time var> - <treatment time>) <= <narrow window>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* --- Goodman-Bacon (2021) 分解 ---
bacondecomp <depvar> <treatment>, id(<group var>) t(<time var>) ddetail
graph export "output/figures/fig_bacon_decomp.pdf", replace

* --- Callaway-Sant'Anna 与 TWFE 比较 ---
csdid <depvar> <controls>, ivar(<group var>) time(<time var>) gvar(<first treat var>) ///
    method(dripw) notyet
csdid_stats simple, estore(cs_simple)
* 比较 CS-DiD ATT(simple) 与 TWFE 系数

* --- HonestDiD 敏感性分析 (Rambachan-Roth) ---
* 运行事件研究，然后检验需要多大程度的平行趋势违反
* 才能推翻结果
reghdfe <depvar> lead* lag* <controls>, absorb(<group var> <time var>) vce(cluster <cluster var>)
honestdid, pre(1/<K_LEADS>) post(1/<K_LAGS>) mvec(0(0.01)0.05)
```

### IV 专属检验

```stata
*===============================================================================
* 10. IV 专属稳健性检验
*===============================================================================

* --- 第一阶段 ---
eststo first_stage: reghdfe <endogenous var> <instruments> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)
test <instruments>
local fs_F = r(F)

* --- 简约式 ---
eststo reduced_form: reghdfe <depvar> <instruments> <controls>, ///
    absorb(<fixed effects>) vce(cluster <cluster var>)

* --- LIML 估计（对弱工具变量稳健） ---
eststo iv_liml: ivreghdfe <depvar> <controls> ///
    (<endogenous var> = <instruments>), ///
    absorb(<fixed effects>) cluster(<cluster var>) liml
* LIML 与 2SLS 差异过大表明弱工具变量问题

* --- Anderson-Rubin 置信集（弱工具变量稳健） ---
ivreg2 <depvar> <controls> (<endogenous var> = <instruments>), ///
    cluster(<cluster var>) first ffirst endog(<endogenous var>)
* AR 置信区间不受工具变量强度影响

* --- 替代工具变量（如有提供） ---
foreach inst in <alternative instruments> {
    eststo iv_alt_`inst': ivreghdfe <depvar> <controls> ///
        (<endogenous var> = `inst'), ///
        absorb(<fixed effects>) cluster(<cluster var>)
}

* --- LOSO（逐一剔除群组） ---
levelsof <cluster var>, local(clusters)
foreach c of local clusters {
    cap ivreghdfe <depvar> <controls> (<endogenous var> = <instruments>) ///
        if <cluster var> != `c', absorb(<fixed effects>) cluster(<cluster var>)
    if _rc == 0 {
        di "LOSO (drop `c'): b = " _b[<endogenous var>] " (SE = " _se[<endogenous var>] ")"
    }
}

* --- 过度识别检验（如为过度识别） ---
* Hansen J 检验由 ivreg2 / ivreghdfe 报告
```

### RDD 专属检验

```stata
*===============================================================================
* 10. RDD 专属稳健性检验
*===============================================================================

* --- 带宽敏感性 ---
rdrobust <depvar> <running var>, c(<cutoff>) kernel(triangular) bwselect(mserd)
local bw_opt = e(h_l)

foreach m in 0.50 0.75 1.00 1.25 1.50 2.00 {
    local bw_test = `bw_opt' * `m'
    rdrobust <depvar> <running var>, c(<cutoff>) kernel(triangular) h(`bw_test')
    di "BW = `m'x optimal: tau = " e(tau_cl) " (SE = " e(se_tau_cl) ")"
}

* --- 多项式阶数敏感性 ---
forvalues p = 1/3 {
    rdrobust <depvar> <running var>, c(<cutoff>) kernel(triangular) bwselect(mserd) p(`p')
    di "p=`p': tau = " e(tau_cl) " (SE = " e(se_tau_cl) ")"
}

* --- 核函数敏感性 ---
foreach kern in triangular uniform epanechnikov {
    rdrobust <depvar> <running var>, c(<cutoff>) kernel(`kern') bwselect(mserd)
    di "`kern': tau = " e(tau_cl) " (SE = " e(se_tau_cl) ")"
}

* --- 甜甜圈 RDD ---
foreach hole in 0.5 1 2 5 {
    rdrobust <depvar> <running var> ///
        if abs(<running var> - <cutoff>) > `hole', c(<cutoff>) bwselect(mserd)
    di "Donut +-`hole': tau = " e(tau_cl)
}

* --- 操纵检验 (CJM 2020) ---
rddensity <running var>, c(<cutoff>) plot
graph export "output/figures/fig_density_test.pdf", replace

* --- 安慰剂断点 ---
sum <running var>, detail
local p25 = r(p25)
local p75 = r(p75)
rdrobust <depvar> <running var> if <running var> < <cutoff>, c(`p25') bwselect(mserd)
rdrobust <depvar> <running var> if <running var> > <cutoff>, c(`p75') bwselect(mserd)
```

### Panel 专属检验

```stata
*===============================================================================
* 10. 面板数据专属稳健性检验
*===============================================================================

* --- 替代滞后结构 ---
forvalues lag = 1/3 {
    gen L`lag'_<treatment> = L`lag'.<treatment>
    eststo lag_`lag': reghdfe <depvar> <treatment> L`lag'_<treatment> <controls>, ///
        absorb(<fixed effects>) vce(cluster <cluster var>)
}

* --- 动态面板 GMM（如适用） ---
xtabond2 <depvar> L.<depvar> <treatment> <controls>, ///
    gmm(L.<depvar>, lag(2 4)) iv(<treatment> <controls>) ///
    robust twostep small
* 报告: AR(1)、AR(2)、Hansen J

* --- Hausman 检验：固定效应 vs 随机效应 ---
xtreg <depvar> <treatment> <controls>, fe
estimates store fe_model
xtreg <depvar> <treatment> <controls>, re
estimates store re_model
hausman fe_model re_model

* --- Driscoll-Kraay 标准误（对截面相关稳健） ---
xtscc <depvar> <treatment> <controls>, fe lag(3)
```

## 步骤 4：生成稳健性汇总表

添加代码以输出汇总所有关键结果的表格：

```stata
*===============================================================================
* 稳健性汇总表
*===============================================================================

esttab baseline alt_* min_ctrl add_ctrl_* sub_* no_outlier ///
    no_fe fe_entity fe_time win_* ///
    using "output/tables/tab_robustness_summary.tex", ///
    keep(<treatment variable>) ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label nomtitle replace booktabs ///
    scalars("N Observations" "r2_within Within R$^2$" "N_clust Clusters") ///
    title("Robustness Summary") ///
    mtitles("Baseline" <appropriate titles for each model>) ///
    addnotes("Standard errors clustered at <cluster var> level in parentheses." ///
             "All specifications include <fixed effects> unless noted.")

log close
```

## 步骤 5：结果标记

运行稳健性检验后，分析结果：

1. **检查方向一致性**：处理变量系数在所有设定中是否保持相同方向？
2. **检查显著性**：在多少个设定中结果在 5% 水平显著？在 10% 水平呢？
3. **检查量级**：系数在各设定间变化幅度多大？如果任何设定偏离基准超过 50%，标记警告。
4. **Oster delta**：delta > 1？若是，则不可观测变量需要比可观测变量更重要才能解释掉该效应。
5. **野蛮聚类自助法**：WCB p 值与解析 p 值是否一致？若显著分歧则标记。
6. **置换 p 值**：实际系数是否处于置换分布的极端尾部？

报告：

```
稳健性检验汇总
=======================
检验设定总数: <N>
系数方向一致: <是/否>
在 5% 水平显著: <X / N 个设定>
在 10% 水平显著: <X / N 个设定>
系数范围: [<min>, <max>]（基准: <baseline coef>）

Oster (2019) delta: <value>（> 1 令人放心）
Oster (2019) beta*: <value>（delta=1 时的偏差修正估计）
野蛮聚类自助法 p 值: <value>
置换 p 值: <value>

主结论不成立的设定:
  - <设定名称>: coef = <value>, p = <value>
  - ...

输出文件:
  - code/stata/XX_robustness.do
  - output/tables/tab_robustness_summary.tex
  - output/logs/robustness.log
  - output/figures/fig_bacon_decomp.pdf（仅 DID）
  - output/figures/fig_density_test.pdf（仅 RDD）
```

## 所需 Stata 包

```stata
ssc install reghdfe
ssc install ftools
ssc install estout
ssc install winsor2
ssc install boottest
ssc install psacalc
* 方法专属:
ssc install bacondecomp     // DID
ssc install csdid           // DID
ssc install honestdid       // DID
ssc install ivreghdfe       // IV
ssc install ivreg2          // IV
ssc install ranktest        // IV
ssc install weakiv          // IV
net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace  // RDD
net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace  // RDD
ssc install xtabond2        // Panel GMM
ssc install xtscc           // Panel Driscoll-Kraay
ssc install coefplot
```
