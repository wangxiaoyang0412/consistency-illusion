"""
Bootstrap confidence intervals for all main CARA comparisons.

Computes 95% percentile bootstrap CIs for:
  - Mean CARA-HYB per cell
  - Pairwise deltas (mean difference)
  - Cohen's d for pairwise comparisons
  - CR (contradiction rate) comparisons
  - CARA-GT (agent↔expert alignment) comparisons

Data sources:
  - D1 N=500: cara_scores_d1_n500.jsonl
  - D2 N=499: cara_scores_d2_n499.jsonl
  - Llama D2 N=100: cara_scores_llama_d2_n100.jsonl
  - D2 CARA-GT N=499: cara_gt_d2_n499.jsonl

Usage:
  python -u bootstrap_ci.py
"""
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
N_BOOT = 10_000
SEED = 42
ALPHA = 0.05  # 95% CI

# ── Data loading ────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent

D1_FILE = BASE / "cara_pilot" / "cara_scores_d1_n500.jsonl"
D2_FILE = BASE / "cara_pilot" / "cara_scores_d2_n499.jsonl"
LLAMA_FILE = BASE / "cara_pilot" / "cara_scores_llama_d2_n100.jsonl"
GT_FILE = BASE / "cara_pilot" / "cara_gt_d2_n499.jsonl"

OUT_FILE = BASE / "bootstrap_ci_report.md"


