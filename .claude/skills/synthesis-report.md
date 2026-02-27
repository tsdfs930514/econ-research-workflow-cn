---
description: "Collect all analysis outputs and generate a structured synthesis report (Markdown + LaTeX)"
user_invocable: true
---

# /synthesis-report — Synthesis Report Generation

When the user invokes `/synthesis-report`, collect all analysis products from the current version directory and generate a comprehensive synthesis report.

## Outputs

- `docs/ANALYSIS_SUMMARY.md` — Markdown version (git-trackable)
- `docs/ANALYSIS_SUMMARY.tex` — LaTeX version (compilable to PDF)

## Report Structure

```
1. Executive Summary (method, status, total score)
2. Data & Sample (data sources, sample size, variable definitions)
3. Main Results (main regression coefficients, SEs, significance, economic interpretation)
4. Identification Diagnostics (method-specific diagnostics summary table)
5. Robustness Summary (robustness check overview)
6. Cross-Validation Results (Stata vs Python/R comparison table)
7. Quality Assessment (6-dimension score + /adversarial-review score)
8. Remaining Issues (unresolved findings)
9. Replication Checklist (filled REPLICATION.md checklist)
10. File Manifest (all output files + Table/Figure mapping)
```

## Step 1: Determine Target Version

- Default: read the current version directory from CLAUDE.md (typically `v1/`)
- User can specify: `/synthesis-report v2/` or `/synthesis-report path/to/directory`
- Confirm the target directory exists and contains output files

## Step 2: Scan Log Files for Key Statistics

- Read all files in `output/logs/*.log`
- Extract from each log:
  - Main regression coefficients and standard errors
  - R-squared values
  - Number of observations and clusters
  - F-statistics (overall and first-stage for IV)
  - Diagnostic test results (parallel trends p-value, density test p-value, Bacon decomposition weights, etc.)
  - Any `r(xxx)` errors or warnings
- Organize extracted statistics by analysis type (main results, robustness, diagnostics)

## Step 3: Collect Table Inventory

- Read `output/tables/*.tex` to build a list of generated tables
- For each table file, extract:
  - Table title (from `\caption{}` or header comment)
  - Type (main results, robustness, summary statistics, etc.)
  - Key statistics shown (which coefficients, how many columns)
- Map tables to their role in the paper (Table 1 = summary stats, Table 2 = main results, etc.)

## Step 4: Collect Figure Inventory

- Read `output/figures/*` (PDF, PNG, EPS) to build a list of generated figures
- For each figure, note:
  - File name and format
  - Type (event study, density test, coefficient plot, RDD plot, etc.)
  - Associated analysis step

## Step 5: Collect Quality Score

- If `docs/QUALITY_SCORE.md` exists, read the score breakdown directly
- Otherwise, if `scripts/quality_scorer.py` exists, run `/score` to generate it
- If neither exists, note "Quality score not yet generated" and recommend running `/score`

## Step 6: Collect Cross-Validation Report

- Check for cross-validation output files:
  - `output/logs/cross_check_report*.txt`
  - `output/tables/tab_cross_check*.tex`
- If found, extract:
  - Overall PASS/FAIL status
  - Max coefficient difference
  - Any FAIL items with details
- If not found, note "Cross-validation not yet performed" and recommend `/cross-check`

## Step 7: Generate docs/ANALYSIS_SUMMARY.md

Create the Markdown report with this structure:

