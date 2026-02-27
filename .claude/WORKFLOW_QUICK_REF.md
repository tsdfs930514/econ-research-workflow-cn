# Econ Research Workflow - Quick Reference

## Skills Reference (30 skills)

### Core Analysis

| Command | Description | Typical Use |
|---------|-------------|-------------|
| `/init-project` | Initialize project structure | Start of project |
| `/data-describe` | Descriptive statistics (Stata + Python) | After data cleaning |
| `/run-did` | DID/TWFE/CS/SDID pipeline with diagnostics | Causal estimation |
| `/run-iv` | IV/2SLS pipeline with first-stage and weak-instrument tests | Causal estimation |
| `/run-rdd` | RDD pipeline with bandwidth sensitivity and density test | Causal estimation |
| `/run-panel` | Panel FE/RE/GMM with Hausman, serial correlation tests | Causal estimation |
| `/run-sdid` | Synthetic DID with unit/time weights and inference | Causal estimation |
| `/run-bootstrap` | Pairs, wild cluster, residual, teffects bootstrap inference | After main results |
| `/run-placebo` | Timing, outcome, instrument, permutation placebo tests | Robustness checks |
| `/run-logit-probit` | Logit/probit, propensity score, RA/IPW/AIPW, conditional logit | Binary/treatment models |
| `/run-lasso` | LASSO, post-double-selection, rigorous LASSO, glmnet matching | Variable selection |
| `/cross-check` | Stata ↔ Python regression cross-validation (< 0.1%) | After any regression |
| `/robustness` | Comprehensive robustness test suite | After main results |

### Output & Writing

| Command | Description | Typical Use |
|---------|-------------|-------------|
| `/make-table` | Publication-quality LaTeX tables (AER or 三线表) | Before paper writing |
| `/write-section` | Write paper section (CN or EN journal conventions) | Paper drafting |
| `/compile-latex` | Run pdflatex/bibtex pipeline with error checking | After paper edits |

### Review & Quality

| Command | Description | Typical Use |
|---------|-------------|-------------|
| `/review-paper` | Three simulated peer reviewers | Before submission |
| `/lit-review` | Structured literature review with BibTeX | Early stage / revision |
| `/adversarial-review` | Critic-fixer loop (code, econometrics, tables) up to 5 rounds | Quality assurance |
| `/score` | Executable quality scorer (6 dimensions, 100 pts) | After any deliverable |

### Session & Project Management

| Command | Description | Typical Use |
|---------|-------------|-------------|
| `/commit` | Smart git commit with type prefix and data safety warnings | After changes |
| `/context-status` | Display version, decisions, scores, git state | Start of work |
| `/session-log` | Session start/end with MEMORY.md integration | Session boundaries |
| `/explore` | Exploration sandbox with relaxed thresholds (>= 60) | Hypothesis testing |
| `/promote` | Graduate files from `explore/` to `vN/` with quality check | After exploration |

### Research Ideation & Governance

| Command | Description | Typical Use |
|---------|-------------|-------------|
| `/interview-me` | Bilingual Socratic interview → structured research proposal | New research ideas |
| `/devils-advocate` | Pre-analysis threat assessment for identification strategy | Before estimation |
| `/learn` | Create new rules or skills from within a session | Codifying conventions |
| `/run-pipeline` | Auto-detect methods, orchestrate full skill pipeline | End-to-end automation |
| `/synthesis-report` | Collect outputs into structured synthesis report (MD + LaTeX) | After scoring |

### Reference Resources

| Resource | Description | Usage |
|----------|-------------|-------|
| `advanced-stata-patterns.md` | Impulse response, Helmert, HHK, k-class, bootstrap, spatial lags | Auto-consulted by run-panel/run-iv for advanced patterns |

This is a non-user-invocable reference file (no slash command). It is consulted automatically by relevant skills when advanced Stata patterns are needed.

---

## Agents Reference (12 agents)

### Legacy Reviewers

| Agent | Role | Status |
|-------|------|--------|
| `econometrics-reviewer` | Checks identification strategy and estimation | **DEPRECATED** (use `econometrics-critic`) |
| `code-reviewer` | Reviews Stata/Python code quality | **DEPRECATED** (use `code-critic`) |
| `paper-reviewer` | Simulates journal referee | Active — wired into `/review-paper` |
| `tables-reviewer` | Checks table formatting and compliance | **DEPRECATED** (use `tables-critic`) |
| `robustness-checker` | Suggests missing robustness tests | Active — wired into `/robustness` |
| `cross-checker` | Compares Stata vs Python results | Active — wired into `/cross-check` |

### Adversarial Critic-Fixer Pairs

