---
description: "Session start/end manager with MEMORY.md context loading and recording"
user_invocable: true
---

# /session-log — Session Continuity Manager

Manage session start/end with MEMORY.md integration for continuity across Claude Code sessions.

## Activation

When the user runs `/session-log`, check for a subcommand:

- `/session-log start` — Begin a session with context loading
- `/session-log end` — Close a session with summary recording

If no subcommand, prompt the user to choose.

---

## `/session-log start`

### Steps

1. **Read MEMORY.md** and display a context dashboard:

```
SESSION START
=============

Project: [from CLAUDE.md Project Identity]
Active Version: v1/

--- Recent Decisions ---
[Last 3 entries from Project Decisions Log]

--- Recent Issues ---
[Last 3 entries from Data Issues Encountered]

--- Last Session ---
Date: YYYY-MM-DD
Summary: [from Session Log table]

--- Current Quality Score ---
[Last known score, or "No score recorded yet"]

--- Pending Items ---
[Any unresolved items from Reviewer Feedback Tracker]
```

2. **Check personal-memory.md** (if it exists) and load machine-specific preferences.

3. **Note session start time** for the end-of-session summary.

4. **Remind the user** of available workflows:
```
Ready to work. Common next steps:
  /context-status  — Full project state overview
  /run-did         — Start DID analysis
  /explore         — Open exploration sandbox
  /adversarial-review — Run QA on existing work
```

---

## `/session-log end`

### Steps

1. **Prompt the user** to record key items from this session:

```
Session wrap-up. Please confirm or edit:

Key decisions made this session:
  [Auto-detected from conversation, or ask user]

Issues encountered:
  [Auto-detected, or ask user]

New learnings:
  [Auto-detected, or ask user]

Current quality score: [if /score was run]
```

2. **Append tagged entries** to MEMORY.md for each item:

```markdown
- [DECISION] YYYY-MM-DD: description
- [ISSUE] YYYY-MM-DD: description
- [LEARN] YYYY-MM-DD: description
```

Place entries in the appropriate sections (Project Decisions Log, Data Issues Encountered, etc.).

3. **Add session summary row** to the Session Log table:

```markdown
| YYYY-MM-DD | Brief summary of session activities, decisions, and outcomes |
```

4. **Confirm** the updates:

```
Session logged to MEMORY.md:
  - X decision(s) recorded
  - X issue(s) documented
  - X learning(s) added
  - Session summary appended

See you next session. Run /session-log start to reload context.
```

## Notes

- Never delete existing MEMORY.md entries — only append
- If MEMORY.md doesn't exist, create it from the template (see MEMORY.md structure in the repo)
- Tagged entries should be concise (1-2 sentences each)
- The session summary row should capture the overall session narrative in one sentence
