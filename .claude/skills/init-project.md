---
description: "Initialize a new economics research project with standardized directory structure"
user_invocable: true
---

# /init-project - Initialize Economics Research Project

When the user invokes `/init-project`, follow these steps:

## Step 1: Gather Project Information

Ask the user for the following (all required unless noted):

1. **Project name** - A short identifier (e.g., `minimum-wage-employment`)
2. **Institution** - University or research institute name
3. **Researcher name** - Primary researcher's name
4. **Brief description** - 1-2 sentence description of the research project
5. **Working language** - Chinese (CN), English (EN), or both (default: both)
6. **Paper format** (optional) - `journal` (default: AER/经济研究), `NBER`, `SSRN`, or `all`
7. **Primary method** (optional) - DID, IV, RDD, Panel, or General

## Step 2: Create Directory Structure

Under the current working directory (or a specified root), create the project folder with the following structure:

```
<project-name>/
  v1/
    data/
      raw/          # Original, untouched data files (READ-ONLY)
      clean/        # Cleaned and processed datasets
      temp/         # Intermediate temporary files
    code/
      stata/        # Stata .do files
      python/       # Python .py scripts
      r/            # R scripts (if needed)
    output/
      tables/       # LaTeX table outputs
      figures/      # Figures and plots
      logs/         # Stata .log and other execution logs
    paper/
      sections/     # Individual .tex section files
      bib/          # Bibliography .bib files
    docs/           # Project documentation
```

## Step 3: Create master.do

Create `<project-name>/v1/code/stata/master.do`:

**Execute master.do via:**
```bash
cd /path/to/project/v1
"D:\Stata18\StataMP-64.exe" -e do "code/stata/master.do"
```

`-e` flag 使 Stata 运行完毕后自动退出，日志文件自动生成在当前目录。

```stata
/*==============================================================================
Project:    <Project Name>
Version:    v1
Script:     master.do
Purpose:    Master script — runs all analysis in sequence
Author:     <Researcher Name>
Created:    <Date>
Modified:   <Date>
==============================================================================*/

version 18
clear all
set more off
cap set maxvar 32767    // MP/SE: max allowed; IC ignores silently
cap set matsize 11000   // MP/SE: increase matrix size; IC uses lower max
set seed 12345

* --- Set paths ---
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

* --- Verify paths exist ---
cap mkdir "$clean"
cap mkdir "$temp"
cap mkdir "$tables"
cap mkdir "$figures"
cap mkdir "$logs"

* --- Install required packages (uncomment on first run) ---
/*
ssc install reghdfe
ssc install ftools
ssc install estout
ssc install coefplot
ssc install winsor2
ssc install boottest
* Method-specific (uncomment as needed):
* ssc install csdid         // DID: Callaway-Sant'Anna
* ssc install did_multiplegt // DID: de Chaisemartin-D'Haultfoeuille
* ssc install did_imputation // DID: Borusyak-Jaravel-Spiess
* ssc install bacondecomp   // DID: Goodman-Bacon decomposition
* ssc install eventstudyinteract // DID: Sun-Abraham
* ssc install honestdid     // DID: Rambachan-Roth sensitivity
* ssc install sdid           // SDID: Synthetic DID
* ssc install ivreghdfe      // IV
* ssc install ivreg2         // IV
* ssc install ranktest       // IV
* ssc install weakiv         // IV: Anderson-Rubin CIs
* net install rdrobust, from(https://raw.githubusercontent.com/rdpackages/rdrobust/master/stata) replace  // RDD
* net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace  // RDD
*/

* --- Run scripts in order ---
* Uncomment each line as the script is ready

* do "$code/01_clean_data.do"
* do "$code/02_desc_stats.do"
* do "$code/03_main_regression.do"
* do "$code/04_robustness.do"
* do "$code/05_tables_export.do"
* do "$code/06_figures.do"

di "=== Master script complete ==="
```

## Step 4: Create _VERSION_INFO.md

Create `<project-name>/v1/_VERSION_INFO.md` with:

```markdown
# Version Information

- **Version**: v1
- **Created**: <current date YYYY-MM-DD>
- **Project**: <project name>
- **Researcher**: <researcher name>
- **Institution**: <institution>
- **Description**: <brief description>

## Version History

| Version | Date       | Description          |
|---------|------------|----------------------|
| v1      | <date>     | Initial version      |
```

