---
description: "检测并消除 AI 生成痕迹，使文本更接近人类研究者写作风格"
user_invocable: true
---

# /de-ai — 去AI化重写

当用户调用 `/de-ai` 时，按以下步骤操作：

## 步骤 1：收集信息

向用户询问：

1. **语言**（必填）— `EN`（英文）或 `CN`（中文）
2. **格式**（可选）— `LaTeX`（默认）或 `Word`
3. **待处理文本**（必填）— 需要去AI化的文本

## 步骤 2：AI 特征检测

**方法：** 以怀疑论审稿人的视角分析文本——该审稿人熟悉人工撰写和 AI 生成的稿件。目标是检测并消除 AI 写作的明显痕迹。

**注意：** 这些模式是启发式的。在自然语境中出现一次的短语可能是合理的。重点关注重复出现的模式或 AI 特征的聚集。

### 2.1 词汇层面

**高频 AI 词汇——标记并替换以下词汇/短语：**

通用 AI 高频词：
- leverage, delve, tapestry, underscore, pivotal, nuanced, intricate
- foster, elucidate, comprehensive, multifaceted, holistic, paradigm, synergy
- landscape, realm, interplay, crucial, vital, cutting-edge, groundbreaking
- harness, navigate, facilitate, bolster, augment, streamline
- noteworthy, commendable, meticulous, indispensable, paramount
- shed light on, pave the way, at the forefront, game changer
- it is important to note, it is worth mentioning, in today's rapidly
- a testament to, serves as a reminder, the cornerstone of
- robust（非统计意义上的"稳健"时）

经济学场景的 AI 模式：
- "comprehensive framework" → "framework"
- "robust evidence"（非统计语境）→ "evidence"
- "nuanced understanding" → "understanding" 或 "detailed understanding"
- "shed light on the mechanisms" → "identify the mechanisms" 或 "examine the mechanisms"
- "comprehensive empirical analysis" → "empirical analysis"
- "robust causal evidence" → "causal evidence"
- "rich dataset" → "detailed dataset" 或直接描述数据集
- "novel contribution" → 直接陈述贡献内容
- "growing body of literature" → "recent literature" 或 "literature on X"
- "fills an important gap" → 直接说明新意

补充黑名单：
- Additionally, Moreover, Furthermore（在段首机械使用时）
- In conclusion, In summary（公式化使用时）
- It is important to note that, It is worth noting that
- plays a crucial role, is of paramount importance
- First and foremost, Last but not least
- This serves as a reminder, This is a testament to

**语境很重要：** 部分黑名单词汇在经济学中有合理用法（如 "leverage" 在 "leverage a natural experiment" 中、"robust" 在 "robust standard errors" 中）。仅在使用不精确、作为填充词或聚集出现时才标记。在语境中单次合理使用不构成 AI 信号。

### 2.2 结构层面

**检测并修复以下 AI 结构特征：**

1. **破折号过度使用** — AI 频繁使用破折号作插入语。替换为逗号、括号或重构句子。

2. **列表格式滥用** — AI 倾向于使用项目符号列表，而连贯的段落更为合适。将独立的项目符号列表转化为流畅的段落。

3. **机械连接词** — AI 使用公式化过渡词：
   - "First and foremost" → "First" 或直接切入要点
   - "It is worth noting that" → 删除或直接表述
   - "In light of the above" → 删除或使用具体引用
   - "Moving forward" → 删除
   - "Building upon this" → 删除或使用具体表述

4. **三段式模式（Rule of Three）** — AI 倾向于恰好提供三个例子/论点/原因。根据实际内容调整数量。

5. **加粗/斜体过度使用** — AI 过度格式化文本。移除正文中纯粹用于强调的格式标记。

6. **"Not only...but also..." 并列结构** — AI 过度使用此句式。使用更简洁的替代方案。

7. **公式化段首** — 每段都以过渡词开头。允许一些段落直接以内容开始。

### 2.3 语气层面

