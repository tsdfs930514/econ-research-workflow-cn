# 路线图

## 第一阶段 — 核心质量基础设施

**状态**: 已实现

- 6 个新的对抗式代理（3 对评审者-修复者配对：代码、计量、表格）
- `/adversarial-review` 技能，编排多轮评审者-修复者循环
- 可执行 `quality_scorer.py`（6 个维度，100 分，自动检测方法）
- `/score`、`/commit`、`/compile-latex`、`/context-status` 技能
- MEMORY.md 激活，含标记条目和会话日志
- README.md，英文正文 + 中文快速入门
- 编排协议更新，含"直接执行"模式

---

## 第二阶段 — 基础设施（已实现）

**状态**: 已实现

### 钩子 (`settings.json`)

`.claude/settings.json` 中的 3 个生命周期钩子：

| 钩子 | 触发条件 | 动作 |
|------|---------|--------|
| 会话启动加载器 | `SessionStart` | 读取 MEMORY.md，显示近期条目、上次会话和最新质量评分 |
| 压缩前保存 | `PreCompact` | 提示 Claude 在上下文压缩前将会话摘要追加到 MEMORY.md |
| Stata 运行后日志检查 | `PostToolUse` (Bash) | Stata 执行后自动解析 `.log` 文件中的 `r(xxx)` 错误 |

钩子脚本：`.claude/hooks/session-loader.py`、`.claude/hooks/stata-log-check.py`

### 路径作用域规则

4 条通过 `paths:` frontmatter 限定作用域的规则；1 条始终加载（第三和第五阶段又各增加 1 条始终加载的规则）：

| 规则 | `paths:` 模式 |
|------|-----------------|
| `stata-conventions.md` | `**/*.do` |
| `python-conventions.md` | `**/*.py` |
| `econometrics-standards.md` | `**/code/**`、`**/output/**` |
| `replication-standards.md` | `**/REPLICATION.md`、`**/master.do`、`**/docs/**` |
| `orchestrator-protocol.md` | *（始终加载，无路径限制）* |

### 探索沙盒

- `/explore` 技能 — 创建 `explore/` 工作空间，放宽质量阈值（>= 60 vs 80）
- `/promote` 技能 — 将文件从 `explore/` 提升至 `vN/`，重新编号，运行 `/score` 验证

### 会话连续性

- `/session-log` 技能 — 显式的会话开始/结束，含 MEMORY.md 上下文加载和记录
- `personal-memory.md`（已 gitignore）— 机器特定偏好设置（Stata 路径、编辑器、目录）

---

## 第三阶段 — 打磨（已实现）

**状态**: 已实现

### 苏格拉底式研究工具

- `/interview-me` — 双语（中/英）苏格拉底式提问，将研究想法形式化
  - 引导流程：研究问题 → 假设 → 识别策略 → 数据需求 → 预期结果
  - 每次提一个问题；各部分可跳过
  - 输出结构化研究提案至 `vN/docs/research_proposal.md`

- `/devils-advocate` — 对识别策略进行系统性预分析挑战
  - 通用威胁（遗漏变量偏差、反向因果、测量误差、选择偏差、SUTVA）
  - 方法特定威胁（DID/IV/RDD/Panel/SDID）
  - 每个关键结果 3 个替代解释
  - 伪造检验建议
  - 威胁矩阵，含严重程度分级（严重/高/中/低，与 `econometrics-critic` 一致）

### 自扩展基础设施

- `/learn` — 在会话中创建新规则或技能
  - 引导式创建：类型 → 内容 → 验证 → 预览 → 写入
  - 自动生成格式正确的 .md 文件至 `.claude/rules/` 或 `.claude/skills/`
  - 基本准则守卫：不得创建违反 `constitution.md` 的规则/技能
  - 向 MEMORY.md 记录 `[LEARN]` 条目

### 治理

- **`constitution.md`** — 5 条不可变原则（始终加载的规则，无 `paths:` frontmatter）：
  1. 原始数据完整性（`data/raw/` 永不修改）
  2. 完全可复现性（每个结果可从代码 + 原始数据追溯）
  3. 强制交叉验证（Stata ↔ Python，< 0.1%；在 `explore/` 中放宽）
  4. 版本保留（`vN/` 永不删除）
  5. 评分完整性（评分如实记录）

