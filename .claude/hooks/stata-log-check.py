#!/usr/bin/env python3
"""
PostToolUse hook: checks Stata .log files for r(xxx) errors after Stata execution.
Reads tool invocation JSON from stdin. Only activates when the command contains
StataMP or runs a .do file. Informational only (exit 0 always).
"""

import glob
import json
import os
import re
import sys


def main():
    # Read stdin JSON
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # Not valid JSON, skip silently

    # Extract the command that was run
    command = ""
    if isinstance(data, dict):
        tool_input = data.get("tool_input", {})
        if isinstance(tool_input, dict):
            command = tool_input.get("command", "")
        elif isinstance(tool_input, str):
            command = tool_input

    # Only activate for Stata commands
    if "StataMP" not in command and ".do" not in command and "run-stata" not in command:
        return

    # Find the most recent .log file in the current working directory
    log_files = glob.glob("*.log")
    if not log_files:
        # Also check output/logs/
        log_files = glob.glob("output/logs/*.log")

    if not log_files:
        print("[Stata Log Check] No .log files found in CWD or output/logs/.")
        return

    # Sort by modification time, most recent first
    log_files.sort(key=os.path.getmtime, reverse=True)
    latest_log = log_files[0]

    # Read and scan for errors
    try:
        with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
            log_content = f.read()
    except OSError as e:
        print(f"[Stata Log Check] Could not read {latest_log}: {e}")
        return

    # Find r(xxx) error patterns
    error_pattern = re.compile(r"r\((\d+)\)")
    errors_found = error_pattern.findall(log_content)

    if errors_found:
        unique_errors = sorted(set(errors_found))
        print(f"[Stata Log Check] WARNING: Errors found in {latest_log}:")
        for err_code in unique_errors:
            # Count occurrences
            count = errors_found.count(err_code)
            print(f"  r({err_code}) - {count} occurrence(s)")
        print(f"  Total: {len(errors_found)} error(s) across {len(unique_errors)} unique code(s).")
        print(f"  Review the log file: {latest_log}")
    else:
        print(f"[Stata Log Check] Clean: no r(xxx) errors in {latest_log}")


if __name__ == "__main__":
    main()
