---
description: "Bilingual Socratic research interview to formalize ideas into structured proposals"
user_invocable: true
---

# /interview-me — Socratic Research Interview

A bilingual (EN/CN) Socratic questioning process that walks through the key elements of a research idea and produces a structured research proposal. The goal is to sharpen vague ideas into testable, implementable research designs.

## Activation

When the user runs `/interview-me`, begin the interview process below.

## Core Principle

Ask **ONE question at a time**. Wait for the user's response before proceeding. Do not dump all questions at once. The user can say "skip" at any stage to move to the next section.

## Language

Detect the user's language from their first response. If Chinese, conduct the interview in Chinese. If English, use English. The user can switch at any time.

---

## Interview Sections

### Section 1: Research Question

**Goal**: Arrive at a precise, testable research question.

Start with:
> What is the broad topic or phenomenon you want to study?
> 你想研究什么现象或主题？

Follow-up probes (as needed):
- What is the specific causal relationship you're interested in? (X -> Y)
- What is the unit of analysis? (firm, individual, province, county-year)
- What is the time period and geographic scope?
- Can you state this as a question with a clear dependent variable and independent variable?

Push for precision: "Does X cause Y?" is better than "What is the relationship between X and Y?"

### Section 2: Hypothesis

**Goal**: Formulate main hypothesis, auxiliary hypotheses, and establish falsifiability.

Ask:
> What do you expect to find? What is your main hypothesis?
> 你预期发现什么？主假说是什么？

Follow-up probes:
- What is the sign of the expected effect? (positive/negative)
- Why do you expect this direction? (theoretical mechanism)
- What auxiliary hypotheses would support the main story? (channels, heterogeneity)
- What result would **falsify** your hypothesis? If no possible result would falsify it, the hypothesis needs work.

### Section 3: Identification Strategy

**Goal**: Choose and justify a credible causal identification approach.

Ask:
> How will you establish that the relationship is causal rather than correlational?
> 你打算如何建立因果关系？

**Method detection**: Based on the user's answer, route to method-specific questions:

**DID / TWFE / Staggered DID**:
- What is the treatment event and when does it occur?
- Which units are treated vs. control?
- Is treatment timing staggered across units?
- Why would parallel trends hold? What evidence can you provide?
- Are there concerns about anticipation effects?

**IV / 2SLS**:
- What is your proposed instrument?
- Why is the instrument relevant (first-stage)?
- Why does the exclusion restriction hold (instrument affects Y only through X)?
- Is monotonicity reasonable?
- What is the LATE you are estimating, and is it policy-relevant?

**RDD**:
- What is the running variable and cutoff?
- Is the cutoff exogenous or potentially manipulable?
- Is the design sharp or fuzzy?
- What bandwidth will you use, and how sensitive are results to bandwidth choice?

**Panel FE**:
- What fixed effects will you include?
- What time-varying confounders remain after FE?
- Is there a dynamic story requiring lagged variables or GMM?

**SDID / Synthetic Control**:
- How many treated units and time periods?
- What is the donor pool?
- Are unit/time weights well-distributed or concentrated?

If the user is unsure about method, discuss the strengths and weaknesses of feasible approaches given their data structure.

### Section 4: Data Requirements

**Goal**: Identify exactly what data is needed and whether it's obtainable.

Ask:
> What data do you need for this analysis? What variables are essential?
> 你需要什么数据？哪些变量是核心变量？

Follow-up probes:
- What is the data source? (CSMAR, CNRDS, Wind, CFPS, survey, admin data)
- What is the unit-time structure? (firm-year, province-month, individual-wave)
- Dependent variable: exact name, how measured, any proxies?
- Independent variable (treatment): exact definition, when does it switch on?
- Control variables: what confounders must you control for?
- Instrument / running variable (if IV/RDD): data source and measurement?
- Sample restrictions: what firms/individuals are excluded and why?
- Is the data currently available or does it need to be acquired?

### Section 5: Expected Results

**Goal**: Pre-commit to expected findings, sign, magnitude, and robustness strategy.

Ask:
> What results do you expect to see in the main regression? Be specific about sign and approximate magnitude.
> 你预期主回归结果的方向和大致程度是什么？

Follow-up probes:
- What sign and rough magnitude do you expect for the main coefficient?
- What would be a "surprisingly large" or "surprisingly small" effect?
- What robustness checks will you pre-commit to running?
  - Placebo tests (treatment/outcome/cutoff)
  - Subsample analysis (by firm size, region, time period)
  - Alternative specifications (different FE, controls, clustering)
  - Dose-response or intensity margin
- What result would change your conclusion?

---

## Output: Structured Proposal

After completing the interview (or after the user says "done"), generate a structured research proposal.

### File Location

Save to `vN/docs/research_proposal.md` (where `vN` is the current active version from CLAUDE.md).

### Template

```markdown
# Research Proposal

**Generated**: YYYY-MM-DD via /interview-me

---

## 1. Research Question

[Precise statement of the causal question]

- **Treatment (X)**: [definition]
- **Outcome (Y)**: [definition]
- **Unit of analysis**: [unit-time]
- **Scope**: [geography, time period]

## 2. Hypotheses

**Main hypothesis**: [H1 — precise, directional statement]

**Auxiliary hypotheses**:
- H2: [channel / mechanism]
- H3: [heterogeneity prediction]

**Falsification condition**: [what result would reject the hypothesis]

## 3. Identification Strategy

**Method**: [DID / IV / RDD / Panel FE / SDID]

**Key assumptions**:
1. [assumption and justification]
2. [assumption and justification]

**Threats**: [top 2-3 concerns to address]

## 4. Data

| Variable | Type | Source | Measurement |
|----------|------|--------|-------------|
| Y        | DV   |        |             |
| X        | IV/Treatment |  |             |
| Z        | Instrument/Running var |  |    |
| Controls | Control |     |             |

**Sample**: [unit-time structure, N estimate, restrictions]

## 5. Expected Results

**Main coefficient**: [sign, approximate magnitude]

**Pre-committed robustness checks**:
1. [test]
2. [test]
3. [test]

## 6. Next Steps

1. [ ] Acquire/clean data
2. [ ] Run descriptive statistics (/data-describe)
3. [ ] Implement main specification (/run-{method})
4. [ ] Cross-validate (/cross-check)
5. [ ] Robustness suite (/robustness)
```

After generating the proposal, display:
```
Research proposal saved to vN/docs/research_proposal.md

Suggested next steps:
  /data-describe    — Explore and describe your data
  /devils-advocate  — Challenge your identification strategy
  /run-{method}     — Run the main estimation
```

## Notes

- The interview should feel like a conversation with a knowledgeable advisor, not a form.
- If the user gives very short answers, probe deeper. If they give detailed answers, move forward.
- Sections can be revisited — if data constraints in Section 4 invalidate the method in Section 3, circle back.
- The proposal is a living document — it can be updated in future sessions.
