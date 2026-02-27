---
description: "初始化经济学研究项目，创建标准化目录结构"
user_invocable: true
---

# /init-project — 初始化经济学研究项目

当用户调用 `/init-project` 时，按以下步骤操作：

## 步骤 1：收集项目信息

向用户询问以下信息（除注明外均为必填）：

1. **项目名称** — 简短标识符（如 `minimum-wage-employment`）
2. **机构** — 大学或研究机构名称
3. **研究者姓名** — 主要研究者姓名
4. **简要描述** — 1-2 句话的研究项目描述
5. **工作语言** — 中文 (CN)、英文 (EN) 或双语（默认：双语）
6. **论文格式**（可选）— `journal`（默认：AER/经济研究）、`NBER`、`SSRN` 或 `all`
7. **主要方法**（可选）— DID、IV、RDD、Panel 或 General

## 步骤 2：创建目录结构

在当前工作目录（或指定的根目录）下创建项目文件夹，结构如下：

```
<project-name>/
  v1/
    data/
      raw/          # 原始数据文件（只读，禁止修改）
      clean/        # 清洗后的数据集
      temp/         # 中间临时文件
    code/
      stata/        # Stata .do 文件
      python/       # Python .py 脚本
      r/            # R 脚本（如需要）
    output/
      tables/       # LaTeX 表格输出
      figures/      # 图表
      logs/         # Stata .log 和其他执行日志
    paper/
      sections/     # 各章节 .tex 文件
      bib/          # 参考文献 .bib 文件
    docs/           # 项目文档
```

## 步骤 3：创建 master.do

创建 `<project-name>/v1/code/stata/master.do`：

**通过以下命令执行 master.do：**
```bash
cd /path/to/project/v1
"D:\Stata18\StataMP-64.exe" -e do "code/stata/master.do"
```

`-e` 参数使 Stata 运行完毕后自动退出，日志文件自动生成在当前目录。

```stata
/*==============================================================================
项目：    <项目名称>
版本：    v1
脚本：    master.do
用途：    主控脚本——按顺序运行所有分析
作者：    <研究者姓名>
创建：    <日期>
修改：    <日期>
==============================================================================*/

version 18
clear all
set more off
cap set maxvar 32767    // MP/SE：允许的最大值；IC 版本会静默忽略
cap set matsize 11000   // MP/SE：增加矩阵大小；IC 版本使用较低上限
set seed 12345

* --- 设置路径 ---
global root     "."
global data     "$root/data"
global raw      "$data/raw"
global clean    "$data/clean"
global temp     "$data/temp"
global code     "$root/code/stata"
global output   "$root/output"
global tables   "$output/tables"
global figures  "$output/figures"
global logs     "$output/logs"

* --- 验证路径存在 ---
cap mkdir "$clean"
cap mkdir "$temp"
cap mkdir "$tables"
cap mkdir "$figures"
cap mkdir "$logs"

* --- 安装所需包（首次运行时取消注释）---
/*
ssc install reghdfe
ssc install ftools
ssc install estout
ssc install coefplot
ssc install winsor2
ssc install boottest
* 方法特定（按需取消注释）：
* ssc install csdid         // DID: Callaway-Sant'Anna
* ssc install did_multiplegt // DID: de Chaisemartin-D'Haultfoeuille
* ssc install did_imputation // DID: Borusyak-Jaravel-Spiess
* ssc install bacondecomp   // DID: Goodman-Bacon 分解
* ssc install eventstudyinteract // DID: Sun-Abraham
* ssc install honestdid     // DID: Rambachan-Roth 敏感性分析
* ssc install sdid           // SDID: 合成 DID
* ssc install ivreghdfe      // IV
* ssc install ivreg2         // IV
* ssc install ranktest       // IV
* ssc install weakiv         // IV: Anderson-Rubin 置信区间
* net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace  // RDD
* net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace  // RDD
*/

* --- 按顺序运行脚本 ---
* 在脚本就绪后逐行取消注释

* do "$code/01_clean_data.do"
* do "$code/02_desc_stats.do"
* do "$code/03_main_regression.do"
* do "$code/04_robustness.do"
* do "$code/05_tables_export.do"
* do "$code/06_figures.do"

di "=== Master script complete ==="
```

## 步骤 4：创建 _VERSION_INFO.md

创建 `<project-name>/v1/_VERSION_INFO.md`：

