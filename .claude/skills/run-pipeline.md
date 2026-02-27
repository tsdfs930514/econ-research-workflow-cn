---
description: "自动识别研究计划中的计量方法，编排并端到端执行完整的技能管道"
user_invocable: true
---

# /run-pipeline — 自动化研究管道

当用户调用 `/run-pipeline` 时，读取研究计划，检测计量方法，生成有序的技能执行方案，并端到端运行。

## 标志参数

- `/run-pipeline` — 交互模式（执行前确认方案）
- `/run-pipeline --quick` — 跳过确认，自动执行所有步骤
- `/run-pipeline --replication <paper.pdf>` — 复现模式：从已发表论文 PDF 中提取方法和变量

## 步骤 0：收集输入

按以下顺序确定研究计划来源：

1. **用户直接提供** — 如果用户附带描述（如 `/run-pipeline DID analysis of minimum wage on employment`）
2. **研究提案** — 检查 `docs/research_proposal.md`（由 `/interview-me` 生成）
3. **论文 PDF** — 如果使用了 `--replication <paper.pdf>` 标志，读取 PDF 并提取：
   - 研究问题与假说
   - 识别策略与计量方法
   - 变量定义（因变量、处理变量、控制变量、工具变量）
   - 数据描述
4. **交互式** — 如果以上均不适用，向用户询问：
   - 研究问题（一句话）
   - 识别策略/计量方法
   - 数据集路径
   - 核心变量（因变量、处理变量、控制变量）

从输入中提取：
- **研究问题**：一句话摘要
- **因果识别方法**：主要方法 + 任何辅助/稳健性方法
- **变量定义**：Y、D/T、X 控制变量、Z 工具变量（若为 IV）、驱动变量（若为 RDD）
- **数据路径**：数据集位置
- **目标期刊**：中文核心 / 英文 TOP5 / 工作论文（影响表格格式）

## 步骤 1：方法检测与技能映射

解析研究计划以识别计量方法，并映射到 `/run-*` 技能：

| 检测到的方法 | 映射技能 |
|-------------|---------|
| DID / TWFE / 事件研究 / 交错处理 / 平行趋势 | `/run-did` |
| IV / 2SLS / 工具变量 / 排除性约束 | `/run-iv` |
| RDD / 断点回归 / 断点 / 阈值 / 带宽 | `/run-rdd` |
| 面板 FE / RE / GMM / Hausman / 组内估计 | `/run-panel` |
| 合成 DID / SDID / 合成控制 + DID | `/run-sdid` |
| Bootstrap / 野生聚类 bootstrap / 重抽样 | `/run-bootstrap` |
| 安慰剂检验 / 随机化推断 / 置换检验 | `/run-placebo` |
| Logit / probit / 倾向得分 / 处理效应 / IPW | `/run-logit-probit` |
| LASSO / 正则化 / 变量选择 / post-double-selection | `/run-lasso` |

**多方法检测**：一个计划可能包含多种方法（如"主分析：DID；稳健性：IV 作为替代"）。检测所有方法并排序：
1. 主要方法优先
2. 替代/稳健性方法在后

**关键词匹配**：在文本中查找以下模式：
- 方法全称（不区分大小写）："difference-in-differences"、"instrumental variable"、"regression discontinuity" 等
- 方法缩写："DID"、"DiD"、"IV"、"2SLS"、"RDD"、"FE"、"RE"、"GMM"、"SDID"
- 识别假设："parallel trends" → DID，"exclusion restriction" → IV，"manipulation test" → RDD
- 提及的 Stata 命令：`csdid` → DID，`ivreghdfe` → IV，`rdrobust` → RDD

## 步骤 2：生成执行方案

根据检测到的方法生成有序的技能执行序列。模板如下：

```
管道方案：[研究问题]
方法：[主要方法]（+ [辅助方法]）
数据：[数据集路径]

执行序列：
  1. /data-describe          — 数据探索与描述性统计
  2. /run-{主要方法}          — 主分析
  3. /cross-check            — Stata vs Python 交叉验证
  4. /robustness             — 综合稳健性检验
  [5. /run-{辅助方法}        — 替代估计（如适用）]
  [6. /run-placebo           — 安慰剂检验（如适用）]
  7. /make-table             — 生成可发表质量的表格
  8. /adversarial-review     — 对抗式质量保障
  9. /score                  — 质量评分（6 维度，100 分）
  10. /synthesis-report      — 综合报告

预期输出：
  - X 个 .do 文件在 code/stata/
  - X 个 .py 文件在 code/python/
  - X 个 .tex 表格在 output/tables/
  - X 个图形在 output/figures/
  - 1 份综合报告在 docs/
```

### 方案定制规则

