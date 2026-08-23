# The Consistency Illusion: How Multi-Agent Debate Hides Reasoning Misalignment

[![EMNLP 2026](https://img.shields.io/badge/EMNLP%202026-Main%20Conference-red)](https://2026.emnlp.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)

Official code and data for the EMNLP 2026 Main Conference paper:

> **The Consistency Illusion: How Multi-Agent Debate Hides Reasoning Misalignment**
> Xiaoyang Wang, Christopher Yang
> *Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing (EMNLP), Budapest, Hungary.*

Multi-agent LLM systems for medical QA treat answer consensus as a reliability signal — but agents can agree on an answer while reasoning in mutually incompatible ways. We introduce **CARA** (Cross-Agent Reasoning Alignment) to measure this, identify the **consistency illusion** (debate suppresses visible contradictions while reasoning similarity *drops*), and propose the **Grounded Debate Protocol (GDP)**, a prompt-level fix that repairs alignment without adding LLM calls.

## Headline results

| Finding | D1 MedQA (Qwen) | D2 MedThink (Qwen) | D2 MedThink (Llama-3) |
|---|---|---|---|
| Consistency illusion (M3 r1 vs. M4, Cohen's *d*) | −0.08 (ns) | **−0.30** | **−1.32** |
| GDP alignment gain (GDP r1 vs. M3 r1, Cohen's *d*) | **+1.43** | **+1.62** | **+1.99** |
| GDP expert-coverage recovery (CARA-GT, D2) | — | 80.2% → **85.6%** | — |

All effects replicate across two datasets and two open-weight 70B backbones; GDP adds zero LLM calls.

## Repository layout

```
code/
  cara/                      CARA-HYB / CARA-SIM / CARA-NLI implementation
                             (step decomposition, NLI scorer, embedding scorer,
                              pipeline, CARA-GT, label-stripping utilities)
  analysis/                  Bootstrap CIs, failure-mode classification,
                             flip decomposition, label-strip comparison
  prompts/                   M3 / GDP prompt builders, CARA-LLM judge invocation
data/
  cara_scores/               Per-question CARA scores for every
                             (system, round, dataset, backbone) cell, incl.
                             label-stripped variants
  cara_gt/                   Agent-to-expert alignment scores (D2)
  cara_llm/                  GPT-4o judge per-pair scores (pre-computed;
                             no API key needed)
  accuracy/                  Majority-vote accuracy + McNemar report
  ablation_e1/               Generic-structure & anti-sycophancy control arms
                             (Appendix G)
  segmentation_sensitivity/  Alternative step-segmentation runs (Appendix E)
  flip_analysis/             Per-question answer-change decomposition
                             (Appendix L)
  failure_modes/             Classified low-CARA cases + taxonomy reports
  annotation/                Human-expert validation: guidelines, blank sheet,
                             three completed per-annotator sheets (Appendix H)
```

## Installation

```bash
git clone https://github.com/wangxiaoyang0412/consistency-illusion-code
cd consistency-illusion-code
pip install -r requirements.txt   # Python >= 3.11
```

Reproducing the paper's numbers needs **no GPU and no API keys** — all CARA, CARA-GT, and GPT-4o judge scores are released pre-computed. The GPU-backed pipeline (`code/cara/`) is included for running CARA on new traces (~9,000 traces/hour on one RTX 4090).

## Reproducing paper results

Every numerical claim rests on the JSONL files in `data/`. The map below links each paper artifact to its data and script.

| Paper artifact | Data | Script / method |
|---|---|---|
| Table 1 (CARA-HYB/SIM/CR per cell) | `data/cara_scores/*.jsonl` | mean per (system, round) cell |
| Figure 2 (Cohen's *d* + 95% CI) | `data/cara_scores/` | `code/analysis/bootstrap_ci.py --B 10000 --seed 42` |
| Table 2 (failure-mode taxonomy) | `data/failure_modes/` | `code/analysis/classify_failure_modes.py`; reports pre-computed |
| §7 GPT-4o head-to-head (4.86 vs. 4.50) | `data/cara_llm/cara_llm_scores.jsonl` | snippet in `data/cara_llm/` records; agreement-set pairs only |
| Appendix C (CARA-GT, expert coverage) | `data/cara_gt/cara_gt_d2_n499.jsonl` | mean per cell + `bootstrap_ci.py` |
| Appendix D (accuracy, McNemar) | `data/accuracy/accuracy_report.md` | pre-computed report (B=10,000, seed 42) |
| Appendix E (parsing rate, segmentation stability) | `data/segmentation_sensitivity/` | `segsens_report.md` + per-strategy score files |
| Appendix G (label-stripping ~90% survives) | `data/cara_scores/cara_scores_labelstripped_*.jsonl` | `code/analysis/compare_labelstripped.py` |
| Appendix G (generic-structure / anti-sycophancy arms) | `data/ablation_e1/` | `e1_ablation_report.md` + `cara_scores_e1.jsonl` |
| Appendix H (annotation IAA, Spearman 0.93–0.99) | `data/annotation/` | pairwise Spearman over the three scored sheets |
| Appendix L (answer-change 2×2 decomposition) | `data/flip_analysis/` | `python code/analysis/flip_decomposition.py` |

Example — the Appendix L decomposition:

```bash
$ python code/analysis/flip_decomposition.py
total correct->incorrect flips (M3 r1 -> GDP r1, D1): 31
flagged by the two D1-checkable signals: 14/31 (45%)
...
strictest residual scenario (unflagged, survives r0, overturned in debate): 5/31
```

## Datasets

We do **not** redistribute the underlying QA datasets. Obtain them from their original sources:
- **MedQA-USMLE**: [github.com/jind11/MedQA](https://github.com/jind11/MedQA) (Jin et al., 2021)
- **MedThink-Bench**: per Zhou et al. (2025), *npj Digital Medicine* — see the paper's data availability

The released JSONL files contain only derived per-question scores keyed by question ID, plus model-generated reasoning fragments used in the human-annotation study (no patient data; see the paper's Ethics Statement).

## Citation

```bibtex
@inproceedings{wang2026consistency,
  title     = {The Consistency Illusion: How Multi-Agent Debate Hides Reasoning Misalignment},
  author    = {Wang, Xiaoyang and Yang, Christopher},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing (EMNLP)},
  year      = {2026},
  address   = {Budapest, Hungary},
  publisher = {Association for Computational Linguistics}
}
```

## Acknowledgments

This work was supported in part by the National Science Foundation under IIS-2235548, and by the Department of Defense under Grant DoD W91XWH-05-1-023.

## Contact

Xiaoyang Wang — wangxiaoyang0412@gmail.com
Issues and questions welcome via GitHub Issues.
