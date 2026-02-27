---
description: "运行完整的面板数据（FE/RE/GMM）分析管道"
user_invocable: true
---

# /run-panel — 面板数据分析管道（FE/RE/GMM）

当用户调用 `/run-panel` 时，执行完整的面板数据分析管道，涵盖面板设定与诊断、固定效应 vs 随机效应估计及 Hausman 检验、序列相关与截面依赖检验、动态面板 GMM（如需要）以及 Python 交叉验证。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 所需 Stata 包

```stata
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install xtabond2, replace      // 系统/差分 GMM
cap ssc install xtserial, replace  // Wooldridge 检验 — 可能已从 SSC 移除（Issue #6）
ssc install xtscc, replace         // Driscoll-Kraay 标准误
ssc install coefplot, replace
```

**关于 xtserial 的说明**：该包在某些时期已从 SSC 移除。Stata 18 可能有内置替代命令。始终使用 `cap ssc install`，并将 `xtserial` 调用包裹在 `cap noisily` 中（Issue #6-7）。

## 第 0 步：收集输入信息

在开始之前，向用户询问以下信息：

- **数据集**：.dta 文件路径
- **面板个体变量**：实体标识符（如 firm_id、state_id、country）
- **面板时间变量**：时间标识符（如 year、quarter、month）
- **因变量**：结果变量 Y
- **核心自变量**：关注的自变量
- **控制变量**：其他协变量
- **聚类变量**：聚类标准误所用变量（通常与个体变量相同）
- **是否需要动态面板？**：是否包含因变量滞后项并使用 GMM 估计（是/否）
- **附加固定效应**：除个体和时间之外的固定效应（如行业、地区）

## 第 1 步：面板设定与描述（Stata .do 文件）

创建 Stata .do 文件进行面板设定和描述性分析：

```stata
* =============================================================================
* 面板数据 — 设定与描述
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear

* --- 设定面板结构 ---
xtset UNIT_VAR TIME_VAR

* --- 面板结构描述 ---
xtdescribe
* 报告：面板数量、时间跨度、缺失、平衡性

* --- 组间/组内变异分解 ---
xtsum OUTCOME_VAR REGRESSORS CONTROLS
* 报告：总体、组间和组内标准差
* 关键洞察：FE 利用组内变异；RE 同时利用两者

* --- 面板平衡性检查 ---
di "Panel balance check:"
tab TIME_VAR, missing
bysort UNIT_VAR: gen T_i = _N
tab T_i
drop T_i

* --- 描述统计 ---
summarize OUTCOME_VAR REGRESSORS CONTROLS, detail
```

执行并检查 .log 文件。报告面板结构（平衡 vs 非平衡、个体数与时间跨度、缺失期数）。着重说明组内与组间变异分解 — 如果组内变异相对于组间变异较小，固定效应估计可能不精确。

## 第 2 步：FE vs RE 估计（Stata .do 文件）

创建 Stata .do 文件进行核心固定效应和随机效应估计：

```stata
* =============================================================================
* 面板数据 — 固定效应 vs 随机效应
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear
xtset UNIT_VAR TIME_VAR

* --- 混合 OLS（基准，可能有偏）---
reg OUTCOME_VAR REGRESSORS CONTROLS, vce(cluster CLUSTER_VAR)
estimates store pooled_ols

* --- 固定效应 ---
xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe vce(cluster CLUSTER_VAR)
estimates store fe_model

* --- 随机效应 ---
xtreg OUTCOME_VAR REGRESSORS CONTROLS, re vce(cluster CLUSTER_VAR)
estimates store re_model

* --- Hausman 检验 ---
* 需要在不使用聚类 VCE 的情况下重新估计，以获得有效的 Hausman 检验
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe
estimates store fe_hausman
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, re
estimates store re_hausman

hausman fe_hausman re_hausman
* 原假设：RE 一致且有效（系数差异非系统性）
* 拒绝 => 使用 FE（RE 因个体效应与回归元相关而不一致）

local hausman_chi2 = r(chi2)
local hausman_p = r(p)
di "Hausman test chi2: `hausman_chi2'"
di "Hausman test p-value: `hausman_p'"
* 注意：当 FE 明显优于 RE 时，Hausman chi2 可以为负
*（方差矩阵之差不是正半定的）。这是 Stata 的已知行为
* — FE 仍然是正确选择。参见 Issue #9。
if `hausman_chi2' < 0 {
    di "Result: Negative chi2 (`hausman_chi2') — FE strongly dominates RE."
    di "  This occurs when V_FE - V_RE is not positive semi-definite."
    di "  Interpretation: FE is the correct model."
}
else if `hausman_p' < 0.05 {
    di "Result: Reject RE in favor of FE (p < 0.05)"
}
else {
    di "Result: Cannot reject RE (p >= 0.05) — RE may be preferred for efficiency"
}

* --- 使用 reghdfe 的多维固定效应（多个固定效应时首选）---
reghdfe OUTCOME_VAR REGRESSORS CONTROLS, absorb(UNIT_VAR TIME_VAR) vce(cluster CLUSTER_VAR)
estimates store fe_reghdfe
```

