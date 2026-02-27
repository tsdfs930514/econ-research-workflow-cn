---
description: "汇集所有分析输出，生成结构化综合报告（Markdown + LaTeX）"
user_invocable: true
---

# /synthesis-report — 综合报告生成

当用户调用 `/synthesis-report` 时，收集当前版本目录中的所有分析产出，生成全面的综合报告。

## 输出文件

- `docs/ANALYSIS_SUMMARY.md` — Markdown 版本（可 git 追踪）
- `docs/ANALYSIS_SUMMARY.tex` — LaTeX 版本（可编译为 PDF）

## 报告结构

```
1. 概要（方法、状态、总评分）
2. 数据与样本（数据来源、样本量、变量定义）
3. 主要结果（主回归系数、标准误、显著性、经济学解读）
4. 识别策略诊断（方法专属诊断汇总表）
5. 稳健性汇总（稳健性检验概览）
6. 交叉验证结果（Stata vs Python/R 比较表）
7. 质量评估（6 维评分 + /adversarial-review 评分）
8. 遗留问题（未解决的发现）
9. 复现清单（已填写的 REPLICATION.md 清单）
10. 文件清单（所有输出文件 + 表格/图表映射）
```

## 步骤 1：确定目标版本

- 默认：从 CLAUDE.md 读取当前版本目录（通常为 `v1/`）
- 用户可指定：`/synthesis-report v2/` 或 `/synthesis-report path/to/directory`
- 确认目标目录存在且包含输出文件

## 步骤 2：扫描日志文件提取关键统计量

- 读取 `output/logs/*.log` 中的所有文件
- 从每个日志中提取：
  - 主回归系数和标准误
  - R 方值
  - 观测值数量和聚类数
  - F 统计量（总体以及 IV 的第一阶段）
  - 诊断检验结果（平行趋势 p 值、密度检验 p 值、Bacon 分解权重等）
  - 任何 `r(xxx)` 错误或警告
- 按分析类型组织提取的统计量（主要结果、稳健性、诊断）

## 步骤 3：收集表格清单

- 读取 `output/tables/*.tex` 以构建已生成表格的列表
- 对每个表格文件，提取：
  - 表格标题（来自 `\caption{}` 或文件头注释）
  - 类型（主要结果、稳健性、描述性统计等）
  - 展示的关键统计量（哪些系数、多少列）
- 将表格映射到论文中的角色（表 1 = 描述性统计、表 2 = 主要结果等）

## 步骤 4：收集图表清单

- 读取 `output/figures/*`（PDF、PNG、EPS）以构建已生成图表的列表
- 对每个图表，记录：
  - 文件名和格式
  - 类型（事件研究图、密度检验图、系数图、RDD 图等）
  - 关联的分析步骤

## 步骤 5：收集质量评分

- 如果 `docs/QUALITY_SCORE.md` 存在，直接读取评分明细
- 否则，如果 `scripts/quality_scorer.py` 存在，运行 `/score` 生成评分
- 如果两者都不存在，注明"尚未生成质量评分"并建议运行 `/score`

## 步骤 6：收集交叉验证报告

- 检查交叉验证输出文件：
  - `output/logs/cross_check_report*.txt`
  - `output/tables/tab_cross_check*.tex`
- 如果找到，提取：
  - 总体 PASS/FAIL 状态
  - 最大系数差异
  - 任何 FAIL 项目的详情
- 如果未找到，注明"尚未执行交叉验证"并建议运行 `/cross-check`

## 步骤 7：生成 docs/ANALYSIS_SUMMARY.md

以如下结构创建 Markdown 报告：

