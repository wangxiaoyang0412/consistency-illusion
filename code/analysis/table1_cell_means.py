"""Reproduce Table 1: mean CARA-HYB, CARA-SIM and CR per (system, round) cell.

Reads the released per-question CARA scores for D1 (MedQA-USMLE) and D2
(MedThink-Bench) and prints the cell means reported in Table 1. Questions whose
agreement set has fewer than two agents are undefined for CARA (their scores
are null) and are excluded, which is why N varies across cells.

With --llama, also prints the Llama 3.3 70B replication cells on D2 and the
three Delta CARA-HYB rows of the cross-backbone table (Appendix).

Usage:
    python code/analysis/table1_cell_means.py
    python code/analysis/table1_cell_means.py --llama
"""
import argparse
import json
from collections import defaultdict
from typing import Dict, List, Tuple

# Row order of Table 1: best-aligned cell first, consistency-illusion cell last.
CELLS: List[Tuple[str, int]] = [
    ("M3-GDP", 1),
    ("M3-GDP", 0),
    ("M4", 0),
    ("M3", 0),
    ("M3", 1),
]
ROUND_NAMES = {0: "r0 (indep.)", 1: "r1 (debate)"}
METRICS = ("cara_hyb_01", "cara_sim", "contradiction_rate")

CellStats = Dict[Tuple[str, int], Tuple[int, float, float, float]]


def cell_means(path: str) -> CellStats:
    """Return {(system, round): (N, mean HYB, mean SIM, mean CR)} for one file."""
    groups: Dict[Tuple[str, int], List[dict]] = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["cara_hyb_01"] is None:  # undefined: agreement set < 2 agents
                continue
            groups[(r["system"], r["cara_round"])].append(r)
    stats: CellStats = {}
    for cell, rows in groups.items():
        n = len(rows)
        means = [sum(r[m] for r in rows) / n for m in METRICS]
        stats[cell] = (n, *means)
    return stats


def print_table(columns: List[Tuple[str, CellStats]]) -> None:
    """Print one row per cell, with an (N, HYB, SIM, CR) block per column."""
    prefix = " " * 20
    print(prefix + "".join(f"   {name:<29}" for name, _ in columns).rstrip())
    print(f"{'System':<8}{'Round':<12}"
          + f"   {'N':>5}{'HYB':>8}{'SIM':>8}{'CR':>8}" * len(columns))
    for system, rnd in CELLS:
        row = f"{system:<8}{ROUND_NAMES[rnd]:<12}"
        for _, stats in columns:
            n, hyb, sim, cr = stats[(system, rnd)]
            row += f"   {n:>5}{hyb:>8.3f}{sim:>8.3f}{cr:>8.3f}"
        print(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--d1", default="data/cara_scores/cara_scores_d1_n500.jsonl",
                        help="D1 (MedQA-USMLE, Qwen 2.5 72B) CARA scores.")
    parser.add_argument("--d2", default="data/cara_scores/cara_scores_d2_n499.jsonl",
                        help="D2 (MedThink-Bench, Qwen 2.5 72B) CARA scores.")
    parser.add_argument("--llama", action="store_true",
                        help="Also print the Llama 3.3 70B replication on D2.")
    parser.add_argument("--llama-file",
                        default="data/cara_scores/cara_scores_llama_d2_n100.jsonl",
                        help="D2 (MedThink-Bench, Llama 3.3 70B) CARA scores.")
    args = parser.parse_args()

    print("Table 1: mean CARA-HYB / CARA-SIM / CR per cell (Qwen 2.5 72B)\n")
    print_table([("D1 MedQA-USMLE", cell_means(args.d1)),
                 ("D2 MedThink-Bench", cell_means(args.d2))])

    if not args.llama:
        return
    llama = cell_means(args.llama_file)
    print("\nCross-backbone replication on D2 (Llama 3.3 70B)\n")
    print_table([("D2 MedThink-Bench (Llama)", llama)])
    hyb = {cell: stats[1] for cell, stats in llama.items()}
    print()
    print(f"M3 debate  Delta HYB (r0 -> r1): {hyb[('M3', 1)] - hyb[('M3', 0)]:+.3f}")
    print(f"GDP debate Delta HYB (r0 -> r1): "
          f"{hyb[('M3-GDP', 1)] - hyb[('M3-GDP', 0)]:+.3f}")
    print(f"Format effect Delta HYB (GDP r0 - M4 r0): "
          f"{hyb[('M3-GDP', 0)] - hyb[('M4', 0)]:+.3f}")


if __name__ == "__main__":
    main()
