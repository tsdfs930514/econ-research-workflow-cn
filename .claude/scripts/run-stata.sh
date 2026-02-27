#!/bin/bash
# Wrapper for Stata execution — auto-approved by permissions.allow
# Usage: bash .claude/scripts/run-stata.sh <project_dir> <do_file>
#
# Example:
#   bash .claude/scripts/run-stata.sh \
#     "F:/Learning/econ-research-workflow/tests/test1-did/v1" \
#     "code/stata/01_did_analysis.do"

set -e

if [ $# -lt 2 ]; then
    echo "Usage: bash run-stata.sh <project_dir> <do_file>"
    exit 1
fi

PROJECT_DIR="$1"
DO_FILE="$2"

cd "$PROJECT_DIR"
"D:/Stata18/StataMP-64.exe" -e do "$DO_FILE"

# --- Inline log check (replaces PostToolUse hook for wrapper calls) ---
DO_BASENAME=$(basename "$DO_FILE" .do)
LOG_FILE="${DO_BASENAME}.log"

if [ ! -f "$LOG_FILE" ]; then
    # Check output/logs/ as fallback
    LOG_FILE="output/logs/${DO_BASENAME}.log"
fi

if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -c 'r([0-9][0-9]*)' "$LOG_FILE" 2>/dev/null || true)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "=== [Stata Log Check] ERRORS FOUND in $LOG_FILE ==="
        grep 'r([0-9][0-9]*)' "$LOG_FILE"
        echo "=== Total: $ERROR_COUNT error(s) ==="
    else
        echo "[Stata Log Check] Clean: no r(xxx) errors in $LOG_FILE"
    fi
else
    echo "[Stata Log Check] Warning: no .log file found for $DO_FILE"
fi