```markdown
# Analysis Summary — [Project Name] (vN/)

Generated: YYYY-MM-DD HH:MM

---

## 1. Executive Summary

- **Research Question**: [extracted from research_proposal.md or CLAUDE.md]
- **Identification Strategy**: [DID / IV / RDD / Panel / SDID]
- **Primary Dataset**: [data source and sample period]
- **Key Finding**: [main coefficient, significance, economic interpretation]
- **Quality Score**: XX/100 — [Publication Ready / Minor Revisions / Major Revisions / Redo]
- **Pipeline Status**: [Complete / Partial — missing steps listed]

## 2. Data & Sample

| Item | Value |
|------|-------|
| Data Source | [source] |
| Sample Period | [years] |
| Total Observations | [N] |
| Cross-sectional Units | [N firms/counties/etc.] |
| Time Periods | [N years/quarters] |
| Treatment Group Size | [N treated units] |
| Control Group Size | [N control units] |

### Key Variables

| Variable | Role | Definition | Source |
|----------|------|------------|--------|
| [Y] | Dependent | [description] | [source] |
| [D] | Treatment | [description] | [source] |
| [X1..Xk] | Controls | [description] | [source] |

## 3. Main Results

| Specification | Coefficient | SE | p-value | N | R² | Significance |
|--------------|-------------|-----|---------|---|-----|-------------|
| Baseline | [b] | ([se]) | [p] | [N] | [R²] | [stars] |
| With controls | [b] | ([se]) | [p] | [N] | [R²] | [stars] |
| Preferred | [b] | ([se]) | [p] | [N] | [R²] | [stars] |

**Economic Interpretation**: [A one-unit increase in X is associated with a b-unit change in Y, which represents X% of the sample mean.]

## 4. Identification Diagnostics

[Method-specific diagnostics table — content varies by method]

### DID Diagnostics
| Test | Statistic | p-value | Result |
|------|-----------|---------|--------|
| Parallel trends (joint F-test) | F = | p = | PASS/FAIL |
| Bacon decomposition (TWFE share) | | | |
| CS-DiD ATT(simple) | | | |
| HonestDiD (M = 0.05) | | | |

### IV Diagnostics
| Test | Statistic | Result |
|------|-----------|--------|
| First-stage F | | > 10? |
| KP rk Wald F | | |
| Anderson-Rubin | | |
| LIML vs 2SLS gap | | |
| Hansen J (if overidentified) | | |

### RDD Diagnostics
| Test | Statistic | p-value | Result |
|------|-----------|---------|--------|
| CJM density test | | | |
| Optimal bandwidth | | | |
| Donut RDD stable | | | |
| Placebo cutoffs insignificant | | | |

## 5. Robustness Summary

| Check | Coefficient | SE | Significant? | Status |
|-------|------------|-----|-------------|--------|
| Baseline | [b] | ([se]) | Yes/No | REF |
| Alt dep var | [b] | ([se]) | Yes/No | PASS/FAIL |
| Drop outliers | [b] | ([se]) | Yes/No | PASS/FAIL |
| Alt clustering | [b] | ([se]) | Yes/No | PASS/FAIL |
| Subsample: early | [b] | ([se]) | Yes/No | PASS/FAIL |
| Subsample: late | [b] | ([se]) | Yes/No | PASS/FAIL |
| Winsorized 1/99 | [b] | ([se]) | Yes/No | PASS/FAIL |
| Oster delta | [delta] | — | > 1? | PASS/FAIL |
| Wild cluster bootstrap | [b] | [CI] | — | PASS/FAIL |

**Summary**: X/Y specifications maintain sign and significance.

## 6. Cross-Validation Results

| Statistic | Stata | Python | Rel. Diff | Status |
|-----------|-------|--------|-----------|--------|
| coef(treatment) | [b] | [b] | [diff]% | PASS/FAIL |
| se(treatment) | [se] | [se] | [diff]% | PASS/FAIL |
| R-squared | [R²] | [R²] | [diff] | PASS/FAIL |
| N | [N] | [N] | [diff] | PASS/FAIL |

**Overall**: [PASS — all within tolerance / FAIL — items listed]

## 7. Quality Assessment

### Automated Score (quality_scorer.py)

| Dimension | Score | Max | Details |
|-----------|-------|-----|---------|
| Code Conventions | /15 | 15 | |
| Log Cleanliness | /15 | 15 | |
| Output Completeness | /15 | 15 | |
| Cross-Validation | /15 | 15 | |
| Documentation | /15 | 15 | |
| Method Diagnostics | /25 | 25 | |
| **TOTAL** | **/100** | **100** | |

**Status**: [Publication Ready / Minor Revisions / Major Revisions / Redo]

### Adversarial Review Score (if available)

| Critic | Score | Key Findings |
|--------|-------|-------------|
| code-critic | /100 | [summary] |
| econometrics-critic | /100 | [summary] |
| tables-critic | /100 | [summary] |

## 8. Remaining Issues

| # | Source | Severity | Description | Suggested Fix |
|---|--------|----------|-------------|--------------|
| 1 | [critic/scorer] | Critical/High/Medium/Low | [description] | [fix] |
| 2 | | | | |

## 9. Replication Checklist

- [ ] Raw data files present in `data/raw/`
- [ ] All .do files run without errors
- [ ] All .py cross-validation scripts run
- [ ] master.do reproduces all results end-to-end
- [ ] REPLICATION.md documents all steps
- [ ] _VERSION_INFO.md is current
- [ ] Output-to-table mapping is complete
- [ ] All packages and versions documented

## 10. File Manifest

### Code Files
| File | Description | Status |
|------|-------------|--------|
| `code/stata/01_*.do` | [description] | [runs clean / has errors] |
| ... | | |

### Output Files
| File | Type | Mapped To |
|------|------|-----------|
| `output/tables/tab_main_results.tex` | Main results | Table 2 |
| `output/figures/fig_event_study.pdf` | Event study | Figure 1 |
| ... | | |

### Documentation
| File | Status |
|------|--------|
| `REPLICATION.md` | [complete / partial / missing] |
| `_VERSION_INFO.md` | [complete / partial / missing] |
| `docs/QUALITY_SCORE.md` | [complete / missing] |
```

