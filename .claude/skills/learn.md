---
description: "Create new rules or skills from within a session (constitution-guarded)"
user_invocable: true
---

# /learn — Self-Extension

Create new rules or skills from within a session. Use this when you discover a convention, pattern, or workflow that should be codified for future sessions.

## Activation

When the user runs `/learn`, begin the guided creation process below.

---

## Step 1: Determine Type

Ask the user:
> What do you want to create — a **rule** (coding convention, standard, constraint) or a **skill** (slash-command workflow)?
> 你想创建什么 —— **rule**（编码规范/标准/约束）还是 **skill**（斜杠命令工作流）？

| Type | Purpose | Location | Loaded |
|------|---------|----------|--------|
| Rule | Standards, conventions, constraints | `.claude/rules/` | Automatically by path match or always-on |
| Skill | Slash-command workflows | `.claude/skills/` | On user invocation (`/name`) |

---

## Step 2: Gather Content

### For Rules

Ask the following (one at a time):

1. **Name**: What should this rule be called? (e.g., `latex-conventions`)
   - Must be lowercase-kebab-case, no spaces
   - File will be `.claude/rules/{name}.md`

2. **Scope**: Should it apply always, or only to specific file types/paths?
   - Always-on: no `paths:` frontmatter
   - Path-scoped: provide glob patterns (e.g., `**/*.tex`, `**/paper/**`)

3. **Content**: What are the standards, conventions, or constraints?
   - Ask for specific do's and don'ts
   - Ask for examples of correct and incorrect usage
   - Ask for any exceptions

### For Skills

Ask the following (one at a time):

1. **Name**: What should the slash command be? (e.g., `clean-data`)
   - Must be lowercase-kebab-case, no spaces
   - File will be `.claude/skills/{name}.md`

2. **Trigger description**: What does this skill do in one sentence?

3. **Steps**: Walk through the workflow steps:
   - What is the input (user provides what)?
   - What actions should be taken?
   - What output is produced?
   - Any conditional logic or branches?

---

## Step 3: Generate File

### Rule Template

```markdown
---
[paths: ["glob1", "glob2"]]  # omit entire line for always-on
---

# {Title}

{Description of what this rule enforces.}

## Standards

1. **{Standard name}**: {description}
2. **{Standard name}**: {description}
...

## Examples

### Correct
{example}

### Incorrect
{example}
```

### Skill Template

```markdown
---
user_invocable: true
---

# /{name} — {Title}

{One-line description.}

## Activation

When the user runs `/{name}`, perform the following:

## Steps

### 1. {Step name}

{Description of what to do.}

### 2. {Step name}

{Description of what to do.}

...

## Notes

- {Any caveats or edge cases.}
```

---

## Step 4: Validate

Before writing the file, check:

1. **YAML frontmatter**: Well-formed (skills have `user_invocable: true`; rules have valid `paths:` globs or no frontmatter)
2. **No duplicates**: No existing file in `.claude/rules/` or `.claude/skills/` with the same name
3. **Valid glob patterns**: If path-scoped, globs use correct syntax (`**/*.ext`, `**/dir/**`)
4. **Naming convention**: Lowercase-kebab-case filename
5. **Constitution compliance**: The new rule/skill does NOT violate any principle in `constitution.md`:
   - Does not permit modifying `data/raw/`
   - Does not bypass cross-validation requirements (outside `explore/`)
   - Does not allow deleting `vN/` directories
   - Does not permit score fabrication
   - Does not compromise reproducibility

If any validation fails, explain the issue and ask the user to correct it.

---

## Step 5: Preview and Confirm

Display the full generated file content and ask:

```
Preview of .claude/{rules|skills}/{name}.md:

---
{frontmatter}
---

{content}

---

Options:
  [yes]    — Write this file
  [edit]   — Let me make changes (describe what to change)
  [cancel] — Discard and exit
```

---

## Step 6: Write and Record

1. **Write the file** to the appropriate directory.

2. **Append a `[LEARN]` entry** to MEMORY.md:
   ```
   - [LEARN] YYYY-MM-DD: Created {rule|skill} `{name}` — {one-line description}
   ```

3. **Confirm** to the user:
   ```
   Created .claude/{rules|skills}/{name}.md

   Logged to MEMORY.md: [LEARN] {description}

   {For rules}: This rule is now active for {scope description}.
   {For skills}: Use /{name} to invoke this skill.
   ```

---

## Guards

- **Cannot modify `constitution.md`**: If the user attempts to create a rule that would override or weaken any constitutional principle, refuse and explain which principle would be violated.
- **Cannot overwrite existing files**: If a file with the same name already exists, ask the user to choose a different name or explicitly confirm overwrite.
- **Cannot create agents**: This skill creates rules and skills only. Agent creation requires manual setup.

## Notes

- Keep generated files concise — match the style of existing rules/skills in the repo.
- The user can run `/learn` multiple times in a session to create multiple items.
- Created items take effect immediately in the current session (rules are auto-loaded; skills are available via `/name`).
