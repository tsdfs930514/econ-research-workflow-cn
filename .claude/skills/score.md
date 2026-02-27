---
description: "Run the executable quality scorer on the current version directory"
user_invocable: true
---

# /score — Quality Scoring

When the user invokes `/score`, run the `quality_scorer.py` script on the current version directory and present the results.

## Step 1: Determine Target

- Default: the current version directory (read from CLAUDE.md, typically `v1/`)
- User can specify: `/score v2/` or `/score path/to/directory`

## Step 2: Run the Scorer

Execute:

```bash
python scripts/quality_scorer.py <target_dir> --verbose
```

If the script is not found at the project root, try:

```bash
python "F:/Learning/econ-research-workflow/scripts/quality_scorer.py" <target_dir> --verbose
```

## Step 3: Display Results

Present the output in a readable format:

```
Quality Score Report for v1/
═══════════════════════════════════════════

  Code Conventions     12/15  ████████████░░░
  Log Cleanliness      15/15  ███████████████
  Output Completeness  10/15  ██████████░░░░░
  Cross-Validation      0/15  ░░░░░░░░░░░░░░░
  Documentation        12/15  ████████████░░░
  Method Diagnostics   20/25  ████████████████████░░░░░

  TOTAL                69/100

  Status: MAJOR REVISIONS NEEDED (< 80)
```

## Step 4: Recommendations

Based on the total score:

| Score | Status | Recommendation |
|-------|--------|----------------|
| >= 95 | Publication Ready | No further action needed |
| >= 90 | Minor Revisions | Fix the specific items flagged, then re-score |
| >= 80 | Major Revisions | Run `/adversarial-review` on failing domains |
| < 80 | Redo | Generate a prioritized fix list (Critical items first) |

### If score < 80:

Generate a prioritized fix list from the scorer output:
1. List all failing checks grouped by dimension
2. Mark which can be fixed automatically (missing headers, logging) vs manually (missing cross-validation script)
3. Suggest running `/adversarial-review` for domains scoring below 12/15

### If specific dimensions score 0:

- **Cross-Validation = 0**: Suggest running `/cross-check` to create the Python validation script
- **Method Diagnostics = 0**: Suggest running the relevant `/run-*` skill to add diagnostics
- **Documentation = 0**: Suggest creating REPLICATION.md and _VERSION_INFO.md

## Step 5: Persist Score to docs/QUALITY_SCORE.md

Generate (or overwrite) `docs/QUALITY_SCORE.md` with the full score breakdown so that `/synthesis-report` and other skills can read it directly:

```markdown
# Quality Score — vN/
Generated: YYYY-MM-DD HH:MM

| Dimension | Score | Max | Details |
|-----------|-------|-----|---------|
| Code Conventions | XX | 15 | [specific checks passed/failed] |
| Log Cleanliness | XX | 15 | [specific checks passed/failed] |
| Output Completeness | XX | 15 | [specific checks passed/failed] |
| Cross-Validation | XX | 15 | [specific checks passed/failed] |
| Documentation | XX | 15 | [specific checks passed/failed] |
| Method Diagnostics | XX | 25 | [specific checks passed/failed] |
| **TOTAL** | **XX** | **100** | |

Status: [Publication Ready / Minor Revisions / Major Revisions / Redo]
```

Ensure the `docs/` directory exists before writing (create it if needed).

## Step 6: Record Score to MEMORY.md

If MEMORY.md exists, append a line:

```
[LEARN] YYYY-MM-DD: Quality score for <target>: XX/100 (Code: XX/15, Logs: XX/15, Output: XX/15, CrossVal: XX/15, Docs: XX/15, Diagnostics: XX/25)
```