| Critic | Fixer | Domain |
|--------|-------|--------|
| `code-critic` | `code-fixer` | Code conventions, safety, reproducibility |
| `econometrics-critic` | `econometrics-fixer` | Identification, diagnostics, robustness |
| `tables-critic` | `tables-fixer` | Table formatting, reporting, compliance |

Critics are read-only and cannot edit files. Fixers have full access but cannot score their own work.

---

## Typical Workflow Sequences

### Research Ideation
```
/interview-me → /devils-advocate → /data-describe → /run-{method}
```

### Full Paper Pipeline
```
/init-project → /data-describe → /run-{method} → /cross-check → /robustness
  → /make-table → /write-section → /review-paper → /adversarial-review
  → /score → /synthesis-report → /compile-latex → /commit
```

### Automated Pipeline (single command)
```
/run-pipeline  →  auto-detects method  →  runs full sequence  →  /synthesis-report
```

### Quick Regression Check
```
/run-{method} → /cross-check → /score
```

### Revision Response
```
/context-status → (address comments) → /adversarial-review → /score → /commit
```

### Exploration Sandbox
```
/explore → (work in explore/) → /promote → /score
```

### Literature Deep-Dive
```
/lit-review → /write-section (Literature Review)
```

---

## Governance

### Constitution (`.claude/rules/constitution.md`)

5 immutable principles — always-on, cannot be overridden:
1. Raw data integrity (`data/raw/` never modified)
2. Full reproducibility (every result from code + raw data)
3. Mandatory cross-validation (< 0.1%; relaxed in `explore/`)
4. Version preservation (`vN/` never deleted)
5. Score integrity (recorded faithfully)

### Orchestrator Protocol

Non-trivial tasks follow: **Spec → Plan → Implement → Verify → Review → Fix → Score → Report**

Phase 0 (Spec) triggers when task affects >= 3 files, changes identification strategy, creates skills/rules/agents, or modifies the protocol. Written once per task — the review loop restarts at Plan.

"Just Do It" mode: trivial tasks (<=2 files, score >= 80, no Critical findings) skip the multi-round loop.

---

## Quality Scoring

| Score | Meaning | Action |
|-------|---------|--------|
| >= 95 | Publication ready | Proceed |
| >= 90 | Minor revisions | One more round |
| >= 80 | Major revisions | Re-enter implementation |
| < 80 | Redo | Re-enter planning |

Scores from `/score` (automated, 6 dimensions) and `/adversarial-review` (critic agents).

---

## Key Conventions

### File Paths
- Raw data (READ-ONLY): `vN/data/raw/`
- Cleaned data: `vN/data/clean/`
- Stata code: `vN/code/stata/`
- Python code: `vN/code/python/`
- All output: `vN/output/`
- Tables: `vN/output/tables/`
- Figures: `vN/output/figures/`
- Paper: `vN/paper/`

### Stata Execution (Git Bash)
```bash
"D:\Stata18\StataMP-64.exe" -e do "code/stata/script.do"
```
- **必须用 `-e`**（自动退出），**禁止用 `-b`**（需手动确认）或 **`/e`**（Git Bash 路径冲突）
- Always check the `.log` file after every Stata run
- Non-zero exit or `r(xxx)` in log = failure

### Versioning
- Each major revision lives in its own `vN/` directory
- `_VERSION_INFO.md` tracks version metadata
- `docs/CHANGELOG.md` tracks project-level changes

### Naming Conventions
- Stata do-files: `01_clean_data.do`, `02_desc_stats.do`, `03_reg_main.do`, ...
- Output tables: `tab_main_results.tex`, `tab_robustness.tex`, ...
- Output figures: `fig_event_study.pdf`, `fig_parallel_trends.pdf`, ...

---

## Common Patterns

### Adding a Robustness Check
1. Run `/robustness` to get suggestions
2. Implement suggested checks in `04_robustness.do`
3. Run `/cross-check` to validate
4. Run `/make-table` to format results

### Responding to Referee Comments
1. Create new version directory `vN+1/`
2. Copy and modify relevant code
3. Run `/robustness` for additional tests
4. Run `/make-table` for updated tables
5. Run `/write-section` for response letter
6. Run `/review-paper` to self-check

### Cross-Validation Workflow
1. Run regression in Stata via `/run-{method}`
2. Run `/cross-check` to replicate in Python
3. Review coefficient comparison table
4. Tolerance: coefficients within 0.1% (strict), SEs within 5%

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Stata log shows error | Read full log, fix do-file, re-run |
| Cross-check mismatch | Check clustering, sample restrictions, variable definitions |
| LaTeX table won't compile | Check `\input{}` paths, missing packages |
| Version conflict | Always work in latest `vN/` directory |
| Exploration results too rough | Use `/promote` to graduate with quality gate |
