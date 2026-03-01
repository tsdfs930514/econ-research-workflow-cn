#!/usr/bin/env python3
"""
raw-data-guard.py — PostToolUse hook: detect unauthorized modifications to data/raw/.
Catches bypass via Python/R scripts that Claude might execute through Bash.

Defence layer 2 (deny rules = layer 1, filesystem attrib +R = layer 3).

Workflow:
  1. First run  → save baseline snapshot (file list + sizes + mtimes)
  2. Later runs → compare current state against baseline
  3. If any file modified/deleted → print loud warning, exit 1
  4. New files are allowed (snapshot updates to include them)
"""
import os
import sys
import json
from pathlib import Path


def snapshot_raw(raw_dirs, project):
    """Build {relative_path: {size, mtime_ns}} for every file under data/raw."""
    snap = {}
    for d in raw_dirs:
        for f in d.rglob("*"):
            if f.is_file():
                key = str(f.relative_to(project))
                s = f.stat()
                snap[key] = {"size": s.st_size, "mtime_ns": int(s.st_mtime_ns)}
    return snap


def main():
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    raw_dirs = sorted(project.glob("**/data/raw"))
    if not raw_dirs:
        return  # no data/raw directory — nothing to guard

    cache = project / ".claude" / ".raw-data-snapshot.json"

    # --- load baseline ---
    baseline = {}
    if cache.exists():
        try:
            baseline = json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            baseline = {}

    current = snapshot_raw(raw_dirs, project)

    # --- first run: save baseline silently ---
    if not baseline:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(current, indent=2), encoding="utf-8")
        return

    # --- compare ---
    modified = []
    deleted = []
    for path, info in baseline.items():
        if path not in current:
            deleted.append(path)
        elif current[path] != info:
            modified.append(path)

    if modified or deleted:
        print("=" * 60)
        print("=== [RAW DATA GUARD] CONSTITUTION VIOLATION ===")
        print("=" * 60)
        print("Principle 1: data/raw/ is READ-ONLY.")
        print()
        for p in deleted:
            print(f"  DELETED:  {p}")
        for p in modified:
            print(f"  MODIFIED: {p}")
        print()
        print("ACTION: STOP immediately. Restore from git/backup.")
        print("=" * 60)
        # Do NOT update snapshot — keep alerting until manually resolved
        sys.exit(1)

    # --- no violations: update snapshot (absorbs legitimately added new files) ---
    cache.write_text(json.dumps(current, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