```markdown
# 版本信息

- **版本**: v1
- **创建日期**: <当前日期 YYYY-MM-DD>
- **项目**: <项目名称>
- **研究者**: <研究者姓名>
- **机构**: <机构名称>
- **描述**: <简要描述>

## 版本历史

| 版本 | 日期 | 描述 |
|------|------|------|
| v1   | <日期> | 初始版本 |
```

## 步骤 5：创建 CLAUDE.md

创建 `<project-name>/CLAUDE.md`，包含项目特定指令：

```markdown
# CLAUDE.md - 项目指令

## 项目概览
- **项目**: <项目名称>
- **研究者**: <研究者姓名>
- **机构**: <机构名称>
- **描述**: <简要描述>
- **当前版本**: v1

## 目录规范
- 所有工作在 `v1/` 内进行（大版本修订时递增版本号）
- 原始数据永不修改；所有清洗产生的文件存放在 `data/clean/`
- 每个 Stata .do 文件必须在 `output/logs/` 有对应的 .log 文件
- 表格存放在 `output/tables/`，格式为 .tex
- 图表存放在 `output/figures/`，格式为 .pdf 或 .png

## 代码规范
- Stata：使用 `eststo`/`esttab` 输出回归结果。始终 `set more off`。记录所有输出。
- Python：使用 `pyfixest` 进行回归复现。使用 `pandas` 进行数据处理。
- 所有脚本必须能够通过 `master.do` 从原始数据复现。

## 命名规范
- 数据文件：`<描述>_<日期>.dta` 或 `.csv`
- Do 文件：`<NN>_<描述>.do`（如 `01_clean_data.do`、`02_main_regression.do`）
- 表格：`tab_<描述>.tex`
- 图表：`fig_<描述>.pdf`

## Stata 配置
- **可执行文件**: `D:\Stata18\StataMP-64.exe`
- **运行命令（Git Bash）**: `"D:\Stata18\StataMP-64.exe" -e do "code/stata/script.do"`
- **参数说明**: 必须用 `-e`（自动退出），禁止用 `-b`（需手动确认）或 `/e`（Git Bash 路径冲突）

## 论文
- 主文件：`main_cn.tex`（中文）和/或 `main_en.tex`（英文）
- 章节存放在 `paper/sections/`，通过 `\input{}` 引入
```

## 步骤 6：创建 REPLICATION.md

创建 `<project-name>/v1/REPLICATION.md`，遵循 AEA 数据编辑标准：

```markdown
# 复现包

## 概述

本复现包包含复现"<论文标题>"（<作者>）中所有结果所需的全部代码和数据。

**数据可用性声明**: [描述数据来源和访问条件]

## 数据来源

| 数据 | 来源 | 访问 | 文件 |
|------|------|------|------|
| [数据集 1] | [提供者] | [公开/限制] | `data/raw/[文件名]` |
| [数据集 2] | [提供者] | [公开/限制] | `data/raw/[文件名]` |

## 计算环境要求

### 软件
- Stata 18/MP（所有 .do 文件必需）
- Python 3.10+ 及包：pyfixest、pandas、numpy

### Stata 包
[列出所有必需的 Stata 包及版本号]

### 硬件
- 预计运行时间：[X 分钟/小时]，于 [机器描述]
- 内存要求：[X GB RAM]

## 使用说明

1. 在 `code/stata/master.do` 中设置根目录
2. 安装必需的 Stata 包（见 `master.do` 头部）
3. 运行 `master.do` 以按顺序执行所有分析
4. 输出表格出现在 `output/tables/`
5. 输出图表出现在 `output/figures/`

## 文件结构

```
v1/
├── code/
│   ├── stata/
│   │   ├── master.do           # 主控脚本（运行此文件）
│   │   ├── 01_clean_data.do    # 数据准备
│   │   ├── 02_desc_stats.do    # 描述性统计
│   │   ├── 03_main_regression.do # 主要结果
│   │   ├── 04_robustness.do    # 稳健性检验
│   │   └── ...
│   └── python/
│       └── cross_validation.py # 交叉验证 Stata 结果
├── data/
│   ├── raw/                    # 原始数据（只读）
│   └── clean/                  # 处理后数据
├── output/
│   ├── tables/                 # LaTeX 表格
│   ├── figures/                # PDF 图表
│   └── logs/                   # 执行日志
└── REPLICATION.md              # 本文件
```

## 输出-表格映射

| 表格/图表 | 脚本 | 输出文件 |
|----------|------|---------|
| 表 1     | `02_desc_stats.do` | `output/tables/tab_descriptive.tex` |
| 表 2     | `03_main_regression.do` | `output/tables/tab_main_results.tex` |
| 图 1     | `06_figures.do` | `output/figures/fig_event_study.pdf` |
| ...      | ...  | ... |

## 数据溯源

对每个原始数据文件记录：
- **来源**：从何处获取？
- **获取日期**：何时下载？
- **DOI/URL**：持久标识符
- **许可证**：使用限制
- **校验和**：文件的 MD5 或 SHA256 哈希值

| 文件 | 来源 | 日期 | DOI/URL | MD5 |
|------|------|------|---------|-----|
| [file.dta] | [来源] | [日期] | [doi] | [哈希值] |
```

