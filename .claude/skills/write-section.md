---
description: "撰写经济学研究论文的特定章节（中文或英文）"
user_invocable: true
---

# /write-section — 撰写论文章节

当用户调用 `/write-section` 时，按以下步骤操作：

## 步骤 1：收集信息

向用户询问：

1. **章节名称**（必填）— 以下之一：
   - `introduction` / 引言
   - `literature` / 文献综述
   - `background` / 制度背景
   - `data` / 数据与变量
   - `strategy` / 实证策略
   - `results` / 实证结果
   - `robustness` / 稳健性检验
   - `conclusion` / 结论
2. **语言**（必填）— `CN`（中文）或 `EN`（英文）
3. **目标期刊/格式**（可选）— 如"经济研究"、"管理世界"、"AER"、"QJE"、"JPE"、"NBER"、"SSRN"
4. **核心要点**（必填）— 用户希望涵盖的主要内容的要点列表
5. **相关文件**（可选）— 可供参考的已有表格、结果或笔记

## 步骤 2：章节特定写作指南

### 1. 引言 (Introduction)

**结构：**
1. 开篇导入：用现实相关性引出研究问题
2. 研究问题：清晰陈述论文研究什么
3. 方法/识别策略简述
4. 主要发现预览
5. 文献贡献（2-3 条具体贡献）
6. 结构安排段落

**中文（经济研究/管理世界风格）：**
- 长度：约 3000-4000 字
- 开篇：从宏观经济背景、政策相关性入手
- 全篇使用正式学术中文
- 常用表达："本文"、"研究发现"、"实证结果表明"、"本文的边际贡献在于"
- 贡献段："与已有文献相比，本文的贡献主要体现在以下几个方面："
- 结构段："本文余下部分结构安排如下：第二部分..."
- 避免口语化表达，保持学术规范
- 引用格式：中文作者-年份制（张三和李四, 2020）

**英文（AER/QJE 风格）：**
- 长度：约 1500-2000 词
- 开篇：直接、吸引人的第一句话
- 语言简洁精确
- 尽可能使用主动语态
- 贡献尽早清晰陈述
- 遵循 AER 风格：避免行话，力求可读性
- 结构段："The remainder of this paper is organized as follows..."

**LaTeX 模板：**
```latex
\section{Introduction}
% 或中文论文使用 \section{引言}

<content>
```

### 2. 文献综述 (Literature Review)

**结构：**
1. 按 2-4 条主题线索组织
2. 每条线索：概括核心发现，指出共识和争议
3. 识别本文填补的空白
4. 相对于已有工作定位本文贡献

**中文风格：**
- "本文与以下几支文献密切相关。"
- "第一支文献关注..."
- "第二支文献研究..."
- "与上述文献不同，本文..."
- 力求全面但聚焦；通常引用 30-50 篇

**英文风格：**
- "This paper contributes to several strands of the literature."
- "First, our work relates to..."
- "Second, we contribute to..."
- "We differ from this literature by..."
- 引用更精选；质量重于数量

### 3. 制度背景 (Institutional Background)

**结构：**
1. 政策/制度描述
2. 关键事件和政策变化时间线
3. 受影响的群体/实体
4. 为什么此背景适合做因果识别
5. 理解实证策略所需的制度细节

**中文风格：**
- 详细的政策描述，引用官方文件
- 时间线格式展示政策演进
- 使用具体日期和政策文号

**英文风格：**
- 简洁的制度描述
- 聚焦于与识别相关的细节
- 如有助于理解，可包含时间线图表

### 4. 数据与变量 (Data and Variables)

**结构：**
1. 数据来源和时间覆盖
2. 样本构建过程（合并、筛选、最终样本）
3. 核心变量定义（因变量、自变量、控制变量）
4. 描述性统计引用（指向表格）
5. 数据局限性（如有）

**中文风格：**
- "本文使用的数据来源于..."
- "样本期间为...年至...年"
- 变量定义以清晰的列表格式呈现
- "表1报告了主要变量的描述性统计结果"
- 变量较多时使用变量定义表

**英文风格：**
- "We use data from..."
- "Our sample covers the period..."
- 变量定义清晰，可使用表格
- "Table 1 presents summary statistics for our main variables."

