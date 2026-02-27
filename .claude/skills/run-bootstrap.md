---
description: "运行 Bootstrap 与重抽样推断管道（配对、Wild Cluster、残差、处理效应）"
user_invocable: true
---

# /run-bootstrap — Bootstrap 与重抽样推断管道

当用户调用 `/run-bootstrap` 时，执行全面的 Bootstrap 推断管道，涵盖配对聚类 Bootstrap、Wild Cluster Bootstrap（Rademacher/Mammen）、残差 Bootstrap、处理效应 Bootstrap（teffects 封装）以及通过 nlcom/parmest 的派生量推断。包含 Python 交叉验证。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 何时使用 Bootstrap 推断

- **聚类数较少**（< 50）：Wild Cluster Bootstrap 校正解析标准误的偏差
- **复杂估计量**：自定义程序、处理效应或无法获得解析标准误的派生量
- **面板数据的聚类重抽样**：配对聚类 Bootstrap 保持组内时间序列结构
- **非线性估计量**：边际效应、nlcom 派生量的 Bootstrap 标准误
- **发表稳健性**：审稿人越来越多地要求在解析 p 值之外提供 Bootstrap p 值

## 第 0 步：收集输入信息

向用户询问以下信息：

- **数据集**：.dta 文件路径
- **基准估计命令**：需要进行 Bootstrap 的回归或估计命令（如 `reghdfe Y X CONTROLS, absorb(FE) vce(cluster C)`）
- **关注的系数**：推断聚焦的变量
- **聚类变量**：聚类层面重抽样的变量
- **面板变量**（如为面板数据）：个体标识符，用于配对聚类 Bootstrap
- **时间变量**（如为面板数据）：时间标识符
- **Bootstrap 类型**：配对聚类、Wild Cluster、残差，或全部（默认：全部适用的）
- **重复次数**：探索性分析 200 次，发表使用 999 次（默认：999）
- **处理效应模型**（可选）：如使用 `teffects`，指定处理模型（如 `probit treatment covars`）
- **派生量**（可选）：需要 Bootstrap 的 nlcom 表达式（如长期效应、累积脉冲响应）

## 简洁 Bootstrap 前缀语法

对于简单回归，Stata 的 `bs` 前缀比 `bootstrap _b, reps(): command` 更简洁。两者均有效。模式来自 Culture & Development 复现（data_programs.zip）：

```stata
* 简洁前缀 — 可在 eststo 链中使用
eststo: bs, reps(500): reg OUTCOME_VAR TREATMENT_VAR CONTROLS, cluster(CLUSTER_VAR)

* 多个设定
eststo m1: bs, reps(500): reg Y X, cluster(cluster)
eststo m2: bs, reps(500): reg Y X CONTROLS, cluster(cluster)
eststo m3: bs, reps(500): reg Y X CONTROLS EXTRA_CONTROLS, cluster(cluster)
esttab m1 m2 m3, se b star(* 0.10 ** 0.05 *** 0.01)
```

`bs` vs `bootstrap _b, reps()`：
- `bs, reps(N): command` — 简写，可与 `eststo` 配合，语法更简单
- `bootstrap _b, reps(N) cluster() idcluster() saving():` — 完全控制，面板 Bootstrap 中需要 `idcluster()` 以及保存抽样结果到文件时必须使用

## 第 1 步：配对聚类 Bootstrap（Stata .do 文件）

对整个聚类进行有放回重抽样，保持聚类内部的相关结构。面板数据的标准方法。

```stata
/*==============================================================================
  Bootstrap 分析 — 第 1 步：配对聚类 Bootstrap
  参考：Cameron, Gelbach & Miller (2008), bootstrap-t
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_01_pairs.log", replace

use "DATASET_PATH", clear

* --- 基准估计（用于对比）---
eststo clear
eststo baseline: BASELINE_COMMAND
local b_analytic = _b[COEF_VAR]
local se_analytic = _se[COEF_VAR]
local p_analytic = 2 * ttail(e(df_r), abs(_b[COEF_VAR] / _se[COEF_VAR]))
di "Analytical: b = `b_analytic', SE = `se_analytic', p = `p_analytic'"

* --- 配对聚类 Bootstrap ---
* 面板数据需要 idcluster() — 每次抽样创建新的连续 ID
gen _cl = CLUSTER_VAR
cap tsset _cl TIME_VAR

bootstrap _b, seed(12345) reps(NREPS) cluster(CLUSTER_VAR) idcluster(_cl) ///
    nodots saving("data/temp/boot_pairs.dta", replace): ///
    BASELINE_COMMAND_WITHOUT_VCE

eststo boot_pairs
local b_boot = _b[COEF_VAR]
local se_boot = _se[COEF_VAR]

* --- 百分位置信区间 ---
* 注意：BCa 需要在 bootstrap 前缀命令中显式使用 saving。
* 默认仅输出百分位和 bc。仅当 bootstrap 使用了
* saving(, bca) 选项时才添加 bca。参见复现测试的 Issue #11。
cap noisily estat bootstrap, percentile bc
* 如需 BCa，使用以下命令重新运行 bootstrap：saving("file.dta", replace) bca

* --- Bootstrap 分布 ---
* 注意：`bootstrap _b` 保存的变量使用 `_b_` 前缀 + 变量名，
* 而非 `_bs_N` 编号。如变量 `x`，保存为 `_b_x`。
* 使用 `ds` 动态识别变量名（Issue #13）。
preserve
use "data/temp/boot_pairs.dta", clear
ds
local boot_var : word 1 of `r(varlist)'
hist `boot_var', bin(50) normal ///
    title("Pairs Cluster Bootstrap Distribution") ///
    xtitle("Coefficient Estimate") ytitle("Density") ///
    xline(`b_analytic', lcolor(cranberry) lpattern(dash)) ///
    note("Vertical line = analytical point estimate. N reps = NREPS")
