# 经济学研究工作流 - 快速参考

## 技能参考（30 个技能）

### 核心分析

| 命令 | 说明 | 典型场景 |
|---------|-------------|-------------|
| `/init-project` | 初始化项目结构 | 项目启动 |
| `/data-describe` | 描述性统计（Stata + Python） | 数据清洗后 |
| `/run-did` | DID/TWFE/CS/SDID 流水线及诊断检验 | 因果估计 |
| `/run-iv` | IV/2SLS 流水线及第一阶段和弱工具变量检验 | 因果估计 |
| `/run-rdd` | RDD 流水线及带宽敏感性和密度检验 | 因果估计 |
| `/run-panel` | 面板 FE/RE/GMM 及 Hausman、序列相关检验 | 因果估计 |
| `/run-sdid` | 合成 DID，含单位/时间权重和推断 | 因果估计 |
| `/run-bootstrap` | 配对、野蛮聚类、残差、处理效应自助法推断 | 主要结果之后 |
| `/run-placebo` | 时间、结果、工具变量、置换安慰剂检验 | 稳健性检验 |
| `/run-logit-probit` | Logit/probit、倾向得分、RA/IPW/AIPW、条件 logit | 二值/处理效应模型 |
| `/run-lasso` | LASSO、双重选择后推断、glmnet 匹配 | 变量选择 |
| `/cross-check` | Stata 与 Python 回归交叉验证（< 0.1%） | 任何回归之后 |
| `/robustness` | 全面稳健性检验套件 | 主要结果之后 |

### 输出与写作

| 命令 | 说明 | 典型场景 |
|---------|-------------|-------------|
| `/make-table` | 可发表的 LaTeX 表格（AER 或三线表） | 论文写作前 |
| `/write-section` | 撰写论文章节（中文或英文期刊格式） | 论文起草 |
| `/compile-latex` | 运行 pdflatex/bibtex 流水线并检查错误 | 论文修改后 |

### 评审与质量

| 命令 | 说明 | 典型场景 |
|---------|-------------|-------------|
| `/review-paper` | 三位模拟审稿人 | 投稿前 |
| `/lit-review` | 结构化文献综述及 BibTeX | 初期 / 修改 |
| `/adversarial-review` | 评审者-修复者循环（代码、计量、表格）最多 5 轮 | 质量保证 |
| `/score` | 可执行质量评分器（6 维度，满分 100 分） | 任何交付物之后 |

### 会话与项目管理

| 命令 | 说明 | 典型场景 |
|---------|-------------|-------------|
| `/commit` | 智能 git commit，带类型前缀和数据安全警告 | 修改后 |
| `/context-status` | 显示版本、决策、评分、git 状态 | 工作开始时 |
| `/session-log` | 会话启动/结束，集成 MEMORY.md | 会话边界 |
| `/explore` | 探索沙盒，放宽阈值（>= 60） | 假设检验 |
| `/promote` | 从 `explore/` 提升文件至 `vN/`，含质量门槛 | 探索结束后 |

### 研究构思与治理

| 命令 | 说明 | 典型场景 |
|---------|-------------|-------------|
| `/interview-me` | 双语苏格拉底访谈 → 结构化研究提案 | 新研究想法 |
| `/devils-advocate` | 预分析识别策略威胁评估 | 估计之前 |
| `/learn` | 在会话中创建新规则或技能 | 编撰规范 |
| `/run-pipeline` | 自动检测方法，编排完整技能流水线 | 端到端自动化 |
| `/synthesis-report` | 汇集输出为结构化综合报告（MD + LaTeX） | 评分之后 |

### 参考资源

| 资源 | 说明 | 用途 |
|----------|-------------|-------|
| `advanced-stata-patterns.md` | 脉冲响应、Helmert、HHK、k 类估计、自助法、空间滞后 | run-panel/run-iv 在需要高级模式时自动引用 |

这是一个不可用户调用的参考文件（无斜杠命令）。当相关技能需要高级 Stata 模式时会自动引用。

---

## 代理参考（12 个代理）

### 旧版审查者

| 代理 | 角色 | 状态 |
|-------|------|--------|
| `econometrics-reviewer` | 检查识别策略和估计 | **已弃用**（请用 `econometrics-critic`） |
| `code-reviewer` | 审查 Stata/Python 代码质量 | **已弃用**（请用 `code-critic`） |
| `paper-reviewer` | 模拟期刊审稿人 | 活跃——接入 `/review-paper` |
| `tables-reviewer` | 检查表格格式和合规性 | **已弃用**（请用 `tables-critic`） |
| `robustness-checker` | 建议遗漏的稳健性检验 | 活跃——接入 `/robustness` |
| `cross-checker` | 比较 Stata 与 Python 结果 | 活跃——接入 `/cross-check` |

### 对抗式评审者-修复者配对

| 评审者 (Critic) | 修复者 (Fixer) | 领域 |
|--------|-------|--------|
| `code-critic` | `code-fixer` | 代码规范、安全性、可复现性 |
| `econometrics-critic` | `econometrics-fixer` | 识别策略、诊断检验、稳健性 |
| `tables-critic` | `tables-fixer` | 表格格式、报告、合规性 |