**变量定义 LaTeX 模板：**
```latex
% 中文
\begin{itemize}
  \item \textbf{被解释变量}：<变量名>，定义为...
  \item \textbf{核心解释变量}：<变量名>，定义为...
  \item \textbf{控制变量}：包括...
\end{itemize}

% 英文
\begin{itemize}
  \item \textbf{Dependent Variable}: <variable name>, defined as...
  \item \textbf{Key Independent Variable}: <variable name>, defined as...
  \item \textbf{Controls}: We include...
\end{itemize}
```

### 5. 实证策略 (Empirical Strategy)

**结构：**
1. 识别策略概述
2. LaTeX 数学公式表达的估计方程
3. 方程中的变量定义
4. 核心识别假设
5. 识别威胁及应对策略
6. 核心系数的预期符号

**中文风格：**
- "本文采用...方法进行因果识别"
- "基准回归模型设定如下："
- 方程：`\begin{equation} Y_{it} = \alpha + \beta D_{it} + \gamma X_{it} + \mu_i + \lambda_t + \varepsilon_{it} \end{equation}`
- "其中，$Y_{it}$表示..., $D_{it}$为..., $X_{it}$为控制变量向量..."
- "识别假设为..."
- "本文关注的核心系数为$\beta$，预期符号为正/负"

**英文风格：**
- "Our identification strategy exploits..."
- "We estimate the following specification:"
- 相同的方程格式
- "where $Y_{it}$ denotes..., $D_{it}$ is..., and $X_{it}$ is a vector of controls..."
- "The key identifying assumption is that..."
- "Our coefficient of interest is $\beta$, which captures..."

**方法特定模板：**

DID:
```latex
Y_{it} = \alpha + \beta \cdot \text{Treat}_i \times \text{Post}_t + \gamma X_{it} + \mu_i + \lambda_t + \varepsilon_{it}
```

IV:
```latex
\text{First stage: } D_{it} = \pi Z_{it} + \gamma X_{it} + \mu_i + \lambda_t + \nu_{it}
\text{Second stage: } Y_{it} = \alpha + \beta \hat{D}_{it} + \gamma X_{it} + \mu_i + \lambda_t + \varepsilon_{it}
```

RDD:
```latex
Y_i = \alpha + \beta \cdot \mathbf{1}(X_i \geq c) + f(X_i - c) + \varepsilon_i
```

### 6. 实证结果 (Results)

**结构：**
1. 主回归结果（引用表格）
2. 经济显著性解释
3. 机制分析 / 渠道检验
4. 异质性分析（如适用）

**中文风格：**
- "表X报告了基准回归结果。"
- "第(1)列仅控制了...，第(2)列进一步加入了..."
- "核心解释变量的系数为...，在1%水平上显著"
- "经济含义上，...每增加一个标准差，...将变化...%"
- "为探究作用机制，本文从以下几个渠道进行分析："

**英文风格：**
- "Table X reports our main results."
- "Column (1) includes only..., while Column (2) adds..."
- "The coefficient on our key variable is..., significant at the 1% level."
- "In terms of economic magnitude, a one standard deviation increase in... is associated with a ...% change in..."
- "To explore the underlying mechanisms, we examine..."

### 7. 稳健性检验 (Robustness Checks)

**结构：**
1. 稳健性策略概述
2. 每种检验类型作为一个小节或段落
3. 引用具体表格/列
4. 每项结果的简要解释
5. 总体评估

**中文风格：**
- "为验证基准回归结果的稳健性，本文从以下几个方面进行检验。"
- 小节："更换被解释变量"、"改变样本范围"、"安慰剂检验"、"替换固定效应"等
- "上述检验结果表明，本文的基准回归结果是稳健的。"

**英文风格：**
- "We conduct a battery of robustness checks to validate our main findings."
- 小节："Alternative Outcomes"、"Sample Restrictions"、"Placebo Tests" 等
- "Taken together, these results confirm the robustness of our baseline estimates."

### 8. 结论 (Conclusion)

**结构：**
1. 研究问题和方法简要回顾
2. 核心发现（2-3 句）
3. 政策含义
4. 局限性
5. 未来研究方向

**中文风格：**
- "本文利用...数据，采用...方法，研究了...问题。"
- "研究发现：第一，...；第二，...；第三，..."
- "本文的研究具有以下政策启示：..."
- "当然，本文也存在一些不足之处：..."
- "未来的研究可以从以下方面进行拓展：..."
- 长度：约 800-1200 字

**英文风格：**
- "This paper studies... using... We find that..."
- "Our findings have several policy implications..."
- "We acknowledge several limitations..."
- "Future research could explore..."
- 长度：约 400-600 词

