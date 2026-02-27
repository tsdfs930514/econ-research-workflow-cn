---
paths:
  - "**/*.do"
---

# Stata 代码规范 (Stata Code Conventions)

以下规范适用于本项目中的所有 Stata .do 文件。

## 文件头模板

每个 .do 文件**必须**以如下头部块开始：

```stata
/*==============================================================================
Project:    [Project Name]
Version:    [vN]
Script:     [filename.do]
Purpose:    [简要说明]
Author:     [Name]
Created:    [Date]
Modified:   [Date]
Input:      [输入文件]
Output:     [输出文件]
==============================================================================*/
```

## 标准设置

每个 .do 文件须在文件头之后立即包含以下设置：

```stata
version 18
clear all
set more off
set maxvar 32767
set matsize 11000
set seed 12345
```

## 日志记录

每个 .do 文件必须：
1. 先关闭已有日志（使用 `cap log close` 避免无日志时报错）
2. 启动新日志
3. 以 `log close` 结束

```stata
cap log close
log using "output/logs/XX_script_name.log", replace
* ... 所有代码 ...
log close
```

## 聚类标准误 (Cluster Standard Errors)

所有回归**默认**使用 `vce(cluster var)`。除非有明确的合理说明，不得报告非聚类标准误。

```stata
reghdfe y x1 x2, absorb(fe) vce(cluster firmid)
```

## 固定效应

多维固定效应使用 `reghdfe`，搭配 `absorb()` 语法：

```stata
reghdfe y x1 x2, absorb(firmid year) vce(cluster firmid)
```

单维固定效应也优先使用 `reghdfe`，以保持一致性。

## 表格输出

使用 `esttab`/`estout` 生成 LaTeX 表格。使用 `estimates store` 存储估计结果：

```stata
eststo clear
reghdfe y x1 x2, absorb(fe) vce(cluster firmid)
estimates store m1
reghdfe y x1 x2 x3, absorb(fe) vce(cluster firmid)
estimates store m2
esttab m1 m2 using "output/tables/results.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace
```

注意：系数使用 4 位小数（TOP5 因果推断标准）。

## 变量标签

所有变量**必须**有标签。在 `gen` 或 `rename` 之后立即使用 `label variable`：

```stata
gen log_wage = ln(wage)
label variable log_wage "Log of hourly wage"
```

## 数据安全

- **不得**写入 `data/raw/`——原始数据为只读。
- 所有修改写入 `data/clean/` 或 `data/temp/`。
- 清洗后数据使用描述性命名，必要时加版本后缀。

```stata
* 正确
save "data/clean/panel_cleaned.dta", replace

* 错误——绝对不要这样做
save "data/raw/original_data.dta", replace
```

## 路径规范

使用相对于项目根目录的相对路径。在每个 .do 文件或 master.do 文件顶部定义全局宏路径：

```stata
global root    "."
global data    "$root/data"
global raw     "$data/raw"
global clean   "$data/clean"
global temp    "$data/temp"
global output  "$root/output"
global tables  "$output/tables"
global figures "$output/figures"
global logs    "$output/logs"
```

## 可复现性

在任何随机化、自助法或模拟操作之前设置 `set seed 12345`：

```stata
set seed 12345
bootstrap, reps(1000) cluster(firmid): reg y x1 x2
```

始终保存中间数据集，使得每个脚本可以独立运行。

## 防御性编程

使用 `isid` 和 `assert` 验证数据完整性：

```stata
* 验证唯一标识符
isid panel_id year

* 验证预期值域
assert treatment >= 0 & treatment <= 1
assert !missing(outcome, treatment, running_var)

* 验证面板结构
xtset panel_id year
assert r(balanced) == "strongly balanced"
```

### 社区包防护（源自 Issues #1-#25）

所有 SSC/社区命令必须使用 `cap noisily` 包裹，原因：
- 可能未安装、被重命名或存在版本兼容性问题
- 其 `e()` 标量可能因版本而异
- 部分已从 SSC 移除（如 `xtserial`——Issue #6-7）

```stata
* 正确：防御性安装 + 防御性调用
cap ssc install xtserial, replace        // cap: 如已从 SSC 移除可能失败
cap noisily xtserial y x1 x2            // cap noisily: 优雅地处理失败
if _rc != 0 {
    di "xtserial unavailable. Skipping."
}

* 错误：裸调用，出错时直接中断脚本
ssc install xtserial, replace
xtserial y x1 x2
```

**以下命令必须始终使用 `cap noisily` 包裹：**

