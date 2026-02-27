---
description: "Set up exploration sandbox with relaxed quality thresholds"
user_invocable: true
---

# /explore — Exploration Sandbox

Set up and work within an exploratory analysis workspace with relaxed quality thresholds. Intended for quick hypothesis testing, alternative specifications, and data exploration.

## Activation

When the user runs `/explore`, perform the following:

## Steps

### 1. Set Up Sandbox Directory

Create the `explore/` directory at the project root if it doesn't exist:

```
explore/
  code/          # Exploratory .do and .py files
  output/        # Tables, figures, logs from exploratory runs
  data/          # Temporary exploratory datasets
```

```bash
mkdir -p explore/code explore/output explore/data
```

### 2. Relaxed Quality Thresholds

Within the `explore/` workspace, apply relaxed quality standards:

| Criterion | Main Pipeline | Exploration |
|-----------|--------------|-------------|
| Quality score threshold | >= 80 | >= 60 |
| Cross-validation required | Yes | No |
| Full adversarial review | Yes | No |
| Variable labels required | Yes | No |
| Full header block | Yes | Abbreviated OK |

### 3. File Naming

All exploratory files should be clearly marked:
- Store everything under `explore/` (preferred), OR
- Append `_EXPLORATORY` suffix to filenames if stored elsewhere (e.g., `03_alt_spec_EXPLORATORY.do`)

### 4. Workflow

1. Scaffold the `explore/` directory
2. Inform the user that exploratory mode is active with relaxed thresholds
3. Generate code in `explore/code/` — skip full headers, use abbreviated logging
4. Run analyses and store output in `explore/output/`
5. Do NOT automatically trigger `/adversarial-review` on exploratory work
6. If the user wants to promote results to the main pipeline, use `/promote`

### 5. Display Status

After setup, display:

```
Exploration sandbox active.
  Directory: explore/
  Quality threshold: >= 60 (relaxed from 80)
  Cross-validation: optional
  Adversarial review: not automatic

Use /promote to graduate files to the main pipeline.
```

## Notes

- Exploratory results are NOT publication-ready — they must pass `/promote` and `/score` before inclusion in the main analysis.
- The `explore/` directory should be added to `.gitignore` if the user wants to keep it out of version control.
- This skill does not modify any files in `vN/` directories.