## 步骤 3：风格指南

### 中文核心期刊（经济研究、管理世界、经济学季刊、中国工业经济）
- 正式学术中文，避免口语化
- 使用"本文"（而非"我们"或"笔者"，虽然"笔者"在部分期刊中可接受）
- 常用表达：
  - 研究发现
  - 实证结果表明
  - 进一步地
  - 具体而言
  - 值得注意的是
  - 与此同时
- 段落结构：主题句 → 论据 → 解释
- 引用：（张三和李四, 2020）或 张三和李四（2020）

### 英文顶级期刊（AER、QJE、JPE、Econometrica、REStud）
- 简洁精确的学术英文
- 优先使用主动语态："We find..." 而非 "It is found that..."
- 尽量使用短句
- 遵循 AER 风格指南：
  - 10 以下的数字拼写英文
  - 正文中用 "percent" 而非 "%"（表格中可用 %）
  - 避免以符号或数字开头的句子
  - "Section 3" 而非 "section 3"
- 避免模棱两可的表述：对发现要直接
- 引用：Author (Year) 或 (Author, Year)

### NBER 工作论文风格
- **语调**：比期刊投稿更详细和探索性；工作论文允许更长的论述、扩展附录和初步发现
- **长度**：通常 30-60 页（含附录）；无严格页数限制
- **标题页**：NBER Working Paper No. XXXXX、JEL 分类码、关键词、致谢作为首页脚注
- **摘要**：100-200 词，放在标题页
- **JEL 分类**：必须，列出 2-4 个代码（如 J31, C21, H53）
- **关键词**：摘要下方 3-5 个关键词
- **致谢**：首页脚注感谢研讨会参与者、讨论人、资助来源
- **行距**：正文 1.5 倍行距
- **章节编号**：标准编号（1, 2, 3...），不加 "Section" 前缀
- **附录**：鼓励详细的数据附录、额外稳健性检验和推导
- **写作习惯**：
  - 比期刊格式有更多的方法论细节空间
  - 可以包含"进行中"的注意事项
  - 更详细地讨论数据构建
  - 更广泛的文献定位是可接受的
  - "In this paper, we..." 是常见表达（第一人称复数）
- **引用**：Author (Year) 格式，与 natbib 兼容
- **图表**：可嵌入正文或汇集在末尾；工作论文偏好嵌入

### SSRN 预印本风格
- **语调**：专业但可以比期刊投稿更非正式；适合快速传播
- **长度**：灵活，通常 20-50 页
- **标题页**：标题、作者（含机构和邮箱）、日期、摘要、关键词、JEL 代码
- **摘要**：150-250 词；应自成一体（许多 SSRN 读者只看摘要）
- **关键词**：4-6 个关键词（SSRN 用于搜索索引——应策略性选择）
- **日期**："This version: Month Year"，可选 "First version: Month Year"
- **页脚**："Available at SSRN: https://ssrn.com/abstract=XXXXXXX"（占位符）
- **行距**：单倍或 1.5 倍；工作论文常用单倍行距
- **写作习惯**：
  - 可以更广泛地讨论动机和政策相关性
  - 初步结果和注意事项是可接受的
  - "Draft — comments welcome" 是常见副标题
  - 比期刊投稿可以更口语化
  - 大量脚注很常见
- **引用**：Author (Year) 格式
- **实用提示**：
  - SSRN 读者大量浏览摘要——摘要要有吸引力且自成一体
  - 包含所有结果（包括负面结果），因为这是工作论文
  - 在摘要中清晰陈述贡献
  - 考虑在引言中添加"结果摘要"小节

## 步骤 4：生成输出

在 `paper/sections/` 中创建 .tex 文件：

```
paper/sections/<NN>_<section_name>.tex
```

其中 `<NN>` 为章节编号：
- 01_introduction.tex
- 02_literature.tex
- 03_background.tex
- 04_data.tex
- 05_strategy.tex
- 06_results.tex
- 07_robustness.tex
- 08_conclusion.tex

打印确认：

```
章节"<章节名称>"生成成功！

输出：paper/sections/<filename>.tex
语言：<CN/EN>
大约长度：<字数/字符数>

在主文档中引用：
  \input{sections/<filename>}

请注意：
  - 审阅并定制内容
  - 从你的参考文献库中添加具体引用
  - 核对表格和图表编号
  - 修改 <...> 标记的占位文字
```
