---
description: "运行完整的双重差分（DID/TWFE/Callaway-Sant'Anna）分析管道"
user_invocable: true
---

# /run-did — 双重差分分析管道

当用户调用 `/run-did` 时，执行完整的 DID 分析管道，涵盖标准 TWFE、异质性稳健估计量（CS-DiD、dCDH、BJS）、Goodman-Bacon 分解、HonestDiD 敏感性分析、Wild Cluster Bootstrap、Python 交叉验证以及完整诊断。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 第 0 步：收集输入信息

在开始之前，向用户询问以下信息：

- **数据集**：.dta 文件路径
- **处理变量**：二值处理指标（0/1），或处理后指标
- **时间变量**：时期/年份标识符
- **因变量**：结果变量 Y（询问是否需要对数变换）
- **组别变量**：个体/实体标识符（如 state_id、firm_id）
- **首次处理变量**：标识每个个体首次接受处理的时期变量（Callaway-Sant'Anna 所需）；未处理组设为 0。如不可用，可协助从处理时间数据中创建
- **控制变量**：纳入的协变量（可为空）
- **聚类变量**：聚类标准误所用变量（默认：与组别变量相同）
- **事件研究的前导/滞后期数**（默认：前 10 期，后 15 期；根据数据跨度调整）
- **对照组偏好**：仅使用从未处理组，还是尚未处理组（默认：从未处理组）
- **CS-DiD 估计方法**：双重稳健（`dripw`）、逆概率加权（`ipw`）或结果回归（`reg`）（默认：`dripw`）

## 第 1 步：数据验证与描述统计（Stata .do 文件）

创建 .do 文件，在估计前验证数据结构：

```stata
/*==============================================================================
  DID 分析 — 第 1 步：数据验证与描述统计
  数据集：DATASET_PATH
  因变量：OUTCOME_VAR
  处理变量：TREAT_VAR（首次处理：FIRST_TREAT_VAR）
==============================================================================*/
clear all
set more off
set maxvar 32767

log using "output/logs/did_01_validation.log", replace

use "DATASET_PATH", clear

* --- 面板结构检查 ---
* 注意：如果 GROUP_VAR 是字符串变量，必须先编码为数值型。
* 当数据来自 CSV 文件时（如 ISO3 国家代码）这种情况很常见。
* 来自复现测试的 Issue #19。
cap confirm numeric variable GROUP_VAR
if _rc != 0 {
    di "GROUP_VAR is string — encoding to numeric..."
    encode GROUP_VAR, gen(_group_id)
    local GROUP_VAR "_group_id"
}
xtset GROUP_VAR TIME_VAR
xtdescribe

* --- 处理时间分布 ---
tab FIRST_TREAT_VAR if FIRST_TREAT_VAR > 0
di "Never-treated units: " _N - r(N)

* --- 处理组规模 ---
preserve
  keep if FIRST_TREAT_VAR > 0
  collapse (count) n_units = GROUP_VAR, by(FIRST_TREAT_VAR)
  list, clean
  save "data/temp/cohort_sizes.dta", replace
restore

* --- 按组别的处理前因变量趋势 ---
preserve
  gen treated_group = (FIRST_TREAT_VAR > 0)
  collapse (mean) mean_y = OUTCOME_VAR, by(TIME_VAR treated_group)
  twoway (connected mean_y TIME_VAR if treated_group == 1, lcolor(cranberry) mcolor(cranberry)) ///
         (connected mean_y TIME_VAR if treated_group == 0, lcolor(navy) mcolor(navy)), ///
    legend(order(1 "Treated" 2 "Control") rows(1)) ///
    title("Pre-Treatment Outcome Trends") ///
    xtitle("Time") ytitle("Mean OUTCOME_VAR") ///
    xline(EARLIEST_TREAT_YEAR, lpattern(dash) lcolor(gray))
  graph export "output/figures/fig_parallel_trends_raw.pdf", replace
restore

* --- 按处理状态的描述统计 ---
estpost tabstat OUTCOME_VAR CONTROLS if TIME_VAR < EARLIEST_TREAT_YEAR, ///
    by(treated_group) stat(mean sd min max n) columns(statistics)
esttab using "output/tables/tab_did_summary.tex", ///
    cells("mean(fmt(3)) sd(fmt(3)) min(fmt(3)) max(fmt(3)) count(fmt(0))") ///
    label booktabs replace noobs

log close
```