graph export "output/figures/fig_boot_pairs_dist.pdf", replace
restore

log close
```

## 第 2 步：Wild Cluster Bootstrap（Stata .do 文件）

当聚类数较少（< 50）时首选。使用 Rademacher 或 Mammen 权重分布。

```stata
/*==============================================================================
  Bootstrap 分析 — 第 2 步：Wild Cluster Bootstrap
  参考：Cameron, Gelbach & Miller (2008); Roodman et al. (2019)
  包：boottest (Roodman)
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_02_wild.log", replace

use "DATASET_PATH", clear

* --- 运行基准回归 ---
BASELINE_COMMAND

* --- Rademacher 权重的 Wild Cluster Bootstrap ---
* 注意：boottest 可能在所有估计量类型后都不适用。在 reghdfe 之后效果最佳。
* 在 plain reg 或 xtreg 之后可能出现 r(198) 错误。对非 reghdfe
* 估计量始终使用 cap noisily 包裹（Issue #12）。
cap noisily boottest COEF_VAR, cluster(CLUSTER_VAR) boottype(rademacher) ///
    reps(NREPS) seed(12345) nograph
local wcb_p_rad = r(p)
local wcb_ci_lo_rad = r(CI)[1,1]
local wcb_ci_hi_rad = r(CI)[1,2]

* --- Mammen 权重的 Wild Cluster Bootstrap ---
boottest COEF_VAR, cluster(CLUSTER_VAR) boottype(mammen) ///
    reps(NREPS) seed(12345) graphname(wcb_mammen)
local wcb_p_mam = r(p)
local wcb_ci_lo_mam = r(CI)[1,1]
local wcb_ci_hi_mam = r(CI)[1,2]
graph export "output/figures/fig_boot_wild_mammen.pdf", replace

* --- Webb 权重（6 点分布）的 Wild Cluster Bootstrap ---
* 当聚类数 < 12 时首选
boottest COEF_VAR, cluster(CLUSTER_VAR) boottype(webb) ///
    reps(NREPS) seed(12345) nograph
local wcb_p_webb = r(p)

* --- 比较 ---
di "============================================="
di "WILD CLUSTER BOOTSTRAP RESULTS"
di "============================================="
di "  Rademacher: p = `wcb_p_rad',  CI = [`wcb_ci_lo_rad', `wcb_ci_hi_rad']"
di "  Mammen:     p = `wcb_p_mam',  CI = [`wcb_ci_lo_mam', `wcb_ci_hi_mam']"
di "  Webb:       p = `wcb_p_webb'"
di "============================================="

* --- 联合检验（如有多个系数）---
* boottest COEF_VAR1 COEF_VAR2, cluster(CLUSTER_VAR) boottype(mammen) reps(NREPS)

log close
```

## 第 3 步：残差 Bootstrap（Stata .do 文件）

在同方差假设下适用。对残差进行重抽样并重构因变量。

```stata
/*==============================================================================
  Bootstrap 分析 — 第 3 步：残差 Bootstrap
  在误差为 iid（同方差、无聚类）时适用
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_03_residual.log", replace

use "DATASET_PATH", clear

* --- 拟合基准模型并保存残差 ---
BASELINE_COMMAND
predict double _resid, residuals
predict double _yhat, xb

* --- 残差 Bootstrap 程序 ---
cap program drop resid_boot
program define resid_boot, rclass
    syntax, yvar(string) xvar(string) controls(string) fe(string) cluster(string)
    tempvar newresid newy
    * 有放回重抽样残差
    bsample
    gen `newresid' = _resid
    gen `newy' = _yhat + `newresid'
    reghdfe `newy' `xvar' `controls', absorb(`fe') vce(cluster `cluster')
    return scalar b = _b[`xvar']
end

simulate b_resid = r(b), reps(NREPS) seed(12345): ///
    resid_boot, yvar(OUTCOME_VAR) xvar(COEF_VAR) ///
    controls(CONTROLS) fe(FIXED_EFFECTS) cluster(CLUSTER_VAR)

* --- 残差 Bootstrap p 值 ---
BASELINE_COMMAND
local b_actual = _b[COEF_VAR]

count if abs(b_resid) >= abs(`b_actual')
local resid_p = r(N) / NREPS
di "Residual bootstrap p-value: `resid_p'"

* --- 残差 Bootstrap 置信区间（百分位法）---
_pctile b_resid, p(2.5 97.5)
di "Residual bootstrap 95% CI: [" r(r1) ", " r(r2) "]"

log close
```

## 第 4 步：处理效应的 Bootstrap（Stata .do 文件）

将 `teffects`（RA、IPW、AIPW）包裹在 `bootstrap` 中进行聚类稳健推断。模式来自 Acemoglu et al. (2019, JPE) Table 5。

```stata
/*==============================================================================
  Bootstrap 分析 — 第 4 步：Bootstrap 处理效应
  参考：Acemoglu, Naidu, Restrepo & Robinson (2019, JPE) Table 5
  模式：bootstrap 包裹计算 ATET 的自定义程序
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_04_teffects.log", replace

use "DATASET_PATH", clear

* --- 定义 RA-ATET 的自定义程序 ---
cap program drop tef_ra
program define tef_ra, rclass
    teffects ra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR), atet
    return scalar atet = _b[r1vs0.TREATMENT_VAR]
end

* --- 定义 IPW-ATET 的自定义程序（probit 第一阶段）---
cap program drop tef_ipw
program define tef_ipw, rclass
    teffects ipw (OUTCOME_VAR) (TREATMENT_VAR COVARIATES, probit), atet
    return scalar atet = _b[r1vs0.TREATMENT_VAR]
end

* --- 定义 AIPW-ATET 的自定义程序（双重稳健）---
cap program drop tef_aipw
program define tef_aipw, rclass
    teffects ipwra (OUTCOME_VAR COVARIATES) (TREATMENT_VAR COVARIATES, probit), atet
    return scalar atet = _b[r1vs0.TREATMENT_VAR]
end

* --- Bootstrap RA ---
bootstrap atet_ra = r(atet), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_tef_ra.dta", replace): tef_ra
eststo tef_ra_boot

* --- Bootstrap IPW ---
bootstrap atet_ipw = r(atet), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_tef_ipw.dta", replace): tef_ipw
eststo tef_ipw_boot

* --- Bootstrap AIPW ---
bootstrap atet_aipw = r(atet), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_tef_aipw.dta", replace): tef_aipw
eststo tef_aipw_boot

* --- 比较表 ---
esttab tef_ra_boot tef_ipw_boot tef_aipw_boot ///
    using "output/tables/tab_teffects_bootstrap.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitles("RA" "IPW" "AIPW") ///
    label booktabs replace ///
    title("Treatment Effects (ATET) with Cluster Bootstrap") ///
    note("Bootstrap SEs with NREPS replications, clustered at CLUSTER_VAR level." ///
         "IPW and AIPW use probit treatment model.")

log close
```

## 第 5 步：使用 parmest 和 nlcom 保存 Bootstrap 置信区间（Stata .do 文件）

用于派生量（如累积脉冲响应、期间平均效应）。

```stata
/*==============================================================================
  Bootstrap 分析 — 第 5 步：派生量与 parmest
  参考：DDCG Table 5 — nlcom 计算期间平均效应，parmest 导出置信区间
==============================================================================*/
clear all
set more off
set seed 12345

