---
description: "生成可发表质量的 LaTeX 回归表格"
user_invocable: true
---

# /make-table — 生成可发表质量的 LaTeX 表格

当用户调用 `/make-table` 时，按以下步骤操作：

## 步骤 1：收集信息

向用户询问：

1. **数据来源**（必填）— 以下之一：
   - Stata 存储的估计结果（通过 `eststo`）或 .log 文件路径
   - Python 回归输出（pyfixest summary 或保存的结果）
   - 需要格式化的原始数据（如系数 CSV 文件）
2. **表格类型**（必填）— 以下之一：
   - `main` — 主回归结果表
   - `first_stage` — 第一阶段 IV 回归表
   - `robustness` — 稳健性汇总表
   - `descriptive` — 描述性统计表
   - `balance` — 分组平衡/汇总统计表
   - `event_study` — 事件研究系数表
   - `comparison` — 多估计量比较表（如 CS-DiD vs TWFE vs BJS）
3. **目标期刊语言**（必填）— `CN`（中文）或 `EN`（英文）
4. **目标期刊风格**（可选）— 如"经济研究"、"管理世界"、"AER"、"QJE"
5. **其他选项**（可选）：
   - 面板数量（Panel A、Panel B 等）
   - 列组标题
   - 是否包含因变量均值
   - 是否包含 95% 置信区间（方括号内，第三行）
   - 自定义注释

## 步骤 2：解析数据来源

### 从 Stata .log 文件
解析日志文件中的回归输出表，提取：
- 变量名称和标签
- 系数及显著性星号
- 标准误（括号内）
- 观测值数量
- R 方（及调整 R 方/组内 R 方）
- 固定效应指示符
- F 统计量（第一阶段 F、KP F）
- 聚类数量

### 从 Python 输出
解析 pyfixest `.summary()` 输出或从模型对象中提取：
- 系数、标准误、p 值
- 模型拟合统计量
- 根据 p 值添加显著性星号：*** p<0.01, ** p<0.05, * p<0.10

## 步骤 3：生成 LaTeX 表格

### 中文期刊格式（三线表）

适用于经济研究、管理世界等中文期刊：

```latex
\begin{table}[htbp]
\centering
\caption{<表格标题>}
\label{tab:<label>}
\begin{threeparttable}
\begin{tabular}{l<列对齐规格>}
\toprule
 & \multicolumn{<n>}{c}{<列组标题>} \\
 \cmidrule(lr){<start>-<end>}
 & (1) & (2) & (3) & (4) \\
 & <因变量1> & <因变量2> & <因变量3> & <因变量4> \\
\midrule
% Panel A: <面板标题>（如有多个面板）
\multicolumn{<n>}{l}{\textit{Panel A: <面板标题>}} \\[3pt]
<核心解释变量> & <coef>*** & <coef>** & <coef>*** & <coef>* \\
 & (<se>) & (<se>) & (<se>) & (<se>) \\[3pt]
<控制变量1> & <coef> & <coef> & <coef> & <coef> \\
 & (<se>) & (<se>) & (<se>) & (<se>) \\
\midrule
% 脚注行
控制变量 & 是 & 是 & 是 & 是 \\
个体固定效应 & 是 & 是 & 是 & 是 \\
时间固定效应 & 否 & 是 & 是 & 是 \\
因变量均值 & <mean> & <mean> & <mean> & <mean> \\
观测值 & <N> & <N> & <N> & <N> \\
R$^2$ & <r2> & <r2> & <r2> & <r2> \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]
\small
\item 注：括号内为聚类稳健标准误。***、**、*分别表示在1\%、5\%、10\%水平上显著。
<附加注释>
\end{tablenotes}
\end{threeparttable}
\end{table}
```

中文期刊格式核心要点：
- 使用 `\toprule`、`\midrule`、`\bottomrule`（三线表格式，需要 `booktabs` 包）
- 列标题使用中文
- 使用"是/否"表示 Yes/No 指示符
- 固定效应行：个体固定效应、时间固定效应、行业固定效应等
- 控制变量行：控制变量
- 观测值：观测值
- 注释使用中文，包含标准的显著性声明
- 使用 `threeparttable` 确保注释对齐
- 千位使用逗号分隔：10,000

