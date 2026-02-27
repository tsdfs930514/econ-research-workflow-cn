# Constitution — Immutable Principles

These five principles govern all skills, agents, and rules in this workflow. They cannot be overridden, relaxed, or contradicted by any other configuration. The `/learn` skill cannot create rules that violate them.

---

## 1. Raw Data Integrity

`data/raw/` is **never** modified, overwritten, or deleted. All transformations read from `data/raw/` and write to `data/clean/` or `data/temp/`. No exception exists for any skill, agent, or manual instruction.

## 2. Full Reproducibility

Every result (table, figure, statistic) must be reproducible from code + raw data by running `master.do` (or the equivalent entry-point script). If a result cannot be traced to a code path from raw data, it is invalid.

## 3. Mandatory Cross-Validation

All regressions are cross-validated between Stata and Python (`pyfixest`). Coefficient differences must be < 0.1%. This requirement is **relaxed only inside `explore/`**, where cross-validation is optional.

## 4. Version Preservation

`vN/` directories are **never** deleted, only superseded by `vN+1/`. Intermediate outputs within a version are preserved — overwriting prior results without saving the previous version is prohibited.

## 5. Score Integrity

Quality scores (from `/score`, `/adversarial-review`, or manual review) are recorded faithfully. Scores are never fabricated, inflated, or omitted to make results appear better than they are.

---

**Enforcement**: Every skill, agent, and rule operates within this envelope. Violations should be flagged immediately and the offending action halted.
