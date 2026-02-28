---
description: "中英文经济学论文互译，支持期刊风格适配"
user_invocable: true
---

# /translate — 学术论文翻译

当用户调用 `/translate` 时，按以下步骤操作：

## 步骤 1：收集信息

向用户询问：

1. **翻译方向**（必填）— 以下之一：
   - `CN→EN` — 中文翻译为英文
   - `EN→CN` — 英文翻译为中文
2. **目标期刊**（可选）— 如 AER、QJE、JPE、Econometrica、REStud、经济研究、管理世界、经济学季刊
3. **格式**（可选）— `LaTeX`（默认）或 `Word`
4. **待翻译文本**（必填）— 源文本

## 步骤 2：经济学术语与期刊风格

在所有翻译中一致使用以下术语：

| 英文 | 中文 |
|---|---|
| Difference-in-Differences (DID) | 双重差分 |
| Instrumental Variables (IV) | 工具变量 |
| Regression Discontinuity Design (RDD) | 断点回归设计 |
| Two-Stage Least Squares (2SLS) | 两阶段最小二乘法 |
| Fixed Effects (FE) | 固定效应 |
| Random Effects (RE) | 随机效应 |
| Generalized Method of Moments (GMM) | 广义矩估计 |
| Propensity Score Matching (PSM) | 倾向得分匹配 |
| Synthetic Control Method (SCM) | 合成控制法 |
| Synthetic DID (SDID) | 合成双重差分 |
| LASSO | LASSO（最小绝对收缩和选择算子） |
| Treatment effect | 处理效应 |
| Average Treatment Effect (ATE) | 平均处理效应 |
| Average Treatment Effect on the Treated (ATT) | 处理组平均处理效应 |
| Local Average Treatment Effect (LATE) | 局部平均处理效应 |
| Intention-to-Treat (ITT) | 意向处理效应 |
| Parallel trends assumption | 平行趋势假设 |
| Event study | 事件研究 |
| Robustness check | 稳健性检验 |
| Heterogeneity analysis | 异质性分析 |
| Mechanism analysis | 机制分析 |
| Endogeneity | 内生性 |
| Exogenous variation | 外生变异 |
| Identification strategy | 识别策略 |
| Causal inference | 因果推断 |
| Standard errors clustered at... | 在...层面聚类的标准误 |
| First stage | 第一阶段 |
| Reduced form | 简约式 |
| Exclusion restriction | 排他性约束 |
| Selection bias | 选择偏差 |
| Omitted variable bias | 遗漏变量偏差 |
| Placebo test | 安慰剂检验 |
| Wild cluster bootstrap | 野蛮聚类自助法 |

如果论文始终使用某一替代术语，以论文的用法为准。

根据目标期刊调整语调和行文规范：

**英文期刊：**
- **AER**：简洁直接；主动语态；面向广泛读者
- **QJE**：行文生动；尽早强调宏观贡献
- **JPE**：平衡正式度；表述清晰
- **Econometrica**：正式、数学化；精确符号
- **REStud**：技术性但可读；逻辑结构清晰

**中文期刊：**
- **经济研究**：正式学术中文；全篇使用"本文"；方法论严谨
- **管理世界**：政策导向；强调实践意义
- **经济学季刊**：方法论导向；技术深度

## 步骤 3：CN→EN 模式（中译英）

**方法：** 以顶级经济学期刊资深审稿人的标准进行翻译。

### LaTeX 感知

- 转义特殊字符：`%` → `\%`、`_` → `\_`、`&` → `\&`
- 保留所有数学环境（`$...$`、`$$...$$`、`\begin{equation}...\end{equation}`）——不翻译数学内容
- 保留 LaTeX 命令（`\cite{}`、`\ref{}`、`\label{}`、`\textbf{}`、`\textit{}` 等）
- 完整保留表格和图表环境
- 如果格式为 `Word`，则输出不含 LaTeX 命令的纯文本

### 翻译原则

- 翻译意思而非逐字翻译——调整句式以符合英文自然表达
- 使用一般现在时描述方法和结论（"This paper examines..." 而非 "This paper examined..."）
- 全篇使用正式学术语体：
  - 不使用缩写形式：`it's` → `it is`、`don't` → `do not`
  - 避免方法名的所有格形式：`DID's results` → `the results of DID`
- 保持原文段落结构
- 精确保留所有数值、变量名和统计结果
- 保留所有引用键和交叉引用

### 输出格式

```
### Part 1: Translation [LaTeX]

[翻译后的英文文本，保留 LaTeX 格式]

### Part 2: Back-Translation Comparison [中文回译]

| 中文原文 | 英文翻译 | 中文回译 |
|---|---|---|
| [关键句子 1] | [翻译] | [回译为中文] |
| [关键句子 2] | [翻译] | [回译为中文] |
| ... | ... | ... |
```

选择 5-10 个关键句子（尤其是包含技术论断、因果陈述或定量结果的句子）用于回译对照表。

### 自我审查协议

翻译完成后，验证：
- [ ] 英文自然流畅，符合经济学期刊表达习惯
- [ ] 术语翻译正确且与术语表一致
- [ ] 翻译未引入歧义
- [ ] 逻辑连贯流畅

如发现问题，修订并在 Part 2 中注明修改。

## 步骤 4：EN→CN 模式（英译中）

**方法：** 以专业学术翻译的严格直译标准进行翻译。

### LaTeX 清洗

- 删除引用命令：`\cite{xxx}` → 直接删除
- 删除引用命令：`\ref{xxx}`、`\label{xxx}` → 删除
- 删除 LaTeX 格式命令但保留内容：`\textbf{word}` → word
- 数学公式适当转化为自然语言：`$\beta$` → β、`$p < 0.01$` → 在1%水平上显著
- 如果复杂方程对理解至关重要，保持原样

### 翻译原则

- 严格直译——保持原始句式结构
- 不重组、不改写、不添加解释性内容
- 全篇使用标准中文学术术语
- 所有标点使用中文全角字符（，。；：""（）)
- 数字、变量名和缩写保持半角
- "we" 译为"本文"（而非"我们"），遵循中文期刊惯例

### 输出格式

```
### Part 1: Translation [中文译文]

[翻译后的中文文本——纯文本段落，不含 LaTeX]
```

---

> **来源**: 翻译方法改编自 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing)（Leey21），针对经济学研究定制。