- **规格优先协议** — 在编排协议中增加阶段 0：
  - 当任务影响 >= 3 个文件、涉及识别策略变更、创建技能/规则/代理或修改协议本身时触发
  - 格式：必须 / 应当 / 可以 需求 + 验收标准 + 超出范围
  - 每个任务编写一次；评审循环从阶段 1 重新开始

---

## 第四阶段 — 方法扩展与整合（已实现）

**状态**: 已实现

### 新方法技能

新增 4 个独立方法技能，覆盖复现压力测试中发现的空白：

| 技能 | 范围 |
|-------|-------|
| `/run-bootstrap` | 配对、野蛮聚类、残差和处理效应自助法推断流水线 |
| `/run-placebo` | 时间、结果、工具变量和置换安慰剂检验流水线 |
| `/run-logit-probit` | Logit/probit、倾向得分、处理效应（RA/IPW/AIPW）、条件 logit |
| `/run-lasso` | LASSO、双重选择后推断、严格 LASSO、R `glmnet` 匹配流水线 |

### 技能整合

- 将高级 Stata 模式（脉冲响应、Helmert、HHK、k 类、自助法、空间滞后）从 `run-panel.md`（665→371 行）和 `run-iv.md`（528→323 行）提取至非用户调用的参考文件 `advanced-stata-patterns.md`（443 行）
- 压缩所有 5 个 `run-*` 文件中的 Stata 执行块
- 净减少：2,175→2,083 行（-92 行）
- 合计：**28 个用户可调用技能 + 1 个参考指南**

### 复现包压力测试

分析 6 个复现包以验证和改进技能：

| 复现包 | 论文 | 更新的技能 |
|---------|-------|---------------|
| Acemoglu et al. (2019) — DDCG | JPE，民主与增长 | `/run-panel`、`/run-iv`、`/make-table` |
| 墨西哥零售进入 | 经济普查 | `/run-iv`、`/data-describe` |
| SEC 评论函 (mnsc.2021.4259) | Management Science | `/data-describe`、`/cross-check` |
| 债券市场流动性 (mnsc.2022.4646) | Management Science | `/cross-check`、`/run-panel` |
| 区域贸易协定与环境 (jvae023) | JEEA 2024 | `/run-lasso` |
| 文化与发展 (data_programs) | — | `/run-bootstrap` |

### APE 参考论文

3 个基于 R 的复现包存档于 `references/ape-winners/ape-papers/`：

| 复现包 | 设计 | 关键 R 包 |
|---------|--------|---------------|
| apep_0119（EERS 与电力） | 交错 DID | `did`、`fixest`、`HonestDiD`、`fwildclusterboot` |
| apep_0185（网络 MW 暴露） | Shift-share IV | `fixest`、暴露置换推断 |
| apep_0439（文化边界） | 空间 RDD + 面板 | `fixest`、`rdrobust`、置换推断 |

这些是 R 专用模式，作为 Stata 主导技能的补充。方法模式作为 `[LEARN]` 条目记录在 MEMORY.md 中。

---

## 第五阶段 — 真实数据复现测试与技能加固（已实现）

**状态**: 已实现 (2026-02-26)

### 端到端复现测试

所有 9 个 `/run-*` 技能均使用真实已发表复现包进行测试。11 个复现包 × 技能组合端到端通过 Stata 运行：

| # | 复现包 × 技能 | 状态 |
|---|----------------|--------|
| 1 | DDCG → `/run-panel`（FE + GMM） | 通过 |
| 2 | DDCG → `/run-iv`（2SLS，区域民主浪潮工具变量） | 通过 |
| 3 | 文化与发展 → `/run-bootstrap`（配对 + 野蛮聚类） | 通过 |
| 4 | jvae023 → `/run-lasso`（logistic LASSO 倾向得分 → 匹配） | 通过 |
| 5 | DDCG → `/run-placebo`（时间 + 置换） | 通过 |
| 6 | DDCG → `/run-logit-probit`（xtlogit、margins、teffects） | 通过 |
| 7 | SEC 评论函 → `/run-panel`（截面吸收 FE） | 通过 |
| 8 | 墨西哥零售 → `/run-iv`（ivreghdfe，大规模） | 通过 |
| 9 | jvae023 → `/run-did`（匹配面板上的 csdid） | 通过 |
| 10 | 合成数据 → `/run-rdd`（rdrobust、rddensity） | 通过 |
| 11 | DDCG → `/run-sdid`（SDID/DID/SC bootstrap VCE） | 通过 |