评审者为只读，不能编辑文件。修复者有完全访问权限，但不能为自己的工作评分。

---

## 典型工作流序列

### 研究构思
```
/interview-me → /devils-advocate → /data-describe → /run-{method}
```

### 完整论文流水线
```
/init-project → /data-describe → /run-{method} → /cross-check → /robustness
  → /make-table → /write-section → /review-paper → /adversarial-review
  → /score → /synthesis-report → /compile-latex → /commit
```

### 自动化流水线（单命令）
```
/run-pipeline  →  自动检测方法  →  运行完整序列  →  /synthesis-report
```

### 快速回归检查
```
/run-{method} → /cross-check → /score
```

### 修改回复
```
/context-status → （处理审稿意见） → /adversarial-review → /score → /commit
```

### 探索沙盒
```
/explore → （在 explore/ 中工作） → /promote → /score
```

### 文献深度研究
```
/lit-review → /write-section（文献综述）
```

---

## 治理机制

### 基本准则 (Constitution)（`.claude/rules/constitution.md`）

5 条不可变原则——始终加载，不可覆盖：
1. 原始数据完整性（`data/raw/` 永不修改）
2. 完全可复现性（每个结果均可从代码 + 原始数据复现）
3. 强制交叉验证（< 0.1%；`explore/` 中放宽）
4. 版本保留（`vN/` 永不删除）
5. 评分完整性（如实记录）

### 编排协议 (Orchestrator Protocol)

非平凡任务遵循：**规格 → 计划 → 实施 → 验证 → 评审 → 修复 → 评分 → 报告**

阶段 0（规格）在以下情况触发：任务影响 >= 3 个文件、变更识别策略、创建技能/规则/代理、或修改协议本身。每个任务只写一次——评审循环从计划重新开始。

"直接执行"模式：平凡任务（<= 2 个文件、评分 >= 80、无严重发现）跳过多轮循环。

---

## 质量评分

| 分数 | 含义 | 操作 |
|-------|---------|--------|
| >= 95 | 可发表 | 继续 |
| >= 90 | 小修 | 再来一轮 |
| >= 80 | 大修 | 重新进入实施阶段 |
| < 80 | 重做 | 重新进入计划阶段 |

评分来源：`/score`（自动化，6 个维度）和 `/adversarial-review`（评审者代理）。

---

## 关键规范

### 文件路径
- 原始数据（只读）：`vN/data/raw/`
- 清洗后数据：`vN/data/clean/`
- Stata 代码：`vN/code/stata/`
- Python 代码：`vN/code/python/`
- 所有输出：`vN/output/`
- 表格：`vN/output/tables/`
- 图表：`vN/output/figures/`
- 论文：`vN/paper/`

### Stata 执行（Git Bash）
```bash
"D:\Stata18\StataMP-64.exe" -e do "code/stata/script.do"
```
- **必须用 `-e`**（自动退出），**禁止用 `-b`**（需手动确认）或 **`/e`**（Git Bash 路径冲突）
- 每次 Stata 运行后必须检查 `.log` 文件
- 非零退出码或日志中出现 `r(xxx)` = 失败

### 版本管理
- 每次重大修改放在独立的 `vN/` 目录中
- `_VERSION_INFO.md` 记录版本元数据
- `docs/CHANGELOG.md` 记录项目级别变更

### 命名规范
- Stata do 文件：`01_clean_data.do`、`02_desc_stats.do`、`03_reg_main.do`……
- 输出表格：`tab_main_results.tex`、`tab_robustness.tex`……
- 输出图表：`fig_event_study.pdf`、`fig_parallel_trends.pdf`……

---

## 常用模式

### 添加稳健性检验
1. 运行 `/robustness` 获取建议
2. 在 `04_robustness.do` 中实施建议的检验
3. 运行 `/cross-check` 验证
4. 运行 `/make-table` 格式化结果

### 回应审稿意见
1. 创建新版本目录 `vN+1/`
2. 复制并修改相关代码
3. 运行 `/robustness` 进行额外检验
4. 运行 `/make-table` 更新表格
5. 运行 `/write-section` 撰写回复信
6. 运行 `/review-paper` 自查

### 交叉验证工作流
1. 通过 `/run-{method}` 在 Stata 中运行回归
2. 运行 `/cross-check` 在 Python 中复现
3. 查看系数比较表
4. 容差：系数差异 0.1% 以内（严格），标准误差异 5% 以内

---

## 故障排除

| 问题 | 解决方案 |
|---------|----------|
| Stata 日志显示错误 | 读取完整日志，修复 do 文件，重新运行 |
| 交叉验证不匹配 | 检查聚类设置、样本限制、变量定义 |
| LaTeX 表格无法编译 | 检查 `\input{}` 路径、缺失的宏包 |
| 版本冲突 | 始终在最新 `vN/` 目录中工作 |
| 探索结果过于粗糙 | 使用 `/promote` 提升，须通过质量门槛 |