## Step 8: Generate docs/ANALYSIS_SUMMARY.tex

Create a LaTeX version that:
- Uses `\documentclass{article}` with `booktabs`, `longtable`, `hyperref`, `geometry` packages
- Converts all Markdown tables to LaTeX `tabular` environments
- Uses `\input{}` to reference existing table .tex files from `output/tables/` where possible (avoid duplicating table content)
- Uses `\includegraphics{}` to reference existing figures from `output/figures/`
- Includes a `\tableofcontents` for navigation
- Is compilable with `pdflatex` (no special engines required)

Structure:
```latex
\documentclass[12pt]{article}
\usepackage{booktabs, longtable, hyperref, geometry, graphicx}
\geometry{margin=1in}

\title{Analysis Summary --- [Project Name] (vN/)}
\date{\today}

\begin{document}
\maketitle
\tableofcontents
\newpage

\section{Executive Summary}
...

\section{Main Results}
% Include existing table if available:
% \input{../output/tables/tab_main_results.tex}
...

\section{File Manifest}
...

\end{document}
```

## Step 9: Update REPLICATION.md

If `REPLICATION.md` exists in the version directory, update its Output-to-Table Mapping section with the actual file manifest generated in Step 7/8:

```markdown
## Output-to-Table Mapping

| Paper Element | Source File | Script |
|--------------|-------------|--------|
| Table 1 (Summary Statistics) | `output/tables/tab_desc_stats.tex` | `code/stata/02_desc_stats.do` |
| Table 2 (Main Results) | `output/tables/tab_main_results.tex` | `code/stata/03_reg_main.do` |
| Figure 1 (Event Study) | `output/figures/fig_event_study.pdf` | `code/stata/03_reg_main.do` |
```

## Step 10: Record to MEMORY.md

Append to MEMORY.md:

```
[LEARN] YYYY-MM-DD: Generated synthesis report for <target>. Score: XX/100, Status: [status]. Report at docs/ANALYSIS_SUMMARY.md.
```
