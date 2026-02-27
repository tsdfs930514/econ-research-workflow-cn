---
description: "显示当前项目上下文：版本、近期决策、质量评分、Git 状态"
user_invocable: true
---

# /context-status — 项目上下文仪表盘

当用户调用 `/context-status` 时，收集并显示当前项目状态的全面快照。适合在会话开始或恢复工作时使用。

## 需要收集的信息

### 1. 当前版本
- 读取 `CLAUDE.md` 获取当前活跃版本（如 `v1`）
- 读取活跃版本目录中的 `_VERSION_INFO.md` 获取版本元数据

### 2. 近期决策（来自 MEMORY.md）
- 读取 `MEMORY.md`
- 显示最近 5 条标记条目（任何标记：LEARN、DECISION、ISSUE、PREFERENCE）
- 显示最近一条会话日志

### 3. 最新质量评分
- 检查 `quality_scorer.py` 是否最近运行过（查找 MEMORY.md 中的评分条目）
- 如果可用，显示最新评分明细

### 4. 输出文件状态
- 检查 `output/tables/` — 列出 .tex 文件及大小
- 检查 `output/figures/` — 列出 .pdf/.png 文件及大小
- 检查 `output/logs/` — 列出 .log 文件，标记包含 `r(` 错误的文件
- 报告任何预期但缺失或为空的文件

### 5. Git 状态
- `git branch` — 当前分支名
- `git status --short` — 是否有未提交的修改、未追踪的文件
- `git log --oneline -3` — 最近 3 次提交

### 6. 数据状态
- 检查 `data/raw/` — 列出文件（确认数据已到位）
- 检查 `data/clean/` — 列出已处理的数据集
- 如果 `data/raw/` 为空则发出提示（数据尚未放置）

## 显示格式

```
项目上下文仪表盘
═══════════════════════════════════════════

版本：  v1（创建于 2026-02-25）
项目：  [项目名称]
分支：  main（干净）

近期活动：
  [ISSUE] 2026-02-25: boottest 与含多维 FE 的 reghdfe 不兼容
  [DECISION] 2026-02-25: 选择 CS-DiD 作为主要估计量（而非 TWFE）
  [LEARN] 2026-02-25: v1/ 的质量评分：82/100

上次会话：2026-02-25 — 完成了 DID 分析，修复了 boottest 问题

质量评分：82/100（最后运行于 2026-02-25）
  代码：12/15 | 日志：15/15 | 输出：10/15
  交叉验证：0/15 | 文档：12/15 | 诊断检验：20/25

输出文件：
  tables/  3 个文件（tab_did_main.tex, tab_did_comparison.tex, tab_summary.tex）
  figures/ 4 个文件（fig_event_study_*.pdf, fig_bacon_decomp.pdf）
  logs/    5 个文件（2 个有错误标记）

数据：
  raw/    2 个文件（panel_data.dta, crosswalk.csv）
  clean/  1 个文件（panel_cleaned.dta）

Git：
  abc1234 [v1] code: add event study with CS-DiD
  def5678 [v1] output: regenerate DID tables
  ghi9012 [v1] data: initial data cleaning pipeline

建议的下一步：
  - 交叉验证评分为 0/15 → 运行 /cross-check
  - 2 个日志文件有错误 → 使用 /adversarial-review code 审查
  - 总分 82 → 修复后运行 /score
```

## 错误处理

- 如果 MEMORY.md 不存在：提示"未找到 memory 文件。请运行 /init-project 或创建 MEMORY.md。"
- 如果没有版本目录：提示"未找到版本目录。请运行 /init-project 开始。"
- 如果未初始化 git：跳过 git 部分，提示"不是 git 仓库。"
- 如果 quality_scorer.py 未运行过：提示"未记录质量评分。请运行 /score。"
