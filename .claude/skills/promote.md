---
description: "Graduate exploratory files to main pipeline with quality check"
user_invocable: true
---

# /promote — Promote Exploratory Results to Main Pipeline

Graduate files from the `explore/` sandbox to the main `vN/` pipeline, applying full quality standards.

## Activation

When the user runs `/promote`, they should specify:
- **Source**: file(s) in `explore/` to promote (e.g., `explore/code/alt_spec.do`)
- **Target**: destination in the version directory (e.g., `v1/code/stata/`)

If arguments are not provided, prompt the user for source and target.

## Steps

### 1. Identify Source Files

List files in `explore/` and ask the user which to promote if not specified:

```
Files in explore/:
  explore/code/alt_spec_EXPLORATORY.do
  explore/code/new_outcome_EXPLORATORY.py
  explore/output/alt_results.tex

Which file(s) to promote? (specify paths or "all")
```

### 2. Copy and Rename

For each source file:

1. Copy from `explore/` to the target `vN/` location
2. Remove `_EXPLORATORY` suffix from the filename if present
3. Renumber to fit the `vN/code/` sequence:
   - Check existing numbered scripts (e.g., `01_`, `02_`, ..., `06_`)
   - Assign the next available number
   - Example: `alt_spec_EXPLORATORY.do` → `07_alt_spec.do`

### 3. Upgrade to Full Standards

After copying, apply full pipeline standards to the promoted file:

- Add full header block (if abbreviated)
- Add proper logging (`cap log close` / `log using` / `log close`)
- Add variable labels if missing
- Ensure `set seed 12345` is present
- Add `vce(cluster ...)` to regressions if missing

### 4. Quality Check

Run `/score` on the promoted files to verify they meet main pipeline standards:

- If score >= 80: promotion successful, inform user
- If score < 80: warn the user and list specific issues that need fixing

```
Promotion complete:
  explore/code/alt_spec_EXPLORATORY.do → v1/code/stata/07_alt_spec.do
  Quality score: 85/100 ✓

  OR

  Quality score: 72/100 ✗
  Issues:
    - Missing cross-validation script
    - No variable labels on generated variables
  Run /adversarial-review on v1/code/stata/07_alt_spec.do to address.
```

### 5. Clean Up (Optional)

Ask the user if they want to remove the source files from `explore/`:

```
Remove promoted files from explore/? (y/n)
```

## Notes

- Never overwrite existing files in `vN/` without confirmation
- Preserve the original exploratory file in `explore/` until the user confirms deletion
- If promoting Python cross-validation scripts, place them in `vN/code/python/`
- Update `master.do` if a new Stata script is added to the sequence
