---
description: "运行 logit/probit、倾向得分、处理效应（RA/IPW/AIPW）和条件 logit 分析管道"
user_invocable: true
---

# /run-logit-probit — Logit/Probit 与离散选择管道

当用户调用 `/run-logit-probit` 时，执行完整的离散选择和处理效应管道，涵盖标准 logit/probit 估计及边际效应、倾向得分估计、RA/IPW/AIPW 处理效应、条件 logit 离散选择、诊断检验（重叠、ROC、Hosmer-Lemeshow）以及 Python 交叉验证。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 适用场景

- **二值因变量**：Y 为 0/1 — 使用 logit 或 probit
- **倾向得分匹配/加权**：估计 P(Treatment=1|X) 用于因果推断
- **处理效应**：通过回归调整、IPW 或双重稳健（AIPW）估计 ATET
- **离散选择**：消费者/企业在备选方案中的选择 — 使用条件 logit (clogit)
- **有序因变量**：李克特量表、评级类别 — 使用 ologit/oprobit
- **多项因变量**：无序类别（职业、交通方式）— 使用 mlogit

## 第 0 步：收集输入信息

向用户询问以下信息：

- **数据集**：.dta 文件路径
- **因变量类型**：二值（0/1）、有序、多项或条件选择
- **因变量**：结果变量
- **处理变量**（如进行倾向得分/处理效应分析）：二值处理指标
- **协变量**：模型中的控制变量
- **选择组变量**（如条件 logit）：组标识符（如 household-year）
- **备选方案特定变量**（如条件 logit）：在备选方案间变化的变量
- **聚类变量**：聚类标准误所用变量
- **固定效应**（如适用）：需吸收的固定效应
- **权重变量**（可选）：抽样权重（如 `[pw=weight]`）
- **目的**：仅估计、用于匹配/加权的倾向得分，还是完整的处理效应分析

## 第 1 步：标准 Logit/Probit 估计（Stata .do 文件）

```stata
/*==============================================================================
  Logit/Probit 分析 — 第 1 步：标准估计与边际效应
  报告 AME（平均边际效应）和 MEM（均值处的边际效应）
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_01_estimation.log", replace

use "DATASET_PATH", clear

eststo clear

* --- Probit ---
eststo probit_main: probit OUTCOME_VAR TREATMENT_VAR COVARIATES, ///
    vce(cluster CLUSTER_VAR)

* 平均边际效应 (AME) — 大多数应用的首选
margins, dydx(*) post
eststo probit_ame
* AME：所有观测值上个体边际效应的平均值

* 重新运行 probit 以计算 MEM
probit OUTCOME_VAR TREATMENT_VAR COVARIATES, vce(cluster CLUSTER_VAR)
* 均值处的边际效应 (MEM) — 在所有 X 的均值处评估的效应
margins, dydx(*) atmeans post
eststo probit_mem

* --- Logit ---
eststo logit_main: logit OUTCOME_VAR TREATMENT_VAR COVARIATES, ///
    vce(cluster CLUSTER_VAR)

* Logit 的 AME
margins, dydx(*) post
eststo logit_ame

* --- 对比：LPM（线性概率模型）---
eststo lpm: reghdfe OUTCOME_VAR TREATMENT_VAR COVARIATES, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- 表格：系数 + AME ---
esttab probit_main logit_main probit_ame logit_ame lpm ///
    using "output/tables/tab_logit_probit.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    mtitles("Probit" "Logit" "Probit AME" "Logit AME" "LPM") ///
    title("Binary Outcome: Logit, Probit, and LPM") ///
    note("Columns (1)-(2): coefficient estimates." ///
         "Columns (3)-(4): average marginal effects." ///
         "Column (5): linear probability model with FE." ///
         "Standard errors clustered at CLUSTER_VAR level.")

* --- AME vs MEM 比较 ---
di "============================================="
di "MARGINAL EFFECTS COMPARISON"
di "============================================="
di "  Probit AME (treatment): " _b[TREATMENT_VAR]  // 来自 margins, dydx post
di "  Probit MEM (treatment): [from MEM estimation]"
di "  Logit AME (treatment):  [from logit margins]"
di "  LPM coefficient:        [from reghdfe]"
di "  If AME ≈ MEM ≈ LPM: effects are approximately linear"
di "  If they diverge: nonlinearity matters"
di "============================================="

log close
```

