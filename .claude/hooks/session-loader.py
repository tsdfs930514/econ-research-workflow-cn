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
        print("[会话加载器] 未找到 MEMORY.md。请使用 /session-log start 开始新会话。")
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
    print("会话上下文 (来自 MEMORY.md)")
    print("=" * 60)

    if recent_entries:
        print("\n--- 近期条目 ---")
        for entry in recent_entries:
            print(f"  {entry}")
    else:
        print("\n--- 暂无标记条目 ---")

    if last_session:
        print(f"\n--- 上次会话 ---")
        print(f"  日期: {last_session[0]}")
        print(f"  摘要: {last_session[1]}")
    else:
        print("\n--- 无历史会话记录 ---")

    if last_score:
        print(f"\n--- 最新质量评分: {last_score}/100 ---")

    print("=" * 60)


if __name__ == "__main__":
    main()
