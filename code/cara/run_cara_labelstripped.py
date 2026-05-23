"""Run CARA pipeline on label-stripped GDP traces — confound rebuttal.

Runs CARA-HYB / CARA-SIM / CR on GDP traces from which CLAIM:/GROUND:/
STANCE: label tokens have been removed (see ``strip_gdp_labels.py``).

Three configurations are computed:
- D1 MedQA, Qwen, N=500 — GDP r0, GDP r1 (stripped)
- D2 MedThink-Bench, Qwen, N=499 — GDP r0, GDP r1 (stripped)
- D2 MedThink-Bench, Llama, N=100 — GDP r0, GDP r1 (stripped)

For each config we re-use the unchanged M3 / M4 trace files from the
original pipeline so the per-question pair structure remains compatible
with bootstrap CI computation against the published GDP-vs-M3 baseline.

Output
------
``analysis/cara_pilot/cara_scores_labelstripped_<config>.jsonl`` for each
of the three configurations, with the same schema as the original
``cara_scores_*.jsonl`` files.

Runtime
-------
Roughly the same as the original Phase-3 runs: ~8 min per dataset on
RTX 4090. Total: ~18-20 min of compute.

Usage
-----
    python -m cara.run_cara_labelstripped
"""
from __future__ import annotations

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cara.pipeline import run_cara_pipeline  # noqa: E402

# Paths configurable via env vars; defaults assume the repo layout in README.
import os
TRACE_DIR = Path(os.environ.get("TRACES_ROOT", "./traces"))
OUTPUT_DIR = Path(os.environ.get("CARA_OUTPUT_DIR", "./data/cara_scores"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --- Configurations ------------------------------------------------------
# Each entry: (config_label, list_of_(stripped_trace_file, system, cell_id, round))
# We only re-compute the GDP cells; M3/M4 cells are unchanged from the
# original pipeline outputs and need not be re-run.

CONFIGS = [
    (
        "d1_n500",
        [
            (TRACE_DIR / "sub200_M3GDP_D1" / "raw_traces_stripped.jsonl",
             "M3-GDP", "sub200_M3GDP_D1_stripped", 0),
            (TRACE_DIR / "sub200_M3GDP_D1" / "raw_traces_stripped.jsonl",
             "M3-GDP", "sub200_M3GDP_D1_stripped", 1),
        ],
    ),
    (
        "d2_n499",
        [
            (TRACE_DIR / "merged_M3GDP_D2" / "raw_traces_stripped.jsonl",
             "M3-GDP", "merged_M3GDP_D2_stripped", 0),
            (TRACE_DIR / "merged_M3GDP_D2" / "raw_traces_stripped.jsonl",
             "M3-GDP", "merged_M3GDP_D2_stripped", 1),
        ],
    ),
    (
        "llama_d2_n100",
        [
            (TRACE_DIR / "llama_M3GDP_D2" / "raw_traces_stripped.jsonl",
             "M3-GDP", "llama_M3GDP_D2_stripped", 0),
            (TRACE_DIR / "llama_M3GDP_D2" / "raw_traces_stripped.jsonl",
             "M3-GDP", "llama_M3GDP_D2_stripped", 1),
        ],
    ),
]


def main() -> None:
    print("=" * 60, flush=True)
    print("CARA on Label-Stripped GDP Traces (rebuttal)", flush=True)
    print("=" * 60, flush=True)

    # Pre-flight: verify all stripped trace files exist
    print("\nPre-flight check:", flush=True)
    missing = []
    for label, trace_files in CONFIGS:
        for path, _system, _cell, rnd in trace_files:
            if path.exists():
                print(f"  OK  [{label}] {path.relative_to(TRACE_DIR)} r{rnd}", flush=True)
            else:
                missing.append(path)
                print(f"  MISS [{label}] {path}", flush=True)
    if missing:
        print(
            f"\nERROR: {len(missing)} stripped trace file(s) missing. "
            f"Run ``python -m cara.strip_gdp_labels`` first.",
            flush=True,
        )
        sys.exit(1)

    # Run pipeline per config
    for label, trace_files in CONFIGS:
        output_file = OUTPUT_DIR / f"cara_scores_labelstripped_{label}.jsonl"
        print(f"\n{'=' * 60}", flush=True)
        print(f"Config: {label}  ->  {output_file.name}", flush=True)
        print("=" * 60, flush=True)
        results = run_cara_pipeline(
            trace_files=trace_files,
            output_file=output_file,
            contradiction_threshold=0.7,  # paper-default tau
            seed=42,
        )
        print(f"  Done: {len(results)} question-level records", flush=True)

    print("\nAll three configurations complete.", flush=True)
    print("Next: run ``python -m analysis.compare_labelstripped``"
          " for the side-by-side Cohen's d table.", flush=True)


if __name__ == "__main__":
    main()
