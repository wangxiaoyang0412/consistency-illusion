# A6 Segmentation-Sensitivity Report

## Dataset d1_n500

### default

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.952 | 0.912 | 0.098 | 498 |
| GDP r0 | 0.912 | 0.835 | 0.117 | 497 |
| M4 r0 | 0.895 | 0.801 | 0.108 | 500 |
| M3 r0 | 0.895 | 0.801 | 0.104 | 498 |
| M3 r1 | 0.892 | 0.787 | 0.035 | 424 |

- observed HYB ranking: GDP r1 > GDP r0 > M4 r0 > M3 r0 > M3 r1
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): PASS
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): PASS
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

### sentence

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.920 | 0.843 | 0.749 | 498 |
| GDP r0 | 0.888 | 0.780 | 0.579 | 497 |
| M4 r0 | 0.871 | 0.756 | 0.311 | 500 |
| M3 r0 | 0.874 | 0.760 | 0.328 | 498 |
| M3 r1 | 0.868 | 0.743 | 0.116 | 424 |

- observed HYB ranking: GDP r1 > GDP r0 > M3 r0 > M4 r0 > M3 r1
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): PASS
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): PASS
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

### paragraph

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.947 | 0.911 | 0.176 | 498 |
| GDP r0 | 0.903 | 0.841 | 0.353 | 497 |
| M4 r0 | 0.886 | 0.793 | 0.211 | 500 |
| M3 r0 | 0.886 | 0.794 | 0.213 | 498 |
| M3 r1 | 0.899 | 0.807 | 0.064 | 424 |

- observed HYB ranking: GDP r1 > GDP r0 > M3 r1 > M3 r0 > M4 r0
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): FAIL
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): FAIL
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

### nofilter

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.952 | 0.912 | 0.098 | 498 |
| GDP r0 | 0.912 | 0.835 | 0.117 | 497 |
| M4 r0 | 0.895 | 0.800 | 0.108 | 500 |
| M3 r0 | 0.895 | 0.801 | 0.105 | 498 |
| M3 r1 | 0.892 | 0.789 | 0.036 | 424 |

- observed HYB ranking: GDP r1 > GDP r0 > M4 r0 > M3 r0 > M3 r1
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): PASS
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): PASS
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

## Dataset d2_n499

### default

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.952 | 0.914 | 0.127 | 497 |
| GDP r0 | 0.912 | 0.836 | 0.137 | 473 |
| M4 r0 | 0.895 | 0.801 | 0.161 | 470 |
| M3 r0 | 0.896 | 0.801 | 0.144 | 471 |
| M3 r1 | 0.881 | 0.769 | 0.053 | 428 |

- observed HYB ranking: GDP r1 > GDP r0 > M3 r0 > M4 r0 > M3 r1
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): PASS
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): PASS
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

### sentence

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.919 | 0.841 | 0.794 | 497 |
| GDP r0 | 0.888 | 0.782 | 0.609 | 473 |
| M4 r0 | 0.878 | 0.769 | 0.287 | 470 |
| M3 r0 | 0.877 | 0.766 | 0.299 | 471 |
| M3 r1 | 0.872 | 0.751 | 0.124 | 428 |

- observed HYB ranking: GDP r1 > GDP r0 > M4 r0 > M3 r0 > M3 r1
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): PASS
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): PASS
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

### paragraph

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.946 | 0.911 | 0.200 | 497 |
| GDP r0 | 0.903 | 0.841 | 0.369 | 473 |
| M4 r0 | 0.891 | 0.800 | 0.231 | 470 |
| M3 r0 | 0.890 | 0.799 | 0.233 | 471 |
| M3 r1 | 0.891 | 0.790 | 0.077 | 428 |

- observed HYB ranking: GDP r1 > GDP r0 > M4 r0 > M3 r1 > M3 r0
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): FAIL
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): PASS
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

### nofilter

| Cell | CARA-HYB | CARA-SIM | CR | n valid |
|---|---|---|---|---|
| GDP r1 | 0.952 | 0.914 | 0.127 | 497 |
| GDP r0 | 0.912 | 0.836 | 0.137 | 473 |
| M4 r0 | 0.895 | 0.800 | 0.162 | 470 |
| M3 r0 | 0.895 | 0.800 | 0.147 | 471 |
| M3 r1 | 0.881 | 0.769 | 0.057 | 428 |

- observed HYB ranking: GDP r1 > GDP r0 > M3 r0 > M4 r0 > M3 r1
- C1 ranking (GDP r1 > GDP r0 > {M4, M3 r0} > M3 r1): PASS
- C2 illusion signature M3 r0->r1 (CR down AND SIM down): PASS
- C3 GDP repair signature GDP r0->r1 (SIM up): PASS

## Summary

| Dataset | Strategy | C1 ranking | C2 illusion | C3 GDP repair |
|---|---|---|---|---|
| d1_n500 | default | PASS | PASS | PASS |
| d1_n500 | sentence | PASS | PASS | PASS |
| d1_n500 | paragraph | FAIL | FAIL | PASS |
| d1_n500 | nofilter | PASS | PASS | PASS |
| d2_n499 | default | PASS | PASS | PASS |
| d2_n499 | sentence | PASS | PASS | PASS |
| d2_n499 | paragraph | FAIL | PASS | PASS |
| d2_n499 | nofilter | PASS | PASS | PASS |