## 第 2 步：倾向得分估计（Stata .do 文件）

遵循 Acemoglu et al. (2019, JPE) Table A11 模式。

```stata
/*==============================================================================
  Logit/Probit 分析 — 第 2 步：倾向得分估计
  参考：DDCG Table A11 — 用 probit 估计倾向得分，predict _pscore
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_02_pscore.log", replace

use "DATASET_PATH", clear

* --- 通过 probit 估计倾向得分 ---
probit TREATMENT_VAR COVARIATES i.YEAR_VAR, vce(cluster CLUSTER_VAR)

* 边际效应（用于报告）
margins, dydx(COVARIATES) post
eststo pscore_margins

* 预测倾向得分
probit TREATMENT_VAR COVARIATES i.YEAR_VAR, vce(cluster CLUSTER_VAR)
predict _pscore, pr

* --- 倾向得分诊断 ---
* 按处理状态的描述统计
tabstat _pscore, by(TREATMENT_VAR) stat(mean sd min p5 p25 p50 p75 p95 max n)

* --- 重叠/共同支撑 ---
* 核密度图（遵循 DDCG Figure A5/A6）
twoway (kdensity _pscore if TREATMENT_VAR == 1, lcolor(cranberry) lwidth(medthick)) ///
       (kdensity _pscore if TREATMENT_VAR == 0, lcolor(navy) lwidth(medthick)), ///
    legend(order(1 "Treated" 2 "Control") rows(1)) ///
    title("Propensity Score Overlap") ///
    xtitle("Propensity Score") ytitle("Density") ///
    note("Adequate overlap requires substantial density overlap.")
graph export "output/figures/fig_pscore_overlap.pdf", replace

* --- 直方图版本 ---
twoway (hist _pscore if TREATMENT_VAR == 1, fcolor(cranberry%40) lcolor(cranberry) width(0.02)) ///
       (hist _pscore if TREATMENT_VAR == 0, fcolor(navy%40) lcolor(navy) width(0.02)), ///
    legend(order(1 "Treated" 2 "Control") rows(1)) ///
    title("Propensity Score Distribution") ///
    xtitle("Propensity Score") ytitle("Frequency")
graph export "output/figures/fig_pscore_hist.pdf", replace

* --- 修剪至共同支撑 ---
sum _pscore if TREATMENT_VAR == 1, detail
local trim_lo = r(min)
sum _pscore if TREATMENT_VAR == 0, detail
local trim_hi = r(max)
gen byte common_support = (_pscore >= `trim_lo' & _pscore <= `trim_hi')
tab common_support TREATMENT_VAR

* --- 加权后的协变量平衡 ---
* IPW 权重
gen _ipw = cond(TREATMENT_VAR == 1, 1/_pscore, 1/(1-_pscore))

foreach var of varlist COVARIATES {
    sum `var' [aw=_ipw] if TREATMENT_VAR == 1
    local mean_t = r(mean)
    sum `var' [aw=_ipw] if TREATMENT_VAR == 0
    local mean_c = r(mean)
    sum `var'
    local sd_pool = r(sd)
    local std_diff = (`mean_t' - `mean_c') / `sd_pool'
    di "Balance `var': std diff = `std_diff' (target: < 0.1)"
}

