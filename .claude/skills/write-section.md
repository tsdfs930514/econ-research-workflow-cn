---
description: "Write a specific section of an economics research paper in Chinese or English"
user_invocable: true
---

# /write-section - Write a Paper Section

When the user invokes `/write-section`, follow these steps:

## Step 1: Gather Information

Ask the user for:

1. **Section name** (required) - One of:
   - `introduction` / 引言
   - `literature` / 文献综述
   - `background` / 制度背景
   - `data` / 数据与变量
   - `strategy` / 实证策略
   - `results` / 实证结果
   - `robustness` / 稳健性检验
   - `conclusion` / 结论
2. **Language** (required) - `CN` (Chinese) or `EN` (English)
3. **Target journal/format** (optional) - e.g., "经济研究", "管理世界", "AER", "QJE", "JPE", "NBER", "SSRN"
4. **Key points to cover** (required) - Bullet points of the main content the user wants included
5. **Related files** (optional) - Any existing tables, results, or notes to reference

## Step 2: Section-Specific Guidelines

### 1. Introduction (引言)

**Structure:**
1. Opening hook: Motivate the research question with real-world relevance
2. Research question: State clearly what the paper studies
3. Brief description of approach/identification strategy
4. Preview of main findings
5. Contribution to literature (2-3 specific contributions)
6. Paper structure paragraph

**Chinese (经济研究/管理世界 style):**
- Length: approximately 3000-4000 Chinese characters
- Opening: Start with broad economic context, policy relevance
- Use formal academic Chinese throughout
- Phrases to use: "本文", "研究发现", "实证结果表明", "本文的边际贡献在于"
- Contribution paragraph: "与已有文献相比，本文的贡献主要体现在以下几个方面："
- Structure paragraph: "本文余下部分结构安排如下：第二部分..."
- Avoid colloquial expressions, maintain academic formality
- Reference format: use author-year in Chinese (张三和李四, 2020)

**English (AER/QJE style):**
- Length: approximately 1500-2000 words
- Opening: Direct, engaging first sentence
- Concise and precise language
- Active voice where possible
- Contribution clearly stated early
- Follow AER style: avoid jargon, be accessible
- Structure paragraph: "The remainder of this paper is organized as follows..."

**LaTeX template:**
```latex
\section{Introduction}
% or \section{引言} for Chinese

<content>
```

### 2. Literature Review (文献综述)

**Structure:**
1. Organize by 2-4 thematic strands of literature
2. For each strand: summarize key findings, identify consensus and debates
3. Identify the gap that this paper fills
4. Position the paper's contribution relative to existing work

**Chinese style:**
- "本文与以下几支文献密切相关。"
- "第一支文献关注..."
- "第二支文献研究..."
- "与上述文献不同，本文..."
- Be comprehensive but focused; cite 30-50 papers typically

**English style:**
- "This paper contributes to several strands of the literature."
- "First, our work relates to..."
- "Second, we contribute to..."
- "We differ from this literature by..."
- More selective citation; quality over quantity

### 3. Institutional Background (制度背景)

**Structure:**
1. Policy/institution description
2. Timeline of key events and policy changes
3. Affected groups / entities
4. Why this setting is suitable for identification
5. Relevant institutional details for understanding the empirical strategy

**Chinese style:**
- Detailed policy description with official document citations
- Timeline format for policy evolution
- Use exact dates and policy document numbers

**English style:**
- Concise institutional description
- Focus on details relevant to identification
- Include a timeline figure if helpful

### 4. Data and Variables (数据与变量)

**Structure:**
1. Data sources and time coverage
2. Sample construction process (merging, filtering, final sample)
3. Key variable definitions (dependent, independent, controls)
4. Summary statistics reference (point to table)
5. Data limitations (if any)

**Chinese style:**
- "本文使用的数据来源于..."
- "样本期间为...年至...年"
- Variable definitions in a clear list format
- "表1报告了主要变量的描述性统计结果"
- Use variable definition table if many variables

**English style:**
- "We use data from..."
- "Our sample covers the period..."
- Clear variable definitions, potentially in a table
- "Table 1 presents summary statistics for our main variables."