执行命令：`"D:\Stata18\StataMP-64.exe" -e do "code/stata/did_01_validation.do"`

读取 .log 文件，验证面板结构和处理编码是否正确。

## 第 2 步：标准 TWFE 与事件研究（Stata .do 文件）

```stata
/*==============================================================================
  DID 分析 — 第 2 步：TWFE 与事件研究
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/did_02_twfe.log", replace

use "DATASET_PATH", clear

* --- 标准 TWFE ---
eststo clear
eststo twfe_main: reghdfe OUTCOME_VAR TREAT_VAR CONTROLS, ///
    absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)

* 存储关键结果
local twfe_b    = _b[TREAT_VAR]
local twfe_se   = _se[TREAT_VAR]
local twfe_n    = e(N)
local twfe_r2   = e(r2_within)
local n_clust   = e(N_clust)
di "TWFE: b = `twfe_b', se = `twfe_se', N = `twfe_n', R2w = `twfe_r2', clusters = `n_clust'"

* --- TWFE 事件研究（手动构建前导/滞后项）---
gen rel_time = TIME_VAR - FIRST_TREAT_VAR
replace rel_time = . if FIRST_TREAT_VAR == 0  // 从未处理组：排除事件研究虚拟变量

* 创建事件时间虚拟变量，以 rel_time == -1 为参照期
forvalues k = K_LEADS(-1)2 {
    gen lead`k' = (rel_time == -`k') if !missing(rel_time)
    replace lead`k' = 0 if missing(lead`k')
}
forvalues k = 0/K_LAGS {
    gen lag`k' = (rel_time == `k') if !missing(rel_time)
    replace lag`k' = 0 if missing(lag`k')
}

eststo twfe_es: reghdfe OUTCOME_VAR lead* lag* CONTROLS, ///
    absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)

* 处理前前导项联合检验
testparm lead*
local pretrend_F = r(F)
local pretrend_p = r(p)
di "Pre-trend joint F-test: F = `pretrend_F', p = `pretrend_p'"

* 事件研究图
coefplot twfe_es, keep(lead* lag*) vertical yline(0, lcolor(gs10)) ///
    xline(K_LEADS, lpattern(dash) lcolor(gs10)) ///
    title("TWFE Event Study") ///
    xtitle("Periods Relative to Treatment") ytitle("Coefficient") ///
    ciopts(recast(rcap) lcolor(navy)) mcolor(navy) ///
    note("Joint pre-trend F = `pretrend_F' (p = `: di %5.3f `pretrend_p'')")
graph export "output/figures/fig_event_study_twfe.pdf", replace

