# CLAUDE.md - 项目配置文件
# 每次 Claude Code 会话启动时自动加载本文件。
# 请将标有 [PLACEHOLDER] 的模板字段替换为你的项目信息。

---

## 项目信息

- **项目名称**: [PROJECT_NAME]
- **机构**: [INSTITUTION_NAME]
- **研究者**: [RESEARCHER_NAMES]
- **当前版本**: v1
- **创建日期**: [DATE]
- **最后更新**: [DATE]

---

## 当前版本

当前工作版本为 **v1/**。所有新代码、输出和分析均应放在此版本目录下，除非正在迁移至新版本。

创建新版本（如 v2/）时，请从上一版本复制目录结构，并更新此字段。

---

## 目录规范

每个版本遵循如下结构：

```
vN/
  _VERSION_INFO.md        # 版本元数据
  code/
    stata/                # .do 文件
    python/               # .py 文件
    sas/                  # .sas 文件（如需要）
  data/
    raw/                  # 原始数据（只读，禁止修改）
    clean/                # 清洗后的数据集
    temp/                 # 中间/临时数据
  output/
    tables/               # LaTeX 表格 (.tex)
    figures/              # 图表 (.pdf/.png)
    logs/                 # Stata .log / Python 输出日志
  paper/
    main_cn.tex           # 中文论文
    main_en.tex           # 英文论文
    sections/             # 章节 .tex 文件
    bib/                  # BibTeX 文件
```

---

## Stata 配置

- **可执行文件路径**: `D:\Stata18\StataMP-64.exe`
- **执行命令**（自动批准的封装脚本）：
  ```bash
  bash .claude/scripts/run-stata.sh "<project_dir>" "<do_file>"
  ```
- **示例**：
  ```bash
  bash .claude/scripts/run-stata.sh "F:/Learning/econ-research-workflow/tests/test1-did/v1" "code/stata/01_did_analysis.do"
  ```
- **参数说明**：
  - 封装脚本内部使用 `-e`（自动退出）
  - 禁止使用 `-b` 和 `/e`（详见原始说明）
  - 日志检查已内置于封装脚本中——无需手动 `tail`
- **备用方案**（封装脚本不可用时）：
  ```bash
  cd "<project_dir>"
  "D:\Stata18\StataMP-64.exe" -e do "<do_file>"
  ```

---

## Python 配置

- **核心包**：
  - `pyfixest` -- 固定效应回归与推断
  - `pandas` -- 数据操作与分析
  - `polars` -- 高性能 DataFrame 库
  - `matplotlib` -- 绑图与可视化
  - `stargazer` -- 回归表格格式化

- **回归交叉验证 (Cross-Validation)**：
  使用 `pyfixest` 的 `feols()` 对 Stata 回归结果进行交叉验证：
  ```python
  import pyfixest as pf
  result = pf.feols("y ~ x1 + x2 | fe1 + fe2", data=df)
  result.summary()
  ```

---

## 代码命名规范

所有脚本使用数字前缀表示执行顺序。

**Stata (.do 文件)**：
```
01_clean_data.do
02_desc_stats.do
03_reg_main.do
04_reg_robust.do
05_tables_export.do
06_figures.do
```

**Python (.py 文件)**：
```
01_clean_data.py
02_desc_stats.py
03_reg_crossval.py
04_figures.py
```

- 前缀数字定义版本内的执行顺序。
- 数字前缀后使用描述性名称。
- Stata 和 Python 脚本放在同一 `code/` 目录下。

---

## 技能快速参考

| 技能 | 说明 |
|---|---|
| `/init-project` | 初始化研究项目，创建标准化目录结构 |
| `/data-describe` | 生成描述性统计和变量分布（Stata + Python） |
| `/run-did` | 运行完整的 DID/TWFE/Callaway-Sant'Anna 分析流水线（合成 DID 请用 `/run-sdid`） |
| `/run-iv` | 运行完整的 IV/2SLS 分析流水线及诊断检验 |
| `/run-rdd` | 运行完整的 RDD 分析流水线及全部诊断检验 |
| `/run-panel` | 运行完整的面板数据 FE/RE/GMM 分析流水线 |
| `/run-sdid` | 运行合成 DID 分析，包括单位/时间权重与推断 |
| `/cross-check` | Stata、Python pyfixest、R fixest 之间的回归结果交叉验证 |
| `/robustness` | 对基准回归结果运行稳健性检验套件——替代规范、子样本、聚类、Oster 界、野蛮聚类自助法 |
| `/make-table` | 生成可发表的 LaTeX 回归表格 |
| `/write-section` | 撰写论文特定章节（中文或英文） |
| `/review-paper` | 模拟三位审稿人给出结构化反馈；可选 APE 风格多轮深度评审 |
| `/lit-review` | 生成结构化文献综述及 BibTeX 条目 |
| `/adversarial-review` | 运行对抗式评审者/修复者 QA 循环（代码、计量、表格） |
| `/score` | 运行可执行质量评分器（6 个维度，满分 100 分） |
| `/commit` | 智能 git commit，带类型前缀和数据安全警告 |
| `/compile-latex` | 使用 pdflatex/bibtex 编译 LaTeX 论文并检查错误 |
| `/context-status` | 显示当前版本、近期决策、质量评分、git 状态 |
| `/explore` | 设置探索沙盒，放宽质量阈值（>= 60），用于快速假设检验和替代规范探索 |
| `/promote` | 将 explore/ 沙盒中的探索性文件提升至主 vN/ 流水线，含重新编号和质量检查 |
| `/session-log` | 会话启动/结束管理器——加载上下文、记录决策和经验 |
| `/interview-me` | 双语苏格拉底式研究访谈——将想法形式化为结构化提案 |
| `/devils-advocate` | 预分析识别策略挑战者——威胁评估，不涉及代码修复 |
| `/learn` | 在会话中创建新规则或技能（受基本准则约束） |
| `/run-bootstrap` | 运行自助法与重抽样推断流水线（配对、野蛮聚类、残差、处理效应） |
| `/run-placebo` | 运行安慰剂检验与随机化推断流水线（时间、结果、工具变量、置换） |
| `/run-logit-probit` | 运行 logit/probit、倾向得分、处理效应（RA/IPW/AIPW）和条件 logit 流水线 |
| `/run-lasso` | 运行 LASSO、双重选择后推断和正则化回归流水线，用于变量选择与因果推断 |
| `/run-pipeline` | 自动检测研究计划中的方法并端到端编排完整技能流水线 |
| `/synthesis-report` | 汇集所有分析输出，生成结构化综合报告（Markdown + LaTeX） |
| `/translate` | 中英文经济学论文互译，支持期刊风格适配 |
| `/polish` | 学术论文润色——英文/中文润色、精炼重写、缩写、扩写（5 种子模式） |
| `/de-ai` | 检测并消除 AI 生成痕迹，使文本更接近人类研究者写作风格 |
| `/logic-check` | 论文终稿红线审查——仅捕捉致命错误，不涉及风格偏好 |

---

## 钩子 (Hooks)

`.claude/settings.json` 中配置了 4 个生命周期钩子：

| 钩子 | 事件 | 动作 |
|------|-------|--------|
| 会话启动加载器 | `SessionStart` | 读取 MEMORY.md，显示近期条目、上次会话和最新质量评分 |
| 压缩前保存 | `PreCompact` | 提示 Claude 在上下文压缩前将会话摘要追加到 MEMORY.md |
| Stata 运行后日志检查 | `PostToolUse` (Bash) | Stata 执行后解析 `.log` 文件中的 `r(xxx)` 错误 |
| 原始数据守卫 | `PostToolUse` (Bash) | 比对 `data/raw/` 文件快照，检测未授权修改（捕获 Python/R 脚本绕过） |

钩子脚本位于 `.claude/hooks/`：
- `session-loader.py` — 会话启动上下文加载器
- `stata-log-check.py` — Stata 错误自动检测
- `raw-data-guard.py` — data/raw 完整性监控（防御层 2）

### 始终加载的规则

4 条始终加载的规则（每次会话均加载，不限路径作用域）：

| 规则 | 用途 |
|------|---------|
| `constitution.md` | 5 条不可变基本准则，约束所有工作流组件 |
| `orchestrator-protocol.md` | 规格-计划-实施-验证-评审-修复-评分 任务循环 |
| `stata-error-verification.md` | Stata 脚本重新运行前必须读取钩子输出 |
| `bash-conventions.md` | 禁止链式命令（`&&`、`||`、`;`）；使用独立工具调用和绝对路径 |

### 权限与安全

权限系统采用**全量放行 + 拒绝清单**模型，配置在 `.claude/settings.json` 中：

**Allow**：`Read`、`Edit`、`Write`、`Bash` — 所有工具自动批准，无弹框。

**Deny**（3 类）：

| 类别 | 规则 | 用途 |
|------|------|------|
| 原始数据保护 | `Edit/Write(data/raw/**)`、`Bash(*rm/mv/cd*data/raw*)` | 基本准则第 1 条 |
| 破坏性操作 | `Bash(*rm -rf /*)`, `Bash(*git push*--force*)`, `Bash(*git reset --hard*)` | 防止不可逆损害 |
| 凭证与基础设施 | `Read/Edit/Write(*.env)`、`Read/Edit/Write(*.credentials*)`、`Edit/Write(.claude/hooks/**)`、`Edit/Write(.claude/scripts/**)`、`Edit/Write(.claude/settings.json)` | 保护密钥和工作流基础设施 |

**纵深防御架构**：

| 层级 | 机制 | 捕获范围 |
|------|------|---------|
| 1 | `deny` 规则 | Claude 工具层的误操作（字符串匹配） |
| 2 | `raw-data-guard.py` 钩子 | Python/R 脚本通过 OS 调用修改 `data/raw/` |
| 3 | `attrib +R`（OS 级） | 所有途径——需在每个项目上手动设置 |
| 4 | 基本准则 + 规则 | 行为约束（Claude 应遵循，非强制） |

---

## 个人偏好

机器特定的偏好设置（Stata 路径、编辑器、目录等）存储在项目根目录的 `personal-memory.md` 中。该文件已加入 **gitignore**，不通过版本控制共享。请复制模板并填入你的本地设置。

---

## 质量阈值（Sant'Anna 评分体系）

所有交付物按 0-100 分制评分：

| 分数 | 等级 | 操作 |
|---|---|---|
| >= 95 | 可发表 | 无需进一步修改 |
| >= 90 | 小修 | 提交前解决小问题 |
| >= 80 | 大修 | 需要大幅修改 |
| < 80 | 重做 | 存在根本性问题；从头开始 |

评分标准包括：方法论严谨性、代码正确性、输出格式、结果稳健性和表述清晰度。

使用 `/adversarial-review` 进行自动化多轮质量保证（评审者/修复者分离），使用 `/score` 进行量化评分。

---

## 质量评分

可执行质量评分器（`scripts/quality_scorer.py`）从 6 个维度评价项目：

| 维度 | 分值 | 关键检查项 |
|-----------|--------|------------|
| 代码规范 | 15 | .do 文件头、`set seed`、编号命名、日志模式、`vce(cluster)` |
| 日志清洁度 | 15 | 无 `r(xxx)` 错误、无 `variable not found`、无 `command not found` |
| 输出完整性 | 15 | 表格 (.tex)、图表 (.pdf/.png) 和日志存在且非空 |
| 交叉验证 | 15 | Python 脚本存在、系数比较、通过/未通过阈值 |
| 文档 | 15 | REPLICATION.md 有内容、_VERSION_INFO.md、数据来源已记录 |
| 方法诊断 | 25 | 自动检测：DID 平行趋势、IV 第一阶段 F 值、RDD 密度检验、面板 Hausman 检验 |

运行方式：`python scripts/quality_scorer.py v1/` 或使用 `/score` 技能。

---

## 数据安全规则

1. **`data/raw/` 为只读目录。** 永远不要修改、覆盖或删除原始数据文件。
2. 所有数据转换必须从 `data/raw/` 读取，写入 `data/clean/` 或 `data/temp/`。
3. 清洗脚本必须记录每一项数据转换操作。
4. 在 `docs/` 中保留原始数据来源和下载日期的记录。
5. 执行任何破坏性操作之前，确认目标不在 `data/raw/` 中。

---

## 论文格式

通过 `/write-section` 和 `/init-project` 支持 4 种输出样式：

| 格式 | 模板 | 适用场景 |
|--------|----------|----------|
| 中文期刊 | `main_cn.tex` | 经济研究、管理世界、经济学季刊投稿 |
| 英文 TOP5 | `main_en.tex` | AER、QJE、JPE、Econometrica、REStud 投稿 |
| NBER 工作论文 | `main_nber.tex` | NBER WP 系列，含 JEL 分类码、致谢、扩展附录 |
| SSRN 预印本 | `main_ssrn.tex` | 快速传播，"草稿——欢迎评论"格式 |

---

## 输出标准

### 数值格式
- **系数**: 默认 3 位小数（如 `0.123`）；TOP5/AER 因果推断表格为 4 位小数（详见 `/make-table`）
- **标准误**: 默认 3 位小数，括号内显示（如 `(0.045)`）；TOP5/AER 为 4 位
- **显著性星号**: `*** p<0.01`, `** p<0.05`, `* p<0.10`
- **R 方**: 3 位小数
- **观测值**: 千位分隔整数（如 `12,345`）

### 表格标准
- 列标题中包含因变量名称。
- 每张表格报告观测值数量和 R 方。
- 表格脚注注明固定效应和聚类标准误。
- 相关表格之间保持一致的列顺序。

### 图表标准
- 所有坐标轴标注变量名称和单位。
- 包含标题和数据来源注释。
- 使用高分辨率导出（光栅图 300+ DPI，优先使用矢量图）。
- 同一版本内所有图表使用一致的配色方案。
