# Roadmap

## Phase 1 — Core Quality Infrastructure

**Status**: Implemented

- 6 new adversarial agents (3 critic-fixer pairs: code, econometrics, tables)
- `/adversarial-review` skill orchestrating multi-round critic-fixer loops
- Executable `quality_scorer.py` (6 dimensions, 100 pts, auto-detects methods)
- `/score`, `/commit`, `/compile-latex`, `/context-status` skills
- MEMORY.md activation with tagged entries and session logging
- README.md with English main body + Chinese quick-start
- Orchestrator protocol update with "Just Do It" mode

---

## Phase 2 — Infrastructure (Implemented)

**Status**: Implemented

### Hooks (`settings.json`)

3 lifecycle hooks in `.claude/settings.json`:

| Hook | Trigger | Action |
|------|---------|--------|
| Session-start loader | `SessionStart` | Read MEMORY.md, display recent entries, last session, last quality score |
| Pre-compact save | `PreCompact` | Prompt Claude to append session summary to MEMORY.md before compaction |
| Post-Stata log check | `PostToolUse` (Bash) | Auto-parse .log for `r(xxx)` errors after Stata execution |

Hook scripts: `.claude/hooks/session-loader.py`, `.claude/hooks/stata-log-check.py`

### Path-Scoped Rules

4 rules scoped via `paths:` frontmatter; 1 always-on (2 more always-on rules added in Phase 3 and 5):

| Rule | `paths:` Pattern |
|------|-----------------|
| `stata-conventions.md` | `**/*.do` |
| `python-conventions.md` | `**/*.py` |
| `econometrics-standards.md` | `**/code/**`, `**/output/**` |
| `replication-standards.md` | `**/REPLICATION.md`, `**/master.do`, `**/docs/**` |
| `orchestrator-protocol.md` | *(always-on, no paths)* |

### Exploration Sandbox

- `/explore` skill — creates `explore/` workspace with relaxed quality thresholds (>= 60 vs 80)
- `/promote` skill — graduates files from `explore/` to `vN/`, renumbers, runs `/score` to verify

### Session Continuity

- `/session-log` skill — explicit session start/end with MEMORY.md context loading and recording
- `personal-memory.md` (gitignored) — machine-specific preferences (Stata path, editor, directories)

---

## Phase 3 — Polish (Implemented)

**Status**: Implemented

### Socratic Research Tools

- `/interview-me` — bilingual (EN/CN) Socratic questioning to formalize research ideas
  - Walks through: research question → hypothesis → identification strategy → data requirements → expected results
  - Asks one question at a time; sections are skippable
  - Outputs structured research proposal to `vN/docs/research_proposal.md`

- `/devils-advocate` — systematic pre-analysis challenges to identification strategy
  - Universal threats (OVB, reverse causality, measurement error, selection, SUTVA)
  - Method-specific threats (DID/IV/RDD/Panel/SDID)
  - 3 alternative explanations per key result
  - Falsification test recommendations
  - Threat matrix with severity levels (Critical/High/Medium/Low, matching `econometrics-critic`)

### Self-Extension Infrastructure

- `/learn` — create new rules or skills from within sessions
  - Guided creation: type → content → validate → preview → write
  - Auto-generates properly formatted .md files in `.claude/rules/` or `.claude/skills/`
  - Constitution guard: cannot create rules/skills violating `constitution.md`
  - Logs `[LEARN]` entries to MEMORY.md

### Governance

- **`constitution.md`** — 5 immutable principles (always-on rule, no `paths:` frontmatter):
  1. Raw data integrity (`data/raw/` never modified)
  2. Full reproducibility (every result traceable from code + raw data)
  3. Mandatory cross-validation (Stata ↔ Python, < 0.1%; relaxed in `explore/`)
  4. Version preservation (`vN/` never deleted)
  5. Score integrity (scores recorded faithfully)