log close
```

## 第 3 步：处理效应 — RA、IPW、AIPW（Stata .do 文件）

遵循 Acemoglu et al. (2019, JPE) Table 5 模式。

**重要提示：`teffects` 命令（ra、ipw、ipwra、nnmatch）仅适用于截面数据。** 对于每个个体有重复观测的面板数据会失败（r(459) 等错误）。处理面板数据时可以：(1) 先折叠为截面（如处理前后均值），(2) 使用手动 IPW 加权配合 `reghdfe`，或 (3) 使用 `bootstrap` 包裹在截面快照上计算 ATET 的自定义程序。当数据结构不确定时，所有 `teffects` 调用都应使用 `cap noisily` 包裹（Issue #15）。

```stata
/*==============================================================================
  Logit/Probit 分析 — 第 3 步：通过 teffects 估计处理效应
  参考：DDCG Table 5 — RA、IPW、AIPW，使用 probit 处理模型
  注意：teffects 要求截面数据（无重复观测）。
  面板数据需先折叠为截面或使用手动 IPW。
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_03_teffects.log", replace

use "DATASET_PATH", clear

eststo clear

* --- 1. 回归调整 (RA) ---
* 结果模型：OUTCOME ~ COVARIATES，分别对处理组和对照组
* 使用 cap noisily 包裹 — 对有重复观测的面板数据会失败（Issue #15）
cap noisily teffects ra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR), atet
if _rc == 0 {
    eststo tef_ra
    local atet_ra = _b[r1vs0.TREATMENT_VAR]
    di "RA-ATET: `atet_ra'"
}
else {
    di "teffects ra failed (likely panel data with repeated obs). Skipping."
}

* --- 2. 逆概率加权 (IPW)，使用 probit ---
* 处理模型：probit(TREATMENT ~ COVARIATES)
cap noisily teffects ipw (OUTCOME_VAR) (TREATMENT_VAR COVARIATES, probit), atet
if _rc == 0 {
    eststo tef_ipw
    local atet_ipw = _b[r1vs0.TREATMENT_VAR]
    di "IPW-ATET: `atet_ipw'"
}
else {
    di "teffects ipw failed (likely panel data). Skipping."
}

* --- 3. 双重稳健：AIPW（增强逆概率加权）---
* 结果模型 + 处理模型 — 任一模型正确即可保持一致性
cap noisily teffects ipwra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR COVARIATES, probit), atet
if _rc == 0 {
    eststo tef_aipw
    local atet_aipw = _b[r1vs0.TREATMENT_VAR]
    di "AIPW-ATET: `atet_aipw'"
}
else {
    di "teffects ipwra failed (likely panel data). Skipping."
}

* --- 4. 最近邻匹配 ---
cap noisily teffects nnmatch (OUTCOME_VAR COVARIATES) (TREATMENT_VAR), ///
    atet nneighbor(5) metric(mahalanobis)
if _rc == 0 {
    eststo tef_nn
    local atet_nn = _b[r1vs0.TREATMENT_VAR]
    di "NN-Match ATET: `atet_nn'"
}
else {
    di "teffects nnmatch failed (likely panel data). Skipping."
}

* --- 比较表 ---
esttab tef_ra tef_ipw tef_aipw tef_nn ///
    using "output/tables/tab_treatment_effects.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("RA" "IPW" "AIPW" "NN-Match") ///
    label booktabs replace ///
    title("Average Treatment Effect on the Treated (ATET)") ///
    note("RA = regression adjustment. IPW = inverse probability weighting (probit)." ///
         "AIPW = augmented IPW (doubly robust). NN = nearest-neighbor matching." ///
         "AIPW is preferred: consistent if either outcome or treatment model correct.")

* --- 总结 ---
di "============================================="
di "TREATMENT EFFECTS COMPARISON"
di "============================================="
di "  RA-ATET:      `atet_ra'"
di "  IPW-ATET:     `atet_ipw'"
di "  AIPW-ATET:    `atet_aipw'"
di "  NN-ATET:      `atet_nn'"
di "  Convergence of RA and IPW supports AIPW."
di "  Large divergence suggests model sensitivity."
di "============================================="

log close
```

## 第 4 步：条件 Logit 离散选择（Stata .do 文件）

遵循 Mexico Retail Table 5 模式。

```stata
/*==============================================================================
  Logit/Probit 分析 — 第 4 步：条件 Logit（离散选择）
  参考：Mexico Retail Table 5 — 家庭门店选择的 clogit
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_04_clogit.log", replace

use "DATASET_PATH", clear

* --- 条件 logit (McFadden 选择模型) ---
* 数据必须为长格式：每个选择场合的每个备选方案一行
* GROUP_VAR 标识选择组（如 household-year）
* CHOICE_VAR 为 1 表示被选中的备选方案，0 表示未选中
* X 变量可以是备选方案特定的或与备选方案虚拟变量的交互项

eststo clear
eststo clogit_main: clogit CHOICE_VAR ALT_SPECIFIC_VARS ///
    [pw=WEIGHT_VAR], group(GROUP_VAR) vce(cluster CLUSTER_VAR)

* 边际效应（在选择组上取平均）
margins, dydx(*) post
eststo clogit_ame

* --- 替代设定 ---
* 加入附加控制变量的设定
eststo clogit_full: clogit CHOICE_VAR ALT_SPECIFIC_VARS ADDITIONAL_CONTROLS ///
    [pw=WEIGHT_VAR], group(GROUP_VAR) vce(cluster CLUSTER_VAR)

* --- 表格 ---
esttab clogit_main clogit_full clogit_ame ///
    using "output/tables/tab_conditional_logit.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("Baseline" "Full Controls" "AME") ///
    label booktabs replace ///
    title("Conditional Logit: Discrete Choice") ///
    note("Conditional logit estimated via clogit." ///
         "Choice groups defined by GROUP_VAR." ///
         "Standard errors clustered at CLUSTER_VAR level.")

log close
```

## 第 5 步：诊断检验（Stata .do 文件）

```stata
/*==============================================================================
  Logit/Probit 分析 — 第 5 步：模型诊断
  ROC、Hosmer-Lemeshow、链接检验、分类
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_05_diagnostics.log", replace

use "DATASET_PATH", clear

* --- 拟合主模型 ---
logit OUTCOME_VAR TREATMENT_VAR COVARIATES, vce(cluster CLUSTER_VAR)

* --- ROC 曲线和 AUC ---
lroc, title("ROC Curve") note("AUC = area under curve; 0.5 = random, 1.0 = perfect")
graph export "output/figures/fig_roc_curve.pdf", replace
lstat
* AUC > 0.7 可接受；> 0.8 良好；> 0.9 优秀

* --- Hosmer-Lemeshow 拟合优度检验 ---
* 不使用 vce(cluster) 重新拟合以兼容 estat gof
logit OUTCOME_VAR TREATMENT_VAR COVARIATES
estat gof, group(10)
* 原假设：模型拟合良好。拒绝（p < 0.05）→ 拟合不佳

* --- 链接检验 (Pregibon) ---
linktest
* _hat 应显著，_hatsq 应不显著
* _hatsq 显著提示误设（函数形式不正确）

* --- 分类表 ---
estat classification
* 报告灵敏度、特异度和总体正确分类率

* --- 伪 R 方比较 ---
di "============================================="
di "MODEL FIT DIAGNOSTICS"
di "============================================="
logit OUTCOME_VAR TREATMENT_VAR COVARIATES
di "  Pseudo R2 (logit):   " e(r2_p)
probit OUTCOME_VAR TREATMENT_VAR COVARIATES
di "  Pseudo R2 (probit):  " e(r2_p)
di "  AIC (logit):         [from estat ic]"
di "  BIC (logit):         [from estat ic]"
estat ic
di "============================================="

log close
```

## 第 6 步：扩展模型（Stata .do 文件）

```stata
/*==============================================================================
  Logit/Probit 分析 — 第 6 步：扩展模型
  多项 logit、有序 logit/probit、IV probit
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/logit_06_extensions.log", replace

use "DATASET_PATH", clear

* --- 多项 Logit（无序类别）---
* 当因变量有 3 个及以上无序类别时使用
eststo mlogit_main: mlogit MULTI_OUTCOME COVARIATES, ///
    vce(cluster CLUSTER_VAR) baseoutcome(BASE_CATEGORY)
margins, dydx(TREATMENT_VAR) predict(outcome(CATEGORY_1)) post
* 对每个因变量类别重复

* --- 有序 Logit ---
* 当因变量为有序变量时使用（李克特量表、评级）
eststo ologit_main: ologit ORDERED_OUTCOME COVARIATES, ///
    vce(cluster CLUSTER_VAR)
margins, dydx(TREATMENT_VAR) predict(outcome(CATEGORY_1)) post

* --- 有序 Probit ---
eststo oprobit_main: oprobit ORDERED_OUTCOME COVARIATES, ///
    vce(cluster CLUSTER_VAR)

* --- IV Probit（内生二值处理变量）---
* 当处理变量为二值且内生时
eststo ivprobit_main: ivprobit OUTCOME_VAR COVARIATES ///
    (TREATMENT_VAR = INSTRUMENT), vce(cluster CLUSTER_VAR)
margins, dydx(TREATMENT_VAR) post

log close
```

## 第 7 步：Python 交叉验证

```python
"""
Logit/Probit 交叉验证：Stata vs Python (statsmodels, sklearn)
"""
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report

df = pd.read_stata("DATASET_PATH")

# --- 通过 statsmodels 的 Logit ---
X = df[["TREATMENT_VAR"] + COVARIATES_LIST]
X = sm.add_constant(X)
y = df["OUTCOME_VAR"]

logit_model = sm.Logit(y, X).fit(cov_type="cluster",
                                  cov_kwds={"groups": df["CLUSTER_VAR"]})
print("=== Python Logit (statsmodels) ===")
print(logit_model.summary())

# --- 边际效应 (AME) ---
ame = logit_model.get_margeff(at="overall")
print("\n=== Average Marginal Effects ===")
print(ame.summary())

# --- 通过 statsmodels 的 Probit ---
probit_model = sm.Probit(y, X).fit(cov_type="cluster",
                                    cov_kwds={"groups": df["CLUSTER_VAR"]})
print("\n=== Python Probit (statsmodels) ===")
print(probit_model.summary())

# --- 与 Stata 交叉验证 ---
stata_logit_ame = STATA_LOGIT_AME  # 来自第 1 步的 AME
python_logit_ame = ame.margeff[0]  # 处理变量的 AME
pct_diff = abs(stata_logit_ame - python_logit_ame) / abs(stata_logit_ame) * 100
print(f"\nCross-validation (Logit AME on treatment):")
print(f"  Stata:  {stata_logit_ame:.6f}")
print(f"  Python: {python_logit_ame:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 0.5 else 'CHECK'}")
# 注意：AME 比较使用 0.5% 阈值（数值积分差异）

# --- ROC/AUC ---
y_pred_prob = logit_model.predict(X)
auc = roc_auc_score(y, y_pred_prob)
print(f"\nPython AUC: {auc:.4f}")

# --- sklearn 对比 ---
lr = LogisticRegression(penalty=None, max_iter=10000)
X_sk = df[["TREATMENT_VAR"] + COVARIATES_LIST]
lr.fit(X_sk, y)
print(f"sklearn Logit coef (treatment): {lr.coef_[0][0]:.6f}")
```

## 第 8 步：诊断总结

所有步骤完成后，提供以下内容：

1. **模型选择**：Logit vs probit — 系数不同但 AME 应相似。如果 AME 不一致，两者均报告并注明哪个更优。
2. **LPM 比较**：LPM 系数 vs logit/probit AME。如果相似，非线性影响较小。
3. **倾向得分**：重叠质量（视觉 + 数值）。如果共同支撑排除了 > 10% 的观测值则标记。
4. **处理效应**：RA、IPW、AIPW 的一致性。如果三者一致，结果稳健。如果 IPW 与 RA 不一致，处理模型可能存在误设。
5. **诊断检验**：ROC/AUC、Hosmer-Lemeshow、链接检验结果。标记拟合不佳的情况（AUC < 0.7 或 H-L 拒绝）。
6. **条件 Logit**（如适用）：IIA 假设讨论，边际效应解释。
7. **交叉验证**：Stata vs Python AME 比较。

## 所需 Stata 包

```stata
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install coefplot, replace
```

## 核心参考文献

- Acemoglu, D., Naidu, S., Restrepo, P. & Robinson, J.A. (2019). "Democracy Does Cause Growth." JPE, 127(1), 47-100.（倾向得分、teffects、bootstrap）
- Imbens, G.W. (2004). "Nonparametric Estimation of Average Treatment Effects Under Exogeneity." REStat.（IPW、重叠）
- McFadden, D. (1974). "Conditional Logit Analysis of Qualitative Choice Behavior."（条件 logit 基础）
- Cattaneo, M.D. (2010). "Efficient Semiparametric Estimation of Multi-Valued Treatment Effects." JoE.（处理效应）
