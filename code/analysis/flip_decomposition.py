"""Reproduce the D1 answer-change (flip) decomposition from Appendix L.

Reads the released per-question records and prints the 2x2 decomposition
(unfounded-consensus signal x round of first divergence) reported in the
paper: 23/31 changes precede any agent interaction; the grounded-debate
round accounts for 8/31, of which 5 are unflagged.

Usage:
    python code/analysis/flip_decomposition.py \
        --records data/flip_analysis/d1_flip_decomposition.jsonl
"""
import argparse
import json
from collections import Counter


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--records",
        default="data/flip_analysis/d1_flip_decomposition.jsonl",
        help="Path to the released flip-decomposition JSONL.",
    )
    args = parser.parse_args()

    with open(args.records, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    cells = Counter(
        (r["round_of_first_divergence"], r["flagged"]) for r in records
    )
    n = len(records)
    flagged = sum(r["flagged"] for r in records)

    print(f"total correct->incorrect flips (M3 r1 -> GDP r1, D1): {n}")
    print(f"flagged by the two D1-checkable signals: {flagged}/{n} "
          f"({flagged / n:.0%})")
    print()
    print("Round of first divergence x signal status:")
    print(f"  GDP r0 (independent)     flagged={cells[('r0', True)]:>2}  "
          f"unflagged={cells[('r0', False)]:>2}  "
          f"total={cells[('r0', True)] + cells[('r0', False)]:>2}")
    print(f"  GDP r1 (grounded debate) flagged={cells[('r1', True)]:>2}  "
          f"unflagged={cells[('r1', False)]:>2}  "
          f"total={cells[('r1', True)] + cells[('r1', False)]:>2}")
    print()
    strictest = cells[("r1", False)]
    print(f"strictest residual scenario (unflagged, survives r0, "
          f"overturned in debate): {strictest}/{n}")


if __name__ == "__main__":
    main()
