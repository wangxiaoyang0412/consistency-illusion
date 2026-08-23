# Accuracy Report

- **Bootstrap iterations**: 10000
- **CI level**: 95%
- **Method**: Paired percentile bootstrap + McNemar test (continuity-corrected)
- **Seed**: 42

## 1. D1 MedQA (N=500, Qwen 2.5 72B)

  Gold answers loaded: 500 questions
  Loaded M4: 1500 traces from raw_traces.jsonl
  Loaded M3: 3000 traces from raw_traces.jsonl
  Loaded M3-GDP: 3000 traces from raw_traces.jsonl

### Majority-Vote Accuracy

| Cell | MV Accuracy | N (questions) | Per-Agent Acc | N (agents) |
|------|------------|---------------|--------------|------------|
| M4_r0 | 0.8380 (83.8%) | 500 | 0.8247 (82.5%) | 1500 |
| M3_r0 | 0.8300 (83.0%) | 500 | 0.8220 (82.2%) | 1500 |
| M3_r1 | 0.8420 (84.2%) | 500 | 0.8393 (83.9%) | 1500 |
| M3-GDP_r0 | 0.8180 (81.8%) | 500 | 0.8023 (80.2%) | 1497 |
| M3-GDP_r1 | 0.8140 (81.4%) | 500 | 0.8105 (81.1%) | 1499 |

### Pairwise Accuracy Comparisons (McNemar + Bootstrap CI)

| Comparison | Δ Acc | 95% CI(Δ) | McNemar χ² | p-value | b (A+B-) | c (A-B+) |
|------------|-------|-----------|------------|---------|----------|----------|
| GDP_r1 vs M3_r1 (debate effect of GDP) | -0.0280 | [-0.0540, -0.0020] | 3.521 | 0.0606 (ns) | 17 | 31 |
| GDP_r1 vs M4_r0 (GDP debate vs no debate) | -0.0240 | [-0.0500, +0.0020] | 2.750 | 0.0973 (ns) | 16 | 28 |
| M3_r1 vs M4_r0 (standard debate vs no debate) | +0.0040 | [-0.0180, +0.0260] | 0.033 | 0.8551 (ns) | 16 | 14 |
| GDP_r0 vs M3_r0 (format effect, pre-debate) | -0.0120 | [-0.0380, +0.0140] | 0.521 | 0.4705 (ns) | 21 | 27 |

**Debate Delta (M3):** +0.0040 (+0.4%)
**Debate Delta (GDP):** -0.0240 (-2.4%)

## 2. D2 MedThink-Bench (N=499, Qwen 2.5 72B)

  Gold answers loaded: 499 questions
  Loaded M4: 1497 traces from raw_traces.jsonl
  Loaded M3: 2994 traces from raw_traces.jsonl
  Loaded M3-GDP: 2994 traces from raw_traces.jsonl

### Majority-Vote Accuracy

| Cell | MV Accuracy | N (questions) | Per-Agent Acc | N (agents) |
|------|------------|---------------|--------------|------------|
| M4_r0 | 0.4148 (41.5%) | 499 | 0.4035 (40.3%) | 1497 |
| M3_r0 | 0.3988 (39.9%) | 499 | 0.4008 (40.1%) | 1497 |
| M3_r1 | 0.4148 (41.5%) | 499 | 0.4175 (41.8%) | 1497 |
| M3-GDP_r0 | 0.3888 (38.9%) | 499 | 0.3821 (38.2%) | 1497 |
| M3-GDP_r1 | 0.3908 (39.1%) | 499 | 0.3881 (38.8%) | 1497 |

### Pairwise Accuracy Comparisons (McNemar + Bootstrap CI)

| Comparison | Δ Acc | 95% CI(Δ) | McNemar χ² | p-value | b (A+B-) | c (A-B+) |
|------------|-------|-----------|------------|---------|----------|----------|
| GDP_r1 vs M3_r1 (debate effect of GDP) | -0.0240 | [-0.0541, +0.0060] | 2.017 | 0.1556 (ns) | 24 | 36 |
| GDP_r1 vs M4_r0 (GDP debate vs no debate) | -0.0240 | [-0.0561, +0.0060] | 1.952 | 0.1624 (ns) | 25 | 37 |
| M3_r1 vs M4_r0 (standard debate vs no debate) | +0.0000 | [-0.0301, +0.0301] | 0.016 | 0.8989 (ns) | 31 | 31 |
| GDP_r0 vs M3_r0 (format effect, pre-debate) | -0.0100 | [-0.0421, +0.0200] | 0.254 | 0.6143 (ns) | 29 | 34 |

