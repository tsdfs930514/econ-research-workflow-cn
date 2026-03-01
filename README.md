# 经济学研究工作流 (Econ Research Workflow)

一个基于 Claude Code 的可复现经济学研究模板，集成了自动化 Stata/Python 分析管道、对抗式质量审查和交叉验证基础设施。

灵感来源：[pedrohcgs/claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow)

> 本仓库为 [econ-research-workflow](https://github.com/Weiyu-USTC/econ-research-workflow) 的中文版。所有技能提示词、代理描述、规则和文档均已中文化。斜杠命令名称保持英文不变（如 `/run-did`），以确保与 Claude Code 的兼容性。

---

## 功能特点

- **34 个技能** — 斜杠命令工作流，覆盖完整研究生命周期：数据清洗、DID/IV/RDD/面板/SDID/Bootstrap/安慰剂/Logit-Probit/LASSO 估计、交叉验证、表格生成、论文撰写、翻译、润色、去AI化重写、逻辑检查、审稿模拟、管道编排、综合报告、探索沙盒、会话连续性、苏格拉底式研究工具和自我扩展
- **12 个代理** — 专业审查者 + 3 对对抗式评审者-修复者（代码、计量、表格），强制关注点分离
- **7 条规则** — 4 条路径限定的编码/计量规范 + 3 条常驻规则（基本准则、编排协议、Stata 错误验证）
- **3 个生命周期钩子** — 自动加载会话上下文、压缩前记忆保存、Stata 运行后错误检测
- **对抗式质量审查循环** — `/adversarial-review` 运行评审者 → 修复者 → 再评审循环（最多 5 轮），直到质量评分 ≥ 95
- **可执行质量评分器** — `quality_scorer.py` 在 6 个维度上评分（满分 100），自动从 .do 文件检测计量方法
- **探索沙盒** — `/explore` 提供宽松阈值的假设检验环境；`/promote` 将结果提升至正式管道
- **Stata + Python/R 交叉验证** — 每个回归均通过 `pyfixest` 和 R `fixest` 跨语言验证
- **多格式输出** — 支持中文期刊（经济研究/管理世界）、英文 TOP5（AER/QJE）、NBER 工作论文和 SSRN 预印本格式
- **版本化分析** — `v1/`、`v2/`、... 目录结构，包含完整复现包
- **会话连续性** — `/session-log` 提供显式会话管理，与 MEMORY.md 集成

---

## 工作原理

本仓库是一个**项目级模板**。`.claude/` 目录包含所有技能、代理和规则——当你在项目目录中运行 `claude` 时，Claude Code 会自动加载它们。无需全局安装任何东西。

两种使用方式：

- **作为完整项目模板** — Fork 本仓库，以完整工作流启动一个新研究项目
- **按需选用单个技能** — 将特定的 `.claude/skills/*.md` 文件复制到你自己项目的 `.claude/skills/` 目录中

## 快速上手

### 1. Fork 并克隆

```bash
# 在 GitHub 上 Fork 本仓库，然后：
git clone https://github.com/<你的用户名>/econ-research-workflow-cn.git
cd econ-research-workflow-cn
```

### 2. 安装前置依赖

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| **Stata** | 18（推荐 MP 版） | 所有计量经济学估计 |
| **Python** | 3.10+ | 交叉验证（`pyfixest`、`pandas`、`numpy`） |
| **Claude Code** | 最新版 | CLI 工具——从 [claude.com/claude-code](https://claude.com/claude-code) 安装 |
| **Git Bash** (Windows) | — | Stata 执行的 Shell 环境 |
| **LaTeX** | 可选 | `/compile-latex` 编译论文（pdflatex + bibtex） |

```bash
pip install pyfixest pandas numpy polars matplotlib stargazer
```

### 3. 配置

打开 `CLAUDE.md`，填写 `[PLACEHOLDER]` 字段：
- `[PROJECT_NAME]` — 你的研究项目名称
- `[INSTITUTION_NAME]` — 你的机构名称
- `[RESEARCHER_NAMES]` — 研究者姓名
- `[DATE]` — 创建日期
- 修改 Stata 可执行文件路径为你的本地路径

### 4. 启动 Claude Code 并开始工作

```bash
# 在项目目录中启动 Claude Code
claude

# 初始化新研究项目（创建 v1/ 目录结构）
/init-project
```

将原始数据放入 `v1/data/raw/`，然后运行分析：

```bash
/data-describe → /run-did（或 /run-iv、/run-rdd、/run-panel）
    → /cross-check → /make-table → /adversarial-review → /score
```

### 完整论文管道

```
/init-project → /data-describe → /run-did → /cross-check → /robustness
    → /make-table → /write-section → /review-paper → /adversarial-review
    → /score → /synthesis-report → /compile-latex → /commit
```

### 一键自动化管道

```bash
# 自动检测计量方法并执行完整技能序列
/run-pipeline
```

### 研究构思流程

```
/interview-me → /devils-advocate → /data-describe → /run-{method}
```

---

## 技能参考

| 技能 | 描述 |
|------|------|
| `/init-project` | 初始化标准化目录结构，生成 master.do、REPLICATION.md 和模板文件 |
| `/data-describe` | 生成描述性统计和变量分布（Stata + Python 双语言） |
| `/run-did` | 完整 DID/TWFE/Callaway-Sant'Anna 分析管道，含平行趋势检验和事件研究图 |
| `/run-iv` | 完整 IV/2SLS 分析管道，含第一阶段诊断、弱工具变量检验和 LIML 对比 |
| `/run-rdd` | 完整 RDD 分析管道，含带宽敏感性、密度检验和安慰剂断点 |
| `/run-panel` | 面板 FE/RE/GMM 分析管道，含 Hausman 检验、序列相关和 CD 检验 |
| `/run-sdid` | 合成双重差分分析，含单位/时间权重和推断 |
| `/run-bootstrap` | Bootstrap 推断管道（配对、野生聚类、残差、teffects） |
| `/run-placebo` | 安慰剂检验管道（时间、结果、工具变量、置换推断） |
| `/run-logit-probit` | Logit/Probit、倾向得分、处理效应（RA/IPW/AIPW）和条件 Logit |
| `/run-lasso` | LASSO、双重选择后推断、严格 LASSO 和 R `glmnet` 匹配管道 |
| `/cross-check` | Stata vs Python/R 回归结果交叉验证（目标：系数差异 < 0.1%） |
| `/robustness` | 对基准回归结果运行稳健性检验套件——替代规范、子样本、聚类、Oster 界、野蛮聚类自助法 |
| `/make-table` | 生成发表质量的 LaTeX 回归表格（AER 格式或三线表） |
| `/write-section` | 按期刊规范撰写论文章节（支持中英文） |
| `/review-paper` | 模拟三位匿名审稿人的结构化反馈；可选 APE 式多轮深度评审 |
| `/lit-review` | 结构化文献综述，生成 BibTeX 条目 |
| `/adversarial-review` | 对抗式评审者-修复者质量审查循环（代码、计量、表格三个领域） |
| `/score` | 运行可执行质量评分器（6 维度，满分 100） |
| `/commit` | 智能 Git 提交，含类型前缀和数据安全警告 |
| `/compile-latex` | 运行 pdflatex/bibtex 编译管道并检查错误 |
| `/context-status` | 显示当前版本、近期决策、质量评分和 Git 状态 |
| `/explore` | 设置探索沙盒，放宽质量阈值（≥ 60），用于快速假设检验和替代规范探索 |
| `/promote` | 将 `explore/` 沙盒中的探索性文件提升至正式 `vN/` 管道，含重新编号和质量检查 |
| `/session-log` | 会话启动/结束管理，加载上下文并记录决策和学习 |
| `/interview-me` | 苏格拉底式研究访谈 — 将模糊想法结构化为研究提案 |
| `/devils-advocate` | 识别策略威胁评估 — 预分析阶段的魔鬼代言人 |
| `/learn` | 在会话内创建新规则或技能（受基本准则约束） |
| `/run-pipeline` | 自动检测计量方法，编排完整技能管道端到端执行 |
| `/synthesis-report` | 收集所有分析输出，生成结构化综合报告（Markdown + LaTeX） |
| `/translate` | 中英文经济学论文互译，支持期刊风格适配 |
| `/polish` | 学术论文润色——英文/中文润色、精炼重写、缩写、扩写（5 种子模式） |
| `/de-ai` | 检测并消除 AI 生成痕迹，使文本更接近人类研究者写作风格 |
| `/logic-check` | 论文终稿红线审查——仅捕捉致命错误，不涉及风格偏好 |

---

## 支持的计量方法

| 方法 | 技能命令 | Stata 主要命令 |
|------|----------|----------------|
| 双重差分 (DID) | `/run-did` | `reghdfe`, `csdid`, `did_multiplegt`, `bacondecomp` |
| 工具变量 (IV) | `/run-iv` | `ivreghdfe`, `ivreg2`, `weakiv` |
| 断点回归 (RDD) | `/run-rdd` | `rdrobust`, `rddensity`, `rdplot` |
| 面板数据 (Panel) | `/run-panel` | `reghdfe`, `xtabond2` |
| 合成双重差分 (SDID) | `/run-sdid` | `sdid` |
| Bootstrap 推断 | `/run-bootstrap` | `boottest`, `fwildclusterboot` |
| 安慰剂检验 (Placebo) | `/run-placebo` | 置换推断, 时间安慰剂 |
| Logit/Probit | `/run-logit-probit` | `logit`, `probit`, `teffects`, `clogit` |
| LASSO 正则化 | `/run-lasso` | `lasso2`, `pdslasso`, `glmnet` |

---

## 代理参考

| 代理 | 角色 | 权限 |
|------|------|------|
| `code-reviewer` | ~~代码质量评估~~ **（已弃用 — 请用 `code-critic`）** | 只读 |
| `econometrics-reviewer` | ~~识别策略审查~~ **（已弃用 — 请用 `econometrics-critic`）** | 只读 |
| `tables-reviewer` | ~~表格格式审查~~ **（已弃用 — 请用 `tables-critic`）** | 只读 |
| `robustness-checker` | 检查缺失的稳健性检验和敏感性分析 | 只读 |
| `paper-reviewer` | 模拟匿名审稿人的全文审查 | 只读 |
| `cross-checker` | Stata vs Python 交叉验证诊断 | 只读 + Bash |
| `code-critic` | 对抗式代码审查（规范、安全性、防御式编程） | 只读 |
| `code-fixer` | 根据 code-critic 发现实施修复 | 完全访问 |
| `econometrics-critic` | 对抗式计量审查（诊断、识别策略、稳健性） | 只读 |
| `econometrics-fixer` | 根据 econometrics-critic 发现实施修复 | 完全访问 |
| `tables-critic` | 对抗式表格审查（格式、星号、报告完整性） | 只读 |
| `tables-fixer` | 根据 tables-critic 发现实施修复 | 完全访问 |

---

## 典型工作流程

### 完整论文管道

```
/init-project → /data-describe → /run-did → /cross-check → /robustness
    → /make-table → /write-section → /review-paper → /adversarial-review
    → /score → /synthesis-report → /compile-latex → /commit
```

### 自动化管道（单条命令）

```
/run-pipeline  →  自动检测方法  →  执行完整序列  →  /synthesis-report
```

### 快速检查（单个回归）

```
/run-{method} → /cross-check → /score
```

支持的方法：`did`、`iv`、`rdd`、`panel`、`sdid`、`bootstrap`、`placebo`、`logit-probit`、`lasso`

### 研究构思

```
/interview-me → /devils-advocate → /data-describe → /run-{method}
```

### 论文写作与编辑

```
/write-section → /polish → /de-ai → /logic-check → /compile-latex
```

翻译：`/translate`（CN→EN 或 EN→CN，支持期刊风格适配）

### 修改回复

```
/context-status → （处理审稿人意见） → /adversarial-review → /score → /commit
```

---

## 目录结构

```
econ-research-workflow-cn/
├── .claude/
│   ├── agents/           # 12 个专业代理
│   ├── hooks/            # 生命周期钩子脚本（会话加载器、Stata 日志检查）
│   ├── scripts/          # 自动批准的包装脚本（run-stata.sh）
│   ├── rules/            # 编码规范、计量标准（4 条路径限定 + 3 条常驻规则含基本准则）
│   ├── settings.json     # 钩子 + 权限配置
│   └── skills/           # 34 个斜杠命令技能 + 1 个参考指南
├── scripts/
│   └── quality_scorer.py # 可执行的 6 维度质量评分器
├── tests/                # 测试用例（DID、RDD、IV、面板、完整管道）
├── CLAUDE.md             # 项目配置（填写占位符）
├── MEMORY.md             # 跨会话学习和决策日志
├── ROADMAP.md            # Phase 1-7 实现历史
└── README.md             # 本文件
```

使用 `/init-project` 创建的每个研究项目遵循以下结构：

```
项目名称/
└── v1/
    ├── code/stata/       # .do 文件（按编号排序：01_、02_、...）
    ├── code/python/      # .py 文件（用于交叉验证）
    ├── data/raw/         # 原始数据（只读，永不修改）
    ├── data/clean/       # 清洗后的数据集
    ├── data/temp/        # 中间文件
    ├── output/tables/    # LaTeX 表格（.tex）
    ├── output/figures/   # 图表（.pdf/.png）
    ├── output/logs/      # Stata .log 文件
    ├── paper/sections/   # LaTeX 章节文件
    ├── paper/bib/        # BibTeX 文件
    ├── _VERSION_INFO.md  # 版本元数据
    └── REPLICATION.md    # AEA 数据编辑格式的复现说明
```

---

## 质量评分

可执行质量评分器（`scripts/quality_scorer.py`）在 6 个维度上评估项目：

| 维度 | 分值 | 关键检查项 |
|------|------|-----------|
| 代码规范 | 15 | .do 文件头、`set seed`、编号命名、日志模式、`vce(cluster)` |
| 日志清洁度 | 15 | 无 `r(xxx)` 错误、无变量未找到、无命令未识别 |
| 输出完整性 | 15 | 表格（.tex）、图表（.pdf/.png）和日志存在且非空 |
| 交叉验证 | 15 | Python 脚本存在、系数比较、通过/失败阈值 |
| 文档 | 15 | REPLICATION.md 有实质内容、_VERSION_INFO.md、数据来源记录 |
| 方法诊断 | 25 | 自动检测：DID 平行趋势、IV 第一阶段 F、RDD 密度检验、面板 Hausman |

运行方式：`python scripts/quality_scorer.py v1/` 或使用 `/score` 技能。

### 评分标准

| 分数 | 等级 | 操作 |
|------|------|------|
| ≥ 95 | 可发表 | 无需修改 |
| ≥ 90 | 小修 | 处理小问题后提交 |
| ≥ 80 | 大修 | 需要显著修改 |
| < 80 | 重做 | 存在根本性问题 |

---

## 治理机制

### 基本准则

工作流在**基本准则**（`.claude/rules/constitution.md`）下运行，定义了 5 条不可变原则：

1. **原始数据完整性** — `data/raw/` 永远不被修改、覆盖或删除
2. **完全可复现性** — 每个结果必须可从代码 + 原始数据复现
3. **强制交叉验证** — 所有回归在 Stata 和 Python 间交叉验证（系数差异 < 0.1%；`explore/` 内可豁免）
4. **版本保存** — `vN/` 目录永不删除，仅被 `vN+1/` 取代
5. **评分诚信** — 质量评分如实记录，永不伪造或膨胀

所有技能、代理和规则在此框架内运行。`/learn` 技能不能创建违反基本准则的规则。

### 编排协议

非琐碎任务遵循 **Spec → Plan → Implement → Verify → Review → Fix → Score → Report** 八阶段循环，最多 5 轮迭代。琐碎任务（影响 ≤ 2 个文件、首轮评分 ≥ 80 且无严重问题）使用"直接执行"模式。

---

## 钩子

4 个生命周期钩子配置在 `.claude/settings.json` 中：

| 钩子 | 触发事件 | 功能 |
|------|----------|------|
| 会话启动加载器 | `SessionStart` | 读取 MEMORY.md，显示近期条目和上次质量评分 |
| 压缩前保存 | `PreCompact` | 提示在上下文压缩前将会话摘要追加到 MEMORY.md |
| Stata 日志检查 | `PostToolUse`（Bash） | Stata 运行后自动解析 `.log` 文件中的 `r(xxx)` 错误 |
| 原始数据守卫 | `PostToolUse`（Bash） | 比对 `data/raw/` 文件快照，检测未授权修改 |

### 常驻规则

4 条常驻规则（无路径限定，每次会话均加载）：

| 规则 | 用途 |
|------|------|
| `constitution.md` | 5 条不可变原则（原始数据完整性、可复现性、交叉验证、版本保存、评分诚信） |
| `orchestrator-protocol.md` | Spec-Plan-Implement-Verify-Review-Fix-Score-Report 任务循环 |
| `stata-error-verification.md` | 强制在重新运行 Stata 前读取钩子输出，防止日志覆盖导致的误判 |
| `bash-conventions.md` | 禁止链式命令（`&&`、`||`、`;`）；使用独立工具调用和绝对路径 |

### 权限与安全

权限系统采用**全量放行 + 拒绝清单**模型：

- **Deny**（共享，在 `settings.json` 中）：35 条规则覆盖 3 类场景——原始数据保护（基本准则第 1 条）、破坏性操作（`rm -rf`、`git push --force`、`git reset --hard`）、凭证与基础设施保护（`.env`、`.credentials`、`.claude/hooks/**`、`.claude/scripts/**`、`.claude/settings.json`）。
- **Allow**（个人，在 `settings.local.json` 中，已 gitignore）：默认 fork 后每次操作都弹框。如需跳过：`cp .claude/settings.local.json.example .claude/settings.local.json`。

纵深防御：

| 层级 | 机制 | 范围 |
|------|------|------|
| 1 | settings.json 中的 `deny` 规则 | 工具层字符串匹配（防止常见误操作） |
| 2 | `raw-data-guard.py` PostToolUse 钩子 | Bash 执行后检测 `data/raw/` 变动（捕获 Python/R 脚本绕过） |
| 3 | OS 级 `attrib +R` 保护 `data/raw/` | 文件系统强制只读（需手动设置） |
| 4 | 基本准则 + 行为规则 | Claude 自主遵循约束 |

---

## 更新日志

| 日期 | 版本 | 描述 |
|------|------|------|
| 2026-02-25 | v0.1 | 初始提交 — 14 个技能、6 个代理、CLAUDE.md 模板、目录规范 |
| 2026-02-25 | v0.2 | Phase 1 — 对抗式质量审查循环、质量评分器、6 个新技能 |
| 2026-02-25 | v0.3 | Phase 2 — 3 个生命周期钩子、路径限定规则、探索沙盒、会话连续性 |
| 2026-02-25 | v0.4 | NBER 工作论文和 SSRN 预印本 LaTeX 格式支持 |
| 2026-02-25 | v0.5 | Phase 3 — 苏格拉底式研究工具、自我扩展、基本准则治理 |
| 2026-02-25 | v0.6 | 4 个新技能（Bootstrap、安慰剂、Logit-Probit、LASSO） |
| 2026-02-26 | v0.7 | Phase 5 — 真实数据复现测试，11 组包×技能组合，19 个问题修复 |
| 2026-02-26 | v0.8 | Stata 自动批准包装器、编排协议更新 |
| 2026-02-26 | v0.9 | Stata 错误验证规则 — 防止日志覆盖误判 |
| 2026-02-26 | v0.10 | 一致性审计 — 修复 31 个文档/正则/YAML/交叉引用问题 |
| 2026-02-27 | v0.11 | Phase 6 — 管道编排、综合报告、遗留代理重连、评分持久化 |
| 2026-02-27 | v0.12-cn | 中文版发布 — 所有技能提示词、代理描述、规则和文档中文化 |
| 2026-02-27 | v0.13-cn | 新增写作工具 — `/translate`、`/polish`、`/de-ai`、`/logic-check` |
| 2026-02-28 | v0.14-cn | 技能审计 — 按 skill-creator 最佳实践更新 8 个技能：移除角色扮演语句、增加模式指南、误报提示、改进描述 |
| 2026-03-01 | v0.15-cn | 安全加固 — 全量放行 + 拒绝清单权限模型、`raw-data-guard.py` 钩子、`bash-conventions.md` 规则（禁止链式命令）、35 条 deny 规则、4 层纵深防御、凭证/基础设施保护 |

---

## 测试套件

5 个端到端测试覆盖所有主要估计方法：

| 测试 | 方法 | 状态 |
|------|------|------|
| `test1-did` | DID / TWFE / Callaway-Sant'Anna | 通过 |
| `test2-rdd` | RDD / rdrobust / 密度检验 | 通过 |
| `test3-iv` | IV / 2SLS / 第一阶段诊断 | 通过 |
| `test4-panel` | 面板 FE / RE / GMM | 通过 |
| `test5-full-pipeline` | 端到端多脚本管道 | 通过 |

测试中发现的问题记录在 `tests/ISSUES_LOG.md` 中，并在 `MEMORY.md` 中跟踪。

---

## 致谢

- 模板架构灵感来源于 [Pedro H.C. Sant'Anna 的 claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow)
- 计量经济学方法遵循 Angrist & Pischke、Callaway & Sant'Anna (2021)、Rambachan & Roth (2023) 以及 Cattaneo, Idrobo & Titiunik (2020) 的指南
- 质量评分框架改编自 AEA 数据编辑复现标准

---

## 许可证

MIT