### 英文期刊格式（AER/QJE 风格）

适用于 AER、QJE、Econometrica 等英文 TOP5 期刊：

```latex
\begin{table}[htbp]
\centering
\caption{<Table Title>}
\label{tab:<label>}
\begin{threeparttable}
\begin{tabular}{l<列对齐规格>}
\toprule\toprule
 & \multicolumn{<n>}{c}{<Column Group Header>} \\
 \cmidrule(lr){<start>-<end>}
 & (1) & (2) & (3) & (4) \\
 & <Dep Var 1> & <Dep Var 2> & <Dep Var 3> & <Dep Var 4> \\
\midrule
% Panel A: <Panel Title>（如有多个面板）
\multicolumn{<n>}{l}{\textit{Panel A: <Panel Title>}} \\[5pt]
<Key Variable> & <coef>$^{***}$ & <coef>$^{**}$ & <coef>$^{***}$ & <coef>$^{*}$ \\
 & (<se>) & (<se>) & (<se>) & (<se>) \\
 & [<ci_lo>, <ci_hi>] & [<ci_lo>, <ci_hi>] & [<ci_lo>, <ci_hi>] & [<ci_lo>, <ci_hi>] \\[3pt]
\midrule\midrule
% Panel B: <Panel Title>（如适用）
\multicolumn{<n>}{l}{\textit{Panel B: <Panel Title>}} \\[5pt]
...
\midrule
% 脚注行
Controls & Yes & Yes & Yes & Yes \\
Entity FE & \checkmark & \checkmark & \checkmark & \checkmark \\
Time FE &  & \checkmark & \checkmark & \checkmark \\
Dep.\ var.\ mean & <mean> & <mean> & <mean> & <mean> \\
Observations & <N> & <N> & <N> & <N> \\
$R^2$ & <r2> & <r2> & <r2> & <r2> \\
\bottomrule\bottomrule
\end{tabular}
\begin{figurenotes}
<Notes text>. Standard errors clustered at <cluster var> level in parentheses.
95\% confidence intervals in brackets. *** p$<$0.01, ** p$<$0.05, * p$<$0.10.
\end{figurenotes}
\end{threeparttable}
\end{table}
```

英文 TOP5 期刊格式核心要点：
- AER 风格：简洁、极简格式，双线 `\toprule\toprule` 和 `\bottomrule\bottomrule`
- 使用 `booktabs` 包（无竖线）
- 显著性星号为上标：$^{***}$、$^{**}$、$^{*}$
- FE 指示符使用勾号（`\checkmark`）（AER 偏好，优于 "Yes/No"）
- 95% 置信区间在方括号内，占据第三行（空间允许时）
- 注释使用 `\begin{figurenotes}` 环境（AER 内部风格）
- Panel A/B 之间用 `\midrule\midrule` 分隔
- 千位逗号分隔：10,000
- 列对齐：结果列通常使用 `c`
- 系数保留 4 位小数（匹配 APE/TOP5 标准）

### Stata `esttab` 命令模板（AER 风格）

直接从 Stata 存储的估计结果生成表格：

```stata
esttab m1 m2 m3 m4 m5 using "output/tables/tab_<name>.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    label booktabs replace ///
    mtitles("OLS" "2SLS" "LIML" "CS-DiD" "Alt.") ///
    keep(<key variable>) ///
    scalars("widstat KP F-stat" "N_clust Clusters" ///
            "r2_within Within R$^2$") ///
    addnotes("Standard errors clustered at <cluster var> level in parentheses." ///
             "Instrument(s): <instruments>." ///
             "*** p$<$0.01, ** p$<$0.05, * p$<$0.10.") ///
    title("Effect of <Treatment> on <Outcome>") ///
    substitute(\_ _)
```

## 步骤 4：按表格类型的特定格式

### 主回归表 (`main`)
- 展示核心自变量的系数和标准误
- 包含控制变量指示符（不展示系数）
- 展示 FE 指示符、N、R 方、聚类数
- 展示因变量均值
- 如果有多组结果变量则使用 Panel A/B 格式

### 第一阶段表 (`first_stage`)

参照 APE 0185 tab3 格式：