**LaTeX template for variable definition:**
```latex
% Chinese
\begin{itemize}
  \item \textbf{被解释变量}：<variable name>，定义为...
  \item \textbf{核心解释变量}：<variable name>，定义为...
  \item \textbf{控制变量}：包括...
\end{itemize}

% English
\begin{itemize}
  \item \textbf{Dependent Variable}: <variable name>, defined as...
  \item \textbf{Key Independent Variable}: <variable name>, defined as...
  \item \textbf{Controls}: We include...
\end{itemize}
```

### 5. Empirical Strategy (实证策略)

**Structure:**
1. Identification strategy overview
2. Estimation equation in LaTeX math
3. Variable definitions within the equation
4. Key identifying assumptions
5. Threats to identification and how they are addressed
6. Expected sign of key coefficient

**Chinese style:**
- "本文采用...方法进行因果识别"
- "基准回归模型设定如下："
- Equation: `\begin{equation} Y_{it} = \alpha + \beta D_{it} + \gamma X_{it} + \mu_i + \lambda_t + \varepsilon_{it} \end{equation}`
- "其中，$Y_{it}$表示..., $D_{it}$为..., $X_{it}$为控制变量向量..."
- "识别假设为..."
- "本文关注的核心系数为$\beta$，预期符号为正/负"

**English style:**
- "Our identification strategy exploits..."
- "We estimate the following specification:"
- Same equation format
- "where $Y_{it}$ denotes..., $D_{it}$ is..., and $X_{it}$ is a vector of controls..."
- "The key identifying assumption is that..."
- "Our coefficient of interest is $\beta$, which captures..."

**Method-specific templates:**

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

### 6. Results (实证结果)

**Structure:**
1. Main regression results (reference table)
2. Economic significance interpretation
3. Mechanism analysis / channel tests
4. Heterogeneity analysis (if applicable)

**Chinese style:**
- "表X报告了基准回归结果。"
- "第(1)列仅控制了...，第(2)列进一步加入了..."
- "核心解释变量的系数为...，在1%水平上显著"
- "经济含义上，...每增加一个标准差，...将变化...%"
- "为探究作用机制，本文从以下几个渠道进行分析："

**English style:**
- "Table X reports our main results."
- "Column (1) includes only..., while Column (2) adds..."
- "The coefficient on our key variable is..., significant at the 1% level."
- "In terms of economic magnitude, a one standard deviation increase in... is associated with a ...% change in..."
- "To explore the underlying mechanisms, we examine..."

### 7. Robustness Checks (稳健性检验)

**Structure:**
1. Overview of robustness strategy
2. Each test type as a subsection or paragraph
3. Reference specific table/column for each test
4. Brief interpretation of each result
5. Overall assessment

**Chinese style:**
- "为验证基准回归结果的稳健性，本文从以下几个方面进行检验。"
- Subsections: "更换被解释变量", "改变样本范围", "安慰剂检验", "替换固定效应", etc.
- "上述检验结果表明，本文的基准回归结果是稳健的。"

**English style:**
- "We conduct a battery of robustness checks to validate our main findings."
- Subsections: "Alternative Outcomes", "Sample Restrictions", "Placebo Tests", etc.
- "Taken together, these results confirm the robustness of our baseline estimates."

### 8. Conclusion (结论)

**Structure:**
1. Brief summary of research question and approach
2. Key findings (2-3 sentences)
3. Policy implications
4. Limitations
5. Future research directions

**Chinese style:**
- "本文利用...数据，采用...方法，研究了...问题。"
- "研究发现：第一，...；第二，...；第三，..."
- "本文的研究具有以下政策启示：..."
- "当然，本文也存在一些不足之处：..."
- "未来的研究可以从以下方面进行拓展：..."
- Length: approximately 800-1200 characters

**English style:**
- "This paper studies... using... We find that..."
- "Our findings have several policy implications..."
- "We acknowledge several limitations..."
- "Future research could explore..."
- Length: approximately 400-600 words

## Step 3: Style Guidelines

