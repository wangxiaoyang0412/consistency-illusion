# CARA & GDP — Code and Data

Anonymous code release for the paper **"The Consistency Illusion: How
Multi-Agent Debate Hides Reasoning Misalignment"** (under review).

This repository contains the implementation of the CARA metric family,
the Grounded Debate Protocol (GDP), and all data needed to reproduce
the numerical results in the paper.

## Repository Layout

```
code/
  cara/          CARA-HYB / CARA-SIM / CARA-NLI implementation
                 (cara_hyb.py, nli_scorer.py, embedding_scorer.py,
                  step_decomposer.py, pipeline.py, cara_gt.py,
                  pipeline_gt.py, __init__.py)
  analysis/     Bootstrap CI and failure-mode classification scripts
                 (bootstrap_ci.py, extract_lowest_cara.py,
                  classify_failure_modes.py, extract_and_classify_d2.py)
  prompts/      M3 / GDP prompt builders and CARA-LLM judge invocation
                 (prompt_builder_m3.py, prompt_builder_gdp.py,
                  run_cara_llm.py)
data/
  cara_scores/  Per-question CARA scores for all (system, round, dataset,
                backbone) cells. JSONL with one record per question:
                question_id, cara_hyb, cara_sim, contradiction_rate,
                num_steps_per_agent, etc.
  cara_gt/      CARA-GT (agent-to-expert) scores on D2 MedThink-Bench.
  cara_llm/     GPT-4o head-to-head per-pair scores. Includes the system
                label per pair, enabling the M3-GDP vs M3 head-to-head
                reported in Section 7 of the paper.
  failure_modes/  Classified low-CARA correct-answer cases, with
                  taxonomy reports.
  annotation/   Human-expert validation: full guidelines, blank sheet,
                three per-annotator completed sheets.
```

## Reproducing Paper Results

All numerical claims rest on the JSONL files in `data/`. Scripts in
`code/analysis/` provide bootstrap CIs and failure-mode classification.
Other numbers (means, deltas, head-to-head comparisons) can be
recomputed in a few lines of Python from the JSONL data.

### Table 1 — Main CARA-HYB / SIM / CR per cell

Each `data/cara_scores/*.jsonl` file contains one record per question
with fields `cara_hyb`, `cara_sim`, `contradiction_rate`, plus system
and round identifiers. Compute the mean over records per cell.

### Figure 2 — Cohen's d forest plot (with 95% bootstrap CI)

```bash
python code/analysis/bootstrap_ci.py \
    --scores data/cara_scores/cara_scores_d1_n500.jsonl \
    --comparisons GDP_r1_vs_M3_r1,GDP_r1_vs_M4_r0,M3_r1_vs_M4_r0 \
    --B 10000 --seed 42
```

### Table 2 — Failure-mode taxonomy on the 50 lowest-CARA-HYB correct-answer cases

```bash
python code/analysis/extract_lowest_cara.py \
    --scores data/cara_scores/cara_scores_d1_n500.jsonl \
    --n 50
python code/analysis/classify_failure_modes.py \
    --cases data/failure_modes/classified_cases.jsonl
```

Pre-computed taxonomy reports are at
`data/failure_modes/taxonomy_report.md` (D1) and
`data/failure_modes/d2_taxonomy_report.md` (D2).

### Section 7 confound defense — GDP-r1 vs M3-r1 on CARA-LLM (GPT-4o judge)

The relevant data is `data/cara_llm/cara_llm_scores.jsonl`. Each record
has fields `system` ("M3" or "M3-GDP"), `pair_type` ("agreement" or
"disagreement"), and `cara_llm_score` (1–5, mean of 3 GPT-4o runs at
temperature 0). To reproduce the head-to-head:

```python
import json
from collections import defaultdict

data = [json.loads(line) for line in open(
    "data/cara_llm/cara_llm_scores.jsonl")]
agree = [d for d in data if d.get("pair_type") is None]
by_sys = defaultdict(list)
for d in agree:
    by_sys[d["system"]].append(d["cara_llm_score"])
print({k: (len(v), sum(v)/len(v)) for k, v in by_sys.items()})
# Expected: {'M3': (22, 4.500), 'M3-GDP': (28, 4.857)}
# d = +0.748, 95% bootstrap CI on Delta = [+0.084, +0.646]
```

**No OpenAI API key needed** — GPT-4o scores are pre-computed.

### Appendix C — CARA-GT per-cell on D2

Records in `data/cara_gt/cara_gt_d2_n499.jsonl` include `system`,
`round`, `cara_gt_hyb`, and `expert_coverage`. Compute the mean per
cell and Cohen's d between cells using `code/analysis/bootstrap_ci.py`.

### Appendix G — Annotation IAA and correlations

The three per-annotator scored sheets in `data/annotation/` contain
columns `pair_id`, `alignment_rating` (1–5), `confidence` (1–3),
`notes`. Pairwise Spearman correlation between annotators reproduces
the inter-annotator agreement reported in Appendix G Table 7.

## Environment

- Python ≥ 3.11
- Key packages (see `requirements.txt` for pinned versions):
  - `torch`, `transformers`, `sentence-transformers` (CARA pipeline)
  - `numpy`, `scipy` (statistics)
  - `openai` (only for re-running CARA-LLM; not needed for reproducing
    numbers from pre-computed scores)
  - `tqdm`, `pandas`

## Model Checkpoints Used

- **NLI**: DeBERTa-v3-large fine-tuned on MNLI/FEVER/ANLI/LingNLI/WANLI
  (Laurer et al. 2024).
  HuggingFace ID: `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli`
- **Embeddings**: Stella-EN-1.5B-v5 (Zhang et al. 2024).
  HuggingFace ID: `dunzhang/stella_en_1.5B_v5`
- **LLM judge**: GPT-4o via OpenAI API
  (`gpt-4o-2024-08-06`, temperature 0.0, three runs averaged).
- **Agent backbones** (used to generate the traces underlying our
  `cara_scores/*.jsonl` files):
  - Qwen 2.5 72B Instruct AWQ
  - Llama 3.3 70B Instruct AWQ

## Datasets

The CARA score files (`data/cara_scores/*.jsonl`, `data/cara_gt/*.jsonl`,
`data/failure_modes/*.jsonl`) reference questions only by their original
`question_id`; raw question text is **not** included in those files. To
recover the raw text for full-scale reproduction, download the benchmarks
from their original releases:

- **MedQA-USMLE**: https://github.com/jind11/MedQA (Jin et al. 2020)
- **MedThink-Bench**: see Jiang et al. 2025 (https://arxiv.org/abs/2507.07988)

The annotation materials (`data/annotation/annotation_booklet.md`) do
contain the full text of the 50 questions used in the human-expert
validation, presented to annotators alongside the two agents' reasoning
steps. This subset is included as documentation of the annotation task;
it is not a redistribution of the full benchmarks.

## Note for Reviewers

All numerical claims in the paper can be reproduced from the JSONL
files in `data/` using the scripts in `code/analysis/` and a few lines
of Python (as shown in the snippet above for the CARA-LLM
head-to-head). The actual agent inference (which produced these JSONL
files) requires GPU resources and the open-weight LLMs noted above;
the inference code is included in `code/cara/` and `code/prompts/` for
inspection, but reviewers are **not** expected to re-run it.

## License

MIT (see `LICENSE`).
