# D1 Flip Deep-Dive (cctu follow-up)

correct->incorrect flips (M3 r1 -> GDP r1): **31** (published: 31)
incorrect->correct flips: **17** (published: 17)

## Step 1 — reproduction gate
- flips with no CARA record at M3 r1: 0 []
- flips with CARA error at M3 r1: 1 [('MQA_0851', 'all_pairs_undefined')]
- signal inter-agent contradiction (num_contradictions>0): 13
- signal zero-step agent: 1
- flagged (>=1 signal): **14/31** (published: 14/31 = 45%)

REPRODUCTION: OK

## Step 2 — residual unflagged flips (n=17)

### Vote margin at M3 r1 (the consensus GDP overturned)
- residual flips: 15/17 unanimous (3-0), 2/17 split (2-1)
- flagged flips:  12/14 unanimous, 2/14 split
- kept-correct baseline (n=390): 385/390 unanimous, 5/390 split
- (symmetric) GDP r1 margins on incorrect->correct flips: 11/17 unanimous, 6/17 split

### r0 -> r1 trajectory at M3 (late-convergence check)
- residual flips: r0 majority already = r1 majority in 14/17; >=1 agent switched INTO the r1 majority during debate in 8/17
- kept-correct baseline: already-majority 386/390; switched-in 21/390

### Graded weakness of residual flips at M3 r1
- mean CARA-HYB: residual 0.900 vs kept-correct 0.893
- min steps/agent <=2: residual 8/17 vs kept-correct 319/390

### GDP-side behavior on residual flips
- GDP r0 (independent, CLAIM+GROUND) already incorrect on 12/17; correct-then-lost-in-debate on 5/17
- GDP r1 margins on residual flips: 12/17 unanimous, 4/17 split

### Pre-debate state: M3 r0 already correct on 14/17 residual flips

### Full-31 round tracing (flagged 14 included; makes the partition hierarchical)
- flagged 14: already incorrect at GDP r0 = 11; correct at GDP r0, lost at r1 = 3
- ALL 31 flips: already incorrect at GDP r0 = 23; lost during GDP debate (r0 correct -> r1 wrong) = 8

### Mean per-agent step count at M3 r1: residual 3.63 vs kept-correct 2.38

### Per-question detail (residual flips)
| qid | M3 r1 margin | M3 HYB | min steps | M3 r0 correct | GDP r0 correct |
|---|---|---|---|---|---|
| MQA_0032 | 3-0 | 0.909 | 5 | True | False |
| MQA_0258 | 2-1 | 0.916 | 4 | False | False |
| MQA_0263 | 3-0 | 0.884 | 2 | True | False |
| MQA_0345 | 3-0 | 0.917 | 4 | True | False |
| MQA_0371 | 3-0 | 0.979 | 5 | False | True |
| MQA_0400 | 3-0 | 0.920 | 2 | True | False |
| MQA_0414 | 3-0 | 0.851 | 2 | True | False |
| MQA_0573 | 3-0 | 0.903 | 2 | True | True |
| MQA_0709 | 2-1 | 0.881 | 4 | False | False |
| MQA_0926 | 3-0 | 0.896 | 4 | True | True |
| MQA_1016 | 3-0 | 0.865 | 2 | True | True |
| MQA_1080 | 3-0 | 0.844 | 3 | True | False |
| MQA_1143 | 3-0 | 0.893 | 3 | True | False |
| MQA_1144 | 3-0 | 0.902 | 2 | True | False |
| MQA_1179 | 3-0 | 0.964 | 2 | True | False |
| MQA_1211 | 3-0 | 0.933 | 2 | True | False |
| MQA_1229 | 3-0 | 0.849 | 4 | True | True |