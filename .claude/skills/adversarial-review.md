---
description: "Run adversarial critic-fixer quality assurance loop across code, econometrics, and tables domains"
user_invocable: true
---

# /adversarial-review — Adversarial Quality Assurance Loop

When the user invokes `/adversarial-review`, orchestrate a multi-round critic → fixer → re-critic cycle that enforces separation of concerns: critics identify issues but cannot fix them; fixers apply corrections but cannot score their own work.

## Step 1: Gather Inputs

Ask the user:

1. **Target**: Directory or specific files to review (default: current version directory, e.g., `v1/`)
2. **Domains**: Which domains to review? Options:
   - `all` (default) — code + econometrics + tables
   - `code` — code conventions, safety, reproducibility only
   - `econometrics` — identification, diagnostics, robustness only
   - `tables` — table formatting and reporting only
   - Any combination (e.g., `code,tables`)
3. **Score threshold**: Minimum acceptable score (default: 95)
4. **Max rounds**: Maximum critic-fixer iterations (default: 5)

## Step 2: Launch Critics

For each selected domain, launch the corresponding critic agent **in parallel** using the Task tool:

| Domain | Agent | Subagent Type |
|--------|-------|---------------|
| Code | `code-critic` | Read-only agent |
| Econometrics | `econometrics-critic` | Read-only agent |
| Tables | `tables-critic` | Read-only agent |

Each critic:
- Reviews all relevant files in the target directory
- Produces a structured findings list with severity levels
- Assigns a score (0-100)

Collect all critic reports.

## Step 3: Evaluate Scores

Display the scores to the user:

```
Round 1 Results:
  Code:          82/100 (3 Critical, 5 High, 2 Medium)
  Econometrics:  75/100 (1 Critical, 4 High, 6 Medium)
  Tables:        90/100 (0 Critical, 2 High, 3 Medium)
```

**Decision logic**:
- If ALL scores >= threshold (default 95): **Done.** Report final scores and exit.
- If any score < threshold: proceed to Step 4.

## Step 4: Launch Fixers

For each domain scoring below threshold, launch the corresponding fixer agent:

| Domain | Agent | Input |
|--------|-------|-------|
| Code | `code-fixer` | code-critic findings |
| Econometrics | `econometrics-fixer` | econometrics-critic findings |
| Tables | `tables-fixer` | tables-critic findings |

Each fixer:
- Receives the critic's findings list
- Applies fixes in priority order (Critical → High → Medium → Low)
- Documents every change with rationale
- Reports what was changed

## Step 5: Re-Launch Critics

After fixers complete, re-launch the same critics on the updated files to produce new scores.

## Step 6: Loop Control

Check termination conditions:

1. **Success**: All scores >= threshold → report final scores, exit
2. **Max rounds**: Round count >= max_rounds → report current scores, list remaining issues, exit
3. **Stagnation**: Score improved < 5 points since last round → report stagnation, list remaining issues, ask user for guidance

If none met, return to Step 4.

## Step 7: Final Report

```markdown
# Adversarial Review Report

## Final Scores (Round N)

| Domain | Score | Status |
|--------|-------|--------|
| Code | XX/100 | PASS/FAIL |
| Econometrics | XX/100 | PASS/FAIL |
| Tables | XX/100 | PASS/FAIL |

## Score History

| Round | Code | Econometrics | Tables |
|-------|------|--------------|--------|
| 1 | XX | XX | XX |
| 2 | XX | XX | XX |
| ... | ... | ... | ... |

## Remaining Issues (if any)
- [List of unfixed findings with severity]

## Recommendation
- [Publication ready / Minor revisions needed / Major revisions needed]
```

## Notes

- Critics CANNOT edit files — they can only read and report
- Fixers CANNOT score their own work — only critics can evaluate
- This separation prevents self-approval loops
- If the quality scorer script is available, run it after the final round for an independent score
- For trivial tasks (score >= 80 on first round with no Critical findings), suggest using "Just Do It" mode from the orchestrator protocol