```markdown
# 分析总结 — [项目名称] (vN/)

生成时间: YYYY-MM-DD HH:MM

---

## 1. 概要

- **研究问题**: [从 research_proposal.md 或 CLAUDE.md 提取]
- **识别策略**: [DID / IV / RDD / Panel / SDID]
- **主要数据集**: [数据来源和样本期]
- **核心发现**: [主要系数、显著性、经济学解读]
- **质量评分**: XX/100 — [可发表 / 小修 / 大修 / 重做]
- **流水线状态**: [完成 / 部分完成 — 列出缺失步骤]

## 2. 数据与样本

| 项目 | 值 |
|------|-----|
| 数据来源 | [来源] |
| 样本期 | [年份] |
| 总观测值 | [N] |
| 截面单位数 | [N 家企业/县等] |
| 时间期数 | [N 年/季度] |
| 处理组规模 | [N 处理单位] |
| 对照组规模 | [N 对照单位] |

### 核心变量

| 变量 | 角色 | 定义 | 来源 |
|------|------|------|------|
| [Y] | 因变量 | [描述] | [来源] |
| [D] | 处理变量 | [描述] | [来源] |
| [X1..Xk] | 控制变量 | [描述] | [来源] |

## 3. 主要结果

| 设定 | 系数 | 标准误 | p 值 | N | R² | 显著性 |
|------|------|--------|------|---|-----|--------|
| 基准 | [b] | ([se]) | [p] | [N] | [R²] | [星号] |
| 加控制变量 | [b] | ([se]) | [p] | [N] | [R²] | [星号] |
| 偏好设定 | [b] | ([se]) | [p] | [N] | [R²] | [星号] |

**经济学解读**: [X 每增加一个单位，Y 变化 b 个单位，相当于样本均值的 X%。]

## 4. 识别策略诊断

[方法专属诊断表——内容因方法而异]

### DID 诊断
| 检验 | 统计量 | p 值 | 结果 |
|------|--------|------|------|
| 平行趋势（联合 F 检验） | F = | p = | PASS/FAIL |
| Bacon 分解（TWFE 份额） | | | |
| CS-DiD ATT(simple) | | | |
| HonestDiD (M = 0.05) | | | |

### IV 诊断
| 检验 | 统计量 | 结果 |
|------|--------|------|
| 第一阶段 F | | > 10? |
| KP rk Wald F | | |
| Anderson-Rubin | | |
| LIML vs 2SLS 差距 | | |
| Hansen J（过度识别时） | | |

### RDD 诊断
| 检验 | 统计量 | p 值 | 结果 |
|------|--------|------|------|
| CJM 密度检验 | | | |
| 最优带宽 | | | |
| 甜甜圈 RDD 稳定 | | | |
| 安慰剂断点不显著 | | | |

## 5. 稳健性汇总

| 检验 | 系数 | 标准误 | 显著？ | 状态 |
|------|------|--------|--------|------|
| 基准 | [b] | ([se]) | 是/否 | 参照 |
| 替代因变量 | [b] | ([se]) | 是/否 | PASS/FAIL |
| 剔除极端值 | [b] | ([se]) | 是/否 | PASS/FAIL |
| 替代聚类标准误 | [b] | ([se]) | 是/否 | PASS/FAIL |
| 子样本: 前期 | [b] | ([se]) | 是/否 | PASS/FAIL |
| 子样本: 后期 | [b] | ([se]) | 是/否 | PASS/FAIL |
| 缩尾 1/99 | [b] | ([se]) | 是/否 | PASS/FAIL |
| Oster delta | [delta] | — | > 1? | PASS/FAIL |
| 野蛮聚类自助法 | [b] | [CI] | — | PASS/FAIL |

**小结**: X/Y 个设定保持方向和显著性一致。

## 6. 交叉验证结果

| 统计量 | Stata | Python | 相对差异 | 状态 |
|--------|-------|--------|----------|------|
| coef(treatment) | [b] | [b] | [diff]% | PASS/FAIL |
| se(treatment) | [se] | [se] | [diff]% | PASS/FAIL |
| R-squared | [R²] | [R²] | [diff] | PASS/FAIL |
| N | [N] | [N] | [diff] | PASS/FAIL |

**总体**: [PASS — 全部在容差范围内 / FAIL — 列出不合格项]

## 7. 质量评估

### 自动化评分 (quality_scorer.py)

| 维度 | 得分 | 满分 | 详情 |
|------|------|------|------|
| 代码规范 | /15 | 15 | |
| 日志清洁度 | /15 | 15 | |
| 输出完整性 | /15 | 15 | |
| 交叉验证 | /15 | 15 | |
| 文档完整性 | /15 | 15 | |
| 方法诊断检验 | /25 | 25 | |
| **总分** | **/100** | **100** | |

**状态**: [可发表 / 小修 / 大修 / 重做]

### 对抗式审查评分（如有）

| 评审者 | 评分 | 主要发现 |
|--------|------|----------|
| code-critic | /100 | [摘要] |
| econometrics-critic | /100 | [摘要] |
| tables-critic | /100 | [摘要] |

## 8. 遗留问题

| # | 来源 | 严重程度 | 描述 | 建议修复 |
|---|------|----------|------|----------|
| 1 | [评审者/评分器] | 严重/高/中/低 | [描述] | [修复方案] |
| 2 | | | | |

## 9. 复现清单

- [ ] 原始数据文件存在于 `data/raw/`
- [ ] 所有 .do 文件运行无错误
- [ ] 所有 .py 交叉验证脚本可运行
- [ ] master.do 可端到端复现所有结果
- [ ] REPLICATION.md 记录了所有步骤
- [ ] _VERSION_INFO.md 是最新的
- [ ] 输出到表格的映射已完成
- [ ] 所有依赖包和版本已记录

## 10. 文件清单

### 代码文件
| 文件 | 描述 | 状态 |
|------|------|------|
| `code/stata/01_*.do` | [描述] | [运行正常 / 有错误] |
| ... | | |

### 输出文件
| 文件 | 类型 | 映射至 |
|------|------|--------|
| `output/tables/tab_main_results.tex` | 主要结果 | 表 2 |
| `output/figures/fig_event_study.pdf` | 事件研究图 | 图 1 |
| ... | | |

### 文档
| 文件 | 状态 |
|------|------|
| `REPLICATION.md` | [完整 / 部分 / 缺失] |
| `_VERSION_INFO.md` | [完整 / 部分 / 缺失] |
| `docs/QUALITY_SCORE.md` | [完整 / 缺失] |
```