- **Spec-then-plan protocol** — Phase 0 added to orchestrator protocol:
  - Triggered when task affects >= 3 files, changes identification strategy, creates skills/rules/agents, or modifies the protocol itself
  - Format: MUST / SHOULD / MAY requirements + acceptance criteria + out of scope
  - Written once per task; review loop restarts at Phase 1

---

## Phase 4 — Methodology Expansion & Consolidation (Implemented)

**Status**: Implemented

### New Methodology Skills

4 standalone methodology skills added to cover gaps identified during replication stress testing:

| Skill | Scope |
|-------|-------|
| `/run-bootstrap` | Pairs, wild cluster, residual, and teffects bootstrap inference pipelines |
| `/run-placebo` | Timing, outcome, instrument, and permutation placebo test pipelines |
| `/run-logit-probit` | Logit/probit, propensity score, treatment effects (RA/IPW/AIPW), conditional logit |
| `/run-lasso` | LASSO, post-double-selection, rigorous LASSO, R `glmnet` matching pipeline |

### Skill Consolidation

- Extracted advanced Stata patterns (impulse response, Helmert, HHK, k-class, bootstrap, spatial lags) from `run-panel.md` (665→371 lines) and `run-iv.md` (528→323 lines) into non-user-invocable reference file `advanced-stata-patterns.md` (443 lines)
- Compressed Stata execution blocks in all 5 `run-*` files
- Net reduction: 2,175→2,083 lines (-92 lines)
- Total: **28 user-invocable skills + 1 reference guide**

### Replication Package Stress Testing

6 replication packages analyzed to validate and improve skills:

| Package | Paper | Skills Updated |
|---------|-------|---------------|
| Acemoglu et al. (2019) — DDCG | JPE, Democracy & Growth | `/run-panel`, `/run-iv`, `/make-table` |
| Mexico Retail Entry | Economic Census | `/run-iv`, `/data-describe` |
| SEC Comment Letters (mnsc.2021.4259) | Management Science | `/data-describe`, `/cross-check` |
| Bond Market Liquidity (mnsc.2022.4646) | Management Science | `/cross-check`, `/run-panel` |
| RTAs & Environment (jvae023) | JEEA 2024 | `/run-lasso` |
| Culture & Development (data_programs) | — | `/run-bootstrap` |

### APE Reference Papers

3 R-based replication packages archived in `references/ape-winners/ape-papers/`:

| Package | Design | Key R Packages |
|---------|--------|---------------|
| apep_0119 (EERS & Electricity) | Staggered DID | `did`, `fixest`, `HonestDiD`, `fwildclusterboot` |
| apep_0185 (Network MW Exposure) | Shift-share IV | `fixest`, exposure permutation inference |
| apep_0439 (Cultural Borders) | Spatial RDD + Panel | `fixest`, `rdrobust`, permutation inference |

These are R-only patterns that supplement Stata-primary skills. Methodology patterns recorded in MEMORY.md as `[LEARN]` entries.

---

## Phase 5 — Real-Data Replication Testing & Skill Hardening (Implemented)

**Status**: Implemented (2026-02-26)

### End-to-End Replication Testing

All 9 `/run-*` skills tested against real published replication packages. 11 package × skill combinations run end-to-end through Stata:

| # | Package × Skill | Status |
|---|----------------|--------|
| 1 | DDCG → `/run-panel` (FE + GMM) | PASS |
| 2 | DDCG → `/run-iv` (2SLS with regional democracy waves) | PASS |
| 3 | Culture & Development → `/run-bootstrap` (pairs + wild cluster) | PASS |
| 4 | jvae023 → `/run-lasso` (logistic LASSO PS → matching) | PASS |
| 5 | DDCG → `/run-placebo` (timing + permutation) | PASS |
| 6 | DDCG → `/run-logit-probit` (xtlogit, margins, teffects) | PASS |
| 7 | SEC Comment Letters → `/run-panel` (cross-section absorbed FE) | PASS |
| 8 | Mexico Retail → `/run-iv` (ivreghdfe, large-scale) | PASS |
| 9 | jvae023 → `/run-did` (csdid on matched panel) | PASS |
| 10 | Synthetic → `/run-rdd` (rdrobust, rddensity) | PASS |
| 11 | DDCG → `/run-sdid` (SDID/DID/SC bootstrap VCE) | PASS |

