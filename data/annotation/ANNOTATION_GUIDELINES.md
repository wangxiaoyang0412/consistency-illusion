# Reasoning Alignment Annotation Guidelines

## Overview

You will be evaluating pairs of AI-generated medical reasoning traces. For each pair, two AI agents answered the same medical question and arrived at the **same answer**. Your task is to judge **how well their reasoning aligns** — not whether the answer is correct, but whether the two agents reached that answer through similar reasoning.

This annotation supports the validation of an automated metric (CARA) that measures cross-agent reasoning alignment. Your human judgments will be compared against the automated scores to assess whether the metric captures real reasoning alignment as perceived by a human expert.

## What You Will See

Each annotation item contains:

1. **A medical question** (from MedThink-Bench, a medical QA dataset)
2. **Agent A's reasoning** — a list of numbered reasoning steps
3. **Agent B's reasoning** — a list of numbered reasoning steps

Both agents selected the same final answer. Some responses follow a structured format (CLAIM / GROUND / STANCE), while others are in free-form text. This format difference is intentional — please evaluate the reasoning content regardless of format.

## What You Judge

For each pair, rate two things:

### Rating 1: Reasoning Alignment (1–5 scale)

> **"To what extent do Agent A and Agent B follow the same reasoning process to reach their shared answer?"**

| Score | Label | Description |
|-------|-------|-------------|
| **5** | **Near-identical reasoning** | Both agents make essentially the same claims, cite the same medical facts, and follow the same logical sequence. If you read only one, you could predict the other's reasoning with high confidence. Minor wording differences are acceptable. |
| **4** | **Substantially aligned** | Both agents cover the same core reasoning path and key medical facts, but one may include additional points or organize ideas differently. The overall diagnostic/therapeutic logic is the same. |
| **3** | **Partially aligned** | The agents share some key reasoning steps but diverge on others. They may agree on the conclusion pathway but disagree on intermediate justifications, or one agent may reason through a different mechanism that happens to reach the same answer. |
| **2** | **Weakly aligned** | The agents reach the same answer but through largely different reasoning. They may invoke different medical principles, focus on different aspects of the patient presentation, or use different chains of inference. Only a few reasoning steps overlap. |
| **1** | **Misaligned reasoning** | The agents reach the same answer through fundamentally different (or contradictory) reasoning. Their reasoning steps have little to no overlap, or one agent's reasoning actively contradicts the other's intermediate claims while still arriving at the same final answer. |

### Rating 2: Confidence (1–3 scale)

| Score | Label | Description |
|-------|-------|-------------|
| **3** | **Confident** | The reasoning is clear enough for me to judge alignment confidently. |
| **2** | **Somewhat confident** | Some ambiguity in the reasoning makes judgment harder, but I can still give a reasonable rating. |
| **1** | **Low confidence** | The reasoning is too vague, too short, or too domain-specific for me to judge alignment reliably. |

### Optional: Notes

A free-text field for anything noteworthy:
- Specific contradictions between the agents
- Cases where one agent gives a much more detailed explanation
- Cases where the format (structured vs free-form) affects your ability to compare
- Any other observations

## Detailed Judgment Criteria

When assessing alignment, consider these aspects in order of importance:

### 1. Core Medical Claims (Most Important)
Do both agents identify the same key medical facts or diagnostic criteria?
- **Example of alignment**: Both agents state "the patient's proteinuria and hypoalbuminemia indicate nephrotic syndrome"
- **Example of misalignment**: Agent A attributes symptoms to "nephrotic syndrome" while Agent B attributes them to "acute interstitial nephritis"

### 2. Reasoning Chain
Do both agents follow the same logical sequence from symptoms → differential → conclusion?
- **Example of alignment**: Both agents first establish the clinical picture, then consider differentials, then narrow to the answer
- **Example of misalignment**: Agent A uses an elimination approach (ruling out other options), while Agent B uses a pattern-matching approach (identifying the best-fit diagnosis)

### 3. Evidence Cited
Do both agents reference the same clinical findings, lab values, or medical knowledge?
- **Example of alignment**: Both agents specifically discuss "serum creatinine increase from 1.1 to 1.5 mg/dL"
- **Example of misalignment**: Agent A focuses on imaging findings while Agent B focuses on lab values

### 4. Specificity Level
Do both agents reason at the same level of specificity?
- **Example of alignment**: Both agents provide detailed pathophysiological mechanisms
- **Example of misalignment**: Agent A gives a brief summary while Agent B provides step-by-step clinical reasoning with specific medical facts

## What NOT to Judge

