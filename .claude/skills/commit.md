---
description: "Smart git commit with type prefix, data safety warnings, and auto-generated message"
user_invocable: true
---

# /commit — Smart Git Commit

When the user invokes `/commit`, follow these steps:

## Step 1: Check Status

Run `git status` to see all changes (staged and unstaged).

## Step 2: Safety Checks

**Warn and block** if any of these are staged:
- Files in `data/raw/` — raw data should not be committed (it's either too large or restricted)
- `.env` files or files containing credentials
- `.dta`, `.csv`, or other large data files (unless in a `tests/` directory)
- Stata `.log` files (usually gitignored)

If flagged files are found, display a warning and ask the user to confirm before proceeding.

## Step 3: Determine Commit Type

Based on the changed files, auto-detect the commit type:

| Type | Trigger (files changed) |
|------|------------------------|
| `data` | Files in `data/clean/`, `data/temp/`, data processing scripts |
| `code` | `.do` files, `.py` files in `code/` |
| `output` | Files in `output/tables/`, `output/figures/` |
| `paper` | `.tex` files in `paper/` |
| `docs` | `.md` files, `REPLICATION.md`, `_VERSION_INFO.md` |
| `fix` | Changes that fix errors (detected from commit context) |
| `refactor` | Code restructuring without logic changes |

If multiple types apply, use the primary one (the type with the most changed files).

## Step 4: Detect Version

Read CLAUDE.md or _VERSION_INFO.md to determine the current version (e.g., `v1`).

## Step 5: Generate Commit Message

Format: `[vN] type: description`

Examples:
- `[v1] code: add DID event study with Callaway-Sant'Anna estimator`
- `[v1] output: regenerate main regression tables with clustered SEs`
- `[v1] fix: correct first-stage F-statistic reporting in IV table`
- `[v1] docs: update REPLICATION.md with data sources`

## Step 6: Show for Approval

Display the proposed commit:

```
Proposed commit:
  Message: [v1] code: add DID event study with Callaway-Sant'Anna estimator
  Files:
    M  v1/code/stata/03_did_analysis.do
    A  v1/code/stata/04_event_study.do
    M  v1/output/logs/did_analysis.log

Proceed? (yes/edit/cancel)
```

- **yes**: Execute the commit
- **edit**: Let user modify the message
- **cancel**: Abort

## Step 7: Commit

```bash
git add <specific files>
git commit -m "[vN] type: description"
```

Stage specific files by name — do NOT use `git add -A` or `git add .`.

## Step 8: Confirm

Show `git log --oneline -1` to confirm the commit was created.