log close
```

## 第 3 步：稳健 DID 估计量（Stata .do 文件）

```stata
/*==============================================================================
  DID 分析 — 第 3 步：异质性稳健估计量
  所需包：csdid, did_multiplegt, did_imputation, bacondecomp,
                     eventstudyinteract
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/did_03_robust.log", replace

use "DATASET_PATH", clear

* 确保从未处理组的 first_treat = 0（csdid 要求）
assert FIRST_TREAT_VAR == 0 if TREAT_VAR == 0

* --- 1. Callaway & Sant'Anna (2021) --- [首选]
* 双重稳健，组-时间 ATT，聚类 Bootstrap
* 注意：csdid 和 csdid_stats 对版本敏感。所有调用使用
* cap noisily 以处理版本差异导致的语法变化（Issue #20）。
cap noisily csdid OUTCOME_VAR CONTROLS, ivar(GROUP_VAR) time(TIME_VAR) gvar(FIRST_TREAT_VAR) ///
    method(dripw) notyet

* 聚合 — 使用 cap noisily 包裹（语法可能因版本而异，Issue #20）
cap noisily csdid_stats simple, estore(cs_simple)
cap noisily csdid_stats event, estore(cs_event)
cap noisily csdid_stats group, estore(cs_group)
cap noisily csdid_stats calendar, estore(cs_calendar)

* CS 事件研究图
cap noisily {
    csdid_plot, style(rcap) title("CS-DiD Event Study") ///
        xtitle("Periods Since Treatment") ytitle("ATT")
    graph export "output/figures/fig_event_study_cs.pdf", replace
}

* --- 2. de Chaisemartin & D'Haultfoeuille (2020) ---
* 使用 cap noisily 包裹 — 版本敏感的社区包（与 csdid 类似）
cap noisily did_multiplegt OUTCOME_VAR GROUP_VAR TIME_VAR TREAT_VAR, ///
    robust_dynamic dynamic(K_LAGS) placebo(K_LEADS) ///
    breps(100) cluster(CLUSTER_VAR)
* 注意：breps=100 是为了速度；最终结果建议增加到 500-1000

* --- 3. Borusyak, Jaravel, Spiess (2024) — 插补法 ---
cap noisily did_imputation OUTCOME_VAR GROUP_VAR TIME_VAR FIRST_TREAT_VAR, ///
    allhorizons pretrends(K_LEADS) minn(0)
if _rc == 0 {
    estimates store bjs
}

* --- 4. Sun & Abraham (2021) — 交互加权估计量 ---
gen event_time = TIME_VAR - FIRST_TREAT_VAR
replace event_time = . if FIRST_TREAT_VAR == 0
cap noisily eventstudyinteract OUTCOME_VAR lead* lag* CONTROLS, ///
    absorb(GROUP_VAR TIME_VAR) cohort(FIRST_TREAT_VAR) ///
    control_cohort(FIRST_TREAT_VAR == 0) ///
    vce(cluster CLUSTER_VAR)

* --- 5. Goodman-Bacon 分解 ---
* 使用 cap noisily 包裹 — bacondecomp 有版本敏感的依赖（Issue #2）
cap noisily {
    bacondecomp OUTCOME_VAR TREAT_VAR, id(GROUP_VAR) t(TIME_VAR) ddetail
    graph export "output/figures/fig_bacon_decomp.pdf", replace
}

* --- 比较表 ---
esttab cs_simple twfe_main bjs using "output/tables/tab_did_comparison.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("CS-DiD" "TWFE" "BJS Imputation") ///
    label booktabs replace ///
    title("DID Estimator Comparison") ///
    note("Standard errors clustered at CLUSTER_VAR level.")

log close
```

## 第 4 步：推断稳健性（Stata .do 文件）

```stata
/*==============================================================================
  DID 分析 — 第 4 步：推断稳健性
  HonestDiD (Rambachan-Roth), Wild Cluster Bootstrap
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/did_04_inference.log", replace

use "DATASET_PATH", clear

* --- Wild Cluster Bootstrap (Roodman et al.) ---
* 解决有限样本聚类推断问题（当聚类数 < 50 时尤为重要）
* 注意：boottest 在 reghdfe 之后效果最佳。在 plain reg、xtreg 或
* 非标准 VCE 的估计量之后可能失败（r(198)）。对非 reghdfe
* 估计量始终使用 cap noisily 包裹（Issue #1, #12）。
reghdfe OUTCOME_VAR TREAT_VAR CONTROLS, absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
cap noisily boottest TREAT_VAR, cluster(CLUSTER_VAR) boottype(mammen) reps(999) seed(12345)
* 报告：WCB p 值和 95% 置信区间

* --- HonestDiD：平行趋势违反的敏感性分析 ---
* 需要：honestdid 包
* 先运行事件研究，再应用 HonestDiD
reghdfe OUTCOME_VAR lead* lag* CONTROLS, absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
honestdid, pre(1/K_LEADS) post(1/K_LAGS) mvec(0(0.01)0.05)
* 解释：平行趋势可以被违反多少（M 参数），
* 处理效应才不再显著？

log close
```

## 第 5 步：Python 交叉验证

> 如需 R `fixest` 交叉验证或多语言比较，请在此步骤后使用 `/cross-check`。

```python
"""
DID 交叉验证：Stata vs Python (pyfixest)
"""
import pandas as pd
import pyfixest as pf

df = pd.read_stata("DATASET_PATH")

# 通过 pyfixest 进行 TWFE（与 Stata reghdfe 对应）
model = pf.feols("OUTCOME_VAR ~ TREAT_VAR + CONTROLS | GROUP_VAR + TIME_VAR",
                 data=df, vcov={"CRV1": "CLUSTER_VAR"})
print("=== Python TWFE ===")
print(model.summary())

# 交叉验证
stata_coef = STATA_TWFE_COEF  # 来自第 2 步日志
python_coef = model.coef()["TREAT_VAR"]
pct_diff = abs(stata_coef - python_coef) / abs(stata_coef) * 100
print(f"\nCross-validation:")
print(f"  Stata TWFE:  {stata_coef:.6f}")
print(f"  Python TWFE: {python_coef:.6f}")
print(f"  Difference:  {pct_diff:.4f}%")
print(f"  Status:      {'PASS' if pct_diff < 0.1 else 'FAIL'}")

# 通过 pyfixest 进行事件研究（如支持）
try:
    es_model = pf.feols(
        "OUTCOME_VAR ~ i(rel_time, ref=-1) + CONTROLS | GROUP_VAR + TIME_VAR",
        data=df, vcov={"CRV1": "CLUSTER_VAR"})
    pf.iplot(es_model)
except Exception as e:
    print(f"Event study in pyfixest failed: {e}")
```

## 第 6 步：可发表质量的输出

生成符合 TOP5 期刊格式的主要结果表：

```stata
/*==============================================================================
  DID 分析 — 第 6 步：最终表格（AER/TOP5 格式）
==============================================================================*/
clear all
set more off

