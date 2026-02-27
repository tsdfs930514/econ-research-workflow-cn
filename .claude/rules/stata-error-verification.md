# Stata Error Verification Protocol

**Origin**: 2026-02-26, discovered during DDCG Phase 5 replication. Claude re-ran a failing script, overwrote the log, then grepped the new clean log and falsely claimed no errors existed. The `run-stata.sh` hook had correctly reported `r(111)` errors that were ignored.

---

## Mandatory Steps After Every Stata Execution

### Step 1: Read the hook output FIRST

After `run-stata.sh` completes, the **inline log check** at the end of the script prints either:
- `[Stata Log Check] Clean: no r(xxx) errors in <file>.log`
- `=== [Stata Log Check] ERRORS FOUND in <file>.log ===`

**You MUST read and report this output before doing anything else.** Do not grep the log independently — trust the hook output as the primary signal.

### Step 2: If errors are reported — STOP and acknowledge

If the hook reports errors:
1. **Say explicitly**: "The hook found N error(s) in `<file>.log`."
2. **Read the relevant portion of the log** to understand the error context.
3. **Diagnose the root cause** before making any changes.
4. **Fix the script** based on the diagnosis.
5. **Only then re-run.**

### Step 3: After re-run — verify the NEW hook output

After re-running, again read the hook output. Confirm it says "Clean" before declaring success.

---

## Prohibited Behaviors

1. **NEVER re-run a script without first acknowledging its errors.** Re-running overwrites the `.log` file, destroying evidence of the failure.

2. **NEVER grep a log file after re-running and claim the ORIGINAL run was clean.** The log was overwritten — you're reading the re-run's log, not the original.

3. **NEVER dismiss hook-reported errors.** If `run-stata.sh` says errors were found, they were found. The regex `r([0-9][0-9]*)` matches real Stata error codes.

4. **NEVER claim "clean" without showing the specific hook output line** that says "Clean: no r(xxx) errors."

---

## Verification Reporting Template

After every Stata run, report to the user in this format:

```
Script: <filename>.do
Hook output: [Clean / N error(s) found]
[If errors: brief description of each error]
[If re-run after fix: "Re-run hook output: Clean"]
```

---

## Why This Matters

The `run-stata.sh` wrapper exists specifically to catch errors automatically. Ignoring its output and doing independent (faulty) verification defeats the purpose of the hook system. The user must be able to trust that when Claude says "clean," it actually is clean.