1. **过度对冲** — 过多的限定语："might potentially"、"could possibly"、"it seems that perhaps"。应直接表述。
2. **通用正面结论** — "This study makes significant contributions..." 直接说明发现了什么。
3. **填充短语** — "In the realm of"、"Within the context of"、"It goes without saying"。删除。

## 步骤 3：重写规范

**核心原则：用朴实精准的词汇替代华丽词汇。**

| AI 模式 | 人类替代 |
|---|---|
| leverage | use |
| utilize | use |
| delve into | examine, study, analyze |
| underscore | show, highlight |
| pivotal | important, key |
| nuanced | detailed, subtle |
| intricate | complex |
| foster | encourage, promote |
| elucidate | explain, clarify |
| comprehensive | thorough, full |
| multifaceted | complex |
| facilitate | enable, help |
| bolster | support, strengthen |
| shed light on | explain, reveal, identify |
| pave the way | enable, allow |
| at the forefront | leading |
| a growing body of | recent, increasing |
| it is important to note | [删除——直接陈述] |
| furthermore / moreover | [删除或用 "also"、"and"] |
| in conclusion | [删除或直接总结] |

**其他重写规则：**
- 将项目符号列表转化为连贯的段落
- 移除段首的机械过渡词
- 变化句子长度——长短句交替
- 在 AI 倾向于模糊的地方增加具体细节
- 如果原文已经自然流畅，**保留原文**并注明无需修改

## 步骤 4：输出

**EN 模式：**

```
### Part 1: Rewritten Text [LaTeX/Word]

[重写后的文本——如果原文已足够自然则保留原文]

### Part 2: Literal Translation [中文直译]

[重写文本的中文翻译]

### Part 3: Change Log [修改日志]

| # | 检测到的 AI 模式 | 原文 | 修改后 | 类别 |
|---|---|---|---|---|
| 1 | [模式名称] | [原文片段] | [修改后片段] | 词汇/结构/语气 |
| 2 | ... | ... | ... | ... |
```

如果未发现显著 AI 模式：
```
### Part 1: Original Text (Preserved)

[原文不变]

### Part 2: Detection Result

检测通过——未发现显著 AI 痕迹。文本读起来自然。
```

**CN 模式：**

```
### Part 1: 重写文本

[重写后的文本——如果原文已足够自然则保留原文]

### Part 2: 修改日志

| # | 检测到的 AI 模式 | 原文 | 修改后 | 类别 |
|---|---|---|---|---|
| 1 | [模式名称] | [原文片段] | [修改后片段] | 词汇/结构/语气 |
```

如果未发现显著 AI 模式：
```
### Part 1: 原文保留

[原文不变]

### Part 2: 检测结果

检测通过——未发现显著 AI 痕迹。文本读起来像人工撰写。
```

**中文特有的 AI 模式（CN 模式下额外检查）：**
- 值得注意的是 — 机械强调
- 综上所述 — 公式化结论
- 不可或缺 — AI 式最高级
- 至关重要 — AI 式强调
- 日益重要 — AI 填充
- 本研究旨在填补这一空白 — AI 式空白填补套话
- 这一研究为...提供了重要参考 — 通用 AI 结论
- 在此背景下 — 机械过渡
- 具有重要的理论意义和实践价值 — 通用 AI 价值声明

## 步骤 5：二次审计

初步重写后，执行自我审计：

**自问："什么因素仍然会让细心的读者怀疑这是 AI 生成的？"**

1. 以怀疑论审稿人的视角重新阅读重写后的文本
2. 识别任何残余的 AI 特征（包括细微的）
3. 简要记录残余痕迹（如有）
4. 如果仍有痕迹，再次修改并产出最终版本

```
### 二次审计

**残余痕迹：** [列出任何剩余问题，或"无——文本读起来像人工撰写"]
**最终修订：** [任何额外修改，或"无需进一步修改"]
```

---

> **来源**: 去AI化方法改编自 [awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing)（Leey21）和 [humanizer](https://github.com/blader/humanizer)（blader），针对经济学研究定制。
