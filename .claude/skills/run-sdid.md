---
description: "运行合成双重差分（Synthetic DID）分析管道"
user_invocable: true
---

# /run-sdid — 合成双重差分管道

当用户调用 `/run-sdid` 时，执行遵循 Arkhangelsky et al. (2021, AER) 的合成双重差分分析。SDID 结合了合成控制的单位权重和 DiD 的时间权重，产生的估计通常比单独使用任一方法更稳健。

## Stata 执行命令

通过自动审批的封装脚本运行 .do 文件：`bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"`。该封装脚本处理 `cd`、Stata 执行（`-e` 标志）以及自动日志错误检查。详见 `CLAUDE.md`。

## 何时使用 SDID vs 其他 DID 方法

- **SDID 首选情形**：处理组较少、对照组较多、交错采纳可通过队列特定 SDID 处理、对平行趋势存在担忧
- **CS-DiD 首选情形**：处理/对照组均较多、交错采纳是主要设计挑战、需要双重稳健估计
- **TWFE 首选情形**：统一处理时间、已确认同质处理效应

## 第 0 步：收集输入信息

向用户询问以下信息：

- **数据集**：.dta 文件路径（必须是平衡面板）
- **因变量**：结果变量 Y
- **个体变量**：实体标识符（州、企业等）
- **时间变量**：时期/年份标识符
- **处理变量**：二值指标（所有个体处理前为 0；处理组处理后为 1）
- **首次处理时期**（交错处理时）：如为交错采纳，最早的处理年份
- **聚类变量**：标准误聚类所用变量（默认：个体变量）

**重要提示**：始终使用用户提供的精确变量名。切勿硬编码 `lgdp`、`gdp` 等变量名 — 使用前先用 `ds` 或 `desc` 确认变量存在于数据集中（Issue #21）。

## 第 1 步：数据准备（Stata .do 文件）

```stata
/*==============================================================================
  SDID 分析 — 第 1 步：数据准备
  参考：Arkhangelsky, Athey, Hirshberg, Imbens & Wager (AER 2021)
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/sdid_01_prep.log", replace

use "DATASET_PATH", clear

* --- 验证平衡面板 ---
xtset UNIT_VAR TIME_VAR
xtdescribe
* SDID 要求平衡面板。如有缺失时期的个体需酌情删除。

* --- 识别处理组 ---
tab TREAT_VAR
bysort UNIT_VAR: egen ever_treated = max(TREAT_VAR)
tab ever_treated

* 用于权重估计的处理前时期
sum TIME_VAR if TREAT_VAR == 0 & ever_treated == 1
local T0 = r(max)  // 最后一个处理前时期
di "Last pre-treatment period: `T0'"

* 描述统计
estpost tabstat OUTCOME_VAR, by(ever_treated) stat(mean sd n) columns(statistics)

log close
```

## 第 2 步：SDID 估计（Stata .do 文件）

```stata
/*==============================================================================
  SDID 分析 — 第 2 步：主估计
  所需包：sdid (Clarke et al. 2023)
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/sdid_02_estimation.log", replace

use "DATASET_PATH", clear

* --- 合成双重差分 ---
* 注意：Jackknife VCE 要求每个处理时期至少有 2 个处理组个体。
* 对于处理时期仅有单个个体的交错处理，会出现 r(451) 错误。
* 使用 Bootstrap VCE 作为回退方案（Issue #25）。
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(jackknife) method(sdid) graph ///
    g1_opt(xtitle("") ytitle("Unit Weights")) ///
    g2_opt(xtitle("Time") ytitle("Outcome"))
if _rc != 0 {
    di "Jackknife VCE failed. Trying bootstrap VCE..."
    sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
        vce(bootstrap) method(sdid) seed(12345) reps(200)
}
graph export "output/figures/fig_sdid_main.pdf", replace

* 将结果存储为局部宏（不使用 ereturn post + estimates store，
* 这会清除 e-class 结果并导致 r(301) — Issue #24）
local sdid_att = e(ATT)
local sdid_se  = e(se)

* --- 对比：传统 DiD ---
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(jackknife) method(did)
if _rc != 0 {
    sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
        vce(bootstrap) method(did) seed(12345) reps(200)
}
local did_att = e(ATT)
local did_se  = e(se)

* --- 对比：合成控制 ---
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(jackknife) method(sc)
if _rc != 0 {
    sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
        vce(bootstrap) method(sc) seed(12345) reps(200)
}
local sc_att = e(ATT)
local sc_se  = e(se)

* --- SDID 诊断比较 ---
* SDID 估计应位于 SC 和 DiD 的边界之间
* 如果 DiD 和 SC 一致 → 对处理效应有高度信心
* 如果二者不一致 → SDID 提供折中方案

di "============================================="
di "SDID COMPARISON"
di "============================================="
di "  SDID:  ATT = `sdid_att' (SE = `sdid_se')"
di "  DiD:   ATT = `did_att' (SE = `did_se')"
di "  SC:    ATT = `sc_att' (SE = `sc_se')"
di "============================================="

* --- 手动比较表（因 estimates store 与 sdid 不兼容）---
* 使用 file write 生成整洁的 LaTeX 表格
file open _tab using "output/tables/tab_sdid_comparison.tex", write replace
file write _tab "\begin{table}[htbp]" _n
file write _tab "\centering" _n
file write _tab "\caption{Treatment Effect: SDID vs DiD vs SC}" _n
file write _tab "\begin{tabular}{lccc}" _n
file write _tab "\hline\hline" _n
file write _tab " & SDID & DiD & SC \\\\" _n
file write _tab "\hline" _n
file write _tab "ATT & " %9.4f (`sdid_att') " & " %9.4f (`did_att') " & " %9.4f (`sc_att') " \\\\" _n
file write _tab "SE  & (" %9.4f (`sdid_se') ") & (" %9.4f (`did_se') ") & (" %9.4f (`sc_se') ") \\\\" _n
file write _tab "\hline\hline" _n
file write _tab "\multicolumn{4}{p{12cm}}{\small\textit{Note:} " _n
file write _tab "SDID = Arkhangelsky et al. (2021). Bootstrap SEs.} \\\\" _n
file write _tab "\end{tabular}" _n
file write _tab "\end{table}" _n
file close _tab

log close
```

## 第 3 步：稳健性（Stata .do 文件）

```stata
/*==============================================================================
  SDID 分析 — 第 3 步：稳健性检验
==============================================================================*/
clear all
set more off
set seed 12345

