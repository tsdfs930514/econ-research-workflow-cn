---
description: "Generate structured literature review with BibTeX entries"
user_invocable: true
---

# /lit-review — Structured Literature Review Generator

## Information Gathering

Before starting, ask the user for:

1. **Research topic/question**: What is the specific research question or topic area?
2. **Method**: DID / IV / RDD / Panel FE / other econometric approach
3. **Key papers already known** (optional): Papers the user is already aware of, to avoid redundancy and to anchor the review
4. **Scope**: Narrow (tightly focused on exact topic) or Broad (includes adjacent topics and broader methodological context)
5. **Language**: CN (Chinese literature only) / EN (English literature only) / Both

## Literature Organization

Generate the review organized into three streams:

### Stream 1: Methodological Stream
Key papers that advance the econometric method being used:
- Foundational/seminal papers establishing the method
- Recent methodological innovations and refinements
- Papers on diagnostics, testing, and best practices for the method
- Critiques and limitations of the method

### Stream 2: Topical Stream
Papers on the same substantive topic regardless of method:
- Foundational work defining the research area
- Major empirical findings in the field
- Theoretical contributions relevant to the topic
- Policy-relevant studies and their conclusions

### Stream 3: Intersection Stream
Papers using the same method on the same or closely related topic:
- Direct precedents for the user's approach
- Papers the user's work must cite and differentiate from
- Studies using similar data or institutional settings

## Entry Format

For each paper referenced, provide:

| Field | Content |
|---|---|
| **Author(s)** | Full author list |
| **Year** | Publication year |
| **Journal** | Journal name (with impact factor tier if relevant) |
| **Key Finding** | One-sentence summary of main result |
| **Method** | Econometric method used |
| **Data/Context** | Dataset, country, time period |
| **Relevance** | How this paper relates to the user's research question |

## Research Gap Identification

After mapping the literature, identify:

1. **Methodological gaps**: Has this method been applied to this topic before? If so, what variation or improvement does the user offer?
2. **Empirical gaps**: Is there a data context (country, time period, population) not yet studied?
3. **Theoretical gaps**: Is there a mechanism or channel not yet explored?
4. **Policy gaps**: Are there policy-relevant questions the literature has not addressed?

Frame the user's potential contribution in terms of filling one or more of these gaps.

## BibTeX Generation

Generate BibTeX entries for all referenced papers in the following format:

```bibtex
@article{author2024title,
  author = {Author, First and Author, Second},
  title = {Paper Title},
  journal = {Journal Name},
  year = {2024},
  volume = {XX},
  number = {X},
  pages = {XX--XX},
  doi = {10.xxxx/xxxxx}
}
```

For Chinese-language papers:

```bibtex
@article{author2024title,
  author = {作者一 and 作者二},
  title = {论文标题},
  journal = {期刊名称},
  year = {2024},
  volume = {XX},
  number = {X},
  pages = {XX--XX},
  language = {chinese}
}
```

**Important disclaimer**: Include a clear note at the top of the BibTeX output:

> **VERIFICATION REQUIRED**: These BibTeX entries are generated from Claude's training data and may contain inaccurate volume numbers, page ranges, or DOIs. All entries should be verified against the actual publications via Google Scholar, CNKI, or the journal's website before use in a manuscript.

## Chinese Literature Sources

For Chinese literature (when scope includes CN):
- Include papers from CSSCI-indexed journals
- Reference CNKI as the primary database
- Cover key Chinese economics journals: 经济研究, 管理世界, 中国工业经济, 经济学(季刊), 金融研究, 中国社会科学, 世界经济
- Use both Chinese and pinyin-romanized citation keys

## Output Files

Generate two output sections:

### 1. Literature Review Section (`lit_review.tex`)
- LaTeX-formatted literature review text
- Organized by the three streams above
- Uses `\cite{}` commands matching the BibTeX keys
- Ready to be `\input{}` into a main paper file

### 2. References (`references.bib`)
- Complete BibTeX file with all entries
- Sorted alphabetically by citation key
- Includes the verification disclaimer as a comment at the top of the file

## Output Format

Present the literature review in structured markdown first (for immediate reading), then provide the LaTeX and BibTeX file contents in code blocks that the user can save.