- 如果方法是交错处理 DID：加入 `/run-placebo`（时间安慰剂）
- 如果方法是 IV：在稳健性之后加入 `/run-placebo`（工具变量安慰剂）
- 如果方法是 RDD：跳过 `/run-placebo`（密度检验和安慰剂断点已内置于 `/run-rdd`）
- 如果用户提及 bootstrap 推断：在主分析之后加入 `/run-bootstrap`
- 如果计划提及倾向得分匹配：在主 DID/IV 之前加入 `/run-logit-probit`
- 如果计划提及变量选择：在主分析之前加入 `/run-lasso`

### 用户确认

除非设置了 `--quick` 标志，展示方案并询问：

```
是否执行此管道？[yes / edit / cancel]
- yes:    按顺序执行所有步骤
- edit:   修改序列（添加、删除或重新排序步骤）
- cancel: 中止管道
```

如果用户选择 `edit`，允许修改序列并重新确认。

## 步骤 3：顺序执行

按方案依次执行每个技能：

### 对于每个步骤：

1. **公告**：显示即将运行的技能及其目的
   ```
   [步骤 2/10] 正在运行 /run-did — 主 DID 分析...
   ```

2. **执行**：使用从步骤 0 获取的参数调用技能
   - 传入变量定义、数据路径和方法特定参数
   - 对于 `/run-*` 技能：提供回归规范
   - 对于 `/cross-check`：指向刚生成的 Stata 日志
   - 对于 `/make-table`：指向存储的估计结果
   - 对于 `/robustness`：提供主分析的基准规范

3. **验证输出**：每个技能完成后检查：
   - 预期输出文件是否已创建？
   - Stata 日志中是否存在 `r(xxx)` 错误？
   - 输出是否非空？

4. **处理错误**：
   - 如果出现 Stata `r(xxx)` 错误：**暂停执行**，显示错误，向用户询问：
     ```
     步骤 2 (/run-did) 出错：Stata r(111) — 找不到变量
     选项：[修复并重试 / 跳过此步骤 / 中止管道]
     ```
   - `--quick` 模式下出错：仍然暂停（错误不应被静默跳过）
   - 非关键性警告（如收敛警告）：记录并继续

5. **记录进度**：每步完成后显示：
   ```
   [步骤 2/10] /run-did — 完成
     输出：code/stata/03_reg_main.do, output/logs/reg_main.log, output/tables/tab_main_results.tex
     状态：干净（无错误）
   ```

### 自动执行 /synthesis-report

所有计划的技能完成后（或 `/score` 作为最后一个分析步骤完成后），自动调用 `/synthesis-report` 生成最终综合报告。

## 步骤 4：管道总结

所有步骤完成后显示总结：

```
管道完成
=================
研究问题：[问题]
方法：[方法]

步骤结果：
  1. /data-describe        — 完成（生成 2 个文件）
  2. /run-did              — 完成（生成 3 个文件）
  3. /cross-check          — 完成（通过 — 最大差异 0.003%）
  4. /robustness           — 完成（12/14 个规范显著）
  5. /make-table           — 完成（生成 3 个表格）
  6. /adversarial-review   — 完成（平均得分：88/100）
  7. /score                — 完成（82/100 — 需要大修）
  8. /synthesis-report     — 完成（docs/ANALYSIS_SUMMARY.md）

最终质量评分：82/100
状态：需要大修 — 建议修复后再次运行 /adversarial-review

输出文件：
  code/stata/     — 5 个 .do 文件
  code/python/    — 2 个 .py 文件
  output/tables/  — 3 个 .tex 表格
  output/figures/ — 2 个 .pdf 图形
  output/logs/    — 5 个 .log 文件
  docs/           — ANALYSIS_SUMMARY.md, ANALYSIS_SUMMARY.tex, QUALITY_SCORE.md
```

### 基于评分的建议

| 最终评分 | 建议 |
|---------|------|
| >= 95 | "可发表。建议运行 `/compile-latex` 和 `/commit`。" |
| >= 90 | "需要小修。查阅 ANALYSIS_SUMMARY.md 中的剩余问题，修复后重新运行 `/score`。" |
| >= 80 | "需要大修。运行 `/adversarial-review` 定位具体问题，然后重新运行受影响的 `/run-*` 技能。" |
| < 80 | "存在重大问题。查阅综合报告，解决关键发现，考虑重新运行管道。" |

## 复现模式 (--replication)

当指定 `--replication <paper.pdf>` 时：

1. 使用 PDF 工具读取论文
2. 从方法论部分提取：
   - 使用的计量方法
   - 回归规范（方程形式）
   - 变量名称和定义
   - 数据来源和样本限制
   - 固定效应和聚类选择
   - 提及的主要稳健性检验
3. 按步骤 2 生成执行方案，但需：
   - 变量名称与原论文匹配
   - 使用相同的规范和诊断
   - 增加交叉验证步骤（原论文中没有，但我们的工作流要求）
4. 正常进行执行

目标是复现论文结果，并通过我们的质量基础设施加以验证。