```stata
esttab fs_main using "output/tables/tab_first_stage.tex", ///
    se(4) b(4) star(* 0.10 ** 0.05 *** 0.01) ///
    keep(<instrument(s)>) label booktabs replace ///
    scalars("r2_within Within R$^2$" "N Observations") ///
    addnotes("F-statistic on excluded instrument(s): <F>" ///
             "Dependent variable: <endogenous var>") ///
    title("First Stage: <Instrument> $\rightarrow$ <Endogenous Var>")
```

第一阶段表核心要素：
- 工具变量系数突出显示
- 排除工具变量的 F 统计量在脚注行
- 异方差/聚类下的 KP rk Wald F 统计量
- Stock-Yogo (2005) / Lee et al. (2022) 临界值在注释中
- 排除工具变量的偏 R 方

### 稳健性汇总表 (`robustness`)
- 每种稳健性规范一列
- 仅展示核心处理系数
- 多列的紧凑格式
- 按稳健性类型用 `\cmidrule` 分组列
- 列标题：简要的规范描述

### 描述性统计表 (`descriptive`)
- 行：变量
- 列：N、均值、标准差、最小值、P25、中位数、P75、最大值
- 无显著性星号
- 整洁的数字格式

### 平衡表 (`balance`)
- 行：变量
- 列：组 1 均值、组 2 均值、差异、t 统计量或 p 值
- 差异列标注星号
- 展示各组 N

### 多估计量比较表 (`comparison`)

参照 APE 0119 tab2 格式：

```latex
\toprule\toprule
 & (1) & (2) & (3) & (4) & (5) \\
 & CS-DiD & TWFE & CS-DiD NYT & BJS & Sun-Abraham \\
\midrule
Treatment & <coef> & <coef> & <coef> & <coef> & <coef> \\
 & (<se>) & (<se>) & (<se>) & (<se>) & (<se>) \\
 & [<ci_lo>, <ci_hi>] & ... \\[5pt]
\midrule
Estimator & CS-DiD & TWFE & CS-DiD & BJS & SA \\
Control Group & Never-treated & All & Not-yet-treated & Never-treated & Never-treated \\
Controls & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
Unit FE & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
Time FE & \checkmark & \checkmark & \checkmark & \checkmark & \checkmark \\
Observations & <N> & <N> & <N> & <N> & <N> \\
\bottomrule\bottomrule
```

## 步骤 5：数值格式化

应用一致的格式化：
- 系数：4 位小数（TOP5 因果推断标准）
- 标准误：4 位小数（与系数一致）
- R 方：3 位小数
- 观测值：整数，千位逗号分隔
- 百分比：1-2 位小数
- 大系数（>100）：2 位小数
- 小系数（<0.001）：科学记数法或更多位小数
- F 统计量：2 位小数

## 通过 `\input{}` 嵌套 LaTeX 表格（多面板已发表论文模式）

已发表论文经常通过嵌套独立 `.tex` 文件来构建复杂表格。主表格包含核心回归输出，辅表 `_Add.tex` 包含衍生统计量（脉冲响应、长期效应），通过 `\input{}` 插入主表格的脚注区域。

### 模式：主表格 + 附加表格

**主表格** (`TableMain.tex`) — 由 `estout` 生成：
```stata
#delimit ;
estout e1 e2 e3 e4 e1gmm e2gmm e3gmm e4gmm e1md e2md e3md e4md
    using "${project}/results/TableMain.tex", style(tex)
    varlabels(L.y "log GDP first lag" L2.y "log GDP second lag"
              L3.y "log GDP third lag" L4.y "log GDP fourth lag"
              dem "Democracy")
    cells(b(star fmt(%9.3f)) se(par))
    stats(ar2p N N_g,
        fmt(%7.2f %7.0f %7.0f)
        labels("\input{results/TableMain_Add} AR2 test p-value"
               "Observations" "Countries in sample"))
    keep(L.y L2.y L3.y L4.y dem)
    order(dem L.y L2.y L3.y L4.y)
    stardrop(dem L.y L2.y L3.y L4.y)
    nolabel replace mlabels(none) collabels(none);
#delimit cr
```