### Issues Found & Fixed (19 total)

| Issue | Category | Root Cause | Skill(s) Updated |
|-------|----------|-----------|------------------|
| #11 | DIAGNOSTIC | `estat bootstrap, bca` requires explicit `saving(, bca)` | `/run-bootstrap` |
| #12 | COMPATIBILITY | `boottest` fails after non-reghdfe estimators | `/run-bootstrap`, `/run-did` |
| #13 | SYNTAX | `bootstrap _b` saves as `_b_varname`, not `_bs_N` | `/run-bootstrap` |
| #14 | DIAGNOSTIC | DWH `e(estatp)` unavailable with `xtivreg2 + partial()` | `/run-iv` |
| #15 | EDGE-CASE | `teffects` commands fail on panel data (repeated obs) | `/run-logit-probit` |
| #16 | EDGE-CASE | CV LASSO selects 0 variables in small samples | `/run-lasso` |
| #17 | TEMPLATE-GAP | No fallback when LASSO selects 0 vars | `/run-lasso` |
| #18 | COMPATIBILITY | `lasso logit` r(430) convergence with near-separation | `/run-lasso` |
| #19 | EDGE-CASE | String panel IDs require `encode` before `xtset` | `/run-did` |
| #20 | COMPATIBILITY | `csdid_stats` syntax varies across package versions | `/run-did` |
| #21 | SYNTAX | Hardcoded variable names (`lgdp`) instead of user params | `/run-sdid` |
| #22 | TEMPLATE-GAP | Significant timing placebo ≠ confounding (anticipation effects) | `/run-placebo` |
| #23 | COMPATIBILITY | Old Stata syntax (`set mem`, `clear matrix`) in packages | `/run-panel` |
| #24 | SYNTAX | `ereturn post` + `estimates store` fails after `sdid` | `/run-sdid` |
| #25 | EDGE-CASE | `vce(jackknife)` requires ≥2 treated units per period | `/run-sdid` |
| #26 | PROCESS | Hook-reported errors ignored; log overwritten before verification | New rule: `stata-error-verification.md` |
| #27 | TEMPLATE-GAP | 8-lag model needs `vareffects8` program (not implemented) | `/run-panel` |
| #28 | SYNTAX | `/` in Stata local macro label caused parsing failure | `/run-panel` |
| #29 | SYNTAX | `levelsof` returns numeric codes for value-labeled vars; loop used as string | `/run-panel` |

### Defensive Programming Patterns Added

Codified 8 defensive patterns in `stata-conventions.md`:

1. **Community package guards**: `cap noisily` + `cap ssc install` for all SSC commands
2. **String panel ID check**: `confirm string variable` + `encode` before `xtset`
3. **e-class availability check**: Test scalars before use (`e(estatp) != .`)
4. **Local macros for non-standard estimators**: Use locals instead of `estimates store` for `sdid`
5. **Continuous vs categorical inspection**: `summarize` not `tab` for continuous variables
6. **Negative Hausman handling**: Check `r(chi2) < 0` and interpret correctly
7. **Old Stata syntax stripping**: Omit deprecated `set mem`, `clear matrix` when adapting old code
8. **Bootstrap variable naming**: Use `ds` to discover `_b_varname` pattern

### Cross-Validation Results

| Package | Method | Stata vs Python Diff |
|---------|--------|---------------------|
| DDCG Panel FE | reghdfe vs pyfixest | 0.0000% — PASS |
| DDCG IV 2SLS | ivreghdfe vs pyfixest | 0.0000% — PASS |

### Regression Verification

Re-ran original test suite (test1-5) after all skill updates: **5/5 PASS with zero r(xxx) errors**. No regressions introduced.

### Stata Error Verification Rule