**Debate Delta (M3):** +0.0000 (+0.0%)
**Debate Delta (GDP):** -0.0240 (-2.4%)

## 3. D2 MedThink-Bench (N=100, Llama 3.3 70B)

  Gold answers loaded: 499 questions (filtering to Llama trace coverage)
  Loaded M4: 300 traces from raw_traces.jsonl
  Loaded M3: 600 traces from raw_traces.jsonl
  Loaded M3-GDP: 600 traces from raw_traces.jsonl

### Majority-Vote Accuracy

| Cell | MV Accuracy | N (questions) | Per-Agent Acc | N (agents) |
|------|------------|---------------|--------------|------------|
| M4_r0 | 0.4900 (49.0%) | 100 | 0.4700 (47.0%) | 300 |
| M3_r0 | 0.4700 (47.0%) | 100 | 0.4567 (45.7%) | 300 |
| M3_r1 | 0.4700 (47.0%) | 100 | 0.4567 (45.7%) | 300 |
| M3-GDP_r0 | 0.4200 (42.0%) | 100 | 0.4267 (42.7%) | 300 |
| M3-GDP_r1 | 0.4300 (43.0%) | 100 | 0.4267 (42.7%) | 300 |

### Pairwise Accuracy Comparisons (McNemar + Bootstrap CI)

| Comparison | Δ Acc | 95% CI(Δ) | McNemar χ² | p-value | b (A+B-) | c (A-B+) |
|------------|-------|-----------|------------|---------|----------|----------|
| GDP_r1 vs M3_r1 (debate effect of GDP) | -0.0400 | [-0.1000, +0.0100] | 1.125 | 0.2888 (ns) | 2 | 6 |
| GDP_r1 vs M4_r0 (GDP debate vs no debate) | -0.0600 | [-0.1200, -0.0100] | 3.125 | 0.0771 (ns) | 1 | 7 |
| M3_r1 vs M4_r0 (standard debate vs no debate) | -0.0200 | [-0.0800, +0.0300] | 0.125 | 0.7237 (ns) | 3 | 5 |
| GDP_r0 vs M3_r0 (format effect, pre-debate) | -0.0500 | [-0.1000, +0.0000] | 2.286 | 0.1306 (ns) | 1 | 6 |

**Debate Delta (M3):** -0.0200 (-2.0%)
**Debate Delta (GDP):** -0.0600 (-6.0%)

## 4. Paper-Ready Summary

| Dataset | Backbone | System | MV Accuracy | Debate Delta |
|---------|----------|--------|-------------|-------------|
| D1 MedQA (N=500) | Qwen 2.5 72B | M4_r0 | 0.8380 (83.8%) | — |
| D1 MedQA (N=500) | Qwen 2.5 72B | M3_r0 | 0.8300 (83.0%) | — |
| D1 MedQA (N=500) | Qwen 2.5 72B | M3_r1 | 0.8420 (84.2%) | +0.0040 |
| D1 MedQA (N=500) | Qwen 2.5 72B | M3-GDP_r0 | 0.8180 (81.8%) | — |
| D1 MedQA (N=500) | Qwen 2.5 72B | M3-GDP_r1 | 0.8140 (81.4%) | -0.0240 |
| D2 MedThink (N=499) | Qwen 2.5 72B | M4_r0 | 0.4148 (41.5%) | — |
| D2 MedThink (N=499) | Qwen 2.5 72B | M3_r0 | 0.3988 (39.9%) | — |
| D2 MedThink (N=499) | Qwen 2.5 72B | M3_r1 | 0.4148 (41.5%) | +0.0000 |
| D2 MedThink (N=499) | Qwen 2.5 72B | M3-GDP_r0 | 0.3888 (38.9%) | — |
| D2 MedThink (N=499) | Qwen 2.5 72B | M3-GDP_r1 | 0.3908 (39.1%) | -0.0240 |
| D2 MedThink (N=100) | Llama 3.3 70B | M4_r0 | 0.4900 (49.0%) | — |
| D2 MedThink (N=100) | Llama 3.3 70B | M3_r0 | 0.4700 (47.0%) | — |
| D2 MedThink (N=100) | Llama 3.3 70B | M3_r1 | 0.4700 (47.0%) | -0.0200 |
| D2 MedThink (N=100) | Llama 3.3 70B | M3-GDP_r0 | 0.4200 (42.0%) | — |
| D2 MedThink (N=100) | Llama 3.3 70B | M3-GDP_r1 | 0.4300 (43.0%) | -0.0600 |

---
*Generated by accuracy_report.py, seed=42, B=10000.*