**附加表格** (`TableMain_Add.tex`) — 脉冲响应结果：
```stata
#delimit ;
estout e1_add e2_add e3_add e4_add e1gmm_add e2gmm_add e3gmm_add e4gmm_add
       e1md_add e2md_add e3md_add e4md_add
    using "${project}/results/TableMain_Add.tex", style(tex)
    varlabels(longrun "Long-run effect of democracy"
              effect${limit} "Effect of democracy after ${limit} years"
              persistence "Persistence of GDP process")
    cells(b(star fmt(%9.3f)) se(par))
    keep(longrun effect${limit} persistence)
    order(longrun effect${limit} persistence)
    stardrop(longrun effect${limit} persistence)
    nolabel replace mlabels(none) collabels(none);
#delimit cr
```

**工作原理**：`\input{results/TableMain_Add}` 出现在 `stats()` 选项的 `labels()` 中。LaTeX 编译时，会将辅表行内联插入。这将核心回归输出与衍生统计量分离，使每个部分可以独立更新。

### 复杂 estout 命令中的 `#delimit ;`

长 `estout` 命令有许多选项时，使用 `///` 续行很难阅读。已发表 Stata 代码使用 `#delimit ;` 将行分隔符从换行符切换为分号：

```stata
#delimit ;
estout m1 m2 m3 m4 m5 m6 m7 m8 m9
    using "output/tables/table.tex", style(tex)
    varlabels(dem "Democracy")
    cells(b(star fmt(%9.3f)) se(par))
    stats(jp N N_g widstat,
        fmt(%7.2f %7.0f %7.0f %7.1f)
        labels("\input{results/Table_Add} Hansen p-value"
               "Observations" "Countries in sample"
               "Exc. Instruments F-stat."))
    keep(dem) order(dem) stardrop(dem)
    nolabel replace mlabels(none) collabels(none);
#delimit cr
```

**重要**：最后务必用 `#delimit cr` 恢复正常的换行分隔模式。

### `stardrop()` 选项

`estout` 中的 `stardrop()` 选项移除指定变量的标准误行上的显著性星号，仅在系数（点估计）旁附加星号。当星号应出现在点估计旁时，这能产生更整洁的输出：

```stata
estout m1 m2 m3, cells(b(star fmt(3)) se(par)) ///
    stardrop(dem L.y L2.y) keep(dem L.y L2.y)
```

### 多估计量表格布局（FE / GMM / HHK 并列）

在比较多个估计量和多个滞后规范的论文中：

| 列 | FE (1-lag) | FE (2-lag) | FE (4-lag) | FE (8-lag) | GMM (1) | GMM (2) | GMM (4) | GMM (8) | HHK (1) | HHK (2) | HHK (4) | HHK (8) |
|----|-----------|-----------|-----------|-----------|---------|---------|---------|---------|---------|---------|---------|---------|

需要 12 个存储的估计结果。在 `estout` 中按顺序列出所有 12 个，LaTeX 表头（手动构建）用 `\multicolumn{4}{c}{Within Estimator}` 等进行分组。

### 辅助 p 值文件模式

某些统计量（如来自 `test` 命令的 p 值）无法存储在 `e()` 标量中。将其写入单独的 `.tex` 文件：

```stata
file open myfile using "${project}/results/TableMain_lags.tex", write replace
file write myfile "p-value lags 5 to 8"

* 在每个模型之后：
xtreg y l(1/8).y dem yy*, fe vce(cluster wbcode2)
test l5.y l6.y l7.y l8.y
file write myfile " &&&& [" %7.3f (r(p)) "] "

* 完成后关闭
file write myfile "\\"
file close myfile
```

然后在主表格中 `\input{results/TableMain_lags}` 引入这些 p 值。

## 步骤 6：保存输出

保存生成的 .tex 文件：

```
output/tables/tab_<表格类型>_<描述>.tex
```

打印确认：

```
表格生成成功！

输出：output/tables/tab_<name>.tex
格式：<CN 三线表 / EN AER 风格>
列数：<N>
面板数：<N 或"无">

在论文中引用：
  \input{../output/tables/tab_<name>}

需要的 LaTeX 包：
  \usepackage{booktabs}
  \usepackage{threeparttable}
  \usepackage{multirow}    % 如使用多行标题
  \usepackage{amssymb}     % 用于 \checkmark
```
