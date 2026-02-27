---
description: "运行 LASSO、双重选择后推断和正则化回归管道，用于变量选择与因果推断"
user_invocable: true
---

# /run-lasso — LASSO 与正则化回归管道

当用户调用 `/run-lasso` 时，执行完整的正则化回归管道，涵盖标准 LASSO 预测、交叉验证惩罚选择、Post-LASSO OLS、因果推断的双重选择后推断（Belloni, Chernozhukov, Hansen 2014）、严格 LASSO 有效推断以及 Python 交叉验证。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 何时使用 LASSO / 正则化

- **大量候选控制变量**：当有数十/数百个潜在控制变量时，需要有原则的变量选择
- **高维协变量下的因果推断**：双重选择后推断同时为因变量和处理变量方程选择控制变量，避免遗漏变量偏误的同时防止过拟合
- **预测任务**：当目标是预测而非推断
- **稳健性变量选择**：用数据驱动的选择补充人工选定的控制变量
- **避免挑选变量**：审稿人关注哪些控制变量被纳入 — LASSO 提供有原则的答案

**重要提示**：标准 LASSO **不提供**被选变量系数的有效推断。用于因果推断时，应使用双重选择后推断（第 4 步）或严格 LASSO（第 5 步）。

## 第 0 步：收集输入信息

向用户询问以下信息：

- **数据集**：.dta 文件路径
- **因变量**：结果变量 Y
- **处理变量**（如为因果推断）：关注其效应的关键变量
- **候选回归元**：全部候选控制变量列表（可以很大）
- **固定效应**（可选）：LASSO 前需吸收的固定效应
- **聚类变量**：选择后推断中聚类标准误所用变量
- **目的**：预测、变量选择，还是通过双重选择后推断进行因果推断
- **模型类型**：线性、logit 或 poisson（Stata 16+ `lasso` 均支持）。**注意**：当二值因变量与某些预测变量存在近乎完全分离时，`lasso logit` 可能出现 r(430) 收敛错误。使用 `cap noisily` 包裹，必要时回退到 `rlasso`（Issue #18）。

确定 Stata 版本：LASSO 内置命令（`lasso`、`dsregress`）需要 Stata 16+。早期版本使用社区包（`lassopack`：`cvlasso`、`rlasso`、`pdslasso`）。

## 第 1 步：标准 LASSO 变量选择（Stata .do 文件）

```stata
/*==============================================================================
  LASSO 分析 — 第 1 步：标准 LASSO 与交叉验证
  Stata 16+ 内置 lasso 命令
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_01_selection.log", replace

use "DATASET_PATH", clear

* --- 检查 Stata 版本是否支持内置 lasso ---
if c(stata_version) >= 16 {

    * 带交叉验证的标准 LASSO
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345)
    estimates store lasso_cv

    * 报告被选变量
    lassocoef, display(coef, penalized)
    di "Number of selected variables: " e(k_nonzero_sel)

    * 交叉验证函数（lambda 路径）
    cvplot
    graph export "output/figures/fig_lasso_cvplot.pdf", replace

    * Lambda 值
    di "Lambda (CV min):     " e(lambda_sel)
    di "Lambda (CV 1se):     " // 使用 selection(cv, serule) 获取 1-SE 规则

    * --- 1-SE 规则的 LASSO（更简约）---
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv, serule) folds(10) rseed(12345)
    estimates store lasso_1se
    lassocoef, display(coef, penalized)
    di "Number of selected (1-SE rule): " e(k_nonzero_sel)

}
else {
    * --- 社区包：cvlasso (lassopack) ---
    cap which cvlasso
    if _rc != 0 {
        ssc install lassopack, replace
    }

    cvlasso OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        lopt seed(12345) nfolds(10)
    local lambda_opt = e(lopt)

    * 在最优 lambda 处的 LASSO
    lasso2 OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        lambda(`lambda_opt')
    di "Selected variables: " e(selected)
}