## 步骤 7：创建 MEMORY.md

创建 `<project-name>/v1/MEMORY.md`：

```markdown
# 项目记忆

## 关键决策
<!-- 在此记录重要的方法论和数据决策 -->

## 数据笔记
<!-- 记录数据来源、获取日期、已知问题 -->

## 变量定义
<!-- 核心变量名称及其定义 -->

## 回归规范
<!-- 记录使用的主要规范 -->

## 待办事项与问题
<!-- 记录未解决的问题 -->
```

## 步骤 8：创建 docs/CHANGELOG.md

创建 `<project-name>/v1/docs/CHANGELOG.md`：

```markdown
# 更新日志

## v1 — <当前日期>
- 项目初始化
- 目录结构已创建
```

## 步骤 9：创建 .gitignore

创建 `<project-name>/.gitignore`：

```
# 数据文件（可能较大或有限制）
*.dta
*.csv
*.xlsx
*.sas7bdat
*.rds
data/raw/*
data/temp/*
!data/raw/.gitkeep
!data/temp/.gitkeep

# Stata 日志和临时文件
*.log
*.smcl
*.gph

# Python
__pycache__/
*.pyc
.ipynb_checkpoints/

# 系统文件
.DS_Store
Thumbs.db

# LaTeX 辅助文件
*.aux
*.bbl
*.blg
*.fdb_latexmk
*.fls
*.synctex.gz
*.out
*.toc
```

## 步骤 10：创建占位用主 TeX 文件

创建 `<project-name>/v1/paper/main_cn.tex`（如果选择 CN 或双语）：

```latex
\documentclass[12pt,a4paper]{article}
\usepackage[UTF8]{ctex}
\usepackage{booktabs,multirow,threeparttable}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage[margin=2.5cm]{geometry}
\usepackage{setspace}
\usepackage{natbib}

\title{<项目标题>}
\author{<研究者姓名>\\<机构名称>}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
% 摘要内容
\end{abstract}

\textbf{关键词：}

% \input{sections/01_introduction}
% \input{sections/02_literature}
% \input{sections/03_background}
% \input{sections/04_data}
% \input{sections/05_strategy}
% \input{sections/06_results}
% \input{sections/07_robustness}
% \input{sections/08_conclusion}

\bibliographystyle{apalike}
\bibliography{bib/references}

\end{document}
```

创建 `<project-name>/v1/paper/main_en.tex`（如果选择 EN 或双语）：

```latex
\documentclass[12pt,a4paper]{article}
\usepackage{booktabs,multirow,threeparttable}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}\doublespacing
\usepackage{natbib}

\title{<Project Title>}
\author{<Researcher Name>\\<Institution>}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
% Abstract content
\end{abstract}

\textbf{Keywords:}

\newpage

% \input{sections/01_introduction}
% \input{sections/02_literature}
% \input{sections/03_background}
% \input{sections/04_data}
% \input{sections/05_strategy}
% \input{sections/06_results}
% \input{sections/07_robustness}
% \input{sections/08_conclusion}

\bibliographystyle{aer}
\bibliography{bib/references}

\end{document}
```

创建 `<project-name>/v1/paper/main_nber.tex`（如果格式为 `NBER` 或 `all`）：

