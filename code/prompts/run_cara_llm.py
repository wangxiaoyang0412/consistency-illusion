"""CARA-LLM: LLM-as-judge validation of CARA-HYB scores.

Uses GPT-4o to rate reasoning alignment for agent pairs. Supports both:
  - Agreement pairs (agents chose same answer) — annotation_pairs.json
  - Disagreement pairs (agents chose different answers) — annotation_pairs_disagree.json

Computes Pearson/Spearman correlation between LLM scores and CARA-HYB.

Output: analysis/cara_pilot/cara_llm_scores.jsonl (all records)
        analysis/cara_pilot/cara_llm_summary.md   (correlation report)

Each pair is scored 3 times; the final score is the mean of valid runs.
This provides noise robustness and allows reporting inter-run SD.

Usage:
    cd Experiment/core_code
    set OPENAI_API_KEY=sk-...
    # Run on agreement pairs only (default):
    python -u -m cara.run_cara_llm
    # Run on disagreement pairs only:
    python -u -m cara.run_cara_llm --disagree
    # Run on both (merged):
    python -u -m cara.run_cara_llm --all

Requires: openai>=1.0
"""
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

# --- Paths (configurable via PROJECT_ROOT env var) ---
BASE_DIR = Path(os.environ.get("PROJECT_ROOT", "."))
AGREE_FILE = BASE_DIR / "data" / "annotation" / "annotation_pairs.json"
DISAGREE_FILE = BASE_DIR / "data" / "annotation" / "annotation_pairs_disagree.json"
OUTPUT_FILE = BASE_DIR / "data" / "cara_llm" / "cara_llm_scores.jsonl"
SUMMARY_FILE = BASE_DIR / "data" / "cara_llm" / "cara_llm_summary.md"

# --- Config ---
MODEL = "gpt-4o"
TEMPERATURE = 0.0  # deterministic
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
NUM_RUNS = 3  # score each pair N times, take mean

# =============================================================================
# Prompt template
# =============================================================================
SYSTEM_PROMPT = """You are an expert evaluator assessing the reasoning alignment between two AI medical agents.

You will be given:
1. A medical question with answer choices
2. The reasoning traces from two agents (they may or may not have selected the same final answer)

Your task: Rate how well the two agents' reasoning processes align with each other on a scale from 1 to 5.

Scoring rubric:
- 5 (Perfect alignment): Both agents follow essentially the same reasoning path, cite the same medical facts, and reach the answer through identical logic.
- 4 (Strong alignment): Both agents share the core reasoning pathway with minor differences in emphasis or supporting details.
- 3 (Moderate alignment): The agents share some reasoning elements but take partially different paths. Some overlap, some divergence.
- 2 (Weak alignment): The agents reason through substantially different paths. Different medical facts, different logical chains, minimal overlap.
- 1 (No alignment / Contradictory): The agents' reasoning contradicts each other, or they rely on completely incompatible explanations.

You must respond with EXACTLY this format:
SCORE: <integer 1-5>
JUSTIFICATION: <1-2 sentences explaining your rating>"""

USER_TEMPLATE_AGREE = """## Medical Question
{question_text}

## Gold Answer
{gold_answer}

## Agents' Shared Answer
{majority_answer}

## Agent A Reasoning ({agent_a_id})
{agent_a_reasoning}

## Agent B Reasoning ({agent_b_id})
{agent_b_reasoning}

Rate the reasoning alignment between Agent A and Agent B (1-5):"""

USER_TEMPLATE_DISAGREE = """## Medical Question
{question_text}

## Gold Answer
{gold_answer}

## Agent A Answer: {answer_a}
## Agent A Reasoning ({agent_a_id})
{agent_a_reasoning}

## Agent B Answer: {answer_b}
## Agent B Reasoning ({agent_b_id})
{agent_b_reasoning}

Rate the reasoning alignment between Agent A and Agent B (1-5):"""