log using "output/logs/sdid_03_robustness.log", replace

use "DATASET_PATH", clear

* --- 替代 VCE：Bootstrap ---
sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(bootstrap) reps(200) method(sdid) seed(12345)
local sdid_boot_att = e(ATT)
local sdid_boot_se  = e(se)

* --- 安慰剂：随机化处理分配 ---
* 置换推断：打乱处理/对照标签
cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(placebo) reps(200) method(sdid)
if _rc == 0 {
    local sdid_plac_att = e(ATT)
    local sdid_plac_se  = e(se)
}

* --- 逐一剔除个体 ---
* 检查对单个个体的敏感性
* LOSO 使用 Bootstrap VCE（Jackknife 可能失败，Issue #25）
levelsof UNIT_VAR if ever_treated == 0, local(controls)
foreach u of local controls {
    cap noisily sdid OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR if UNIT_VAR != `u', ///
        vce(bootstrap) method(sdid) seed(12345) reps(50)
    if _rc == 0 {
        di "LOSO (drop unit `u'): ATT = " e(ATT) " (SE: " e(se) ")"
    }
}

* --- 替代因变量 ---
cap noisily sdid ALT_OUTCOME_VAR UNIT_VAR TIME_VAR TREAT_VAR, ///
    vce(bootstrap) method(sdid) seed(12345) reps(200)
if _rc == 0 {
    local sdid_alt_att = e(ATT)
    local sdid_alt_se  = e(se)
}

log close
```

## 第 4 步：Python 交叉验证

```python
"""
SDID 交叉验证：使用 synthdid Python 包或手动实现
"""
import pandas as pd
import numpy as np

df = pd.read_stata("DATASET_PATH")

# 方案 1：使用 synthdid Python 包（如可用）
try:
    from synthdid.model import SynthDID
    model = SynthDID(df, unit="UNIT_VAR", time="TIME_VAR",
                     outcome="OUTCOME_VAR", treatment="TREAT_VAR")
    model.fit()
    print(f"Python SDID estimate: {model.att:.6f}")
    print(f"Python SDID SE (jackknife): {model.se:.6f}")
except ImportError:
    print("synthdid not available. Using pyfixest for TWFE comparison.")
    import pyfixest as pf
    model = pf.feols("OUTCOME_VAR ~ TREAT_VAR | UNIT_VAR + TIME_VAR",
                     data=df, vcov={"CRV1": "UNIT_VAR"})
    print(model.summary())

# 与 Stata 交叉验证
stata_sdid = STATA_SDID_COEF
python_coef = model.att if hasattr(model, 'att') else model.coef()["TREAT_VAR"]
pct_diff = abs(stata_sdid - python_coef) / abs(stata_sdid) * 100
print(f"\nCross-validation (SDID):")
print(f"  Stata:  {stata_sdid:.6f}")
print(f"  Python: {python_coef:.6f}")
print(f"  Diff:   {pct_diff:.4f}%")
```

## 第 5 步：诊断总结

所有步骤完成后，提供以下内容：

1. **SDID vs DiD vs SC**：SDID 是否位于 DiD 和 SC 之间？如果三者一致，可信度高。如果 DiD 和 SC 差异较大，讨论哪个识别假设更合理。
2. **单位权重**：权重集中在少数对照组个体上还是分散？集中的权重可能表明脆弱性。
3. **时间权重**：时间权重是否强调临近处理发生的处理前时期？这是预期的。
4. **推断**：报告 Jackknife 标准误、Bootstrap 标准误和安慰剂 p 值。注意是否存在不一致。
5. **LOSO 敏感性**：剔除单个对照组个体时结果是否变化？
6. **建议**：当 SC 权重产生良好的处理前拟合且 DiD 平行趋势存疑时，SDID 更优。如果 SC 的处理前拟合不佳且平行趋势可信，DiD 可能更优。

## 所需 Stata 包

```stata
ssc install sdid
ssc install reghdfe
ssc install ftools
```

## 核心参考文献

- Arkhangelsky, D., Athey, S., Hirshberg, D., Imbens, G. & Wager, S. (2021). "Synthetic Difference-in-Differences." AER, 111(12), 4088-4118.
- Clarke, D., Pailañir, D., Athey, S. & Imbens, G. (2023). "Synthetic Difference-in-Differences Estimation." Stata Journal.