```latex
\documentclass[12pt,a4paper]{article}
\usepackage{booktabs,multirow,threeparttable}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}\onehalfspacing
\usepackage[round]{natbib}
\usepackage{hyperref}
\usepackage{caption}

% --- NBER 工作论文格式 ---
\title{<Project Title>\thanks{We thank [acknowledgments: seminar participants, discussants, funding agencies]. Author1: [affiliation], [email]. Author2: [affiliation], [email].}}
\author{<Author 1>\\ \textit{<Institution 1>} \and <Author 2>\\ \textit{<Institution 2>}}
\date{This draft: \today}

\begin{document}
\maketitle

\begin{abstract}
\noindent
% 摘要：100-200 词。概述研究问题、方法和主要发现。
\end{abstract}

\medskip

\noindent\textbf{JEL Classification:} <J31, C21, H53>

\noindent\textbf{Keywords:} <keyword1, keyword2, keyword3>

\bigskip
\noindent\rule{\textwidth}{0.4pt}

\newpage

% \input{sections/01_introduction}
% \input{sections/02_literature}
% \input{sections/03_background}
% \input{sections/04_data}
% \input{sections/05_strategy}
% \input{sections/06_results}
% \input{sections/07_robustness}
% \input{sections/08_conclusion}

\newpage
\bibliographystyle{aer}
\bibliography{bib/references}

% \newpage
% \appendix
% \input{sections/appendix_a_data}
% \input{sections/appendix_b_robustness}

\end{document}
```

创建 `<project-name>/v1/paper/main_ssrn.tex`（如果格式为 `SSRN` 或 `all`）：

```latex
\documentclass[12pt,a4paper]{article}
\usepackage{booktabs,multirow,threeparttable}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}\singlespacing
\usepackage[round]{natbib}
\usepackage{hyperref}
\usepackage{caption}
\usepackage{fancyhdr}

% --- SSRN 预印本格式 ---
\pagestyle{fancy}
\fancyhf{}
\rhead{\thepage}
\lfoot{\footnotesize Draft --- comments welcome}
\rfoot{\footnotesize Available at SSRN: \url{https://ssrn.com/abstract=XXXXXXX}}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0.4pt}

\title{<Project Title>}
\author{
  <Author 1>\\
  \textit{<Institution 1>}\\
  \href{mailto:author1@example.com}{author1@example.com}
  \and
  <Author 2>\\
  \textit{<Institution 2>}\\
  \href{mailto:author2@example.com}{author2@example.com}
}
\date{
  This version: \today\\
  First version: <Month Year>
}

\begin{document}
\maketitle
\thispagestyle{empty}

\begin{abstract}
\noindent
% 摘要：150-250 词。应当自成一体——很多 SSRN 读者只看摘要。
% 明确说明：(1) 研究问题，(2) 方法，(3) 数据，(4) 核心发现，(5) 贡献。
\end{abstract}

\medskip

\noindent\textbf{Keywords:} <keyword1, keyword2, keyword3, keyword4>

\noindent\textbf{JEL Classification:} <J31, C21, H53>

\newpage
\setcounter{page}{1}

% \input{sections/01_introduction}
% \input{sections/02_literature}
% \input{sections/03_background}
% \input{sections/04_data}
% \input{sections/05_strategy}
% \input{sections/06_results}
% \input{sections/07_robustness}
% \input{sections/08_conclusion}

\newpage
\bibliographystyle{aer}
\bibliography{bib/references}

% \newpage
% \appendix
% \input{sections/appendix_a_data}
% \input{sections/appendix_b_robustness}

\end{document}
```

同时创建空白占位文件：
- `<project-name>/v1/paper/bib/references.bib`
- `<project-name>/v1/data/raw/.gitkeep`
- `<project-name>/v1/data/temp/.gitkeep`

## 步骤 11：打印总结

创建完成后，打印总结：

```
项目"<project-name>"初始化成功！

已创建结构：
  v1/
    data/raw/  data/clean/  data/temp/
    code/stata/  code/python/  code/r/
    output/tables/  output/figures/  output/logs/
    paper/sections/  paper/bib/
    docs/

已创建文件：
  - CLAUDE.md（项目配置）
  - v1/_VERSION_INFO.md
  - v1/MEMORY.md
  - v1/REPLICATION.md（AEA 数据编辑标准格式）
  - v1/code/stata/master.do
  - v1/docs/CHANGELOG.md
  - v1/paper/main_cn.tex（如选择 CN 或双语）
  - v1/paper/main_en.tex（如选择 EN 或双语）
  - v1/paper/main_nber.tex（如选择 NBER 或 all）
  - v1/paper/main_ssrn.tex（如选择 SSRN 或 all）
  - v1/paper/bib/references.bib
  - .gitignore

下一步：
  1. 将原始数据文件放入 v1/data/raw/
  2. 更新 REPLICATION.md 填写数据来源
  3. 使用 /data-describe 探索数据
  4. 使用 /run-did、/run-iv、/run-rdd 或 /run-panel 进行分析
```