cap log close
log using "output/logs/bootstrap_05_derived.log", replace

use "DATASET_PATH", clear

* --- Bootstrap 完整估计 + 派生量 ---
cap program drop boot_derived
program define boot_derived, rclass
    BASELINE_COMMAND
    * 派生量：如期间平均效应
    * nlcom (avg_effect: (_b[lag0] + _b[lag1] + _b[lag2]) / 3)
    * return scalar avg = r(table)[1,1]
    return scalar b = _b[COEF_VAR]
end

bootstrap b = r(b), reps(NREPS) cluster(CLUSTER_VAR) seed(12345) ///
    saving("data/temp/boot_derived.dta", replace): boot_derived

* --- 通过 parmest 导出 Bootstrap 置信区间 ---
cap which parmest
if _rc != 0 {
    ssc install parmest, replace
}
parmest, saving("data/temp/boot_parmest.dta", replace) ///
    label eform stars(0.10 0.05 0.01)

* --- BCa vs 百分位比较 ---
* 注意：BCa 需要在 bootstrap 命令中显式使用 saving 和 bca 选项。
* 默认仅输出百分位和 bc（Issue #11）。
cap noisily estat bootstrap, percentile bc

di "============================================="
di "BOOTSTRAP CI COMPARISON"
di "============================================="
di "  Percentile CI:      [reported above]"
di "  Bias-corrected CI:  [reported above]"
di "  BCa CI:             [reported above]"
di "  If CIs differ substantially, the bootstrap"
di "  distribution is skewed — prefer BCa."
di "============================================="