执行并检查 .log 文件。报告 Hausman 检验结果及推荐模型（FE 或 RE）。

## 第 3 步：诊断检验（Stata .do 文件）

创建 Stata .do 文件进行面板诊断检验：

```stata
* =============================================================================
* 面板数据 — 诊断检验
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear
xtset UNIT_VAR TIME_VAR

* --- 1. 序列相关：Wooldridge 检验 ---
* 原假设：面板数据中不存在一阶自相关
* 注意：xtserial 可能不可用（已从 SSC 移除）。使用 cap noisily 包裹。
cap noisily xtserial OUTCOME_VAR REGRESSORS CONTROLS
if _rc != 0 {
    di "xtserial not available. Skipping Wooldridge serial correlation test."
    di "Alternative: check AR(1) via xtabond2 diagnostics or estat abond."
}
* 如拒绝：使用聚类标准误或 Newey-West，或 AR(1) 校正

* --- 2. 截面依赖：Pesaran CD 检验 ---
* 原假设：不存在截面依赖
* 先运行 FE 模型
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe
cap noisily xtcsd, pesaran abs
if _rc != 0 {
    di "xtcsd not available. Skipping Pesaran CD test."
}
* 如拒绝：考虑使用 Driscoll-Kraay 标准误

* --- 3. 异方差性：修正的 Wald 检验 ---
* 原假设：各面板误差同方差
quietly xtreg OUTCOME_VAR REGRESSORS CONTROLS, fe
cap noisily xttest3
if _rc != 0 {
    di "xttest3 not available. Skipping Modified Wald test."
}
* 如拒绝：使用稳健/聚类标准误（已在使用）

* --- 4. 单位根检验（当 T 较大时）---
* 仅对 T 较大的宏观面板有意义
* xtunitroot llc OUTCOME_VAR, trend lags(aic 10)   // Levin-Lin-Chu
* xtunitroot ips OUTCOME_VAR, trend lags(aic 10)    // Im-Pesaran-Shin
* xtunitroot fisher OUTCOME_VAR, dfuller lags(4)     // Fisher 型 ADF

* --- 总结 ---
di "============================================="
di "Panel Diagnostics Summary"
di "============================================="
di "Run serial correlation, CD, and heteroskedasticity"
di "tests above. Use results to choose appropriate SEs."
di "============================================="
```

执行并检查 .log 文件。总结哪些诊断检验拒绝以及对标准误计算的影响：
- 序列相关 => 在个体层面聚类或使用 Newey-West
- 截面依赖 => 考虑 Driscoll-Kraay 标准误
- 异方差性 => 使用稳健/聚类标准误

## 第 4 步：动态面板 GMM（如需要）（Stata .do 文件）

仅在用户要求动态面板分析时创建此文件：

