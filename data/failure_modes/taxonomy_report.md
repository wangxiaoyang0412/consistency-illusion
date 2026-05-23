# Failure Mode Taxonomy — D1 N=500 GDP_r1 (50 Lowest-CARA Correct Cases)

## 1. Distribution

| Code | Category | Count | % |
|------|----------|-------|---|
| FM6 | Partial Overlap | 31 | 62% |
| FM3 | Contradictory Premises | 12 | 24% |
| FM2 | Granularity Mismatch | 5 | 10% |
| FM2+FM3 | Granularity Mismatch + Contradictory Premises | 2 | 4% |
| **Total** | | **50** | **100%** |

## 2. Category Definitions

### FM2: Granularity Mismatch

One agent produces significantly more detailed reasoning than another (step count ratio >2x). The embedding similarity is lowered primarily by the granularity difference rather than substantive disagreement. This is an artifact of response verbosity differences rather than genuine reasoning misalignment.

**Representative examples** (5 cases):

- **MQA_0336** (Rank 1, HYB=0.7901, CR=0.00): Granularity mismatch: step ratio 3.0x (3 vs 9 steps), CR=0.00 (low)
- **MQA_0975** (Rank 5, HYB=0.8889, CR=0.17): Granularity mismatch: step ratio 3.0x (4 vs 12 steps), CR=0.17 (low)
- **MQA_1011** (Rank 7, HYB=0.8918, CR=0.07): Granularity mismatch: step ratio 3.0x (7 vs 21 steps), CR=0.07 (low)

### FM2+FM3: Granularity Mismatch + Contradictory Premises

Combination of granularity mismatch and contradictory premises. Agents differ in both reasoning depth and substance, with some steps directly contradicting each other.

**Representative examples** (2 cases):

- **MQA_0014** (Rank 8, HYB=0.8955, CR=0.59): Both granularity mismatch (step ratio 3.0x) and contradictory premises (CR=0.59)
- **MQA_1156** (Rank 9, HYB=0.8991, CR=0.98): Both granularity mismatch (step ratio 3.4x) and contradictory premises (CR=0.98)

### FM3: Contradictory Premises

Agents cite contradictory medical facts, mechanisms, or clinical interpretations but still converge on the same answer. High contradiction rate (CR >0.3) indicates NLI-detected logical conflicts between reasoning steps. This is the most clinically concerning failure mode — correct answers may be reached for partially wrong reasons.

**Representative examples** (12 cases):

- **MQA_0790** (Rank 2, HYB=0.8245, CR=3.08): Contradictory premises: CR=3.08, 80 contradictions, steps balanced (11/15)
- **MQA_0045** (Rank 3, HYB=0.8626, CR=1.14): Contradictory premises: CR=1.14, 48 contradictions, steps balanced (8/7/6)
- **MQA_0078** (Rank 4, HYB=0.8646, CR=0.45): Contradictory premises: CR=0.45, 5 contradictions, steps balanced (5/6)

### FM6: Partial Overlap

Agents share some reasoning steps but diverge on others, producing moderate alignment scores without extreme CR or SIM values. This is the baseline misalignment mode — partial but not complete reasoning overlap.

**Representative examples** (31 cases):

- **MQA_0058** (Rank 12, HYB=0.9073, CR=0.11): Partial overlap: moderate misalignment (HYB=0.9073, SIM=0.828, CR=0.11, steps 8/7/7)
- **MQA_1098** (Rank 15, HYB=0.9087, CR=0.00): Partial overlap: moderate misalignment (HYB=0.9087, SIM=0.817, CR=0.00, steps 4/4/4)
- **MQA_0980** (Rank 16, HYB=0.9098, CR=0.20): Partial overlap: moderate misalignment (HYB=0.9098, SIM=0.830, CR=0.20, steps 8/7/7)

## 3. Quantitative Profiles

| Category | N | Mean HYB | Mean CR | Mean SIM | Mean Step Ratio | Mean Steps |
|----------|---|----------|---------|----------|----------------|------------|
| FM6 (Partial Overlap) | 31 | 0.9267 | 0.06 | 0.861 | 1.2x | 6.3 |
| FM3 (Contradictory Premises) | 12 | 0.8964 | 0.83 | 0.877 | 1.4x | 6.8 |
| FM2 (Granularity Mismatch) | 5 | 0.8781 | 0.11 | 0.773 | 2.9x | 7.6 |
| FM2+FM3 (Granularity Mismatch + Contradictory Premises) | 2 | 0.8973 | 0.78 | 0.796 | 3.2x | 13.2 |

## 4. Cross-System View

For the same 50 questions, how do M3_r1 and M4_r0 compare?