### 发现并修复的问题（共 19 个）

| 问题 | 类别 | 根本原因 | 更新的技能 |
|-------|----------|-----------|------------------|
| #11 | 诊断 | `estat bootstrap, bca` 需要显式 `saving(, bca)` | `/run-bootstrap` |
| #12 | 兼容性 | `boottest` 在非 reghdfe 估计量后失败 | `/run-bootstrap`、`/run-did` |
| #13 | 语法 | `bootstrap _b` 保存为 `_b_varname` 而非 `_bs_N` | `/run-bootstrap` |
| #14 | 诊断 | DWH `e(estatp)` 在 `xtivreg2 + partial()` 时不可用 | `/run-iv` |
| #15 | 边界情况 | `teffects` 命令在面板数据上失败（重复观测） | `/run-logit-probit` |
| #16 | 边界情况 | CV LASSO 在小样本中选择 0 个变量 | `/run-lasso` |
| #17 | 模板缺口 | LASSO 选择 0 个变量时无回退方案 | `/run-lasso` |
| #18 | 兼容性 | `lasso logit` r(430) 近分离导致收敛失败 | `/run-lasso` |
| #19 | 边界情况 | 字符串面板 ID 在 `xtset` 前需要 `encode` | `/run-did` |
| #20 | 兼容性 | `csdid_stats` 语法因包版本不同而变化 | `/run-did` |
| #21 | 语法 | 硬编码变量名 (`lgdp`) 而非使用用户参数 | `/run-sdid` |
| #22 | 模板缺口 | 显著的时间安慰剂 ≠ 混淆（预期效应） | `/run-placebo` |
| #23 | 兼容性 | 旧 Stata 语法（`set mem`、`clear matrix`）出现在复现包中 | `/run-panel` |
| #24 | 语法 | `ereturn post` + `estimates store` 在 `sdid` 后失败 | `/run-sdid` |
| #25 | 边界情况 | `vce(jackknife)` 要求每个处理期至少有 2 个处理单元 | `/run-sdid` |
| #26 | 流程 | 钩子报告的错误被忽略；验证前日志被覆盖 | 新规则：`stata-error-verification.md` |
| #27 | 模板缺口 | 8 阶滞后模型需要 `vareffects8` 程序（未实现） | `/run-panel` |
| #28 | 语法 | Stata 本地宏标签中的 `/` 导致解析失败 | `/run-panel` |
| #29 | 语法 | `levelsof` 对值标签变量返回数字代码；循环按字符串使用 | `/run-panel` |

### 新增防御性编程模式

在 `stata-conventions.md` 中编纂了 8 个防御性模式：

1. **社区包保护**：对所有 SSC 命令使用 `cap noisily` + `cap ssc install`
2. **字符串面板 ID 检查**：`confirm string variable` + 在 `xtset` 前 `encode`
3. **e 类可用性检查**：使用前测试标量（`e(estatp) != .`）
4. **SDID 本地宏**：对 `sdid` 使用本地宏而非 `estimates store`
5. **连续 vs 分类变量检查**：对连续变量使用 `summarize` 而非 `tab`
6. **负 Hausman 值处理**：检查 `r(chi2) < 0` 并正确解读
7. **旧 Stata 语法剥离**：改编旧代码时省略已弃用的 `set mem`、`clear matrix`
8. **Bootstrap 变量命名**：使用 `ds` 发现 `_b_varname` 模式

### 交叉验证结果

| 复现包 | 方法 | Stata vs Python 差异 |
|---------|--------|---------------------|
| DDCG 面板 FE | reghdfe vs pyfixest | 0.0000% — 通过 |
| DDCG IV 2SLS | ivreghdfe vs pyfixest | 0.0000% — 通过 |

### 回归验证

在所有技能更新后重新运行原始测试套件（test1-5）：**5/5 通过，零 r(xxx) 错误**。未引入回归问题。

### Stata 错误验证规则

新增 `stata-error-verification.md` 作为始终加载的规则（问题 #26）。强制要求 Claude 在重新运行脚本前必须读取钩子输出，防止 DDCG 复现中发现的日志覆盖导致的误判。