### Chinese Core Journals (经济研究、管理世界、经济学季刊、中国工业经济)
- Formal academic Chinese, never colloquial
- Use 本文 (not 我们 or 笔者, though 笔者 is acceptable in some journals)
- Common phrases:
  - 研究发现 (research finds)
  - 实证结果表明 (empirical results show)
  - 进一步地 (furthermore)
  - 具体而言 (specifically)
  - 值得注意的是 (it is worth noting)
  - 与此同时 (meanwhile)
- Paragraph structure: topic sentence -> evidence -> interpretation
- Citations: (张三和李四, 2020) or 张三和李四(2020)

### English Top Journals (AER, QJE, JPE, Econometrica, REStud)
- Concise, precise academic English
- Active voice preferred: "We find..." not "It is found that..."
- Short sentences where possible
- Follow AER style guide:
  - Spell out numbers below 10
  - Use "percent" not "%"  in text (% is fine in tables)
  - Avoid starting sentences with symbols or numbers
  - "Section 3" not "section 3"
- Avoid hedging language: be direct about findings
- Citations: Author (Year) or (Author, Year)

### NBER Working Paper Style
- **Tone**: More detailed and exploratory than journal submissions; working papers allow longer exposition, extended appendices, and preliminary findings
- **Length**: Typically 30-60 pages including appendices; no strict page limit
- **Title page**: NBER Working Paper No. XXXXX, JEL codes, keywords, acknowledgments as first-page footnote
- **Abstract**: 100-200 words, placed on title page
- **JEL Classification**: Required, list 2-4 codes (e.g., J31, C21, H53)
- **Keywords**: 3-5 keywords below abstract
- **Acknowledgments**: First-page footnote thanking seminar participants, discussants, funding sources
- **Spacing**: 1.5-spaced body text
- **Sections**: Standard numbering (1, 2, 3...) without "Section" prefix
- **Appendix**: Detailed data appendix, additional robustness, and derivations encouraged
- **Writing conventions**:
  - More room for methodological detail than in journal format
  - Can include "work in progress" caveats
  - Discuss data construction in more detail
  - More extensive literature positioning is acceptable
  - "In this paper, we..." is fine (first person plural)
- **Citations**: Author (Year) format, natbib compatible
- **Figures/tables**: Can be embedded in text or collected at end; embedded preferred for working papers

### SSRN Preprint Style
- **Tone**: Professional but can be more informal than journal submissions; suitable for rapid dissemination
- **Length**: Flexible, typically 20-50 pages
- **Title page**: Title, author(s) with affiliations and email, date, abstract, keywords, JEL codes
- **Abstract**: 150-250 words; should be self-contained (readers often only see the abstract on SSRN)
- **Keywords**: 4-6 keywords (SSRN uses these for search indexing — choose strategically)
- **Date**: "This version: Month Year" and optionally "First version: Month Year"
- **Footer**: "Available at SSRN: https://ssrn.com/abstract=XXXXXXX" (placeholder until assigned)
- **Spacing**: Single or 1.5-spaced; single-spaced is common for working papers
- **Writing conventions**:
  - Can discuss motivation and policy relevance more extensively
  - Preliminary results and caveats are acceptable
  - "Draft — comments welcome" is a common subtitle
  - More conversational tone than journal submissions is acceptable
  - Extensive footnotes are common
- **Citations**: Author (Year) format
- **Practical notes**:
  - SSRN readers scan abstracts heavily — make it compelling and self-contained
  - Include all results (even negative) since this is a working paper
  - Clearly state contribution in the abstract itself
  - Consider adding a "Summary of Results" subsection in the introduction

## Step 4: Generate Output

Create the .tex file in `paper/sections/`:

```
paper/sections/<NN>_<section_name>.tex
```

Where `<NN>` is the section number:
- 01_introduction.tex
- 02_literature.tex
- 03_background.tex
- 04_data.tex
- 05_strategy.tex
- 06_results.tex
- 07_robustness.tex
- 08_conclusion.tex

Print confirmation:

```
Section "<section name>" generated successfully!

Output: paper/sections/<filename>.tex
Language: <CN/EN>
Approximate length: <word/character count>

To include in your main document:
  \input{sections/<filename>}

Remember to:
  - Review and customize the content
  - Add specific citations from your bibliography
  - Reference correct table and figure numbers
  - Adjust any placeholder text marked with <...>
```