| Category | GDP_r1 Mean | M3_r1 Mean (avail) | M4_r0 Mean |
|----------|-------------|---------------------|------------|
| FM6 | 0.9267 | 0.8854 (N=31) | 0.8865 (N=31) |
| FM3 | 0.8964 | 0.8949 (N=11) | 0.9020 (N=12) |
| FM2 | 0.8781 | 0.9187 (N=5) | 0.8644 (N=5) |
| FM2+FM3 | 0.8973 | 0.8736 (N=1) | 0.9103 (N=2) |

## 5. Difficulty Stratification

| Category | Step1 | Step2&3 |
|----------|-------|---------|
| FM6 | 9 | 22 |
| FM3 | 10 | 2 |
| FM2 | 2 | 3 |
| FM2+FM3 | 1 | 1 |

## 6. Full Case List

| Rank | QID | HYB | CR | SIM | Steps | Agree | FM | Notes |
|------|-----|-----|-----|-----|-------|-------|-----|-------|
| 1 | MQA_0336 | 0.7901 | 0.00 | 0.580 | 3/9 | 2 | FM2 | Granularity mismatch: step ratio 3.0x (3 vs 9 steps), CR=0.0... |
| 2 | MQA_0790 | 0.8245 | 3.08 | 0.841 | 11/15 | 2 | FM3 | Contradictory premises: CR=3.08, 80 contradictions, steps ba... |
| 3 | MQA_0045 | 0.8626 | 1.14 | 0.887 | 8/7/6 | 3 | FM3 | Contradictory premises: CR=1.14, 48 contradictions, steps ba... |
| 4 | MQA_0078 | 0.8646 | 0.45 | 0.884 | 5/6 | 2 | FM3 | Contradictory premises: CR=0.45, 5 contradictions, steps bal... |
| 5 | MQA_0975 | 0.8889 | 0.17 | 0.789 | 4/12/4 | 3 | FM2 | Granularity mismatch: step ratio 3.0x (4 vs 12 steps), CR=0.... |
| 6 | MQA_0313 | 0.8896 | 0.39 | 0.788 | 5/5/9 | 3 | FM3 | Contradictory premises: CR=0.39, 15 contradictions, steps ba... |
| 7 | MQA_1011 | 0.8918 | 0.07 | 0.784 | 21/7/8 | 3 | FM2 | Granularity mismatch: step ratio 3.0x (7 vs 21 steps), CR=0.... |
| 8 | MQA_0014 | 0.8955 | 0.59 | 0.794 | 15/5/15 | 3 | FM2+FM3 | Both granularity mismatch (step ratio 3.0x) and contradictor... |
| 9 | MQA_1156 | 0.8991 | 0.98 | 0.799 | 8/9/27 | 3 | FM2+FM3 | Both granularity mismatch (step ratio 3.4x) and contradictor... |
| 10 | MQA_0447 | 0.9039 | 0.44 | 0.911 | 5/6/6 | 3 | FM3 | Contradictory premises: CR=0.44, 15 contradictions, steps ba... |
| 11 | MQA_1045 | 0.9050 | 1.24 | 0.898 | 7/6/8 | 3 | FM3 | Contradictory premises: CR=1.24, 52 contradictions, steps ba... |
| 12 | MQA_0058 | 0.9073 | 0.11 | 0.828 | 8/7/7 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9073, SIM=0.82... |
| 13 | MQA_0847 | 0.9083 | 0.02 | 0.817 | 12/5/4 | 3 | FM2 | Granularity mismatch: step ratio 3.0x (4 vs 12 steps), CR=0.... |
| 14 | MQA_0465 | 0.9086 | 0.53 | 0.883 | 6/6/6 | 3 | FM3 | Contradictory premises: CR=0.53, 19 contradictions, steps ba... |
| 15 | MQA_1098 | 0.9087 | 0.00 | 0.817 | 4/4/4 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9087, SIM=0.81... |
| 16 | MQA_0980 | 0.9098 | 0.20 | 0.830 | 8/7/7 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9098, SIM=0.83... |
| 17 | MQA_1213 | 0.9106 | 0.71 | 0.931 | 8/8/5 | 3 | FM3 | Contradictory premises: CR=0.71, 30 contradictions, steps ba... |
| 18 | MQA_0431 | 0.9113 | 0.05 | 0.845 | 6/7/7 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9113, SIM=0.84... |
| 19 | MQA_0901 | 0.9116 | 0.29 | 0.895 | 9/4/4 | 3 | FM2 | Granularity mismatch: step ratio 2.2x (4 vs 9 steps), CR=0.2... |
| 20 | MQA_1155 | 0.9139 | 0.53 | 0.854 | 7/4/5 | 3 | FM3 | Contradictory premises: CR=0.53, 17 contradictions, steps ba... |
| 21 | MQA_0387 | 0.9198 | 0.00 | 0.840 | 8/7/7 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9198, SIM=0.84... |
| 22 | MQA_0771 | 0.9210 | 0.59 | 0.873 | 6/9/8 | 3 | FM3 | Contradictory premises: CR=0.59, 27 contradictions, steps ba... |
| 23 | MQA_0669 | 0.9211 | 0.02 | 0.844 | 7/7/7 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9211, SIM=0.84... |
| 24 | MQA_0752 | 0.9214 | 0.46 | 0.862 | 7/7/9 | 3 | FM3 | Contradictory premises: CR=0.46, 21 contradictions, steps ba... |
| 25 | MQA_0666 | 0.9216 | 0.17 | 0.883 | 5/5/5 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9216, SIM=0.88... |
| 26 | MQA_0276 | 0.9223 | 0.30 | 0.894 | 9/7/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9223, SIM=0.89... |
| 27 | MQA_1109 | 0.9229 | 0.22 | 0.863 | 8/5/5 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9229, SIM=0.86... |
| 28 | MQA_0253 | 0.9237 | 0.00 | 0.847 | 7/6/8 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9237, SIM=0.84... |
| 29 | MQA_1252 | 0.9238 | 0.00 | 0.848 | 4/4/4 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9238, SIM=0.84... |
| 30 | MQA_0954 | 0.9243 | 0.00 | 0.849 | 4/4/4 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9243, SIM=0.84... |
| 31 | MQA_0109 | 0.9272 | 0.00 | 0.854 | 5/6/8 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9272, SIM=0.85... |
| 32 | MQA_0353 | 0.9275 | 0.00 | 0.855 | 6/7/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9275, SIM=0.85... |
| 33 | MQA_0592 | 0.9285 | 0.19 | 0.869 | 5/5/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9285, SIM=0.86... |
| 34 | MQA_0395 | 0.9287 | 0.00 | 0.857 | 6/6/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9287, SIM=0.85... |
| 35 | MQA_0195 | 0.9288 | 0.00 | 0.858 | 6/5/5 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9288, SIM=0.85... |
| 36 | MQA_0386 | 0.9294 | 0.26 | 0.887 | 7/7/7 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9294, SIM=0.88... |
| 37 | MQA_0767 | 0.9314 | 0.00 | 0.863 | 8/10/8 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9314, SIM=0.86... |
| 38 | MQA_0904 | 0.9315 | 0.36 | 0.917 | 4/5/5 | 3 | FM3 | Contradictory premises: CR=0.36, 10 contradictions, steps ba... |
| 39 | MQA_0759 | 0.9323 | 0.00 | 0.865 | 4/6/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9323, SIM=0.86... |
| 40 | MQA_0215 | 0.9327 | 0.00 | 0.865 | 10/6/5 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9327, SIM=0.86... |
| 41 | MQA_1149 | 0.9332 | 0.00 | 0.866 | 5/4/4 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9332, SIM=0.86... |
| 42 | MQA_1056 | 0.9337 | 0.00 | 0.867 | 5/4/4 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9337, SIM=0.86... |
| 43 | MQA_1093 | 0.9337 | 0.11 | 0.888 | 11/10/10 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9337, SIM=0.88... |
| 44 | MQA_1201 | 0.9338 | 0.00 | 0.868 | 5/5/5 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9338, SIM=0.86... |
| 45 | MQA_1267 | 0.9340 | 0.00 | 0.868 | 7/5/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9340, SIM=0.86... |
| 46 | MQA_0557 | 0.9347 | 0.00 | 0.869 | 6/7/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9347, SIM=0.86... |
| 47 | MQA_0108 | 0.9350 | 0.00 | 0.870 | 6/7/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9350, SIM=0.87... |
| 48 | MQA_0393 | 0.9350 | 0.03 | 0.883 | 7/7/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9350, SIM=0.88... |
| 49 | MQA_0611 | 0.9351 | 0.04 | 0.870 | 5/9/10 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9351, SIM=0.87... |
| 50 | MQA_1057 | 0.9353 | 0.03 | 0.871 | 7/7/6 | 3 | FM6 | Partial overlap: moderate misalignment (HYB=0.9353, SIM=0.87... |

---

*Classification method: Heuristic rules on CARA sub-metrics (CR, SIM, step ratio). Manual verification recommended for paper.*
*Source: `lowest_cara_cases.jsonl` → `classified_cases.jsonl`*
