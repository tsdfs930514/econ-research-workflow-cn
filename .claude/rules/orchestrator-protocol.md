# Orchestrator Protocol: Contractor Mode

All non-trivial tasks follow the **Spec - Plan - Implement - Verify - Review - Fix - Score - Report** cycle, with a maximum of 5 rounds through the Plan–Score loop.

## "Just Do It" Mode

For trivial tasks (simple fixes, single-file changes, formatting corrections): if the initial score >= 80 and there are no Critical findings, skip the multi-round review loop. Apply fixes directly and verify once.

Criteria for "Just Do It" mode:
- Task affects <= 2 files
- No identification strategy or data safety implications
- First-round score >= 80 with zero Critical findings
- User has not explicitly requested full review

---

## Phase 0: Spec

Triggered for non-trivial tasks meeting **any** of these criteria:
- Affects >= 3 files
- Involves identification strategy changes
- Creates new skills, rules, or agents
- Modifies the orchestrator protocol itself

### Format

Produce a requirements spec with:

1. **MUST** requirements — non-negotiable deliverables and constraints
2. **SHOULD** requirements — expected but negotiable with justification
3. **MAY** requirements — optional enhancements if time/complexity permits
4. **Acceptance criteria** — concrete, verifiable conditions for completion
5. **Out of scope** — explicitly excluded items to prevent scope creep

### Rules

- The spec is written **once** per task. If the review loop (Phases 1–6) cycles back, it restarts at Phase 1, not Phase 0.
- Skipped if the task qualifies for "Just Do It" mode.
- The spec must not contradict `constitution.md`.
- Present the spec for user approval before proceeding to Phase 1.

**Exit criterion**: Spec approved by user or team lead.

---

## Phase 1: Plan

1. Understand the research question and identification strategy.
2. Identify required data sources, variables, and econometric methods.
3. Draft an analysis plan with specific Stata/Python commands to be used.
4. List all expected output files (datasets, tables, figures, logs).
5. Present the plan for approval before proceeding.

**Exit criterion**: Plan approved by user or team lead.

---

## Phase 2: Implement

1. Generate code files (`.do` for Stata, `.py` for Python).
2. Execute Stata via CLI (Git Bash):
   ```
   bash .claude/scripts/run-stata.sh "<project_dir>" "code/stata/script.do"
   ```
   Flag: 必须用 `-e`（自动退出），禁止用 `-b`（需手动确认）或 `/e`（Git Bash 路径冲突）
3. Parse the resulting `.log` file for errors and warnings.
4. Execute Python scripts:
   ```
   python "script.py"
   ```
5. Collect all outputs (tables, figures, datasets).

**Exit criterion**: Code runs without errors; all expected output files are generated.

---

## Phase 3: Verify

1. Check Stata `.log` files for errors, warnings, and unexpected messages.
2. Verify that all expected output files exist and are non-empty.
3. Cross-check Stata vs Python results: coefficient differences must be < 0.1%.
4. Validate table formatting against the standards in `econometrics-standards.md`.
5. Confirm that all required statistics (N, R-squared, clusters, dep var mean) are reported.

**Exit criterion**: All verification checks pass.

---

## Phase 4: Review

For non-trivial tasks, invoke `/adversarial-review` which enforces critic/fixer separation across up to 5 rounds. This launches domain-specific critic agents that cannot edit files, ensuring independent evaluation.

| Critic Agent             | Scope                                      |
|--------------------------|--------------------------------------------|
| code-critic              | Code conventions, safety, reproducibility  |
| econometrics-critic      | Identification, diagnostics, robustness    |
| tables-critic            | Table formatting, reporting, compliance    |

Legacy reviewer agents remain available for lighter-weight reviews:

| Reviewer               | Scope                                      |
|------------------------|--------------------------------------------|
| econometrics-reviewer  | Methods, identification, robustness        |
| code-reviewer          | Code quality, conventions, reproducibility |
| tables-reviewer        | Table formatting, labeling, completeness   |
| robustness-checker     | Missing robustness checks, sensitivity     |

Each critic/reviewer assigns a score from 0 to 100 and provides specific findings.

**Exit criterion**: All relevant reviews completed; scores and findings collected.

---

## Phase 5: Fix

For non-trivial tasks, `/adversarial-review` automatically launches the corresponding fixer agents (code-fixer, econometrics-fixer, tables-fixer) which:

1. Receive the critic's findings list.
2. Apply fixes in priority order (Critical → High → Medium → Low).
3. Re-run affected analyses.
4. Update output files (tables, figures, logs).
5. Document every change with rationale.

Fixers CANNOT score their own work — the critic re-evaluates after fixes.

**Exit criterion**: All findings addressed; outputs regenerated.

---

## Phase 6: Score

Calculate the final quality score as the average of all reviewer scores.

| Score Range | Action                                        |
|-------------|-----------------------------------------------|
| >= 95       | Publication ready. Proceed to next task.      |
| >= 90       | Minor fixes needed. One more round (Phase 5). |
| >= 80       | Significant issues. Re-enter Phase 2.         |
| < 80        | Major redo required. Re-enter Phase 1.        |

**Exit criterion**: Score >= 95, or maximum iterations reached.

---

## Phase 7: Report

After scoring (Phase 6), generate a synthesis report:

1. Run `/synthesis-report` to collect all outputs into `docs/ANALYSIS_SUMMARY.md`
2. Generate LaTeX version (`docs/ANALYSIS_SUMMARY.tex`) for compilation
3. Update REPLICATION.md with actual data, scripts, and output mapping
4. Log final score and status to MEMORY.md

**Exit criterion**: `ANALYSIS_SUMMARY.md` exists and is complete.

---

## Loop Control

- **Maximum iterations**: 5 rounds through the cycle.
- **Stagnation check**: If the score improves by less than 5 points between rounds, stop the loop and escalate to user with a summary of remaining issues and suggested manual interventions.
- **Version preservation**: Always preserve ALL intermediate versions of code and output. Never overwrite without saving the prior version.
- **Executable scoring**: After the final round, run `python scripts/quality_scorer.py <version_dir>` for an independent, automated quality score across 6 dimensions (100 pts total).

---

## Workflow Diagram

```
Spec --> Plan --> Implement --> Verify --> Review --> Fix --> Score --> Report
           ^                                                  |
           |                                                  |
           +--------------------------------------------------+
                         (if score < 95, loop)
```

Spec is executed once per task. The loop restarts at Plan (not Spec). After 5 iterations or upon reaching score >= 95, the cycle proceeds to Report (Phase 7) and the task is complete.