def build_user_prompt(pair: dict) -> str:
    agent_a_reasoning = "\n".join(
        f"  {i+1}. {step}" for i, step in enumerate(pair["agent_a"]["reasoning_steps"])
    )
    agent_b_reasoning = "\n".join(
        f"  {i+1}. {step}" for i, step in enumerate(pair["agent_b"]["reasoning_steps"])
    )

    is_disagree = pair.get("pair_type") == "disagreement"

    if is_disagree:
        return USER_TEMPLATE_DISAGREE.format(
            question_text=pair["question_text"],
            gold_answer=pair["gold_answer"],
            answer_a=pair["agent_a"]["answer"],
            agent_a_id=pair["agent_a"]["id"],
            agent_a_reasoning=agent_a_reasoning,
            answer_b=pair["agent_b"]["answer"],
            agent_b_id=pair["agent_b"]["id"],
            agent_b_reasoning=agent_b_reasoning,
        )
    else:
        return USER_TEMPLATE_AGREE.format(
            question_text=pair["question_text"],
            gold_answer=pair["gold_answer"],
            majority_answer=pair["majority_answer"],
            agent_a_id=pair["agent_a"]["id"],
            agent_a_reasoning=agent_a_reasoning,
            agent_b_id=pair["agent_b"]["id"],
            agent_b_reasoning=agent_b_reasoning,
        )


def parse_response(text: str) -> tuple:
    """Parse SCORE and JUSTIFICATION from LLM response.
    Returns (score: int, justification: str) or (None, error_msg)."""
    lines = text.strip().split("\n")
    score = None
    justification = ""
    for line in lines:
        line = line.strip()
        if line.upper().startswith("SCORE:"):
            try:
                score = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.upper().startswith("JUSTIFICATION:"):
            justification = line.split(":", 1)[1].strip()

    if score is None or score < 1 or score > 5:
        return None, f"Failed to parse score from: {text[:200]}"
    return score, justification


def call_llm_once(client, pair: dict) -> dict:
    """Single GPT-4o call for one pair. Returns {score, justification, usage} or error."""
    user_prompt = build_user_prompt(pair)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=200,
            )
            text = response.choices[0].message.content
            score, justification = parse_response(text)
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }

            if score is None:
                log.warning(f"  {pair['pair_id']}: parse error (attempt {attempt+1}): {justification}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return {"score": None, "justification": justification, "raw": text, "usage": usage, "error": "parse_failed"}

            return {"score": score, "justification": justification, "usage": usage, "error": None}

        except Exception as e:
            log.warning(f"  {pair['pair_id']}: API error (attempt {attempt+1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return {"score": None, "justification": "", "usage": None, "error": str(e)}


def call_llm(client, pair: dict) -> dict:
    """Call GPT-4o NUM_RUNS times for a single pair, return mean score."""
    scores = []
    justifications = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0}
    errors = []

    for run_idx in range(NUM_RUNS):
        r = call_llm_once(client, pair)
        if r["score"] is not None:
            scores.append(r["score"])
            justifications.append(r["justification"])
        else:
            errors.append(r.get("error", "unknown"))
        if r.get("usage"):
            total_usage["prompt_tokens"] += r["usage"]["prompt_tokens"]
            total_usage["completion_tokens"] += r["usage"]["completion_tokens"]

    if scores:
        mean_score = sum(scores) / len(scores)
        sd_score = (sum((s - mean_score) ** 2 for s in scores) / len(scores)) ** 0.5 if len(scores) > 1 else 0.0
        mean_01 = (mean_score - 1) / 4.0  # normalize 1-5 → 0-1
        return {
            "pair_id": pair["pair_id"],
            "question_id": pair["question_id"],
            "system": pair["system"],
            "pair_type": pair.get("pair_type", "agreement"),
            "stratum": pair["stratum"],
            "cara_hyb": pair["cara_hyb"],
            "cara_sim": pair["cara_sim"],
            "contradiction_rate": pair["contradiction_rate"],
            "cara_llm_scores": scores,           # all individual runs
            "cara_llm_score": round(mean_score, 4),  # mean of valid runs
            "cara_llm_sd": round(sd_score, 4),        # inter-run SD
            "cara_llm_01": round(mean_01, 4),
            "n_valid_runs": len(scores),
            "justifications": justifications,
            "error": None,
            "model": MODEL,
            "usage": total_usage,
        }
    else:
        return {
            "pair_id": pair["pair_id"],
            "question_id": pair["question_id"],
            "system": pair["system"],
            "pair_type": pair.get("pair_type", "agreement"),
            "cara_hyb": pair["cara_hyb"],
            "cara_llm_scores": [],
            "cara_llm_score": None,
            "cara_llm_sd": None,
            "cara_llm_01": None,
            "n_valid_runs": 0,
            "justifications": [],
            "error": "; ".join(errors),
            "model": MODEL,
            "usage": total_usage if total_usage["prompt_tokens"] > 0 else None,
        }


def compute_correlation(results: list) -> dict:
    """Compute Pearson and Spearman correlation between CARA-HYB and CARA-LLM."""
    valid = [(r["cara_hyb"], r["cara_llm_01"]) for r in results
             if r["cara_llm_01"] is not None]
    n = len(valid)
    if n < 5:
        return {"n": n, "pearson": None, "spearman": None, "error": "too_few_valid"}

    x = [v[0] for v in valid]
    y = [v[1] for v in valid]

    # Pearson
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
    std_x = (sum((xi - mean_x) ** 2 for xi in x) / n) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y) / n) ** 0.5
    pearson = cov / (std_x * std_y) if std_x > 0 and std_y > 0 else None

    # Spearman (rank correlation)
    def rank(vals):
        sorted_vals = sorted(enumerate(vals), key=lambda t: t[1])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(sorted_vals):
            j = i
            while j < len(sorted_vals) - 1 and sorted_vals[j + 1][1] == sorted_vals[j][1]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[sorted_vals[k][0]] = avg_rank
            i = j + 1
        return ranks

    rx = rank(x)
    ry = rank(y)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    cov_r = sum((rxi - mean_rx) * (ryi - mean_ry) for rxi, ryi in zip(rx, ry)) / n
    std_rx = (sum((rxi - mean_rx) ** 2 for rxi in rx) / n) ** 0.5
    std_ry = (sum((ryi - mean_ry) ** 2 for ryi in ry) / n) ** 0.5
    spearman = cov_r / (std_rx * std_ry) if std_rx > 0 and std_ry > 0 else None

    return {"n": n, "pearson": pearson, "spearman": spearman, "error": None}