- **Answer correctness**: Both agents chose the same answer. Do not evaluate whether that answer is medically correct.
- **Writing quality**: Grammar, verbosity, and style differences are irrelevant. Focus on the medical content and reasoning logic.
- **Response format**: Some agents use a CLAIM/GROUND/STANCE structure, others use free text. Judge the reasoning content, not the format.
- **Step count**: More steps does not mean better reasoning. An agent with 3 highly specific steps may be more aligned with another 3-step agent than a 10-step agent that covers different ground.

## Worked Examples

### Example A: Score 5 (Near-identical)

**Question**: What is the most likely diagnosis for a patient with cyanosis and Fontan circulation?

**Agent A**:
1. The patient's new-onset cyanosis is likely due to a complication of Fontan circulation.
2. CT angiogram can visualize the Fontan pathway and identify thrombosis or stenosis.
3. A mean gradient of 3 mmHg through the Fontan conduit is not sufficient to explain the severe desaturation.

**Agent B**:
1. The patient's cyanosis and hypoxemia are likely due to a problem in the Fontan circulation.
2. CT angiogram can visualize the Fontan pathway and identify thrombosis or stenosis.
3. A mean gradient of 3 mmHg is not sufficient to explain the desaturation.

**Reasoning**: Both agents make the same three core claims in the same order, citing the same medical facts (Fontan complication, CT angiogram utility, gradient insufficiency). Only wording differs. **Score: 5.**

### Example B: Score 3 (Partially aligned)

**Question**: A patient presents with cough, weight loss, and works in a pet store. What histological finding is expected?

**Agent A**:
1. Exposure to birds suggests hypersensitivity pneumonitis.
2. The most characteristic finding is poorly formed granulomas.

**Agent B**:
1. The occupational history and BAL findings suggest an immune-mediated lung disease.
2. The HRCT findings of ground-glass opacities support a diagnosis of hypersensitivity pneumonitis.
3. The most characteristic finding is poorly formed granulomas with multinucleated giant cells.

**Reasoning**: Both agents conclude hypersensitivity pneumonitis and identify granulomas. However, Agent A focuses on the bird exposure as the key clue, while Agent B builds through BAL and HRCT findings — a different evidentiary pathway. They share the conclusion and final claim but not the full reasoning chain. **Score: 3.**

### Example C: Score 1 (Misaligned)

**Question**: What medication should be prescribed for a patient's condition?

**Agent A**:
1. The symptoms suggest a bacterial infection requiring antibiotic therapy.
2. First-line treatment is azithromycin based on typical pathogen coverage.

**Agent B**:
1. The clinical presentation is consistent with an inflammatory condition.
2. Anti-inflammatory therapy with NSAIDs is the initial approach.
3. Azithromycin is added for its anti-inflammatory properties, not its antibiotic effect.

**Reasoning**: Both agents arrive at azithromycin but for completely different reasons — Agent A treats it as an antibiotic for infection, Agent B treats it as an anti-inflammatory. These are contradictory medical rationales leading to the same prescription. **Score: 1.**

## Practical Instructions

1. **Read the question first** to understand the clinical context.
2. **Read Agent A's reasoning** completely before moving to Agent B.
3. **Read Agent B's reasoning** and mentally note overlaps and divergences with Agent A.
4. **Assign the alignment rating** based on the criteria above.
5. **Assign confidence** based on how clear the reasoning was.
6. **Add notes** if anything is particularly striking.

Expected time: **3–4 minutes per pair**, approximately **2.5–3 hours total** for 50 pairs. Please take breaks as needed to maintain judgment quality.

## Output Format

Please fill in the provided spreadsheet (annotation_sheet.tsv or equivalent) with:
- `alignment_rating`: integer 1–5
- `confidence`: integer 1–3
- `notes`: free text (optional)

Thank you for your time.

---

## Appendix: Technical Context (For Reference Only)

This annotation is part of the CARA (Cross-Agent Reasoning Alignment) project. CARA is an automated metric that:
1. Decomposes each agent's response into reasoning steps
2. Computes pairwise semantic similarity between steps using embeddings
3. Detects contradictions between steps using NLI (Natural Language Inference)
4. Produces a composite alignment score (CARA-HYB, range 0–1)

Your annotations will be used to compute the Spearman rank correlation between human alignment judgments and automated CARA-HYB scores. A strong positive correlation validates that CARA measures what it claims to measure.

The 50 pairs in this annotation set are stratified across low, medium, and high automated CARA scores to ensure coverage of the full score range. The system identity (which multi-agent framework produced the traces) and the automated CARA score are withheld from you during annotation to prevent bias.
