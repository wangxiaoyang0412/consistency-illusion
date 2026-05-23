# D2 Failure Mode Taxonomy — MedThink-Bench N=499

## 1. GDP_r1 Distribution (D2)

| Code | Category | D2 Count | D2 % | D1 Count | D1 % |
|------|----------|----------|------|----------|------|
| FM2 | Granularity Mismatch | 2 | 4% | 5 | 10% |
| FM2+FM3 | Granularity + Contradictory | 1 | 2% | 2 | 4% |
| FM3 | Contradictory Premises | 15 | 30% | 12 | 24% |
| FM6 | Partial Overlap | 32 | 64% | 31 | 62% |
| **Total** | | **50** | **100%** | **50** | **100%** |

## 2. M3_r1 Distribution (D2)

| Code | Category | D2 Count | D2 % | D1 Count | D1 % |
|------|----------|----------|------|----------|------|
| FM1 | Complementary Reasoning | 18 | 36% | 23 | 46% |
| FM2 | Granularity Mismatch | 15 | 30% | 12 | 24% |
| FM3 | Contradictory Premises | 1 | 2% | 2 | 4% |
| FM4 | Sycophantic Convergence | 15 | 30% | 11 | 22% |
| FM5 | Terminology Divergence | 1 | 2% | 2 | 4% |
| **Total** | | **50** | **100%** | **50** | **100%** |

## 3. GDP Elimination Effect (D2 vs D1)

Key comparisons — does GDP eliminate the same failure modes on D2?

| Pattern | D1 | D2 | Replicates? |
|---------|----|----|-------------|
| FM4 in M3 vs GDP | M3: 11/50 → GDP: 0/50 | M3: 15/50 → GDP: 0/50 | YES |
| FM1 in M3 vs GDP | M3: 23/50 → GDP: 0/50 | M3: 18/50 → GDP: 0/50 | YES |
| FM6 dominates GDP | D1: 31/50 (62%) | D2: 32/50 (64%) | YES |

## 4. Difficulty Stratification (D2)

MedThink-Bench uses QA_Type instead of MedQA's step1/step2&3.

### GDP_r1 bottom 50 by QA_Type

| QA_Type | Count | FM distribution |
|---------|-------|-----------------|
| Disease Diagnosis | 12 | FM6=10, FM3=2 |
| Pharmacology | 7 | FM6=3, FM3=2, FM2+FM3=1, FM2=1 |
| Public Health & Etiology & Risk Factors & Prevention & Epidemiology | 6 | FM6=3, FM3=2, FM2=1 |
| Treatment | 6 | FM6=5, FM3=1 |
| Patient Information collection & Diagnostic Workup | 4 | FM3=2, FM6=2 |
| Pathophysiology | 4 | FM3=2, FM6=2 |
| Anatomy & Physiology | 3 | FM3=2, FM6=1 |
| Policy & Ethics & Legal Question | 3 | FM6=2, FM3=1 |
| Patient Management & Discharge Planning | 3 | FM6=3 |
| Prognosis and Outcomes | 2 | FM3=1, FM6=1 |

### M3_r1 bottom 50 by QA_Type

| QA_Type | Count | FM distribution |
|---------|-------|-----------------|
| Pharmacology | 9 | FM4=5, FM1=2, FM2=2 |
| Policy & Ethics & Legal Question | 7 | FM1=5, FM2=1, FM4=1 |
| Disease Diagnosis | 7 | FM1=5, FM4=1, FM2=1 |
| Anatomy & Physiology | 6 | FM4=3, FM2=1, FM3=1, FM1=1 |
| Treatment | 6 | FM1=3, FM2=2, FM4=1 |
| Patient Information collection & Diagnostic Workup | 5 | FM2=3, FM1=2 |
| Pathophysiology | 4 | FM4=2, FM2=2 |
| Patient Management & Discharge Planning | 3 | FM2=3 |
| Public Health & Etiology & Risk Factors & Prevention & Epidemiology | 2 | FM4=2 |
| Prognosis and Outcomes | 1 | FM5=1 |