log close
```

## 第 6 步：Python 交叉验证

```python
"""
Bootstrap 交叉验证：Stata vs Python (scipy, pyfixest)
"""
import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_stata("DATASET_PATH")

# --- 配对 Bootstrap（手动实现）---
np.random.seed(12345)
n_reps = 999
clusters = df["CLUSTER_VAR"].unique()
boot_coefs = []

for i in range(n_reps):
    # 有放回重抽样聚类
    boot_clusters = np.random.choice(clusters, size=len(clusters), replace=True)
    boot_df = pd.concat([df[df["CLUSTER_VAR"] == c].assign(**{"_boot_cl": j})
                         for j, c in enumerate(boot_clusters)])
    try:
        import pyfixest as pf
        model = pf.feols("OUTCOME_VAR ~ COEF_VAR + CONTROLS | FIXED_EFFECTS",
                         data=boot_df, vcov={"CRV1": "_boot_cl"})
        boot_coefs.append(model.coef()["COEF_VAR"])
    except Exception:
        pass

boot_coefs = np.array(boot_coefs)

# --- Bootstrap 统计量 ---
b_mean = np.mean(boot_coefs)
b_se = np.std(boot_coefs, ddof=1)
b_ci_pct = np.percentile(boot_coefs, [2.5, 97.5])

print("=== Python Pairs Cluster Bootstrap ===")
print(f"  Mean:          {b_mean:.6f}")
print(f"  SE:            {b_se:.6f}")
print(f"  95% CI (pct):  [{b_ci_pct[0]:.6f}, {b_ci_pct[1]:.6f}]")

# --- 与 Stata 交叉验证 ---
stata_boot_se = STATA_BOOT_SE  # 来自第 1 步日志
pct_diff = abs(b_se - stata_boot_se) / abs(stata_boot_se) * 100
print(f"\nCross-validation (bootstrap SE):")
print(f"  Stata:  {stata_boot_se:.6f}")
print(f"  Python: {b_se:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
print(f"  Status: {'PASS' if pct_diff < 5 else 'CHECK'}")
# 注意：Bootstrap 标准误比较使用 5% 阈值（非 0.1%），
# 因为 Bootstrap 标准误具有固有的模拟方差

# --- 覆盖率检查 ---
# 如果真实系数已知（如模拟），计算覆盖率
# coverage = np.mean((boot_ci_lo <= true_b) & (true_b <= boot_ci_hi))
```

## 第 7 步：诊断总结

所有步骤完成后，提供以下内容：

1. **解析 vs Bootstrap**：比较解析标准误、配对 Bootstrap 标准误和 Wild Cluster Bootstrap p 值。如果差异较大则标记。
2. **置信区间方法比较**：百分位、偏差校正和 BCa 置信区间。如果 BCa 与百分位不同，说明 Bootstrap 分布有偏。
3. **权重敏感性**（Wild Cluster）：Rademacher、Mammen 和 Webb 权重给出的 p 值是否相似？不一致暗示对少数聚类敏感。
4. **有效重复次数**：报告有效的重复次数（复杂估计量的 Bootstrap 中部分可能失败）。
5. **处理效应**：如果运行了第 4 步，比较 RA、IPW 和 AIPW 的 ATET 估计。一致性支持稳健性；不一致暗示模型敏感性。
6. **交叉验证**：Python vs Stata Bootstrap 标准误比较（目标：< 5% 差异，考虑模拟方差）。

## 所需 Stata 包

```stata
ssc install boottest, replace    // Wild Cluster Bootstrap (Roodman)
ssc install reghdfe, replace
ssc install ftools, replace
ssc install estout, replace
ssc install parmest, replace     // 导出 Bootstrap 置信区间
ssc install coefplot, replace
```

## 核心参考文献

- Cameron, A.C., Gelbach, J.B. & Miller, D.L. (2008). "Bootstrap-Based Improvements for Inference with Clustered Errors." REStat.
- Roodman, D., Nielsen, M.O., MacKinnon, J.G. & Webb, M.D. (2019). "Fast and Wild: Bootstrap Inference in Stata Using boottest." Stata Journal.
- Acemoglu, D., Naidu, S., Restrepo, P. & Robinson, J.A. (2019). "Democracy Does Cause Growth." JPE, 127(1), 47-100.