log using "output/logs/did_06_tables.log", replace

use "DATASET_PATH", clear

* 运行所有设定并存储
eststo clear
* (1) CS-DiD，从未处理对照组
eststo m1: ... /* CS-DiD 设定 */
* (2) TWFE
eststo m2: reghdfe OUTCOME_VAR TREAT_VAR CONTROLS, absorb(GROUP_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
* (3) CS-DiD，尚未处理对照组
eststo m3: ... /* CS-DiD 尚未处理 */
* (4) 替代因变量
eststo m4: ... /* 替代因变量 */
* (5) 替代因变量 2
eststo m5: ... /* 如价格 */

* --- AER 风格表格 ---
esttab m1 m2 m3 m4 m5 using "output/tables/tab_did_main.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    mtitles("CS-DiD" "TWFE" "CS-DiD NYT" "Alt. Outcome" "Prices") ///
    scalars("N_clust Clusters" "r2_within Within R$^2$") ///
    addnotes("Standard errors clustered at CLUSTER_VAR level in parentheses." ///
             "CS-DiD: Callaway \& Sant'Anna (2021) doubly-robust estimator." ///
             "Column (1) uses never-treated; column (3) uses not-yet-treated control.") ///
    title("Effect of TREATMENT on OUTCOME") ///
    substitute(\_ _)

log close
```

## 第 7 步：诊断总结

所有步骤完成后，提供书面总结，涵盖以下内容：

1. **面板结构**：平衡/非平衡，N 个个体，T 个时期，N 个处理组，N 个从未处理组
2. **平行趋势**：处理前前导项是否联合不显著？前趋势图的视觉评估。HonestDiD M 敏感性结果。
3. **处理效应异质性**：CS-DiD、dCDH、BJS 给出的 ATT 与 TWFE 是否不同？Bacon 分解：TWFE 权重中有多大比例来自有问题的比较？
4. **推断稳健性**：Wild Cluster Bootstrap p 值（聚类数 < 50 时尤为重要）。HonestDiD：M 达到多少时显著性消失？
5. **推荐估计量**：基于诊断结果：
   - 统一处理时间 → TWFE 即可
   - 交错处理，同质效应 → TWFE 与稳健估计量一致
   - 交错处理，异质效应 → 优先使用 CS-DiD 或 BJS
6. **交叉验证**：Stata vs Python 系数匹配（目标：< 0.1% 差异）
7. **事件研究叙述**：描述动态处理效应模式

## 所需 Stata 包

首次运行前安装：
```stata
ssc install reghdfe
ssc install ftools
ssc install csdid
ssc install drdid
ssc install did_multiplegt
ssc install did_imputation
ssc install bacondecomp
ssc install eventstudyinteract
ssc install event_plot
ssc install boottest
ssc install honestdid
ssc install coefplot
```

## 执行注意事项

- 通过以下命令运行所有 Stata .do 文件：`"D:\Stata18\StataMP-64.exe" -e do "script.do"`
- 每次 Stata 执行后务必读取 `.log` 文件以检查错误
- 如果某个包未安装，先运行 `ssc install PACKAGE`，然后重新运行
- 在任何 Bootstrap/置换检验前使用 `set seed 12345` 以确保可重复性
- 图形导出为 PDF（矢量格式）以满足发表质量
- 所有表格使用 `booktabs` 格式，DID 系数保留 4 位小数