## Step 5: Create CLAUDE.md

Create `<project-name>/CLAUDE.md` with project-specific instructions:

```markdown
# CLAUDE.md - Project Instructions

## Project Overview
- **Project**: <project name>
- **Researcher**: <researcher name>
- **Institution**: <institution>
- **Description**: <brief description>
- **Current Version**: v1

## Directory Conventions
- All work happens inside `v1/` (increment version for major revisions)
- Raw data is NEVER modified; all cleaning produces files in `data/clean/`
- Every Stata .do file must have a corresponding .log file in `output/logs/`
- Tables go in `output/tables/` as .tex files
- Figures go in `output/figures/` as .pdf or .png

## Code Standards
- Stata: Use `eststo`/`esttab` for regression output. Always `set more off`. Log all output.
- Python: Use `pyfixest` for regression replication. Use `pandas` for data manipulation.
- All scripts must be reproducible from raw data via `master.do`.

## Naming Conventions
- Data files: `<description>_<date>.dta` or `.csv`
- Do files: `<NN>_<description>.do` (e.g., `01_clean_data.do`, `02_main_regression.do`)
- Tables: `tab_<description>.tex`
- Figures: `fig_<description>.pdf`

## Stata Configuration
- **Executable**: `D:\Stata18\StataMP-64.exe`
- **Run command (Git Bash)**: `"D:\Stata18\StataMP-64.exe" -e do "code/stata/script.do"`
- **Flag**: 必须用 `-e`（自动退出），禁止用 `-b`（需手动确认）或 `/e`（Git Bash 路径冲突）

## Paper
- Main files: `main_cn.tex` (Chinese) and/or `main_en.tex` (English)
- Sections stored in `paper/sections/` and included via `\input{}`
```

## Step 6: Create REPLICATION.md

Create `<project-name>/v1/REPLICATION.md` following AEA Data Editor standards:

```markdown
# Replication Package

## Overview

This replication package contains all code and data necessary to reproduce the
results in "<Paper Title>" by <Author(s)>.

**Data Availability Statement**: [Describe data sources and access conditions]

## Data Sources

| Data | Source | Access | Files |
|------|--------|--------|-------|
| [Dataset 1] | [Provider] | [Public/Restricted] | `data/raw/[filename]` |
| [Dataset 2] | [Provider] | [Public/Restricted] | `data/raw/[filename]` |

## Computational Requirements

### Software
- Stata 18/MP (required for all .do files)
- Python 3.10+ with packages: pyfixest, pandas, numpy

### Stata Packages
[List all required Stata packages with version numbers]

### Hardware
- Approximate runtime: [X minutes/hours] on [machine description]
- Memory requirements: [X GB RAM]

## Instructions

1. Set the root directory in `code/stata/master.do`
2. Install required Stata packages (see `master.do` header)
3. Run `master.do` to execute all analyses in sequence
4. Output tables appear in `output/tables/`
5. Output figures appear in `output/figures/`

## File Structure

```
v1/
├── code/
│   ├── stata/
│   │   ├── master.do           # Master script (run this)
│   │   ├── 01_clean_data.do    # Data preparation
│   │   ├── 02_desc_stats.do    # Descriptive statistics
│   │   ├── 03_main_regression.do # Main results
│   │   ├── 04_robustness.do    # Robustness checks
│   │   └── ...
│   └── python/
│       └── cross_validation.py # Cross-validates Stata results
├── data/
│   ├── raw/                    # Original data (READ-ONLY)
│   └── clean/                  # Processed data
├── output/
│   ├── tables/                 # LaTeX tables
│   ├── figures/                # PDF figures
│   └── logs/                   # Execution logs
└── REPLICATION.md              # This file
```

## Output-to-Table Mapping

| Table/Figure | Script | Output File |
|-------------|--------|-------------|
| Table 1     | `02_desc_stats.do` | `output/tables/tab_descriptive.tex` |
| Table 2     | `03_main_regression.do` | `output/tables/tab_main_results.tex` |
| Figure 1    | `06_figures.do` | `output/figures/fig_event_study.pdf` |
| ...         | ...    | ... |

## Data Provenance

For each raw data file, document:
- **Source**: Where was it obtained?
- **Date accessed**: When was it downloaded?
- **DOI/URL**: Persistent identifier
- **License**: Usage restrictions
- **Checksum**: MD5 or SHA256 hash of the file

| File | Source | Date | DOI/URL | MD5 |
|------|--------|------|---------|-----|
| [file.dta] | [source] | [date] | [doi] | [hash] |
```