### 修改的文件

- 9 个技能文件：`run-did.md` 到 `run-sdid.md`（防御性模式 + 问题注记）
- `advanced-stata-patterns.md`（新增 SDID 本地宏模式）
- `stata-conventions.md`（新增全面的防御性编程章节）
- `stata-error-verification.md`（新的始终加载规则，用于错误验证协议）
- `ISSUES_LOG.md`（记录 19 个问题及根本原因和修复方案）
- `MEMORY.md`（会话日志和技能更新条目）

---

## 第六阶段 — 工作流完善：流水线编排、代理重连、综合报告（已实现）

**状态**: 已实现 (2026-02-27)

### 流水线编排

- `/run-pipeline` 技能 — 从研究计划文本、`research_proposal.md` 或论文 PDF 中自动检测计量方法，生成有序的技能执行计划，并端到端运行
  - 支持 `--quick`（跳过确认）和 `--replication <paper.pdf>`（从已发表论文提取方法）标志
  - 方法检测：DID、IV、RDD、Panel、SDID、Bootstrap、Placebo、Logit-Probit、LASSO
  - 多方法支持：主分析 + 稳健性替代方案
  - 错误处理：遇到 Stata `r(xxx)` 错误时暂停，提供修复/跳过/中止选项
  - 结束时自动运行 `/synthesis-report`

### 综合报告

- `/synthesis-report` 技能 — 汇集所有分析输出（日志、表格、图表、评分、交叉验证）生成结构化综合报告
  - 输出：`docs/ANALYSIS_SUMMARY.md`（Markdown）+ `docs/ANALYSIS_SUMMARY.tex`（LaTeX）
  - 10 节结构：摘要、数据与样本、主要结果、识别诊断、稳健性总结、交叉验证、质量评估、遗留问题、复现清单、文件清单
  - 更新 REPLICATION.md 的输出-表格映射

### 旧版代理重连

3 个旧版代理接入活跃技能：

| 代理 | 接入技能 | 角色 |
|-------|-----------|------|
| `paper-reviewer` | `/review-paper` | 通过 Task 工具执行 3 个审稿人角色 |
| `robustness-checker` | `/robustness` | 在生成 .do 文件前识别缺失的稳健性检验 |
| `cross-checker` | `/cross-check` | 独立诊断 Stata 与 Python 之间的差异 |

3 个旧版代理已弃用（被对抗式评审者-修复者配对取代）：

| 代理 | 被取代者 |
|-------|--------------|
| `code-reviewer` | `code-critic` |
| `econometrics-reviewer` | `econometrics-critic` |
| `tables-reviewer` | `tables-critic` |

### 编排协议更新

- 在阶段 6（评分）之后新增**阶段 7：报告**
- 工作流：规格 → 计划 → 实施 → 验证 → 评审 → 修复 → 评分 → 报告
- 退出条件：`ANALYSIS_SUMMARY.md` 存在且内容完整

### 评分持久化

- `/score` 现在生成 `docs/QUALITY_SCORE.md`，含完整的维度细分
- 使 `/synthesis-report` 可直接读取评分，无需重新运行评分器

### 变更的文件

- 2 个新技能：`synthesis-report.md`、`run-pipeline.md`
- 4 个修改的技能：`score.md`、`review-paper.md`、`robustness.md`、`cross-check.md`
- 3 个弃用的代理：`code-reviewer.md`、`econometrics-reviewer.md`、`tables-reviewer.md`
- 1 个修改的规则：`orchestrator-protocol.md`
- 4 个更新的文档：`README.md`、`CLAUDE.md`、`ROADMAP.md`、`WORKFLOW_QUICK_REF.md`

---

## 时间线

| 阶段 | 目标 | 依赖 |
|-------|--------|------------|
| 第一阶段 | 完成 | — |
| 第二阶段 | 完成 | 第一阶段稳定 |
| 第三阶段 | 完成 | 第二阶段钩子可靠运行 |
| 第四阶段 | 完成 | 第三阶段完成；复现包可用 |
| 第五阶段 | 完成 | 第四阶段完成；真实复现数据可用 |
| 第六阶段 | 完成 | 第五阶段完成；工作流结构稳定 |