| 命令 | 包名 | 风险 |
|---------|---------|------|
| `csdid` / `csdid_stats` | csdid | 语法随版本变化（Issue #20） |
| `bacondecomp` | bacondecomp | 依赖问题（Issue #2） |
| `did_multiplegt` | did_multiplegt | 版本敏感 |
| `did_imputation` | did_imputation | 版本敏感 |
| `eventstudyinteract` | eventstudyinteract | 版本敏感 |
| `sdid` | sdid | 渐进处理时 jackknife 失败（Issue #25） |
| `boottest` | boottest | 非 reghdfe 估计后失败（Issue #1, #12） |
| `xtserial` | xtserial | 已从 SSC 移除（Issue #6-7） |
| `xtcsd` | xtcsd | 可能不可用（Issue #8） |
| `xttest3` | xttest3 | 可能不可用（Issue #8） |
| `teffects`（全部） | 内置 | 面板数据重复观测时失败（Issue #15） |
| `lasso logit` | 内置 | 近似分离时收敛失败（Issue #18） |
| `weakiv` | weakiv | 可能未安装 |
| `rddensity` | rddensity | p 值标量因版本而异（Issue #3） |

### 字符串面板 ID 检查

`xtset` 之前必须检查面板 ID 变量是否为字符串。`xtset` 要求数值 ID：

```stata
* 检查单位变量是否为字符串，如是则编码（Issue #19）
cap confirm string variable UNIT_VAR
if _rc == 0 {
    encode UNIT_VAR, gen(_unit_num)
    local UNIT_VAR _unit_num
}
xtset `UNIT_VAR' TIME_VAR
```

### e-class 结果可用性

使用 e-class 标量前必须检查其是否存在。某些命令可能不生成特定标量：

```stata
* 正确：使用前检查（Issue #14——xtivreg2 的 DWH 可能缺失）
if e(estatp) != . {
    di "DWH p-value: " e(estatp)
}
else {
    di "DWH p-value unavailable for this estimator."
}

* 错误：假设标量存在
di "DWH p-value: " e(estatp)   // 如缺失则崩溃
```

### 非标准估计量的结果存储模式

对于 `e()` 结果与 `estimates store` 不兼容的命令（如 `sdid`），将结果存储在局部宏中并手动构建表格：

```stata
* 正确：局部宏 + 文件写入（Issue #24）
cap noisily sdid Y unit time treat, vce(bootstrap) method(sdid) seed(12345)
if _rc == 0 {
    local att = e(ATT)
    local se  = e(se)
}
* 然后通过 file write 使用局部宏构建 LaTeX 表格

* 错误：sdid 后使用 ereturn post + estimates store
ereturn post b V       // 清除 e-class，r(301) 失败
estimates store m1      // 无法到达
```

### 连续变量与分类变量检查

连续变量使用 `summarize`，`tab` 仅用于低基数分类变量：

```stata
* 正确
summarize wage, detail      // 连续变量
tab industry, missing       // 类别数较少的分类变量

* 错误：对连续变量使用 tab（Issue #5）
tab wage                    // 每个唯一值一行，输出巨大
```

### 负 Hausman 卡方值

Hausman 检验在 FE 明显优于 RE 时可能产生负 chi2。这是已知行为，不是错误：

```stata
hausman fe_model re_model
if r(chi2) < 0 {
    di "Negative chi2: FE strongly dominates RE (Issue #9)."
    di "Interpretation: V_FE - V_RE is not positive semi-definite. Choose FE."
}
```

### 旧版 Stata 语法处理

已发表的复现包可能包含已弃用的命令（Issue #23）：

| 旧命令 | 处理方式 | 现代替代 |
|-------------|--------|-------------------|
| `set mem 250m` | 直接删除 | Stata 18 内存为动态分配 |
| `set memory 500m` | 直接删除 | Stata 18 内存为动态分配 |
| `clear matrix` | 替换 | `matrix drop _all` 或 `clear all` |
| `set matsize 800` | 删除（默认 11000） | 仅在明确需要时设置 |

改编旧复现代码时，删除已弃用命令。新 `.do` 文件中不要包含它们。

## 内存管理

保存大型数据集前使用 `compress`：

```stata
compress
save "data/clean/panel_cleaned.dta", replace
```

## 所需安装包

在每个 .do 文件或 master.do 文件顶部的注释块中列出所有所需包：

```stata
* 所需安装包：
*   ssc install reghdfe
*   ssc install ftools
*   ssc install estout
*   ssc install coefplot
```

## Master.do 模式

使用 master.do 文件组织项目：
1. 设置所有全局宏
2. 创建输出目录
3. 按顺序运行所有分析脚本
4. 验证输出

详见 `init-project.md` 的完整 master.do 模板。