log close
```

## 第 2 步：变量选择路径与诊断（Stata .do 文件）

```stata
/*==============================================================================
  LASSO 分析 — 第 2 步：选择路径与模型比较
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_02_path.log", replace

use "DATASET_PATH", clear

* --- LASSO 路径（系数随 lambda 的变化）---
if c(stata_version) >= 16 {
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, selection(cv) rseed(12345)

    * 系数路径图
    lassoknots, display(nonzero penalized)
    coefpath
    graph export "output/figures/fig_lasso_coefpath.pdf", replace
}
else {
    * lassopack 路径
    lasso2 OUTCOME_VAR CANDIDATE_REGRESSORS, long
    lasso2, lic(ebic)  // 扩展 BIC 用于选择
}

* --- 比较：LASSO 选择 vs 人工选择的控制变量 ---
eststo clear

* 全模型（所有候选变量）
eststo full_ols: reghdfe OUTCOME_VAR CANDIDATE_REGRESSORS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* LASSO 选择的模型
eststo lasso_ols: reghdfe OUTCOME_VAR LASSO_SELECTED_VARS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* 人工选择的控制变量（研究者选择）
eststo hand_ols: reghdfe OUTCOME_VAR HANDPICKED_CONTROLS, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* 最简模型（仅处理变量）
eststo min_ols: reghdfe OUTCOME_VAR TREATMENT_VAR, ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

esttab full_ols lasso_ols hand_ols min_ols ///
    using "output/tables/tab_lasso_comparison.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    mtitles("Full" "LASSO" "Hand-Picked" "Minimal") ///
    scalars("N Observations" "r2_within Within R$^2$") ///
    title("Treatment Effect: LASSO vs Alternative Control Sets") ///
    note("LASSO-selected controls chosen by 10-fold CV." ///
         "Treatment coefficient stability across control sets supports robustness.")

log close
```

## 第 3 步：Post-LASSO OLS（Stata .do 文件）

对 LASSO 选择的变量运行 OLS，获得无偏的系数估计。

```stata
/*==============================================================================
  LASSO 分析 — 第 3 步：Post-LASSO OLS
  LASSO 选择变量；OLS 在选定变量集上估计系数。
  这消除了 LASSO 系数的正则化偏误。
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_03_postlasso.log", replace

use "DATASET_PATH", clear

if c(stata_version) >= 16 {
    * LASSO 选择
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345)

    * Post-LASSO OLS：提取被选变量并运行 OLS
    * lassocoef 存储被选变量名
    * 注意：在小样本或信号较弱时，CV LASSO 可能选择 0 个变量。
    * 继续之前检查 e(k_nonzero_sel)（Issue #16-17）。
    local selected_vars ""
    if e(k_nonzero_sel) > 0 {
        matrix b = e(b_postselection)
        local names : colnames b
        foreach v of local names {
            if "`v'" != "_cons" {
                local selected_vars "`selected_vars' `v'"
            }
        }
        eststo postlasso: reghdfe OUTCOME_VAR `selected_vars', ///
            absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
    }
    else {
        di "WARNING: LASSO selected 0 variables. Skipping post-LASSO OLS."
        di "This can happen with small samples or low signal-to-noise ratio."
        di "Consider using rlasso (rigorous LASSO) from lassopack instead."
    }
}
else {
    * lassopack：rlasso 内置 post-LASSO
    rlasso OUTCOME_VAR CANDIDATE_REGRESSORS, cluster(CLUSTER_VAR)
    local selected = e(selected)
    reghdfe OUTCOME_VAR `selected', absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)
}

di "============================================="
di "POST-LASSO OLS"
di "============================================="
di "  Selected variables: `selected_vars'"
di "  N selected: " wordcount("`selected_vars'")
di "  N candidates: " wordcount("CANDIDATE_REGRESSORS")
di "============================================="

log close
```

## 第 4 步：因果推断的双重选择后推断（Stata .do 文件）

这是在因果推断中使用 LASSO 的核心方法。同时为因变量方程和处理变量方程选择控制变量，然后在选定控制变量的并集上估计处理效应。这避免了仅基于因变量方程选择控制变量所导致的遗漏变量偏误。

```stata
/*==============================================================================
  LASSO 分析 — 第 4 步：双重选择后推断 (PDS)
  参考文献：Belloni, Chernozhukov & Hansen (2014, REStud)
  核心思想：同时为 Y 和 D 方程选择控制变量
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_04_pds.log", replace

use "DATASET_PATH", clear

* --- 方法 1：Stata 16+ dsregress（推荐）---
if c(stata_version) >= 16 {
    * dsregress：内置双重选择
    * 语法：dsregress Y D, controls(候选控制变量) [选项]
    dsregress OUTCOME_VAR TREATMENT_VAR, ///
        controls(CANDIDATE_REGRESSORS) ///
        selection(cv) folds(10) rseed(12345) ///
        vce(cluster CLUSTER_VAR)
    estimates store pds_main

    * 报告各阶段选择的控制变量
    lassoinfo
    di "Controls selected for outcome equation: " e(k_nonzero_sel_o)
    di "Controls selected for treatment equation: " e(k_nonzero_sel_d)
}

* --- 方法 2：pdslasso（社区包，适用于任何 Stata 版本）---
cap which pdslasso
if _rc != 0 {
    net install pdslasso, from("https://raw.githubusercontent.com/statalasso/pdslasso/master")
}

pdslasso OUTCOME_VAR TREATMENT_VAR (CANDIDATE_REGRESSORS), ///
    cluster(CLUSTER_VAR)
estimates store pds_community

* --- 方法 3：手动双重选择 ---
* 步骤 A：因变量方程的 LASSO（Y 对候选变量）
* 步骤 B：处理变量方程的 LASSO（D 对候选变量）
* 步骤 C：Y 对 D + （A 选择 ∪ B 选择）的并集 进行 OLS

* 步骤 A
rlasso OUTCOME_VAR CANDIDATE_REGRESSORS
local selected_y = e(selected)

* 步骤 B
rlasso TREATMENT_VAR CANDIDATE_REGRESSORS
local selected_d = e(selected)

* 步骤 C：取并集
local union_controls : list selected_y | selected_d
local union_controls : list uniq union_controls

eststo pds_manual: reghdfe OUTCOME_VAR TREATMENT_VAR `union_controls', ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- 比较表 ---
esttab pds_main pds_community pds_manual ///
    using "output/tables/tab_pds_results.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(TREATMENT_VAR) label booktabs replace ///
    mtitles("dsregress" "pdslasso" "Manual PDS") ///
    title("Post-Double-Selection: Treatment Effect") ///
    note("Belloni, Chernozhukov \& Hansen (2014) post-double-selection." ///
         "LASSO selects controls for both outcome and treatment equations." ///
         "Final OLS uses union of selected controls.")

di "============================================="
di "POST-DOUBLE-SELECTION SUMMARY"
di "============================================="
di "  Y-equation selected controls: `selected_y'"
di "  D-equation selected controls: `selected_d'"
di "  Union (final controls):       `union_controls'"
di "  Treatment effect (PDS):       " _b[TREATMENT_VAR]
di "============================================="

log close
```

## 第 5 步：严格 LASSO 有效推断（Stata .do 文件）

```stata
/*==============================================================================
  LASSO 分析 — 第 5 步：严格 LASSO (rlasso)
  参考文献：Belloni, Chen, Chernozhukov & Hansen (2012)
  基于理论的惩罚，用于有效的选择后推断
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/lasso_05_rlasso.log", replace

use "DATASET_PATH", clear

* --- 严格 LASSO ---
* 使用理论证明的惩罚（非交叉验证），用于有效推断
* 惩罚考虑异方差性和聚类
cap which rlasso
if _rc != 0 {
    ssc install lassopack, replace
}

* 带聚类稳健惩罚的 rlasso
rlasso OUTCOME_VAR CANDIDATE_REGRESSORS, ///
    cluster(CLUSTER_VAR) robust

di "Rigorous LASSO selected: " e(selected)
di "N selected: " e(s)

* Post-rlasso OLS
local rlasso_selected = e(selected)
eststo rlasso_post: reghdfe OUTCOME_VAR TREATMENT_VAR `rlasso_selected', ///
    absorb(FIXED_EFFECTS) vce(cluster CLUSTER_VAR)

* --- 弹性网络 (alpha 在 0 和 1 之间) ---
* Alpha = 1 是 LASSO，alpha = 0 是岭回归
if c(stata_version) >= 16 {
    lasso linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345) grid(10, ratio(0.001))
    * 弹性网络：
    elasticnet linear OUTCOME_VAR CANDIDATE_REGRESSORS, ///
        selection(cv) folds(10) rseed(12345) alphas(0 0.25 0.5 0.75 1)
    estimates store enet
}

log close
```

## 第 6 步：Python 交叉验证

```python
"""
LASSO 交叉验证：Stata vs Python (sklearn, hdm 风格)
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV, Lasso, ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
import statsmodels.api as sm

df = pd.read_stata("DATASET_PATH")

# --- 准备数据 ---
y = df["OUTCOME_VAR"].values
X_candidates = df[CANDIDATE_REGRESSOR_LIST].values
treatment = df["TREATMENT_VAR"].values

# 标准化候选变量（LASSO 要求标准化输入）
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_candidates)

# --- 带交叉验证的 LASSO ---
lasso_cv = LassoCV(cv=10, random_state=12345, max_iter=10000)
lasso_cv.fit(X_scaled, y)

# 被选变量（非零系数）
selected_mask = lasso_cv.coef_ != 0
selected_names = [CANDIDATE_REGRESSOR_LIST[i]
                  for i in range(len(CANDIDATE_REGRESSOR_LIST))
                  if selected_mask[i]]
print(f"=== Python LASSO CV ===")
print(f"  Optimal lambda: {lasso_cv.alpha_:.6f}")
print(f"  N selected: {sum(selected_mask)}")
print(f"  Selected: {selected_names}")

# --- Post-LASSO OLS ---
X_selected = df[selected_names]
X_post = sm.add_constant(pd.concat([df[["TREATMENT_VAR"]], X_selected], axis=1))
post_lasso = sm.OLS(y, X_post).fit(cov_type="cluster",
                                    cov_kwds={"groups": df["CLUSTER_VAR"]})
print(f"\n=== Post-LASSO OLS ===")
print(f"  Treatment coef: {post_lasso.params['TREATMENT_VAR']:.6f}")
print(f"  Treatment SE:   {post_lasso.bse['TREATMENT_VAR']:.6f}")

# --- 双重选择后推断（手动实现）---
# 步骤 A：LASSO Y ~ 候选变量
lasso_y = LassoCV(cv=10, random_state=12345, max_iter=10000)
lasso_y.fit(X_scaled, y)
selected_y = set(np.where(lasso_y.coef_ != 0)[0])

# 步骤 B：LASSO D ~ 候选变量
lasso_d = LassoCV(cv=10, random_state=12345, max_iter=10000)
lasso_d.fit(X_scaled, treatment)
selected_d = set(np.where(lasso_d.coef_ != 0)[0])

# 步骤 C：OLS Y ~ D + 并集
union_idx = selected_y | selected_d
union_names = [CANDIDATE_REGRESSOR_LIST[i] for i in union_idx]
X_pds = sm.add_constant(pd.concat([df[["TREATMENT_VAR"]], df[union_names]], axis=1))
pds_model = sm.OLS(y, X_pds).fit(cov_type="cluster",
                                   cov_kwds={"groups": df["CLUSTER_VAR"]})
print(f"\n=== Python Post-Double-Selection ===")
print(f"  Y-selected: {len(selected_y)} vars")
print(f"  D-selected: {len(selected_d)} vars")
print(f"  Union: {len(union_idx)} vars")
print(f"  Treatment coef: {pds_model.params['TREATMENT_VAR']:.6f}")

# --- 与 Stata 交叉验证 ---
stata_pds_coef = STATA_PDS_COEF  # 来自第 4 步日志
python_pds_coef = pds_model.params["TREATMENT_VAR"]
pct_diff = abs(stata_pds_coef - python_pds_coef) / abs(stata_pds_coef) * 100
print(f"\nCross-validation (PDS treatment coef):")
print(f"  Stata:  {stata_pds_coef:.6f}")
print(f"  Python: {python_pds_coef:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 1 else 'CHECK'}")
# 注意：PDS 比较使用 1% 阈值（不同 CV 折叠可能选择
# 不同变量，导致最终估计略有差异）

# --- CV 误差图 ---
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 5))
m_log_alphas = -np.log10(lasso_cv.alphas_)
ax.plot(m_log_alphas, np.mean(lasso_cv.mse_path_, axis=1), color="steelblue")
ax.fill_between(m_log_alphas,
                np.mean(lasso_cv.mse_path_, axis=1) - np.std(lasso_cv.mse_path_, axis=1),
                np.mean(lasso_cv.mse_path_, axis=1) + np.std(lasso_cv.mse_path_, axis=1),
                alpha=0.2, color="steelblue")
ax.axvline(-np.log10(lasso_cv.alpha_), linestyle="--", color="crimson",
           label=f"Optimal lambda = {lasso_cv.alpha_:.4f}")
ax.set_xlabel("-log10(lambda)")
ax.set_ylabel("Mean Squared Error (CV)")
ax.set_title("LASSO Cross-Validation Error")
ax.legend()
fig.savefig("output/figures/fig_lasso_cv_python.pdf", bbox_inches="tight")
plt.close()
```

## 第 7 步：R 中的 LASSO 倾向得分匹配（Stata .do 文件 + R）

LASSO 可用于估计倾向得分进行匹配样本的因果推断。模式来自 Abman, Lundberg & Ruta (JEEA 2024) — RTAs & Environment 复现（`jvae023`）：logistic LASSO 选择预测处理的协变量，然后在 LASSO 倾向得分上进行最近邻匹配，再在匹配面板上进行 DID/事件研究。

```r
# ============================================================
# R 中的 LASSO 倾向得分匹配 (glmnet)
# 参考：Abman, Lundberg & Ruta (JEEA 2024) jvae023
# ============================================================
library(glmnet)
library(lfe)         # 用于 felm() 面板回归
library(data.table)

# --- 步骤 A：为 LASSO 准备模型矩阵 ---
# 因变量：二值处理指标 (enviro_rta)
# 协变量：rta_cross_section 中除因变量和处理变量外的所有变量
lasso_data <- data.table(read.csv("rta_cross_section.csv"))

# model.matrix 为因子变量创建虚拟变量
X_mat <- model.matrix(
  ~ .,
  lasso_data[, date_signed := as.factor(date_signed)][
    !is.na(avg_biodiver),
    -c("Agreement", "Entry.into.Force", "treatment", "outcome")]
)
y_vec <- lasso_data[!is.na(avg_biodiver), treatment_var]

# --- 步骤 B：交叉验证的 logistic LASSO（50 折）---
set.seed(12345)
lasso_obj <- cv.glmnet(X_mat, y_vec, family = "binomial", nfolds = 50)

# 两种惩罚选择：
# lambda.min：最小化 CV 误差
# lambda.1se：高于最小值 1 个标准误（更简约，匹配时首选）
cat("Lambda min:", lasso_obj$lambda.min, "\n")
cat("Lambda 1SE:", lasso_obj$lambda.1se, "\n")

# --- 步骤 C：预测倾向得分 ---
panel_data[, prop_score := predict(lasso_obj, newx = X_panel,
                                    s = "lambda.min", type = "response")]

# --- 步骤 D：基于倾向得分的 1:1 最近邻匹配 ---
# 对每个处理组个体，找到倾向得分差异最小的对照组个体
treated_ids <- unique(panel_data[treatment == 1, id])
match_key <- data.table(treat_id = treated_ids, match_id = 0L, abs_diff = 99)

for (i in treated_ids) {
  ps_i <- unique(panel_data[id == i, prop_score])
  controls <- panel_data[treatment == 0 & id != i,]
  nearest <- controls[which.min(abs(prop_score - ps_i)), .(id, abs(prop_score - ps_i))]
  match_key[treat_id == i, c("match_id", "abs_diff") := nearest]
}

# --- 步骤 E：构建匹配面板 ---
matched_ids <- unique(c(match_key$treat_id, match_key$match_id))
matched_panel <- panel_data[id %in% matched_ids]

# 处理重复匹配（同一对照个体匹配多个处理个体）
rep_ids <- match_key[, .N, by = match_id][N > 1]
for (i in rep_ids$match_id) {
  n_extra <- match_key[match_id == i, .N] - 1
  matched_panel <- rbind(matched_panel,
                         rep(list(panel_data[id == i]), n_extra))
}

# --- 步骤 F：在匹配面板上进行 DID/事件研究 ---
# 注意：areg 或 lfe::felm 用于个体 + 年份固定效应
result <- felm(log(1 + outcome) ~ treatment + enviro_treatment | unit_id + year | 0 | 0,
               data = matched_panel)

# --- 步骤 G：匹配前后的重叠图 ---
par(mfrow = c(1, 2))
density_ctrl <- density(panel_data[treatment == 0, prop_score], bw = 0.03)
density_trt  <- density(panel_data[treatment == 1, prop_score], bw = 0.03)
plot(density_ctrl, main = "Full Sample P-Score", xlab = "Propensity Score")
lines(density_trt, col = "red")
legend("topright", c("Treated", "Control"), lty = 1, col = c("red", "black"))

density_ctrl_m <- density(matched_panel[treatment == 0, prop_score], bw = 0.03)
density_trt_m  <- density(matched_panel[treatment == 1, prop_score], bw = 0.03)
plot(density_ctrl_m, main = "Matched Sample P-Score", xlab = "Propensity Score")
lines(density_trt_m, col = "red")
```

**近零因变量的 IHS 变换**（同样来自 jvae023）：
```r
# 反双曲正弦变换：对于小正值优于 log(x+1)
# IHS(x) ≈ log(2x)（x 较大时）；≈ x（x 较小时）
ihs <- function(x) log(x + sqrt(x^2 + 1))
panel_data[, y_ihs := ihs(outcome_var)]
# 在 felm() 中使用 ihs(outcome) 作为因变量
```

**Stata 等价实现**（从 R 切换到 Stata 进行匹配样本回归时）：
```stata
* 在 R 中完成匹配后，将匹配面板导出为 .dta 并在 Stata 中运行
* areg 用于吸收匹配对固定效应（配对变量）
eststo m1: areg OUTCOME_VAR TREATMENT_VAR, a(MATCH_PAIR_FE) cluster(CLUSTER_VAR)
* reghdfe 等价写法：
eststo m1: reghdfe OUTCOME_VAR TREATMENT_VAR, absorb(MATCH_PAIR_FE) vce(cluster CLUSTER_VAR)
```

## 第 8 步：诊断总结

所有步骤完成后，提供以下内容：

1. **变量选择**：LASSO 选择了多少变量（对比总候选变量数）？关键理论控制变量是否被纳入？
2. **CV 误差图**：最小值是否清晰可辨，还是误差曲线平坦（暗示信号较弱）？
3. **Post-LASSO vs 全 OLS**：从 LASSO 选择切换到完整控制变量集时，处理效应系数是否发生较大变化？稳定性支持稳健性。
4. **双重选择后推断**：报告 Y 方程 vs D 方程选择的控制变量。如果并集远大于任一单独选择，说明单方程选择遗漏了重要混淆变量。
5. **PDS vs 人工选择**：比较 PDS 处理效应与人工设定。差异较大表明人工设定可能存在误设。
6. **严格 LASSO**：比较基于 CV 和基于理论（rlasso）选择的变量。如果一致，说明选择稳定。
7. **交叉验证**：Stata vs Python 双重选择后系数比较。

## 所需 Stata 包

```stata
* Stata 16+ 内置：lasso, dsregress, elasticnet（无需安装）

* 社区包（任何 Stata 版本）：
ssc install lassopack, replace     // cvlasso, rlasso, lasso2
net install pdslasso, from("https://raw.githubusercontent.com/statalasso/pdslasso/master")
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
```

## 核心参考文献

- Belloni, A., Chernozhukov, V. & Hansen, C. (2014). "Inference on Treatment Effects after Selection among High-Dimensional Controls." REStud, 81(2), 608-650.
- Belloni, A., Chen, D., Chernozhukov, V. & Hansen, C. (2012). "Sparse Models and Methods for Optimal Instruments with an Application to Eminent Domain." Econometrica, 80(6), 2369-2429.
- Tibshirani, R. (1996). "Regression Shrinkage and Selection via the Lasso." JRSSB.（LASSO 原始论文）
- Ahrens, A., Hansen, C.B. & Schaffer, M.E. (2020). "lassopack: Model Selection and Prediction with Regularized Regression in Stata." Stata Journal.
