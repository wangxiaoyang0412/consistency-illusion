"""Compare label-stripped GDP CARA scores against the published baseline.

For each of the three dataset-backbone configurations, this script:
  1. Loads the published CARA scores (which contain both M3 and GDP cells).
  2. Loads the new label-stripped GDP CARA scores.
  3. Pairs them by ``question_id`` (CARA is question-level).
  4. Computes paired Cohen's ``d`` for GDP_r1 (stripped) vs. M3_r1.
  5. Compares against the original published Cohen's ``d`` (from the paper).

Output
------
A markdown report at ``analysis/labelstripping/labelstripped_report.md``
suitable for inclusion in the rebuttal.

Interpretation
--------------
- If stripped d >> 0: GDP's CARA-HYB gain is NOT mainly from label
  tokens; the reviewer's structural-confound hypothesis is refuted.
- If stripped d is materially smaller than the original d: the labels
  contribute meaningfully to the gain (but if d is still positive,
  GDP still helps; if d collapses to zero, the labels are the gain).

Usage
-----
    python -m analysis.labelstripping.compare_labelstripped
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# --- Paths ---------------------------------------------------------------
# Configurable via PROJECT_ROOT env var; defaults to current directory.

import os
BASE = Path(os.environ.get("PROJECT_ROOT", "."))
CARA_DIR = BASE / "data" / "cara_scores"
OUT_DIR = BASE / "data" / "labelstripping"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original published CARA scores + reported Cohen's d (GDP_r1 vs M3_r1)
PUBLISHED = {
    "d1_n500": {
        "scores_file": CARA_DIR / "cara_scores_d1_n500.jsonl",
        "stripped_file": CARA_DIR / "cara_scores_labelstripped_d1_n500.jsonl",
        "label": "D1 MedQA (Qwen, N=500)",
        "published_d": 1.43,
        "published_ci": "[+1.29, +1.60]",
    },
    "d2_n499": {
        "scores_file": CARA_DIR / "cara_scores_d2_n499.jsonl",
        "stripped_file": CARA_DIR / "cara_scores_labelstripped_d2_n499.jsonl",
        "label": "D2 MedThink-Bench (Qwen, N=499)",
        "published_d": 1.62,
        "published_ci": "[+1.48, +1.78]",
    },
    "llama_d2_n100": {
        "scores_file": CARA_DIR / "cara_scores_llama_d2_n100.jsonl",
        "stripped_file": CARA_DIR / "cara_scores_labelstripped_llama_d2_n100.jsonl",
        "label": "D2 MedThink-Bench (Llama-3.3, N=100)",
        "published_d": 1.99,
        "published_ci": "[+1.65, +2.44]",
    },
}

BOOTSTRAP_B = 10_000
RANDOM_SEED = 42

# --- Helpers -------------------------------------------------------------

def load_scores(path: Path) -> List[dict]:
    """Load a CARA scores JSONL file."""
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def filter_cell(
    records: List[dict], cell_id_substring: str, round_idx: int
) -> Dict[str, float]:
    """Return {question_id: cara_hyb_01} for records matching a cell+round."""
    out = {}
    for r in records:
        # The schema uses `cara_round`, not `round`.
        if r.get("cell_id", "").startswith(cell_id_substring) and r.get("cara_round") == round_idx:
            qid = r.get("question_id")
            hyb = r.get("cara_hyb_01")
            if qid is not None and hyb is not None:
                out[qid] = hyb
    return out


def paired_cohens_d_and_ci(
    a: List[float], b: List[float], b_iter: int = BOOTSTRAP_B, seed: int = RANDOM_SEED
) -> Tuple[float, Tuple[float, float], int]:
    """Compute paired Cohen's d_z and 95% percentile bootstrap CI.

    Assumes ``a`` and ``b`` are paired (same question_id at same index).
    Returns (d, (ci_lo, ci_hi), n_pairs).
    """
    assert len(a) == len(b), f"length mismatch: {len(a)} vs {len(b)}"
    n = len(a)
    if n == 0:
        return (float("nan"), (float("nan"), float("nan")), 0)

    diffs = [ai - bi for ai, bi in zip(a, b)]
    mean_diff = sum(diffs) / n
    sd_diff = math.sqrt(sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)) if n > 1 else 0.0
    d = mean_diff / sd_diff if sd_diff > 0 else 0.0

    rng = random.Random(seed)
    ds = []
    for _ in range(b_iter):
        sample_diffs = [diffs[rng.randint(0, n - 1)] for _ in range(n)]
        sm = sum(sample_diffs) / n
        ssd = math.sqrt(sum((x - sm) ** 2 for x in sample_diffs) / (n - 1)) if n > 1 else 0.0
        ds.append(sm / ssd if ssd > 0 else 0.0)
    ds.sort()
    ci_lo = ds[int(0.025 * b_iter)]
    ci_hi = ds[int(0.975 * b_iter)]
    return (d, (ci_lo, ci_hi), n)


# --- Main ----------------------------------------------------------------

def compare_one_config(cfg_key: str, cfg: dict, report_lines: List[str]) -> None:
    label = cfg["label"]
    print(f"\n--- {label} ---", flush=True)
    report_lines.append(f"\n## {label}\n")

    orig = load_scores(cfg["scores_file"])
    strip = load_scores(cfg["stripped_file"])

    if not orig:
        msg = f"[SKIP] {cfg['scores_file']} not found."
        print(msg, flush=True)
        report_lines.append(msg)
        return
    if not strip:
        msg = f"[SKIP] {cfg['stripped_file']} not found — did you run run_cara_labelstripped.py?"
        print(msg, flush=True)
        report_lines.append(msg)
        return

    # Extract cells. The original file's GDP r1 uses cell_id like
    # "sub200_M3GDP_D1" / "merged_M3GDP_D2" / "llama_M3GDP_D2".
    # The M3 r1 cell uses the analogous M3-named cell.
    # The stripped file has cell_ids suffixed with "_stripped".
    if "d1" in cfg_key:
        m3_substr, gdp_substr = "sub200_M3_D1", "sub200_M3GDP_D1"
    elif "llama" in cfg_key:
        m3_substr, gdp_substr = "llama_M3_D2", "llama_M3GDP_D2"
    else:
        m3_substr, gdp_substr = "merged_M3_D2", "merged_M3GDP_D2"

    m3_r1 = filter_cell(orig, m3_substr, 1)
    gdp_r1_orig = filter_cell(orig, gdp_substr, 1)
    gdp_r1_strip = filter_cell(strip, gdp_substr + "_stripped", 1)

    print(f"  M3 r1: {len(m3_r1)} questions", flush=True)
    print(f"  GDP r1 (original): {len(gdp_r1_orig)} questions", flush=True)
    print(f"  GDP r1 (stripped): {len(gdp_r1_strip)} questions", flush=True)

    # Common question IDs (paired)
    common_orig = sorted(set(m3_r1) & set(gdp_r1_orig))
    common_strip = sorted(set(m3_r1) & set(gdp_r1_strip))

    # Means
    mean_m3 = sum(m3_r1[q] for q in common_orig) / len(common_orig)
    mean_gdp_o = sum(gdp_r1_orig[q] for q in common_orig) / len(common_orig)
    mean_gdp_s = sum(gdp_r1_strip[q] for q in common_strip) / len(common_strip)

    # Paired d
    d_orig, ci_orig, n_orig = paired_cohens_d_and_ci(
        [gdp_r1_orig[q] for q in common_orig],
        [m3_r1[q] for q in common_orig],
    )
    d_strip, ci_strip, n_strip = paired_cohens_d_and_ci(
        [gdp_r1_strip[q] for q in common_strip],
        [m3_r1[q] for q in common_strip],
    )

    # Report
    rows = [
        f"| Metric | Original (paper) | Label-stripped |",
        f"|---|---:|---:|",
        f"| Mean CARA-HYB GDP r1 | {mean_gdp_o:.3f} | {mean_gdp_s:.3f} |",
        f"| Mean CARA-HYB M3 r1  | {mean_m3:.3f} | {mean_m3:.3f} |",
        f"| Cohen's d (paired) | {d_orig:+.3f} | {d_strip:+.3f} |",
        f"| 95% bootstrap CI | [{ci_orig[0]:+.3f}, {ci_orig[1]:+.3f}] | [{ci_strip[0]:+.3f}, {ci_strip[1]:+.3f}] |",
        f"| Paired N | {n_orig} | {n_strip} |",
    ]
    report_lines.extend(rows)
    report_lines.append("")
    report_lines.append(
        f"Published d in paper: {cfg['published_d']:+.2f}, "
        f"CI {cfg['published_ci']}"
    )
    if d_strip > 0.5 and ci_strip[0] > 0:
        report_lines.append(
            "\n**Interpretation:** GDP's CARA-HYB gain over M3 persists after"
            " removing the literal CLAIM/GROUND/STANCE label tokens. The"
            " structural-confound hypothesis (that GDP wins because of"
            " template self-similarity) is not supported by these data."
        )
    elif d_strip <= 0.2:
        report_lines.append(
            "\n**Interpretation:** GDP's CARA-HYB gain over M3 largely"
            " disappears after removing the literal label tokens. The"
            " structural-confound hypothesis is supported. (Honest reporting.)"
        )
    else:
        report_lines.append(
            "\n**Interpretation:** GDP's CARA-HYB gain over M3 attenuates but"
            " does not vanish after label removal. Some of the gain is"
            " content-driven, some structural."
        )

    print("\n".join(rows), flush=True)


def main() -> None:
    report = [
        "# Label-Stripped CARA — Confound Rebuttal Results\n",
        "Bootstrap CI: B=10,000, seed=42. Cohen's d computed paired "
        "(by question_id) at the question level.\n",
    ]
    for key, cfg in PUBLISHED.items():
        compare_one_config(key, cfg, report)

    report_path = OUT_DIR / "labelstripped_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"\nReport written to: {report_path}", flush=True)


if __name__ == "__main__":
    main()
