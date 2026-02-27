---
description: "智能 Git 提交，带类型前缀、数据安全警告和自动生成消息"
user_invocable: true
---

# /commit — 智能 Git 提交

当用户调用 `/commit` 时，按以下步骤操作：

## 步骤 1：检查状态

运行 `git status` 查看所有变更（已暂存和未暂存）。

## 步骤 2：安全检查

如果以下文件被暂存，**发出警告并阻止**：
- `data/raw/` 中的文件——原始数据不应被提交（文件过大或有限制）
- `.env` 文件或包含凭据的文件
- `.dta`、`.csv` 或其他大型数据文件（除非在 `tests/` 目录中）
- Stata `.log` 文件（通常在 gitignore 中）

如果发现上述文件，显示警告并在继续之前请求用户确认。

## 步骤 3：确定提交类型

根据变更的文件自动检测提交类型：

| 类型 | 触发条件（变更的文件） |
|------|----------------------|
| `data` | `data/clean/`、`data/temp/` 中的文件，数据处理脚本 |
| `code` | `code/` 中的 `.do` 文件、`.py` 文件 |
| `output` | `output/tables/`、`output/figures/` 中的文件 |
| `paper` | `paper/` 中的 `.tex` 文件 |
| `docs` | `.md` 文件、`REPLICATION.md`、`_VERSION_INFO.md` |
| `fix` | 修复错误的变更（从提交上下文中检测） |
| `refactor` | 代码重构，无逻辑变更 |

如果适用多种类型，使用主要类型（变更文件最多的类型）。

## 步骤 4：检测版本

读取 CLAUDE.md 或 _VERSION_INFO.md 以确定当前版本（如 `v1`）。

## 步骤 5：生成提交消息

格式：`[vN] type: description`

示例：
- `[v1] code: add DID event study with Callaway-Sant'Anna estimator`
- `[v1] output: regenerate main regression tables with clustered SEs`
- `[v1] fix: correct first-stage F-statistic reporting in IV table`
- `[v1] docs: update REPLICATION.md with data sources`

## 步骤 6：展示确认

显示拟议的提交：

```
拟议提交：
  消息：[v1] code: add DID event study with Callaway-Sant'Anna estimator
  文件：
    M  v1/code/stata/03_did_analysis.do
    A  v1/code/stata/04_event_study.do
    M  v1/output/logs/did_analysis.log

是否继续？(yes/edit/cancel)
```

- **yes**：执行提交
- **edit**：允许用户修改消息
- **cancel**：中止

## 步骤 7：提交

```bash
git add <specific files>
git commit -m "[vN] type: description"
```

按名称暂存特定文件——不要使用 `git add -A` 或 `git add .`。

## 步骤 8：确认

显示 `git log --oneline -1` 确认提交已创建。