## 5. Quantitative Profiles (D2 GDP_r1)

| Category | N | Mean HYB | Mean CR | Mean SIM | Mean Step Ratio |
|----------|---|----------|---------|----------|-----------------|
| FM6 (Partial Overlap) | 32 | 0.9351 | 0.04 | 0.873 | 1.4x |
| FM3 (Contradictory Premises) | 15 | 0.9163 | 0.65 | 0.903 | 1.3x |
| FM2 (Granularity Mismatch) | 2 | 0.9091 | 0.12 | 0.818 | 3.0x |
| FM2+FM3 (Granularity + Contradictory) | 1 | 0.9313 | 1.40 | 0.895 | 2.2x |

## 6. Full Case List (D2 GDP_r1)

| Rank | QID | HYB | CR | SIM | Steps | FM | QA_Type |
|------|-----|-----|-----|-----|-------|-----|---------|
| 1 | MTB_035 | 0.8530 | 0.57 | 0.886 | 4/5/5 | FM3 | Patient Information collection |
| 2 | MTB_140 | 0.8560 | 0.83 | 0.829 | 5/7 | FM3 | Pharmacology |
| 3 | MTB_438 | 0.8832 | 0.17 | 0.766 | 6/11/18 | FM2 | Public Health & Etiology & Ris |
| 4 | MTB_304 | 0.9052 | 1.13 | 0.973 | 5/7/7 | FM3 | Anatomy & Physiology |
| 5 | MTB_238 | 0.9133 | 0.68 | 0.828 | 9/12/10 | FM3 | Policy & Ethics & Legal Questi |
| 6 | MTB_443 | 0.9148 | 0.14 | 0.833 | 8/6/8 | FM6 | Public Health & Etiology & Ris |
| 7 | MTB_459 | 0.9189 | 0.42 | 0.905 | 10/10/10 | FM3 | Pathophysiology |
| 8 | MTB_019 | 0.9221 | 0.00 | 0.844 | 5/6/7 | FM6 | Patient Information collection |
| 9 | MTB_405 | 0.9222 | 0.44 | 0.859 | 11/6/10 | FM3 | Public Health & Etiology & Ris |
| 10 | MTB_042 | 0.9223 | 0.19 | 0.849 | 7/9 | FM6 | Patient Information collection |
| 11 | MTB_353 | 0.9224 | 0.00 | 0.845 | 6/5/6 | FM6 | Disease Diagnosis |
| 12 | MTB_110 | 0.9230 | 0.40 | 0.863 | 5/5 | FM3 | Pharmacology |
| 13 | MTB_221 | 0.9230 | 0.00 | 0.846 | 7/7 | FM6 | Policy & Ethics & Legal Questi |
| 14 | MTB_180 | 0.9262 | 0.47 | 0.911 | 4/6/5 | FM3 | Prognosis and Outcomes |
| 15 | MTB_043 | 0.9267 | 0.62 | 0.978 | 8/5 | FM3 | Patient Information collection |
| 16 | MTB_281 | 0.9275 | 0.79 | 0.887 | 9/10 | FM3 | Disease Diagnosis |
| 17 | MTB_303 | 0.9284 | 0.00 | 0.857 | 5/5/5 | FM6 | Anatomy & Physiology |
| 18 | MTB_456 | 0.9303 | 1.46 | 0.983 | 9/9/9 | FM3 | Pathophysiology |
| 19 | MTB_146 | 0.9313 | 1.40 | 0.895 | 18/8/10 | FM2+FM3 | Pharmacology |
| 20 | MTB_369 | 0.9322 | 0.03 | 0.875 | 7/6/6 | FM6 | Disease Diagnosis |
| 21 | MTB_322 | 0.9324 | 0.75 | 0.957 | 4/4 | FM3 | Anatomy & Physiology |
| 22 | MTB_439 | 0.9328 | 0.00 | 0.866 | 8/12/12 | FM6 | Public Health & Etiology & Ris |
| 23 | MTB_143 | 0.9330 | 0.00 | 0.866 | 10/12/7 | FM6 | Pharmacology |
| 24 | MTB_270 | 0.9332 | 0.00 | 0.866 | 8/8/8 | FM6 | Patient Management & Discharge |
| 25 | MTB_086 | 0.9334 | 0.45 | 0.872 | 10/10 | FM3 | Treatment |
| 26 | MTB_367 | 0.9334 | 0.06 | 0.867 | 6/6/6 | FM6 | Disease Diagnosis |
| 27 | MTB_368 | 0.9337 | 0.08 | 0.905 | 6/6/6 | FM6 | Disease Diagnosis |
| 28 | MTB_280 | 0.9348 | 0.00 | 0.870 | 7/5/6 | FM6 | Patient Management & Discharge |
| 29 | MTB_139 | 0.9349 | 0.07 | 0.870 | 18/6/6 | FM2 | Pharmacology |
| 30 | MTB_085 | 0.9354 | 0.00 | 0.871 | 6/8/8 | FM6 | Treatment |
| 31 | MTB_358 | 0.9357 | 0.03 | 0.872 | 5/6/9 | FM6 | Disease Diagnosis |
| 32 | MTB_062 | 0.9362 | 0.15 | 0.879 | 7/6/10 | FM6 | Treatment |
| 33 | MTB_376 | 0.9367 | 0.16 | 0.873 | 9/14/9 | FM6 | Disease Diagnosis |
| 34 | MTB_420 | 0.9372 | 0.33 | 0.925 | 5/4/6 | FM3 | Public Health & Etiology & Ris |
| 35 | MTB_449 | 0.9377 | 0.00 | 0.875 | 5/5/5 | FM6 | Public Health & Etiology & Ris |
| 36 | MTB_454 | 0.9381 | 0.04 | 0.881 | 4/5/4 | FM6 | Pathophysiology |
| 37 | MTB_360 | 0.9384 | 0.00 | 0.877 | 8/8/6 | FM6 | Disease Diagnosis |
| 38 | MTB_374 | 0.9388 | 0.33 | 0.889 | 10/6/5 | FM3 | Disease Diagnosis |
| 39 | MTB_289 | 0.9393 | 0.12 | 0.879 | 18/10/15 | FM6 | Disease Diagnosis |
| 40 | MTB_064 | 0.9395 | 0.07 | 0.895 | 5/4/5 | FM6 | Treatment |
| 41 | MTB_251 | 0.9400 | 0.00 | 0.880 | 11/6/6 | FM6 | Patient Management & Discharge |
| 42 | MTB_094 | 0.9407 | 0.00 | 0.881 | 7/5/8 | FM6 | Treatment |
| 43 | MTB_106 | 0.9412 | 0.09 | 0.882 | 7/5/5 | FM6 | Pharmacology |
| 44 | MTB_215 | 0.9417 | 0.00 | 0.883 | 5/9/10 | FM6 | Policy & Ethics & Legal Questi |
| 45 | MTB_483 | 0.9418 | 0.00 | 0.884 | 5/7/5 | FM6 | Pathophysiology |
| 46 | MTB_155 | 0.9420 | 0.13 | 0.892 | 8/7/8 | FM6 | Prognosis and Outcomes |
| 47 | MTB_357 | 0.9426 | 0.00 | 0.885 | 4/4/4 | FM6 | Disease Diagnosis |
| 48 | MTB_371 | 0.9431 | 0.00 | 0.886 | 8/7/5 | FM6 | Disease Diagnosis |
| 49 | MTB_243 | 0.9436 | 0.00 | 0.887 | 5/5/5 | FM6 | Treatment |
| 50 | MTB_124 | 0.9438 | 0.00 | 0.888 | 6/11/6 | FM6 | Pharmacology |

---

*Classification: same heuristic rules as D1 (CR>0.3, step_ratio>2.0, SIM<0.80).*
*Source: cara_scores_d2_n499.jsonl, 50 GDP_r1 + 50 M3_r1 cases classified.*