## 步骤 8：生成 docs/ANALYSIS_SUMMARY.tex

创建 LaTeX 版本：
- 使用 `\documentclass{article}`，搭配 `booktabs`、`longtable`、`hyperref`、`geometry` 宏包
- 将所有 Markdown 表格转换为 LaTeX `tabular` 环境
- 尽可能使用 `\input{}` 引用 `output/tables/` 中的已有表格 .tex 文件（避免重复表格内容）
- 使用 `\includegraphics{}` 引用 `output/figures/` 中的已有图表
- 包含 `\tableofcontents` 用于导航
- 可用 `pdflatex` 编译（无需特殊引擎）

结构：
```latex
\documentclass[12pt]{article}
\usepackage{booktabs, longtable, hyperref, geometry, graphicx}
\geometry{margin=1in}

\title{分析总结 --- [项目名称] (vN/)}
\date{\today}

\begin{document}
\maketitle
\tableofcontents
\newpage

\section{概要}
...

\section{主要结果}
% 如有已存在的表格则引用:
% \input{../output/tables/tab_main_results.tex}
...

\section{文件清单}
...

\end{document}
```

## 步骤 9：更新 REPLICATION.md

如果版本目录中存在 `REPLICATION.md`，使用步骤 7/8 中生成的实际文件清单更新其输出-表格映射部分：

```markdown
## 输出-表格映射

| 论文元素 | 来源文件 | 生成脚本 |
|----------|----------|----------|
| 表 1（描述性统计） | `output/tables/tab_desc_stats.tex` | `code/stata/02_desc_stats.do` |
| 表 2（主要结果） | `output/tables/tab_main_results.tex` | `code/stata/03_reg_main.do` |
| 图 1（事件研究） | `output/figures/fig_event_study.pdf` | `code/stata/03_reg_main.do` |
```

## 步骤 10：记录到 MEMORY.md

追加到 MEMORY.md：

```
[LEARN] YYYY-MM-DD: 已为 <target> 生成综合报告。评分: XX/100，状态: [状态]。报告位于 docs/ANALYSIS_SUMMARY.md。
```
