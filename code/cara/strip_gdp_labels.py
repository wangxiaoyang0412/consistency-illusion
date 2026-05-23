"""Label-stripping for GDP traces — confound rebuttal experiment.

Purpose
-------
A reviewer raised the concern that GDP's gain on CARA-HYB could be
partly mechanical: the literal CLAIM/GROUND/STANCE label tokens that
GDP requires create lexical regularity that may inflate step-pair
embedding cosine similarity. This script tests that hypothesis by
stripping just the label tokens from GDP traces (keeping all content)
and re-running the CARA pipeline.

What gets stripped
------------------
- ``CLAIM:`` / ``GROUND:`` / ``STANCE:`` keywords (case-insensitive)
- Bold-wrapped variants (``**CLAIM**:``, ``**CLAIM:**``, ``__CLAIM__:``)
- Surrounding extra whitespace introduced by the removal

What is preserved
-----------------
- Numbered step markers (``1.``, ``2.``, ...) — M3 traces also use these
- AGREE / DISAGREE / EXTEND tokens — these are agent decisions, not template
- All free-text content (claim text, ground text, stance justifications)
- counter-Ground content
- The trace's question_id, agent_id, round, system, and all metadata

Output
------
For each input ``raw_traces.jsonl``, writes ``raw_traces_stripped.jsonl``
in the same directory. Only M3-GDP traces are stripped; M3 and M4
traces are passed through unchanged so the new file is a drop-in
replacement for the original.

Usage
-----
    python -m cara.strip_gdp_labels
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Tuple

# --- Stripping patterns ---------------------------------------------------

# 1) Bold-wrapped labels (handle first so they don't leave stray bold markers)
#    Matches: **CLAIM**, **CLAIM:**, __CLAIM__:, etc., followed by optional ":".
_LABEL_BOLD_RE = re.compile(
    r"(?:\*{2}|_{2})\s*(?:CLAIM|GROUND|STANCE)\s*:?\s*(?:\*{2}|_{2})\s*:?\s*",
    re.IGNORECASE,
)

# 2) Plain labels. Anchored to either start-of-line or whitespace boundary
#    to avoid matching inside body text (e.g., the word "claim" mid-sentence).
_LABEL_PLAIN_RE = re.compile(
    r"(?:^|(?<=\s))(?:CLAIM|GROUND|STANCE)\s*:\s*",
    re.IGNORECASE | re.MULTILINE,
)

# 3) Collapse multiple consecutive blank lines introduced by the removals.
_MULTI_BLANK_RE = re.compile(r"\n\s*\n\s*\n+")

# --- Stripping function ---------------------------------------------------

def strip_labels(response: str) -> str:
    """Remove CLAIM/GROUND/STANCE label tokens, preserve all content.

    The transformation is intentionally conservative:
    - Labels and the colon immediately following them are removed.
    - Markdown bold delimiters around labels are removed only if they
      wrap the label itself (not arbitrary bold in body text).
    - Numbered list markers, AGREE/DISAGREE/EXTEND tokens, and all
      free-text content are preserved verbatim.
    """
    if not response:
        return response

    text = response
    # Order matters: bold-wrapped first, then plain.
    text = _LABEL_BOLD_RE.sub("", text)
    text = _LABEL_PLAIN_RE.sub("", text)
    # Tidy: collapse triple+ blank lines (some labels lived on their own line).
    text = _MULTI_BLANK_RE.sub("\n\n", text)
    return text


# --- Driver ---------------------------------------------------------------

def strip_traces_file(
    input_path: Path, output_path: Path, only_system: str = "M3-GDP"
) -> Tuple[int, int]:
    """Strip labels from ``only_system`` traces. Pass through other systems.

    Returns
    -------
    (n_stripped, n_total): number of stripped records and total records.
    """
    n_stripped = 0
    n_total = 0
    with open(input_path, encoding="utf-8") as f_in, \
            open(output_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            trace = json.loads(line)
            n_total += 1
            if trace.get("system") == only_system and trace.get("response"):
                original = trace["response"]
                stripped = strip_labels(original)
                if stripped != original:
                    trace["response"] = stripped
                    trace["response_label_stripped"] = True
                    n_stripped += 1
            f_out.write(json.dumps(trace, ensure_ascii=False) + "\n")
    return n_stripped, n_total


def main() -> None:
    """Strip label tokens from all GDP trace files used in the paper.

    Set TRACES_ROOT env var to point to the directory containing the
    raw_traces.jsonl files. Defaults to ``./traces``.
    """
    import os
    base = Path(os.environ.get("TRACES_ROOT", "./traces"))

    # All three GDP configurations used to generate the paper's headline numbers
    targets = [
        # D1 MedQA, Qwen, N=500
        base / "sub200_M3GDP_D1" / "raw_traces.jsonl",
        # D2 MedThink-Bench, Qwen, N=499 (merged_M3GDP_D2 is the full sample
        # used by run_cara_d2_n499.py)
        base / "merged_M3GDP_D2" / "raw_traces.jsonl",
        # D2 MedThink-Bench, Llama, N=100
        base / "llama_M3GDP_D2" / "raw_traces.jsonl",
    ]

    print("=" * 60, flush=True)
    print("GDP Label-Stripping (rebuttal confound experiment)", flush=True)
    print("=" * 60, flush=True)

    for src in targets:
        if not src.exists():
            print(f"  [MISS] {src}", flush=True)
            continue
        dst = src.with_name("raw_traces_stripped.jsonl")
        n_strip, n_tot = strip_traces_file(src, dst)
        rel_src = src.relative_to(base)
        print(
            f"  [OK] {rel_src}: stripped {n_strip}/{n_tot} traces "
            f"-> {dst.name}",
            flush=True,
        )

    print("\nDone. Next: run CARA pipeline on the *_stripped.jsonl files.", flush=True)


if __name__ == "__main__":
    main()