Added `stata-error-verification.md` as a new always-on rule (Issue #26). Enforces that Claude must read hook output before re-running scripts, preventing log-overwrite false positives discovered during DDCG replication.

### Files Modified

- 9 skill files: `run-did.md` through `run-sdid.md` (defensive patterns + issue notes)
- `advanced-stata-patterns.md` (SDID local macros pattern added)
- `stata-conventions.md` (comprehensive defensive programming section added)
- `stata-error-verification.md` (new always-on rule for error verification protocol)
- `ISSUES_LOG.md` (19 issues documented with root cause and fix)
- `MEMORY.md` (session log and skill update entries)

---

## Phase 6 — Workflow Completion: Pipeline Orchestration, Agent Rewiring, Synthesis Report (Implemented)

**Status**: Implemented (2026-02-27)

### Pipeline Orchestration

- `/run-pipeline` skill — auto-detects econometric method(s) from research plan text, `research_proposal.md`, or paper PDF, generates an ordered skill execution plan, and runs it end-to-end
  - Supports `--quick` (skip confirmation) and `--replication <paper.pdf>` (extract methods from published paper) flags
  - Method detection: DID, IV, RDD, Panel, SDID, Bootstrap, Placebo, Logit-Probit, LASSO
  - Multi-method support: primary analysis + robustness alternatives
  - Error handling: pauses on Stata `r(xxx)` errors, offers fix/skip/abort
  - Automatic `/synthesis-report` at the end

### Synthesis Report

- `/synthesis-report` skill — collects all analysis outputs (logs, tables, figures, scores, cross-validation) into a structured comprehensive report
  - Outputs: `docs/ANALYSIS_SUMMARY.md` (Markdown) + `docs/ANALYSIS_SUMMARY.tex` (LaTeX)
  - 10-section structure: Executive Summary, Data & Sample, Main Results, Identification Diagnostics, Robustness Summary, Cross-Validation, Quality Assessment, Remaining Issues, Replication Checklist, File Manifest
  - Updates REPLICATION.md Output-to-Table Mapping

### Legacy Agent Rewiring

3 legacy agents wired into active skills:

| Agent | Wired Into | Role |
|-------|-----------|------|
| `paper-reviewer` | `/review-paper` | Executes 3 reviewer personas via Task tool |
| `robustness-checker` | `/robustness` | Identifies missing robustness checks before .do generation |
| `cross-checker` | `/cross-check` | Independent diagnosis of Stata vs Python discrepancies |

3 legacy agents deprecated (superseded by adversarial critic-fixer pairs):

| Agent | Superseded By |
|-------|--------------|
| `code-reviewer` | `code-critic` |
| `econometrics-reviewer` | `econometrics-critic` |
| `tables-reviewer` | `tables-critic` |

### Orchestrator Protocol Update

- Added **Phase 7: Report** after Phase 6 (Score)
- Workflow: Spec → Plan → Implement → Verify → Review → Fix → Score → Report
- Exit criterion: `ANALYSIS_SUMMARY.md` exists and is complete

### Score Persistence

- `/score` now generates `docs/QUALITY_SCORE.md` with full dimension breakdown
- Enables `/synthesis-report` to read scores directly without re-running the scorer

### Files Changed

- 2 new skills: `synthesis-report.md`, `run-pipeline.md`
- 4 modified skills: `score.md`, `review-paper.md`, `robustness.md`, `cross-check.md`
- 3 deprecated agents: `code-reviewer.md`, `econometrics-reviewer.md`, `tables-reviewer.md`
- 1 modified rule: `orchestrator-protocol.md`
- 4 updated docs: `README.md`, `CLAUDE.md`, `ROADMAP.md`, `WORKFLOW_QUICK_REF.md`

---

## Timeline

| Phase | Target | Depends On |
|-------|--------|------------|
| Phase 1 | Done | — |
| Phase 2 | Done | Phase 1 stable |
| Phase 3 | Done | Phase 2 hooks working reliably |
| Phase 4 | Done | Phase 3 complete; replication packages available |
| Phase 5 | Done | Phase 4 complete; real replication data available |
| Phase 6 | Done | Phase 5 complete; workflow structure stable |
