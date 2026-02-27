#!/usr/bin/env python3
"""
Session-start hook: reads MEMORY.md, displays recent entries and session log.
Outputs summary to stdout for injection into Claude's context.
"""

import os
import re
import sys


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    memory_path = os.path.join(project_dir, "MEMORY.md")

    if not os.path.isfile(memory_path):
        print("[Session Loader] No MEMORY.md found. Start a new session with /session-log start.")
        return

    with open(memory_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract tagged entries (last 5)
    tagged_pattern = re.compile(
        r"\[(?:LEARN|DECISION|ISSUE|PREFERENCE)\]\s+\d{4}-\d{2}-\d{2}:.*"
    )
    tagged_entries = tagged_pattern.findall(content)
    recent_entries = tagged_entries[-5:] if len(tagged_entries) > 5 else tagged_entries

    # Extract session log entries (last row from the table)
    session_log_pattern = re.compile(
        r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|"
    )
    session_rows = session_log_pattern.findall(content)
    # Filter out header/separator rows
    session_rows = [
        (date, summary)
        for date, summary in session_rows
        if not summary.strip().startswith("---") and summary.strip() != "Session Summary"
    ]
    last_session = session_rows[-1] if session_rows else None

    # Extract last quality score mention
    score_pattern = re.compile(r"(?:score|Score)[:\s]*(\d{1,3})\s*/?\s*100", re.IGNORECASE)
    score_matches = score_pattern.findall(content)
    last_score = score_matches[-1] if score_matches else None

    # Build output
    print("=" * 60)
    print("SESSION CONTEXT (from MEMORY.md)")
    print("=" * 60)

    if recent_entries:
        print("\n--- Recent Entries ---")
        for entry in recent_entries:
            print(f"  {entry}")
    else:
        print("\n--- No tagged entries yet ---")

    if last_session:
        print(f"\n--- Last Session ---")
        print(f"  Date: {last_session[0]}")
        print(f"  Summary: {last_session[1]}")
    else:
        print("\n--- No previous session log ---")

    if last_score:
        print(f"\n--- Last Quality Score: {last_score}/100 ---")

    print("=" * 60)


if __name__ == "__main__":
    main()