```stata
* =============================================================================
* 面板数据 — 动态面板 GMM (Arellano-Bond / Blundell-Bond)
* =============================================================================
clear all
set more off

use "DATASET_PATH", clear
xtset UNIT_VAR TIME_VAR

* --- 系统 GMM (Blundell-Bond) 通过 xtabond2 ---
* 需要：ssc install xtabond2
* 注意：使用 cap noisily，xtabond2 可能因特定面板结构而失败
*
* 动态滞后语法：已发表论文常用 L(1/N).var 表示 N 阶滞后：
*   L(1/4).y  = l.y l2.y l3.y l4.y   （因变量的 4 阶滞后）
*   L(1/8).y  = l.y ... l8.y          （8 阶滞后）
* 当 N > 4 阶滞后时，检验高阶滞后是否联合显著：
*   test l5.y l6.y l7.y l8.y
*
* HELMERT / 前向正交偏差：
* 部分论文（如 Acemoglu et al. 2019 JPE）使用 Helmert 变换数据
* 代替一阶差分。xtabond2 原生支持：
*   xtabond2 ... , orthogonal ...
* 也有作者定义自定义程序进行 Helmert 变换
*（参见已发表复现代码中的 "program define helm" 模式）。
*
* 仅差分 GMM (noleveleq)：
* 部分论文仅估计差分 GMM（非系统 GMM），添加：
*   xtabond2 ... , noleveleq ...
* 这将去掉水平方程，仅从一阶差分中估计。
*
cap noisily xtabond2 OUTCOME_VAR L.OUTCOME_VAR REGRESSORS CONTROLS, ///
    gmm(L.OUTCOME_VAR, lag(2 4)) ///
    iv(REGRESSORS CONTROLS) ///
    two robust small

if _rc != 0 {
    di "xtabond2 failed (rc = " _rc "). Skipping GMM estimation."
    di "Common causes: too few time periods, singular matrix, or panel gaps."
}
else {
    estimates store gmm_sys
}

* --- 关键诊断 ---
* 1. Hansen J 过度识别检验
*    原假设：工具变量有效。不希望拒绝。
di "Hansen J test p-value: " e(hansenp)

* 2. AR(1) 和 AR(2) 检验
*    AR(1)：预期拒绝（构造决定的）
*    AR(2)：不应拒绝，GMM 一致性要求
di "AR(1) test p-value: " e(ar1p)
di "AR(2) test p-value: " e(ar2p)

* 3. 工具变量过多检查
*    经验法则：工具变量数应 <= 组数
di "Number of instruments: " e(j)
di "Number of groups: " e(g)
if e(j) > e(g) {
    di "WARNING: Too many instruments relative to groups — consider collapsing"
    * 使用 collapse 选项重新估计
    xtabond2 OUTCOME_VAR L.OUTCOME_VAR REGRESSORS CONTROLS, ///
        gmm(L.OUTCOME_VAR, lag(2 4) collapse) ///
        iv(REGRESSORS CONTROLS) ///
        two robust small
    estimates store gmm_sys_collapse
}

* --- 差分 GMM (Arellano-Bond) 作为对比 ---
xtabond2 OUTCOME_VAR L.OUTCOME_VAR REGRESSORS CONTROLS, ///
    gmm(L.OUTCOME_VAR, lag(2 4)) ///
    iv(REGRESSORS CONTROLS) ///
    two robust small nodiffsargan
estimates store gmm_diff
```

执行并检查 .log 文件。报告：
- AR(2) 检验：GMM 有效性要求不拒绝
- Hansen J：工具变量有效性要求不拒绝
- 工具变量数与组数的比较

## 第 5 步：Python 交叉验证

创建 Python 脚本进行交叉验证：

```python
import pandas as pd
import pyfixest as pf

# 加载数据
df = pd.read_stata("DATASET_PATH")

# 通过 pyfixest 进行 FE 估计
model_fe = pf.feols("OUTCOME_VAR ~ REGRESSORS + CONTROLS | UNIT_VAR + TIME_VAR",
                     data=df,
                     vcov={"CRV1": "CLUSTER_VAR"})
print("=== Fixed Effects (pyfixest) ===")
print(model_fe.summary())

# 混合 OLS
model_ols = pf.feols("OUTCOME_VAR ~ REGRESSORS + CONTROLS",
                      data=df,
                      vcov={"CRV1": "CLUSTER_VAR"})
print("\n=== Pooled OLS (pyfixest) ===")
print(model_ols.summary())

# 与 Stata 交叉验证 FE 系数
stata_fe_coef = STATA_FE_COEF  # 来自第 2 步日志（reghdfe）
python_fe_coef = model_fe.coef()["MAIN_REGRESSOR"]
pct_diff = abs(stata_fe_coef - python_fe_coef) / abs(stata_fe_coef) * 100
print(f"\nCross-validation (FE coefficient on MAIN_REGRESSOR):")
print(f"  Stata FE:  {stata_fe_coef:.6f}")
print(f"  Python FE: {python_fe_coef:.6f}")
print(f"  Pct diff:  {pct_diff:.4f}%")
if pct_diff < 0.01:
    print("  PASS: Coefficients match within tolerance")
else:
    print("  WARNING: Coefficients diverge — investigate specification")
```

