---
description: "Display current project context: version, recent decisions, quality scores, git state"
user_invocable: true
---

# /context-status — Project Context Dashboard

When the user invokes `/context-status`, gather and display a comprehensive snapshot of the current project state. This is useful at the start of a session or when resuming work.

## Information to Gather

### 1. Current Version
- Read `CLAUDE.md` for the active version (e.g., `v1`)
- Read `_VERSION_INFO.md` in the active version directory for version metadata

### 2. Recent Decisions (from MEMORY.md)
- Read `MEMORY.md`
- Display the last 5 tagged entries (any tag: LEARN, DECISION, ISSUE, PREFERENCE)
- Display the last session log entry

### 3. Last Quality Score
- Check if `quality_scorer.py` has been run recently by looking for score entries in MEMORY.md
- If available, display the last score breakdown

### 4. Output File Status
- Check `output/tables/` — list .tex files with sizes
- Check `output/figures/` — list .pdf/.png files with sizes
- Check `output/logs/` — list .log files, flag any containing `r(` errors
- Report any expected files that are missing or empty

### 5. Git State
- `git branch` — current branch name
- `git status --short` — dirty/clean state, untracked files
- `git log --oneline -3` — last 3 commits

### 6. Data Status
- Check `data/raw/` — list files (confirm data is present)
- Check `data/clean/` — list processed datasets
- Flag if `data/raw/` is empty (data not yet placed)

## Display Format

```
Project Context Dashboard
═══════════════════════════════════════════

Version:  v1 (created 2026-02-25)
Project:  [Project Name]
Branch:   main (clean)

Recent Activity:
  [ISSUE] 2026-02-25: boottest incompatible with multi-FE reghdfe
  [DECISION] 2026-02-25: Use CS-DiD as primary estimator over TWFE
  [LEARN] 2026-02-25: Quality score for v1/: 82/100

Last Session: 2026-02-25 — Completed DID analysis, fixed boottest issue

Quality Score: 82/100 (last run 2026-02-25)
  Code: 12/15 | Logs: 15/15 | Output: 10/15
  CrossVal: 0/15 | Docs: 12/15 | Diagnostics: 20/25

Output Files:
  tables/  3 files (tab_did_main.tex, tab_did_comparison.tex, tab_summary.tex)
  figures/ 4 files (fig_event_study_*.pdf, fig_bacon_decomp.pdf)
  logs/    5 files (2 with errors flagged)

Data:
  raw/    2 files (panel_data.dta, crosswalk.csv)
  clean/  1 file (panel_cleaned.dta)

Git:
  abc1234 [v1] code: add event study with CS-DiD
  def5678 [v1] output: regenerate DID tables
  ghi9012 [v1] data: initial data cleaning pipeline

Suggested Next Steps:
  - Cross-validation score is 0/15 → run /cross-check
  - 2 log files have errors → review with /adversarial-review code
  - Overall score 82 → run /score after fixes
```

## Error Handling

- If MEMORY.md doesn't exist: note "No memory file found. Run /init-project or create MEMORY.md."
- If no version directory exists: note "No version directory found. Run /init-project to start."
- If git is not initialized: skip git section, note "Not a git repository."
- If quality_scorer.py hasn't been run: note "No quality score recorded. Run /score."