## Step 7: Create MEMORY.md

Create `<project-name>/v1/MEMORY.md`:

```markdown
# Project Memory

## Key Decisions
<!-- Record important methodological and data decisions here -->

## Data Notes
<!-- Record data sources, access dates, known issues -->

## Variable Definitions
<!-- Key variable names and their definitions -->

## Regression Specifications
<!-- Track the main specifications used -->

## Issues & TODOs
<!-- Track outstanding issues -->
```

## Step 8: Create docs/CHANGELOG.md

Create `<project-name>/v1/docs/CHANGELOG.md`:

```markdown
# Changelog

## v1 - <current date>
- Project initialized
- Directory structure created
```

## Step 9: Create .gitignore

Create `<project-name>/.gitignore`:

```
# Data files (may be large or restricted)
*.dta
*.csv
*.xlsx
*.sas7bdat
*.rds
data/raw/*
data/temp/*
!data/raw/.gitkeep
!data/temp/.gitkeep

# Stata logs and temporary files
*.log
*.smcl
*.gph

# Python
__pycache__/
*.pyc
.ipynb_checkpoints/

# OS files
.DS_Store
Thumbs.db

# LaTeX auxiliary files
*.aux
*.bbl
*.blg
*.fdb_latexmk
*.fls
*.synctex.gz
*.out
*.toc
```

## Step 10: Create Placeholder Main TeX Files

Create `<project-name>/v1/paper/main_cn.tex` (if CN or both):

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

Create `<project-name>/v1/paper/main_en.tex` (if EN or both):

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

Create `<project-name>/v1/paper/main_nber.tex` (if format is `NBER` or `all`):

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

% --- NBER Working Paper Formatting ---
\title{<Project Title>\thanks{We thank [acknowledgments: seminar participants, discussants, funding agencies]. Author1: [affiliation], [email]. Author2: [affiliation], [email].}}
\author{<Author 1>\\ \textit{<Institution 1>} \and <Author 2>\\ \textit{<Institution 2>}}
\date{This draft: \today}

\begin{document}
\maketitle

\begin{abstract}
\noindent
% Abstract: 100-200 words. Summarize research question, method, and key findings.
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

Create `<project-name>/v1/paper/main_ssrn.tex` (if format is `SSRN` or `all`):

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

% --- SSRN Preprint Formatting ---
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
% Abstract: 150-250 words. Make it self-contained — many SSRN readers only see the abstract.
% Clearly state: (1) research question, (2) method, (3) data, (4) key finding, (5) contribution.
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

Also create empty placeholder files:
- `<project-name>/v1/paper/bib/references.bib`
- `<project-name>/v1/data/raw/.gitkeep`
- `<project-name>/v1/data/temp/.gitkeep`

## Step 11: Print Summary

After creating everything, print a summary:

```
Project "<project-name>" initialized successfully!

Structure created:
  v1/
    data/raw/  data/clean/  data/temp/
    code/stata/  code/python/  code/r/
    output/tables/  output/figures/  output/logs/
    paper/sections/  paper/bib/
    docs/

Files created:
  - CLAUDE.md (project configuration)
  - v1/_VERSION_INFO.md
  - v1/MEMORY.md
  - v1/REPLICATION.md (AEA Data Editor format)
  - v1/code/stata/master.do
  - v1/docs/CHANGELOG.md
  - v1/paper/main_cn.tex (if CN or both)
  - v1/paper/main_en.tex (if EN or both)
  - v1/paper/main_nber.tex (if NBER or all)
  - v1/paper/main_ssrn.tex (if SSRN or all)
  - v1/paper/bib/references.bib
  - .gitignore

Next steps:
  1. Place raw data files in v1/data/raw/
  2. Update REPLICATION.md with data sources
  3. Start with /data-describe to explore your data
  4. Use /run-did, /run-iv, /run-rdd, or /run-panel for analysis
```
