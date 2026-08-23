# E1 Ablation Report (D2, Qwen, same 100 pilot+ext questions)

| Condition | CARA-HYB | CARA-SIM | CR | n |
|---|---|---|---|---|
| M4 r0  (no structure, no debate) | 0.894 | 0.796 | 0.121 | 97 |
| M3 r1  (standard debate) | 0.878 | 0.761 | 0.043 | 84 |
| Arm D r0  (generic structure, indep) | 0.863 | 0.729 | 0.079 | 98 |
| Arm D r1  (generic structure + std debate) | 0.886 | 0.774 | 0.061 | 88 |
| GDP r0  (CLAIM+GROUND, indep) | 0.913 | 0.836 | 0.135 | 96 |
| Arm C r1  (GDP minus anti-sycophancy) | 0.947 | 0.906 | 0.127 | 100 |
| GDP r1  (full GDP) | 0.951 | 0.910 | 0.101 | 100 |

## Key contrasts (CARA-HYB)

- **Named grounding (format)**: GDP r0 0.913 vs Arm D r0 0.863 vs M4 r0 0.894 — gap GDP r0 - Arm D r0 = +0.050
- **Anti-sycophancy**: GDP r1 0.951 vs Arm C r1 0.947 — gap = +0.004
- **Generic structure in debate**: Arm D r1 0.886 vs M3 r1 0.878 (structure lift) ; vs GDP r1 0.951 (remaining GDP-specific gap +0.066)

Interpretation guide: if GDP r1 - Arm D r1 remains large, the dominant GDP gain is NOT reproduced by generic structure + standard debate; if GDP r0 - Arm D r0 is positive, named grounding (not mere structure) drives the format-level effect; the GDP r1 - Arm C r1 gap is the anti-sycophancy contribution. Report absolute values within-condition only.