# =============================================================================
# Main
# =============================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="CARA-LLM validation")
    parser.add_argument("--disagree", action="store_true",
                        help="Score disagreement pairs only")
    parser.add_argument("--all", action="store_true",
                        help="Score both agreement + disagreement pairs")
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY environment variable.", flush=True)
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # Load pairs based on mode
    pairs = []
    if args.all:
        # Load both
        with open(AGREE_FILE, "r", encoding="utf-8") as f:
            agree_pairs = json.load(f)
        for p in agree_pairs:
            p.setdefault("pair_type", "agreement")
        pairs.extend(agree_pairs)
        print(f"Loaded {len(agree_pairs)} agreement pairs from {AGREE_FILE.name}", flush=True)

        if DISAGREE_FILE.exists():
            with open(DISAGREE_FILE, "r", encoding="utf-8") as f:
                disagree_pairs = json.load(f)
            pairs.extend(disagree_pairs)
            print(f"Loaded {len(disagree_pairs)} disagreement pairs from {DISAGREE_FILE.name}", flush=True)
        else:
            print(f"WARNING: {DISAGREE_FILE.name} not found, using agreement pairs only", flush=True)
    elif args.disagree:
        with open(DISAGREE_FILE, "r", encoding="utf-8") as f:
            pairs = json.load(f)
        print(f"Loaded {len(pairs)} disagreement pairs from {DISAGREE_FILE.name}", flush=True)
    else:
        with open(AGREE_FILE, "r", encoding="utf-8") as f:
            pairs = json.load(f)
        for p in pairs:
            p.setdefault("pair_type", "agreement")
        print(f"Loaded {len(pairs)} agreement pairs from {AGREE_FILE.name}", flush=True)

    print(f"Total pairs to process: {len(pairs)}", flush=True)

    # Resume support: skip already-scored pairs
    done_ids = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                done_ids.add(rec["pair_id"])
        print(f"Resuming: {len(done_ids)} pairs already scored", flush=True)

    remaining = [p for p in pairs if p["pair_id"] not in done_ids]
    print(f"Remaining: {len(remaining)} pairs to score", flush=True)
    print(f"Model: {MODEL}, temperature: {TEMPERATURE}", flush=True)
    print(flush=True)

    # Process
    total_prompt_tokens = 0
    total_completion_tokens = 0
    results = []

    with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
        for i, pair in enumerate(remaining):
            result = call_llm(client, pair)
            results.append(result)
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()

            if result["cara_llm_score"] is not None:
                runs_str = ",".join(str(s) for s in result["cara_llm_scores"])
                status = f"runs=[{runs_str}] mean={result['cara_llm_score']:.2f} sd={result['cara_llm_sd']:.2f}"
            else:
                status = f"error={result['error']}"
            print(f"  [{i+1}/{len(remaining)}] {pair['pair_id']} ({pair['system']}, "
                  f"hyb={pair['cara_hyb']:.3f}): {status}", flush=True)

            if result.get("usage"):
                total_prompt_tokens += result["usage"]["prompt_tokens"]
                total_completion_tokens += result["usage"]["completion_tokens"]

    # Load all results (including previously completed)
    all_results = []
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            all_results.append(json.loads(line))

    # Compute correlation
    print(flush=True)
    print("=" * 60, flush=True)
    print("CARA-LLM VALIDATION SUMMARY", flush=True)
    print("=" * 60, flush=True)

    errors = sum(1 for r in all_results if r["error"] is not None)
    print(f"  Total pairs: {len(all_results)}", flush=True)
    print(f"  Errors: {errors}", flush=True)
    print(f"  Runs per pair: {NUM_RUNS}", flush=True)
    print(f"  Tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}", flush=True)

    # Inter-run stability
    sds = [r["cara_llm_sd"] for r in all_results if r.get("cara_llm_sd") is not None]
    if sds:
        mean_sd = sum(sds) / len(sds)
        max_sd = max(sds)
        print(f"\n  Inter-run stability ({NUM_RUNS} runs/pair):", flush=True)
        print(f"    Mean SD: {mean_sd:.4f}", flush=True)
        print(f"    Max SD:  {max_sd:.4f}", flush=True)
        print(f"    Pairs with SD=0 (perfect agreement): {sum(1 for s in sds if s == 0.0)}/{len(sds)}", flush=True)

    corr = compute_correlation(all_results)
    print(f"\n  Correlation (CARA-HYB vs CARA-LLM):", flush=True)
    print(f"    Pearson r  = {corr['pearson']:.4f}" if corr["pearson"] else "    Pearson r  = N/A", flush=True)
    print(f"    Spearman ρ = {corr['spearman']:.4f}" if corr["spearman"] else "    Spearman ρ = N/A", flush=True)
    print(f"    n = {corr['n']}", flush=True)

    # Score distribution
    from collections import Counter
    score_dist = Counter(r["cara_llm_score"] for r in all_results if r["cara_llm_score"] is not None)
    print(f"\n  Score distribution:", flush=True)
    for s in range(1, 6):
        print(f"    {s}: {score_dist.get(s, 0)}", flush=True)

    # Per-stratum mean
    print(f"\n  Per-stratum mean:", flush=True)
    from collections import defaultdict
    strata = defaultdict(lambda: {"hyb": [], "llm": []})
    for r in all_results:
        if r.get("cara_llm_01") is not None:
            strata[r.get("stratum", "unknown")]["hyb"].append(r["cara_hyb"])
            strata[r.get("stratum", "unknown")]["llm"].append(r["cara_llm_01"])
    for s in ["low", "mid", "high"]:
        if s in strata:
            mean_h = sum(strata[s]["hyb"]) / len(strata[s]["hyb"])
            mean_l = sum(strata[s]["llm"]) / len(strata[s]["llm"])
            print(f"    {s:4s}: CARA-HYB={mean_h:.4f}, CARA-LLM={mean_l:.4f}, n={len(strata[s]['hyb'])}", flush=True)

    # Per-pair-type breakdown
    from collections import Counter as Ctr
    type_counts = Ctr(r.get("pair_type", "agreement") for r in all_results)
    print(f"\n  Per-pair-type:", flush=True)
    for pt in ["agreement", "disagreement"]:
        subset = [r for r in all_results if r.get("pair_type", "agreement") == pt and r.get("cara_llm_01") is not None]
        if subset:
            pt_corr = compute_correlation(subset)
            mean_hyb = sum(r["cara_hyb"] for r in subset) / len(subset)
            mean_llm = sum(r["cara_llm_01"] for r in subset) / len(subset)
            r_str = f"r={pt_corr['pearson']:.4f}" if pt_corr["pearson"] else "r=N/A"
            print(f"    {pt:12s}: n={len(subset)}, CARA-HYB={mean_hyb:.4f}, CARA-LLM={mean_llm:.4f}, {r_str}", flush=True)

    # Write summary
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("# CARA-LLM Validation Summary\n\n")
        f.write(f"Generated by `run_cara_llm.py` using `{MODEL}`\n\n")
        f.write("## Overall Correlation: CARA-HYB vs CARA-LLM\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Pearson r | {corr['pearson']:.4f} |\n" if corr["pearson"] else "| Pearson r | N/A |\n")
        f.write(f"| Spearman rho | {corr['spearman']:.4f} |\n" if corr["spearman"] else "| Spearman rho | N/A |\n")
        f.write(f"| n | {corr['n']} |\n")
        f.write(f"| Errors | {errors} |\n")
        f.write(f"| Runs per pair | {NUM_RUNS} |\n")
        if sds:
            f.write(f"| Mean inter-run SD | {mean_sd:.4f} |\n")
            f.write(f"| Max inter-run SD | {max_sd:.4f} |\n")
            f.write(f"| Pairs with perfect agreement | {sum(1 for s in sds if s == 0.0)}/{len(sds)} |\n")
        f.write("\n")

        # Per pair type
        f.write("## Per Pair Type\n\n")
        f.write("| Type | n | CARA-HYB mean | CARA-LLM mean | Pearson r | Spearman rho |\n")
        f.write("|------|---|---------------|---------------|-----------|-------------|\n")
        for pt in ["agreement", "disagreement"]:
            subset = [r for r in all_results if r.get("pair_type", "agreement") == pt and r.get("cara_llm_01") is not None]
            if subset:
                pt_corr = compute_correlation(subset)
                mean_hyb = sum(r["cara_hyb"] for r in subset) / len(subset)
                mean_llm = sum(r["cara_llm_01"] for r in subset) / len(subset)
                r_val = f"{pt_corr['pearson']:.4f}" if pt_corr["pearson"] else "N/A"
                rho_val = f"{pt_corr['spearman']:.4f}" if pt_corr["spearman"] else "N/A"
                f.write(f"| {pt} | {len(subset)} | {mean_hyb:.4f} | {mean_llm:.4f} | {r_val} | {rho_val} |\n")
        f.write("\n")

        f.write("## Score Distribution\n\n")
        f.write("| Score | Count |\n|-------|-------|\n")
        for s in range(1, 6):
            f.write(f"| {s} | {score_dist.get(s, 0)} |\n")
        f.write(f"\n## Per-Stratum Mean\n\n")
        f.write("| Stratum | CARA-HYB | CARA-LLM | n |\n")
        f.write("|---------|----------|----------|---|\n")
        for s in ["low", "mid", "high"]:
            if s in strata:
                mean_h = sum(strata[s]["hyb"]) / len(strata[s]["hyb"])
                mean_l = sum(strata[s]["llm"]) / len(strata[s]["llm"])
                f.write(f"| {s} | {mean_h:.4f} | {mean_l:.4f} | {len(strata[s]['hyb'])} |\n")
        f.write(f"\n## Configuration\n\n")
        f.write(f"- Model: `{MODEL}`\n")
        f.write(f"- Temperature: {TEMPERATURE}\n")
        f.write(f"- Runs per pair: {NUM_RUNS} (mean of valid runs)\n")
        f.write(f"- Total tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}\n")

    print(f"\n  Summary written to {SUMMARY_FILE}", flush=True)
    print("DONE.", flush=True)


if __name__ == "__main__":
    main()