def load_jsonl(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        records.append(json.loads(line))
    return records


def bucket_by_cell_round(records: list[dict], metric: str) -> dict[str, list[float]]:
    """Group metric values by cell_id + round, filtering errors and None."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r.get("error") is not None:
            continue
        val = r.get(metric)
        if val is None:
            continue
        key = f"{r['cell_id']}_r{r['cara_round']}"
        buckets[key].append(val)
    return dict(buckets)


# ── Bootstrap core ──────────────────────────────────────────────────────
def bootstrap_mean(data: list[float], rng: random.Random) -> list[float]:
    """Generate N_BOOT bootstrap means."""
    n = len(data)
    means = []
    for _ in range(N_BOOT):
        sample = [data[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    return means


def bootstrap_paired_delta(a: list[float], b: list[float],
                           paired_ids_a: list[str], paired_ids_b: list[str],
                           rng: random.Random) -> list[float]:
    """Bootstrap delta = mean(a) - mean(b).

    If samples share question_ids (paired), resample by question.
    Otherwise, resample independently.
    """
    # Independent resampling (different N or unpaired)
    na, nb = len(a), len(b)
    deltas = []
    for _ in range(N_BOOT):
        sa = [a[rng.randint(0, na - 1)] for _ in range(na)]
        sb = [b[rng.randint(0, nb - 1)] for _ in range(nb)]
        deltas.append(sum(sa) / na - sum(sb) / nb)
    return deltas


def bootstrap_cohens_d(a: list[float], b: list[float],
                       rng: random.Random) -> list[float]:
    """Bootstrap Cohen's d = (mean_a - mean_b) / pooled_sd."""
    na, nb = len(a), len(b)
    ds = []
    for _ in range(N_BOOT):
        sa = [a[rng.randint(0, na - 1)] for _ in range(na)]
        sb = [b[rng.randint(0, nb - 1)] for _ in range(nb)]
        ma = sum(sa) / na
        mb = sum(sb) / nb
        var_a = sum((x - ma) ** 2 for x in sa) / na
        var_b = sum((x - mb) ** 2 for x in sb) / nb
        pooled_sd = math.sqrt((var_a + var_b) / 2)
        if pooled_sd < 1e-12:
            ds.append(0.0)
        else:
            ds.append((ma - mb) / pooled_sd)
    return ds


def percentile_ci(boot_vals: list[float], alpha: float = ALPHA) -> tuple[float, float]:
    """Percentile method CI."""
    s = sorted(boot_vals)
    lo_idx = int(math.floor(alpha / 2 * len(s)))
    hi_idx = int(math.ceil((1 - alpha / 2) * len(s))) - 1
    lo_idx = max(0, min(lo_idx, len(s) - 1))
    hi_idx = max(0, min(hi_idx, len(s) - 1))
    return s[lo_idx], s[hi_idx]


def mean_val(data: list[float]) -> float:
    return sum(data) / len(data) if data else 0.0


def sd_val(data: list[float]) -> float:
    if len(data) < 2:
        return 0.0
    m = mean_val(data)
    return math.sqrt(sum((x - m) ** 2 for x in data) / len(data))


def cohens_d(a: list[float], b: list[float]) -> float:
    ma, mb = mean_val(a), mean_val(b)
    va = sum((x - ma) ** 2 for x in a) / len(a)
    vb = sum((x - mb) ** 2 for x in b) / len(b)
    pooled = math.sqrt((va + vb) / 2)
    return (ma - mb) / pooled if pooled > 1e-12 else 0.0


# ── Main ────────────────────────────────────────────────────────────────
def main():
    rng = random.Random(SEED)

    print("Loading data...")
    d1_records = load_jsonl(D1_FILE)
    d2_records = load_jsonl(D2_FILE)
    llama_records = load_jsonl(LLAMA_FILE)
    gt_records = load_jsonl(GT_FILE)
    print(f"  D1: {len(d1_records)} records")
    print(f"  D2: {len(d2_records)} records")
    print(f"  Llama: {len(llama_records)} records")
    print(f"  CARA-GT: {len(gt_records)} records")

    # Bucket by metric
    d1_hyb = bucket_by_cell_round(d1_records, "cara_hyb_01")
    d1_cr = bucket_by_cell_round(d1_records, "contradiction_rate")
    d1_sim = bucket_by_cell_round(d1_records, "cara_sim")
    d2_hyb = bucket_by_cell_round(d2_records, "cara_hyb_01")
    d2_cr = bucket_by_cell_round(d2_records, "contradiction_rate")
    d2_sim = bucket_by_cell_round(d2_records, "cara_sim")
    llama_hyb = bucket_by_cell_round(llama_records, "cara_hyb_01")
    llama_cr = bucket_by_cell_round(llama_records, "contradiction_rate")
    gt_hyb = bucket_by_cell_round(gt_records, "cara_gt_hyb_01")
    gt_coverage = bucket_by_cell_round(gt_records, "expert_coverage_rate")

    lines: list[str] = []
    lines.append("# Bootstrap Confidence Intervals Report")
    lines.append("")
    lines.append(f"- **Bootstrap iterations**: {N_BOOT}")
    lines.append(f"- **CI level**: {100*(1-ALPHA):.0f}%")
    lines.append(f"- **Method**: Percentile bootstrap (independent resampling)")
    lines.append(f"- **Seed**: {SEED}")
    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 1: D1 per-cell means
    # ────────────────────────────────────────────────────────────────
    lines.append("## 1. D1 N=500 — Per-Cell CARA-HYB Mean [95% CI]")
    lines.append("")
    lines.append("| Cell | Mean | SD | N | 95% CI |")
    lines.append("|------|------|----|---|--------|")

    d1_cells_of_interest = [
        "sub200_M3GDP_D1_r1",
        "sub200_M3GDP_D1_r0",
        "sub200_M3_D1_r1",
        "sub200_M3_D1_r0",
        "sub200_M4_D1_r0",
    ]
    for cell in d1_cells_of_interest:
        vals = d1_hyb.get(cell, [])
        if not vals:
            continue
        m = mean_val(vals)
        s = sd_val(vals)
        boot = bootstrap_mean(vals, rng)
        lo, hi = percentile_ci(boot)
        lines.append(f"| {cell} | {m:.4f} | {s:.4f} | {len(vals)} | [{lo:.4f}, {hi:.4f}] |")
        print(f"  {cell}: {m:.4f} [{lo:.4f}, {hi:.4f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 2: D1 pairwise deltas (CARA-HYB)
    # ────────────────────────────────────────────────────────────────
    lines.append("## 2. D1 N=500 — Pairwise CARA-HYB Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ (mean diff) | 95% CI(Δ) | Cohen's d | 95% CI(d) | N_a | N_b |")
    lines.append("|------------|---------------|-----------|-----------|-----------|-----|-----|")

    comparisons_hyb = [
        ("GDP_r1 vs M3_r1", "sub200_M3GDP_D1_r1", "sub200_M3_D1_r1"),
        ("GDP_r1 vs M4_r0", "sub200_M3GDP_D1_r1", "sub200_M4_D1_r0"),
        ("M3_r1 vs M4_r0", "sub200_M3_D1_r1", "sub200_M4_D1_r0"),
        ("GDP_r1 vs GDP_r0", "sub200_M3GDP_D1_r1", "sub200_M3GDP_D1_r0"),
        ("M3_r1 vs M3_r0", "sub200_M3_D1_r1", "sub200_M3_D1_r0"),
    ]

    for label, cell_a, cell_b in comparisons_hyb:
        a = d1_hyb.get(cell_a, [])
        b = d1_hyb.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        d = cohens_d(a, b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        boot_d = bootstrap_cohens_d(a, b, rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lo_cd, hi_cd = percentile_ci(boot_d)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {d:+.3f} | [{lo_cd:+.3f}, {hi_cd:+.3f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}], d={d:+.3f} [{lo_cd:+.3f}, {hi_cd:+.3f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 3: D1 CR comparisons
    # ────────────────────────────────────────────────────────────────
    lines.append("## 3. D1 N=500 — Pairwise CR (Contradiction Rate) Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ (mean diff) | 95% CI(Δ) | N_a | N_b |")
    lines.append("|------------|---------------|-----------|-----|-----|")

    comparisons_cr = [
        ("GDP_r1 vs M3_r1", "sub200_M3GDP_D1_r1", "sub200_M3_D1_r1"),
        ("GDP_r1 vs M4_r0", "sub200_M3GDP_D1_r1", "sub200_M4_D1_r0"),
        ("M3_r1 vs M4_r0", "sub200_M3_D1_r1", "sub200_M4_D1_r0"),
    ]

    for label, cell_a, cell_b in comparisons_cr:
        a = d1_cr.get(cell_a, [])
        b = d1_cr.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  CR {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 4: D1 CARA-SIM comparisons
    # ────────────────────────────────────────────────────────────────
    lines.append("## 4. D1 N=500 — Pairwise CARA-SIM Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ (mean diff) | 95% CI(Δ) | N_a | N_b |")
    lines.append("|------------|---------------|-----------|-----|-----|")

    for label, cell_a, cell_b in comparisons_cr:  # same cell pairs
        a = d1_sim.get(cell_a, [])
        b = d1_sim.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  SIM {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 5: D2 Qwen per-cell means
    # ────────────────────────────────────────────────────────────────
    lines.append("## 5. D2 N=499 (Qwen) — Per-Cell CARA-HYB Mean [95% CI]")
    lines.append("")
    lines.append("| Cell | Mean | SD | N | 95% CI |")
    lines.append("|------|------|----|---|--------|")

    d2_cells_of_interest = [
        "merged_M3GDP_D2_r1",
        "merged_M3GDP_D2_r0",
        "merged_M3_D2_r1",
        "merged_M3_D2_r0",
        "merged_M4_D2_r0",
    ]
    for cell in d2_cells_of_interest:
        vals = d2_hyb.get(cell, [])
        if not vals:
            continue
        m = mean_val(vals)
        s = sd_val(vals)
        boot = bootstrap_mean(vals, rng)
        lo, hi = percentile_ci(boot)
        lines.append(f"| {cell} | {m:.4f} | {s:.4f} | {len(vals)} | [{lo:.4f}, {hi:.4f}] |")
        print(f"  {cell}: {m:.4f} [{lo:.4f}, {hi:.4f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 6: D2 Qwen pairwise CARA-HYB
    # ────────────────────────────────────────────────────────────────
    lines.append("## 6. D2 N=499 (Qwen) — Pairwise CARA-HYB Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ (mean diff) | 95% CI(Δ) | Cohen's d | 95% CI(d) | N_a | N_b |")
    lines.append("|------------|---------------|-----------|-----------|-----------|-----|-----|")

    d2_comparisons_hyb = [
        ("GDP_r1 vs M3_r1", "merged_M3GDP_D2_r1", "merged_M3_D2_r1"),
        ("GDP_r1 vs M4_r0", "merged_M3GDP_D2_r1", "merged_M4_D2_r0"),
        ("M3_r1 vs M4_r0", "merged_M3_D2_r1", "merged_M4_D2_r0"),
        ("GDP_r1 vs GDP_r0", "merged_M3GDP_D2_r1", "merged_M3GDP_D2_r0"),
        ("M3_r1 vs M3_r0", "merged_M3_D2_r1", "merged_M3_D2_r0"),
    ]

    for label, cell_a, cell_b in d2_comparisons_hyb:
        a = d2_hyb.get(cell_a, [])
        b = d2_hyb.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        d = cohens_d(a, b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        boot_d = bootstrap_cohens_d(a, b, rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lo_cd, hi_cd = percentile_ci(boot_d)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {d:+.3f} | [{lo_cd:+.3f}, {hi_cd:+.3f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  D2 {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}], d={d:+.3f} [{lo_cd:+.3f}, {hi_cd:+.3f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 7: D2 Qwen CR comparisons
    # ────────────────────────────────────────────────────────────────
    lines.append("## 7. D2 N=499 (Qwen) — Pairwise CR Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ (mean diff) | 95% CI(Δ) | N_a | N_b |")
    lines.append("|------------|---------------|-----------|-----|-----|")

    d2_comparisons_cr = [
        ("GDP_r1 vs M3_r1", "merged_M3GDP_D2_r1", "merged_M3_D2_r1"),
        ("GDP_r1 vs M4_r0", "merged_M3GDP_D2_r1", "merged_M4_D2_r0"),
        ("M3_r1 vs M4_r0", "merged_M3_D2_r1", "merged_M4_D2_r0"),
    ]

    for label, cell_a, cell_b in d2_comparisons_cr:
        a = d2_cr.get(cell_a, [])
        b = d2_cr.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  D2 CR {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 8: Llama D2 cross-backbone
    # ────────────────────────────────────────────────────────────────
    lines.append("## 8. Llama D2 N=100 — Cross-Backbone CARA-HYB")
    lines.append("")
    lines.append("### 8a. Per-Cell Means")
    lines.append("")
    lines.append("| Cell | Mean | SD | N | 95% CI |")
    lines.append("|------|------|----|---|--------|")

    llama_cells = [
        "llama_M3GDP_D2_r1",
        "llama_M3GDP_D2_r0",
        "llama_M3_D2_r1",
        "llama_M3_D2_r0",
        "llama_M4_D2_r0",
    ]
    for cell in llama_cells:
        vals = llama_hyb.get(cell, [])
        if not vals:
            continue
        m = mean_val(vals)
        s = sd_val(vals)
        boot = bootstrap_mean(vals, rng)
        lo, hi = percentile_ci(boot)
        lines.append(f"| {cell} | {m:.4f} | {s:.4f} | {len(vals)} | [{lo:.4f}, {hi:.4f}] |")
        print(f"  {cell}: {m:.4f} [{lo:.4f}, {hi:.4f}]")

    lines.append("")
    lines.append("### 8b. Pairwise Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ (mean diff) | 95% CI(Δ) | Cohen's d | 95% CI(d) | N_a | N_b |")
    lines.append("|------------|---------------|-----------|-----------|-----------|-----|-----|")

    llama_comparisons = [
        ("GDP_r1 vs M3_r1", "llama_M3GDP_D2_r1", "llama_M3_D2_r1"),
        ("GDP_r1 vs M4_r0", "llama_M3GDP_D2_r1", "llama_M4_D2_r0"),
        ("M3_r1 vs M4_r0", "llama_M3_D2_r1", "llama_M4_D2_r0"),
    ]

    for label, cell_a, cell_b in llama_comparisons:
        a = llama_hyb.get(cell_a, [])
        b = llama_hyb.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        d = cohens_d(a, b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        boot_d = bootstrap_cohens_d(a, b, rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lo_cd, hi_cd = percentile_ci(boot_d)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {d:+.3f} | [{lo_cd:+.3f}, {hi_cd:+.3f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  Llama {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}], d={d:+.3f} [{lo_cd:+.3f}, {hi_cd:+.3f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 9: CARA-GT per-cell means
    # ────────────────────────────────────────────────────────────────
    lines.append("## 9. D2 CARA-GT N=499 — Per-Cell GT-HYB Mean [95% CI]")
    lines.append("")
    lines.append("| Cell | Mean | SD | N | 95% CI |")
    lines.append("|------|------|----|---|--------|")

    gt_cells = [
        "merged_M4_D2_r0",
        "merged_M3_D2_r0",
        "merged_M3_D2_r1",
        "merged_M3GDP_D2_r0",
        "merged_M3GDP_D2_r1",
    ]
    for cell in gt_cells:
        vals = gt_hyb.get(cell, [])
        if not vals:
            continue
        m = mean_val(vals)
        s = sd_val(vals)
        boot = bootstrap_mean(vals, rng)
        lo, hi = percentile_ci(boot)
        lines.append(f"| {cell} | {m:.4f} | {s:.4f} | {len(vals)} | [{lo:.4f}, {hi:.4f}] |")
        print(f"  GT {cell}: {m:.4f} [{lo:.4f}, {hi:.4f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 10: CARA-GT pairwise comparisons
    # ────────────────────────────────────────────────────────────────
    lines.append("## 10. D2 CARA-GT N=499 — Pairwise GT-HYB Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ (mean diff) | 95% CI(Δ) | Cohen's d | 95% CI(d) | N_a | N_b |")
    lines.append("|------------|---------------|-----------|-----------|-----------|-----|-----|")

    gt_comparisons = [
        ("GDP_r1 vs M3_r1", "merged_M3GDP_D2_r1", "merged_M3_D2_r1"),
        ("GDP_r1 vs M4_r0", "merged_M3GDP_D2_r1", "merged_M4_D2_r0"),
        ("M3_r1 vs M4_r0", "merged_M3_D2_r1", "merged_M4_D2_r0"),
        ("GDP_r1 vs GDP_r0", "merged_M3GDP_D2_r1", "merged_M3GDP_D2_r0"),
        ("M3_r1 vs M3_r0", "merged_M3_D2_r1", "merged_M3_D2_r0"),
    ]

    for label, cell_a, cell_b in gt_comparisons:
        a = gt_hyb.get(cell_a, [])
        b = gt_hyb.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        d = cohens_d(a, b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        boot_d = bootstrap_cohens_d(a, b, rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lo_cd, hi_cd = percentile_ci(boot_d)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {d:+.3f} | [{lo_cd:+.3f}, {hi_cd:+.3f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  GT {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}], d={d:+.3f} [{lo_cd:+.3f}, {hi_cd:+.3f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 11: CARA-GT expert coverage comparisons
    # ────────────────────────────────────────────────────────────────
    lines.append("## 11. D2 CARA-GT N=499 — Expert Coverage Comparisons")
    lines.append("")
    lines.append("| Comparison | Δ Coverage | 95% CI(Δ) | N_a | N_b |")
    lines.append("|------------|-----------|-----------|-----|-----|")

    gt_cov_comparisons = [
        ("GDP_r1 vs M3_r1", "merged_M3GDP_D2_r1", "merged_M3_D2_r1"),
        ("GDP_r1 vs M4_r0", "merged_M3GDP_D2_r1", "merged_M4_D2_r0"),
        ("M3_r1 vs M4_r0", "merged_M3_D2_r1", "merged_M4_D2_r0"),
    ]

    for label, cell_a, cell_b in gt_cov_comparisons:
        a = gt_coverage.get(cell_a, [])
        b = gt_coverage.get(cell_b, [])
        if not a or not b:
            continue
        delta = mean_val(a) - mean_val(b)
        boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
        lo_d, hi_d = percentile_ci(boot_delta)
        lines.append(
            f"| {label} | {delta:+.4f} | [{lo_d:+.4f}, {hi_d:+.4f}] "
            f"| {len(a)} | {len(b)} |"
        )
        print(f"  GT Coverage {label}: Δ={delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}]")

    lines.append("")

    # ────────────────────────────────────────────────────────────────
    # Section 12: Summary table for paper
    # ────────────────────────────────────────────────────────────────
    lines.append("## 12. Paper-Ready Summary — Key Comparisons")
    lines.append("")
    lines.append("All intervals exclude zero unless noted.")
    lines.append("")
    lines.append("| Dataset | Backbone | Comparison | Δ CARA-HYB [95% CI] | d [95% CI] |")
    lines.append("|---------|----------|------------|---------------------|------------|")

    # Re-compute for clean summary (values already computed above, but
    # let's be explicit for the paper table)
    paper_rows = []

    for ds_label, ds_hyb, comparisons, backbone in [
        ("D1 MedQA (N=500)", d1_hyb, comparisons_hyb[:3], "Qwen 2.5 72B"),
        ("D2 MedThink (N=499)", d2_hyb, d2_comparisons_hyb[:3], "Qwen 2.5 72B"),
        ("D2 MedThink (N=100)", llama_hyb, llama_comparisons, "Llama 3.3 70B"),
    ]:
        for label, cell_a, cell_b in comparisons:
            a = ds_hyb.get(cell_a, [])
            b = ds_hyb.get(cell_b, [])
            if not a or not b:
                continue
            delta = mean_val(a) - mean_val(b)
            d = cohens_d(a, b)
            boot_delta = bootstrap_paired_delta(a, b, [], [], rng)
            boot_d = bootstrap_cohens_d(a, b, rng)
            lo_d, hi_d = percentile_ci(boot_delta)
            lo_cd, hi_cd = percentile_ci(boot_d)
            excludes_zero = (lo_d > 0 and hi_d > 0) or (lo_d < 0 and hi_d < 0)
            note = "" if excludes_zero else " *"
            lines.append(
                f"| {ds_label} | {backbone} | {label} "
                f"| {delta:+.4f} [{lo_d:+.4f}, {hi_d:+.4f}]{note} "
                f"| {d:+.3f} [{lo_cd:+.3f}, {hi_cd:+.3f}]{note} |"
            )

    lines.append("")
    lines.append("\\* CI includes zero — effect not statistically significant at α=0.05.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by bootstrap_ci.py, seed={SEED}, B={N_BOOT}.*")

    # Write report
    report = "\n".join(lines) + "\n"
    OUT_FILE.write_text(report, encoding="utf-8")
    print(f"\nReport written to {OUT_FILE}")


if __name__ == "__main__":
    main()