执行并报告结果。

## 第 6 步：输出生成

创建合并的 LaTeX 表格：

```stata
* --- 合并输出表 ---
esttab pooled_ols fe_model re_model fe_reghdfe using "output/tables/panel_results.tex", ///
    mtitles("Pooled OLS" "FE (xtreg)" "RE (xtreg)" "FE (reghdfe)") ///
    cells(b(star fmt(3)) se(par fmt(3))) ///
    starlevels(* 0.10 ** 0.05 *** 0.01) ///
    stats(N r2_w r2_b r2_o, labels("Observations" "R2 (within)" "R2 (between)" "R2 (overall)")) ///
    addnotes("Hausman test p-value: [from Step 2]" ///
             "Wooldridge serial corr test p-value: [from Step 3]" ///
             "Pesaran CD test p-value: [from Step 3]" ///
             "Cluster: CLUSTER_VAR") ///
    title("Panel Estimation Results") replace

* 如果估计了 GMM，添加单独的表格
* esttab fe_reghdfe gmm_sys gmm_diff using "output/tables/panel_gmm_results.tex", ///
*     mtitles("FE" "System GMM" "Difference GMM") ...
```

确保所有输出已保存：

- `output/tables/panel_results.tex` — 主要面板结果（Pooled OLS、FE、RE）
- `output/tables/panel_gmm_results.tex` — GMM 结果（如适用）
- 交叉验证报告（控制台输出）

## 解释指南

所有步骤完成后，提供书面总结：

1. **面板结构**：平衡还是非平衡？多少个体和时间跨度？是否有缺失期？
2. **组内与组间变异**：组内变异是否足以支持 FE？如果组内变异极小，FE 估计将会不精确。
3. **FE vs RE (Hausman)**：Hausman 检验倾向于哪个模型？如果选择 FE，表明个体效应与回归元存在相关性。
4. **诊断检验**：
   - 序列相关：是否存在？对推断的影响。
   - 截面依赖：是否存在？可能需要 Driscoll-Kraay 标准误。
   - 异方差性：是否存在？聚类标准误可处理此问题。
5. **GMM（如适用）**：
   - AR(2) 是否不显著？（有效性所需）
   - Hansen J 是否未拒绝？（工具变量有效性所需）
   - 工具变量数相对于组数是否合理？
   - GMM 中因变量滞后项的系数与 OLS 上界和 FE 下界的比较如何？（Nickell 偏误检查）
6. **交叉验证**：Stata 与 Python 的 FE 系数是否匹配？
7. **推荐设定**：基于诊断结果，推荐使用哪个模型和标准误设定。

## 执行注意事项

- 通过以下命令运行所有 Stata .do 文件：`"D:\Stata18\StataMP-64.exe" -e do "script.do"`（必须用 `-e` 自动退出）
- 每次 Stata 执行后务必读取 `.log` 文件以检查错误
- 所需 Stata 包：`reghdfe`、`ftools`、`estout`、`xtabond2`、`xtserial`、`xtscc`、`coefplot`（通过 `ssc install PACKAGE, replace` 安装）
- 如 `output/tables/` 和 `output/figures/` 目录不存在则创建
- 为每个管道生成 Stata 和 Python 代码
- Hausman 检验需先在不使用稳健/聚类标准误的情况下估计模型，再用聚类标准误重新估计用于报告

## 处理复现代码中的旧版 Stata 语法

已发表的复现包可能包含已废弃的 Stata 命令（Issue #23）：
- `set mem 250m` / `set memory` — Stata 18 中不需要（内存为动态分配）
- `clear matrix` — 已替换为 `clear all` 或 `matrix drop _all`
- `set matsize 800` — Stata 18 默认为 11000，通常足够

改编旧复现代码时，直接省略这些命令。不要在新 .do 文件中包含它们。

## 高级模式参考

关于已发表论文中的高级模式（通过 `nlcom` 链计算脉冲响应、Helmert/前向正交偏差、HHK 最小距离估计量、k 类估计、带 `cluster()`/`idcluster()` 的 Bootstrap、多维聚类、交互异质性、矩阵运算），参见 `advanced-stata-patterns.md`。
