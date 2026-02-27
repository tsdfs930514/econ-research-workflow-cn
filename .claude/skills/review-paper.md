---
description: "Simulate peer review with three reviewers giving structured feedback, with optional APE-style multi-round deep review"
user_invocable: true
---

# /review-paper — Simulated Peer Review

## Information Gathering

Before starting, ask the user for:

1. **Paper file path** (or paste key sections: introduction, methodology, results)
2. **Target journal**: Chinese core (经济研究/管理世界/中国工业经济/etc.) or English top 5 (AER/QJE/JPE/Econometrica/RES)
3. **Method used**: DID / IV / RDD / Panel FE / SDID / other
4. **Review mode**:
   - `standard` (default) — 3 simulated reviewers with distinct styles
   - `ape` — APE-style multi-round review: internal deep review → structured revision plan

## Review Process

### Standard Mode: Three Independent Reviewers

Use the Task tool to invoke the `paper-reviewer` agent for each of the 3 reviewer roles below. Each invocation should specify the reviewer persona (Supportive, Balanced, or Critical), the paper content, and the target journal. The agent returns a structured referee report.

Simulate **3 independent reviewers** with distinct evaluation styles:

#### Reviewer 1 — The Supportive Reviewer
- Focuses on strengths and potential of the paper
- Suggests incremental improvements rather than fundamental rethinking
- Gives benefit of the doubt on identification strategy
- Tends toward constructive framing: "This could be strengthened by..." rather than "This fails to..."
- More likely to recommend Minor Revision or Accept

#### Reviewer 2 — The Balanced Reviewer
- Fair and even-handed assessment
- Weighs strengths and weaknesses equally
- Provides practical, actionable suggestions
- Evaluates whether the paper meets the bar for the target journal specifically
- Recommendation reflects honest middle-ground assessment

#### Reviewer 3 — The Critical Reviewer
- Skeptical of identification strategy; looks for holes
- Demands additional robustness checks and sensitivity analyses
- Pushes hard on contribution novelty: "How does this advance beyond X (2020)?"
- Questions data quality and sample selection
- More likely to recommend Major Revision or Reject

### APE Mode: Multi-Round Deep Review

Inspired by the APE paper competition review process (where AI reviewers systematically improved papers through multiple rounds):

#### Round 1: Internal Deep Review

Conduct a comprehensive internal review covering:

1. **Identification Strategy Audit**
   - Is the identifying assumption clearly stated?
   - Are all testable implications tested? (parallel trends, balance, manipulation, etc.)
   - What are the main threats to identification? How well are they addressed?
   - Is there a missing robustness check that a referee would ask for?

2. **Code-Results Consistency Check**
   - Do the described methods match what the code actually does?
   - Are all statistics referenced in the text actually computed?
   - Do table notes accurately describe the specification?

3. **Missing Analysis Detection**
   - Method-specific checklist:
     - **DID**: Bacon decomposition? HonestDiD? Wild cluster bootstrap (if few clusters)? Event study with pre-trend test?
     - **IV**: Anderson-Rubin CIs? LIML comparison? LOSO? Oster bounds?
     - **RDD**: Bandwidth sensitivity table? CER bandwidth? Kernel sensitivity? Placebo cutoffs? Density test?
     - **SDID**: Unit/time weights analysis? Comparison with pure SC and DID?
   - Is there a cross-validation between Stata and Python/R?

4. **Presentation Quality**
   - Tables: Do they follow TOP5 formatting standards?
   - Figures: Clear labels, appropriate scales, publication-quality?
   - Writing: Is the contribution clearly stated in the first paragraph?

#### Round 2: Structured Revision Plan

Based on Round 1 findings, generate a prioritized revision plan:

```
Priority | Finding | Severity | Action Required
---------|---------|----------|----------------
1        | Missing Bacon decomposition | High | Add bacondecomp to Step 3
2        | Pre-trend test not formal | Medium | Add joint F-test on leads
3        | Table 2 missing dep var mean | Low | Add scalar to esttab
...
```

Severity levels:
- **Critical**: Would likely lead to desk rejection (e.g., wrong SE, missing key test)
- **High**: Referee would demand this in R&R (e.g., missing robustness check)
- **Medium**: Improves paper quality substantially (e.g., better presentation)
- **Low**: Nice to have (e.g., formatting polish)

## Evaluation Dimensions

Each reviewer scores the paper on a **1-10 scale** for each dimension:

| Dimension | Description |
|---|---|
| **Contribution/Novelty** | Does the paper add something new to the literature? |
| **Identification Strategy** | Is the causal identification credible? Are assumptions testable and tested? |
| **Data Quality** | Is the data appropriate, well-described, and sufficient? |
| **Econometric Execution** | Are estimations correctly implemented? Standard errors appropriate? Robustness sufficient? |
| **Writing Quality** | Is the paper clearly written, well-organized, logically structured? |
| **Tables/Figures Quality** | Are results well-presented, publication-ready, easy to interpret? |
| **Literature Coverage** | Is the related work comprehensive and correctly positioned? |
| **Replication Quality** | Is the code reproducible? Is documentation sufficient? (APE mode only) |

## Reviewer Output Format

For **each reviewer**, provide:

1. **Overall Recommendation**: Accept / Minor Revision / Major Revision / Reject
2. **Aggregate Score**: weighted average of dimension scores
3. **Top 3 Strengths**: specific, with references to sections/paragraphs
4. **Top 3 Weaknesses**: specific, with references to sections/paragraphs
5. **Specific Actionable Suggestions**: numbered list, each referencing the relevant section, paragraph, table, or equation
6. **Questions for the Authors**: numbered list of clarification questions
7. **Missing Robustness Checks** (if any): specific tests the reviewer would require

## Journal-Specific Standards

### For Chinese Core Journals (经济研究 / 管理世界 / 中国工业经济)
- **Policy relevance**: Does the paper speak to current Chinese economic policy concerns?
- **Chinese institutional context**: Does it demonstrate deep understanding of China's institutional environment (户籍制度, 财政分权, 产业政策, etc.)?
- **Theoretical framework**: Is there a formal or semi-formal theoretical model motivating the empirics?
- **Data sources**: Are Chinese datasets (CFPS, CHIP, CSMAR, industrial enterprise database, etc.) used appropriately?
- **Writing conventions**: 中文学术规范, proper citation format, 三线表
- **Minimum robustness**: PSM-DID, placebo test, parallel trends, subsample

### For English Top 5 Journals (AER / QJE / JPE / Econometrica / RES)
- **Clean identification**: Is there a credible natural experiment or design-based approach?
- **Careful inference**: Are results interpreted cautiously? Is external validity discussed?
- **Clear contribution**: Can the main contribution be stated in one sentence?
- **Literature positioning**: Is the paper clearly situated relative to frontier work?
- **Presentation**: AER-style formatting, booktabs tables, clear figure design
- **Modern econometrics**: Heterogeneity-robust estimators for DID, weak-IV-robust inference, bandwidth sensitivity for RDD
- **Replication package**: Code and data organized per AEA Data Editor standards

## Summary Report

After all three reviews, generate a **Summary Section**:

- **Aggregate scores** across all three reviewers (table format)
- **Consensus areas**: where all reviewers agree (strengths or weaknesses)
- **Disagreement areas**: where reviewers diverge, and why
- **Priority revision list**: top 5 things the authors should address first, ranked by importance and frequency of mention
- **Overall assessment**: synthesized recommendation considering all three perspectives
- **Estimated revision scope**: What percentage of the paper needs rework?

## Output Format

Output the complete review as a structured markdown report with clear headers for each reviewer and the summary section.
