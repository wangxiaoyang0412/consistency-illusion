"""Extract 50 lowest-CARA correct-answer cases from D1 N=500 for failure mode taxonomy.

For the "consistency illusion" analysis (§7 of paper), we want cases where:
  - Agents agree on the CORRECT answer (majority_answer == gold_answer)
  - But CARA-HYB is low → reasoning is misaligned despite correct consensus

We focus on M3-GDP_r1 (the best system) because:
  - Even GDP's best still has misalignment cases → shows limits of intervention
  - Also extract M3_r1 and M4_r0 for comparison

Output:
  analysis/failure_modes/lowest_cara_cases.jsonl
    - 50 cases with full question, traces, CARA details
  analysis/failure_modes/lowest_cara_summary.md
    - Overview statistics and initial observations

Usage:
    python extract_lowest_cara.py

Note: This script expects raw agent traces and the MedQA subsample, which
are not redistributed in this anonymous release (license + size). The
pre-computed output (`classified_cases.jsonl`) is provided under
`data/failure_modes/`.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
import os

# --- Paths (configurable via PROJECT_ROOT env var) ---
PROJECT = Path(os.environ.get("PROJECT_ROOT", "."))
CARA_FILE = PROJECT / "data" / "cara_scores" / "cara_scores_d1_n500.jsonl"
MEDQA_FILE = PROJECT / "data" / "datasets" / "medqa_sub500.json"  # not redistributed
TRACE_DIRS = {
    "sub200_M3GDP_D1": PROJECT / "data" / "traces" / "sub200_M3GDP_D1" / "raw_traces.jsonl",
    "sub200_M3_D1": PROJECT / "data" / "traces" / "sub200_M3_D1" / "raw_traces.jsonl",
    "sub200_M4_D1": PROJECT / "data" / "traces" / "sub200_M4_D1" / "raw_traces.jsonl",
}  # raw traces not redistributed
OUTPUT_DIR = PROJECT / "data" / "failure_modes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# STEP 1: Load gold answers
# =============================================================================
print("=" * 60, flush=True)
print("STEP 1: Loading gold answers from MedQA sub500", flush=True)
print("=" * 60, flush=True)

with open(MEDQA_FILE, encoding="utf-8") as f:
    medqa_raw = json.load(f)

# Build question_id → gold_answer mapping
# question_indices maps position-in-subsample to original-test-index
q_indices = medqa_raw["question_indices"]
questions = medqa_raw["questions"]

gold_answers = {}  # question_id -> answer_letter
question_texts = {}  # question_id -> full question text with options
question_meta = {}  # question_id -> {meta_info, options, answer_text}

for i, (orig_idx, q) in enumerate(zip(q_indices, questions)):
    qid = f"MQA_{orig_idx:04d}"
    gold_answers[qid] = q["answer_idx"]
    # Build question text with options
    opts = q["options"]
    q_text = q["question"]
    for letter in sorted(opts.keys()):
        q_text += f"\n{letter}. {opts[letter]}"
    question_texts[qid] = q_text
    question_meta[qid] = {
        "meta_info": q["meta_info"],
        "options": q["options"],
        "answer_text": q["answer"],
        "answer_idx": q["answer_idx"],
    }

print(f"  Loaded {len(gold_answers)} gold answers", flush=True)


# =============================================================================
# STEP 2: Load CARA scores and filter for correct-answer cases
# =============================================================================
print("\n" + "=" * 60, flush=True)
print("STEP 2: Loading CARA scores and filtering", flush=True)
print("=" * 60, flush=True)

cara_records = []
with open(CARA_FILE, encoding="utf-8") as f:
    for line in f:
        rec = json.loads(line.strip())
        cara_records.append(rec)

print(f"  Total CARA records: {len(cara_records)}", flush=True)

# Filter for GDP_r1 (primary), M3_r1 (comparison), M4_r0 (baseline)
target_cells = {
    ("sub200_M3GDP_D1", 1): "GDP_r1",
    ("sub200_M3_D1", 1): "M3_r1",
    ("sub200_M4_D1", 0): "M4_r0",
}

# Collect valid records per cell
cell_records = defaultdict(list)
for rec in cara_records:
    key = (rec["cell_id"], rec["cara_round"])
    if key in target_cells:
        cell_records[target_cells[key]].append(rec)

for cell_name, recs in cell_records.items():
    print(f"  {cell_name}: {len(recs)} records", flush=True)

# Filter for correct-answer cases with valid CARA scores
correct_cases = defaultdict(list)
for cell_name, recs in cell_records.items():
    for rec in recs:
        qid = rec["question_id"]
        if qid not in gold_answers:
            continue
        if rec["error"] is not None:
            continue
        if rec["cara_hyb_01"] is None:
            continue
        # Check if majority answer matches gold
        if rec["majority_answer"] == gold_answers[qid]:
            correct_cases[cell_name].append(rec)

for cell_name in sorted(correct_cases.keys()):
    print(f"  {cell_name} correct-answer cases: {len(correct_cases[cell_name])}", flush=True)


# =============================================================================
# STEP 3: Extract 50 lowest-CARA cases from GDP_r1
# =============================================================================
print("\n" + "=" * 60, flush=True)
print("STEP 3: Extracting 50 lowest-CARA from GDP_r1", flush=True)
print("=" * 60, flush=True)

gdp_correct = correct_cases["GDP_r1"]
gdp_correct.sort(key=lambda r: r["cara_hyb_01"])

n_extract = min(50, len(gdp_correct))
lowest_50 = gdp_correct[:n_extract]

print(f"  GDP_r1 correct-answer cases: {len(gdp_correct)}", flush=True)
print(f"  Extracting bottom {n_extract} by CARA-HYB", flush=True)
print(f"  CARA-HYB range: [{lowest_50[0]['cara_hyb_01']:.4f}, "
      f"{lowest_50[-1]['cara_hyb_01']:.4f}]", flush=True)

# Also get M3_r1 and M4_r0 CARA for the same questions (for comparison)
m3_cara = {r["question_id"]: r for r in cell_records.get("M3_r1", [])}
m4_cara = {r["question_id"]: r for r in cell_records.get("M4_r0", [])}


# =============================================================================
# STEP 4: Load traces for the 50 questions
# =============================================================================
print("\n" + "=" * 60, flush=True)
print("STEP 4: Loading traces for 50 questions", flush=True)
print("=" * 60, flush=True)

target_qids = {r["question_id"] for r in lowest_50}

# Load all traces indexed by (cell_id, question_id)
all_traces = defaultdict(list)  # (cell_id, question_id) -> [trace, ...]
for cell_id, trace_path in TRACE_DIRS.items():
    with open(trace_path, encoding="utf-8") as f:
        for line in f:
            trace = json.loads(line.strip())
            if trace["question_id"] in target_qids:
                all_traces[(cell_id, trace["question_id"])].append(trace)

print(f"  Loaded traces for {len(target_qids)} questions across "
      f"{len(TRACE_DIRS)} systems", flush=True)


# =============================================================================
# STEP 5: Build enriched output
# =============================================================================
print("\n" + "=" * 60, flush=True)
print("STEP 5: Building enriched output", flush=True)
print("=" * 60, flush=True)

output_cases = []
for rank, cara_rec in enumerate(lowest_50, 1):
    qid = cara_rec["question_id"]

    # Get traces for this question — GDP system
    gdp_traces = all_traces.get(("sub200_M3GDP_D1", qid), [])
    m3_traces = all_traces.get(("sub200_M3_D1", qid), [])
    m4_traces = all_traces.get(("sub200_M4_D1", qid), [])

    # Build agent responses for GDP_r1 (round 1 only for debate)
    gdp_r0 = [t for t in gdp_traces if t["round"] == 0]
    gdp_r1 = [t for t in gdp_traces if t["round"] == 1]

    m3_r0 = [t for t in m3_traces if t["round"] == 0]
    m3_r1 = [t for t in m3_traces if t["round"] == 1]

    m4_r0 = [t for t in m4_traces if t["round"] == 0]

    case = {
        "rank": rank,
        "question_id": qid,
        "question_text": question_texts.get(qid, "NOT FOUND"),
        "gold_answer": gold_answers.get(qid, "?"),
        "meta_info": question_meta.get(qid, {}).get("meta_info", "?"),
        "options": question_meta.get(qid, {}).get("options", {}),
        # CARA scores
        "gdp_r1_cara_hyb": cara_rec["cara_hyb_01"],
        "gdp_r1_cara_sim": cara_rec["cara_sim"],
        "gdp_r1_cr": cara_rec["contradiction_rate"],
        "gdp_r1_agreement_set": cara_rec["agreement_set"],
        "gdp_r1_agreement_set_size": cara_rec["agreement_set_size"],
        "gdp_r1_num_contradictions": cara_rec["num_contradictions"],
        "gdp_r1_num_nli_pairs": cara_rec["num_nli_pairs_total"],
        "gdp_r1_num_steps_per_agent": cara_rec["num_steps_per_agent"],
        "gdp_r1_zero_step_agents": cara_rec["zero_step_agents"],
        # Comparison CARA scores
        "m3_r1_cara_hyb": m3_cara.get(qid, {}).get("cara_hyb_01"),
        "m3_r1_cr": m3_cara.get(qid, {}).get("contradiction_rate"),
        "m3_r1_error": m3_cara.get(qid, {}).get("error"),
        "m4_r0_cara_hyb": m4_cara.get(qid, {}).get("cara_hyb_01"),
        "m4_r0_cr": m4_cara.get(qid, {}).get("contradiction_rate"),
        # Agent reasoning traces (GDP round 1 — the post-debate reasoning)
        "gdp_r1_traces": [
            {
                "agent_id": t["agent_id"],
                "extracted_answer": t["extracted_answer"],
                "response": t["response"],
                "gdp_parse": t.get("gdp_parse"),
            }
            for t in sorted(gdp_r1, key=lambda x: x["agent_id"])
        ],
        # GDP round 0 for reference
        "gdp_r0_traces": [
            {
                "agent_id": t["agent_id"],
                "extracted_answer": t["extracted_answer"],
                "response": t["response"],
                "gdp_parse": t.get("gdp_parse"),
            }
            for t in sorted(gdp_r0, key=lambda x: x["agent_id"])
        ],
        # Failure mode classification (to be filled in)
        "failure_mode": None,
        "failure_mode_notes": None,
    }
    output_cases.append(case)

# Write JSONL output
output_file = OUTPUT_DIR / "lowest_cara_cases.jsonl"
with open(output_file, "w", encoding="utf-8") as f:
    for case in output_cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")

print(f"  Wrote {len(output_cases)} cases to {output_file}", flush=True)


# =============================================================================
# STEP 6: Generate summary statistics
# =============================================================================
print("\n" + "=" * 60, flush=True)
print("STEP 6: Summary statistics", flush=True)
print("=" * 60, flush=True)

hyb_scores = [c["gdp_r1_cara_hyb"] for c in output_cases]
cr_scores = [c["gdp_r1_cr"] for c in output_cases if c["gdp_r1_cr"] is not None]
mean_hyb = sum(hyb_scores) / len(hyb_scores)
mean_cr = sum(cr_scores) / len(cr_scores) if cr_scores else 0

# Count by meta_info (step1 vs step2&3)
meta_counts = Counter(c["meta_info"] for c in output_cases)

# Agreement set size distribution
agree_sizes = Counter(c["gdp_r1_agreement_set_size"] for c in output_cases)

# Zero-step agent cases
zero_step_cases = sum(1 for c in output_cases if c["gdp_r1_zero_step_agents"])

# Step count statistics
all_steps = []
for c in output_cases:
    for agent, n_steps in c["gdp_r1_num_steps_per_agent"].items():
        all_steps.append(n_steps)
mean_steps = sum(all_steps) / len(all_steps) if all_steps else 0

# Contradiction statistics
contradictions = [c["gdp_r1_num_contradictions"] for c in output_cases]
any_contradiction = sum(1 for x in contradictions if x > 0)

print(f"  Cases extracted: {len(output_cases)}", flush=True)
print(f"  CARA-HYB range: [{min(hyb_scores):.4f}, {max(hyb_scores):.4f}]", flush=True)
print(f"  CARA-HYB mean:  {mean_hyb:.4f}", flush=True)
print(f"  CR mean:         {mean_cr:.4f}", flush=True)
print(f"  Meta info:       {dict(meta_counts)}", flush=True)
print(f"  Agreement sizes: {dict(agree_sizes)}", flush=True)
print(f"  Zero-step cases: {zero_step_cases}", flush=True)
print(f"  Mean steps/agent:{mean_steps:.1f}", flush=True)
print(f"  Cases w/ contradictions: {any_contradiction}/{len(output_cases)}", flush=True)

# Compare with M3_r1 and M4_r0 on same questions
m3_available = [c for c in output_cases if c["m3_r1_cara_hyb"] is not None]
m4_available = [c for c in output_cases if c["m4_r0_cara_hyb"] is not None]

if m3_available:
    m3_mean = sum(c["m3_r1_cara_hyb"] for c in m3_available) / len(m3_available)
    gdp_mean_matched = sum(c["gdp_r1_cara_hyb"] for c in m3_available) / len(m3_available)
    print(f"\n  M3_r1 on same Qs: {m3_mean:.4f} (N={len(m3_available)}) "
          f"vs GDP {gdp_mean_matched:.4f}", flush=True)

if m4_available:
    m4_mean = sum(c["m4_r0_cara_hyb"] for c in m4_available) / len(m4_available)
    print(f"  M4_r0 on same Qs: {m4_mean:.4f} (N={len(m4_available)})", flush=True)

# Write summary markdown
summary_file = OUTPUT_DIR / "lowest_cara_summary.md"
with open(summary_file, "w", encoding="utf-8") as f:
    f.write("# Failure Mode Taxonomy: 50 Lowest-CARA Correct-Answer Cases (D1 GDP_r1)\n\n")
    f.write(f"Source: `{CARA_FILE.name}` filtered for GDP_r1 correct-answer cases\n\n")
    f.write("## Selection Criteria\n\n")
    f.write("- System: M3-GDP round 1 (post-debate, best system)\n")
    f.write("- Filter: majority_answer == gold_answer (correct consensus)\n")
    f.write("- Sort: CARA-HYB ascending (worst alignment first)\n")
    f.write(f"- Pool: {len(gdp_correct)} correct-answer cases from {len(cell_records['GDP_r1'])} total\n")
    f.write(f"- Extracted: bottom {n_extract} cases\n\n")

    f.write("## Summary Statistics\n\n")
    f.write(f"| Metric | Value |\n")
    f.write(f"|--------|-------|\n")
    f.write(f"| CARA-HYB range | [{min(hyb_scores):.4f}, {max(hyb_scores):.4f}] |\n")
    f.write(f"| CARA-HYB mean | {mean_hyb:.4f} |\n")
    f.write(f"| CR mean | {mean_cr:.4f} |\n")
    f.write(f"| Cases w/ contradictions | {any_contradiction}/{len(output_cases)} |\n")
    f.write(f"| Zero-step agent cases | {zero_step_cases} |\n")
    f.write(f"| Mean steps per agent | {mean_steps:.1f} |\n")
    f.write(f"| Step1 questions | {meta_counts.get('step1', 0)} |\n")
    f.write(f"| Step2&3 questions | {meta_counts.get('step2&3', 0)} |\n")
    f.write(f"| Agreement set = 2 | {agree_sizes.get(2, 0)} |\n")
    f.write(f"| Agreement set = 3 | {agree_sizes.get(3, 0)} |\n\n")

    if m3_available:
        f.write("## Cross-System Comparison (Same Questions)\n\n")
        f.write(f"| System | Mean CARA-HYB | N |\n")
        f.write(f"|--------|--------------|---|\n")
        f.write(f"| GDP_r1 | {gdp_mean_matched:.4f} | {len(m3_available)} |\n")
        f.write(f"| M3_r1 | {m3_mean:.4f} | {len(m3_available)} |\n")
        if m4_available:
            f.write(f"| M4_r0 | {m4_mean:.4f} | {len(m4_available)} |\n")
        f.write("\n")

    f.write("## Proposed Failure Mode Categories\n\n")
    f.write("| Code | Category | Description |\n")
    f.write("|------|----------|-------------|\n")
    f.write("| FM1 | Complementary Reasoning | Agents reach same answer via genuinely different (non-contradictory) reasoning paths. Low SIM but low CR. |\n")
    f.write("| FM2 | Granularity Mismatch | One agent reasons in detail, another gives superficial analysis. Step count imbalance drives low SIM. |\n")
    f.write("| FM3 | Contradictory Premises | Agents cite contradictory medical facts/mechanisms but arrive at same answer. High CR. |\n")
    f.write("| FM4 | Sycophantic Convergence | Agent copies answer without substantive reasoning in round 1. Near-zero steps or BERTScore >0.9 to majority. |\n")
    f.write("| FM5 | Terminology Divergence | Agents use different medical terminology for same concept. Low embedding similarity despite conceptual agreement. |\n")
    f.write("| FM6 | Partial Overlap | Agents share some reasoning steps but diverge on key ones. Mixed SIM/CR signals. |\n\n")

    f.write("## Case List (Top 10 Preview)\n\n")
    for c in output_cases[:10]:
        f.write(f"### Rank {c['rank']}: {c['question_id']} "
                f"(CARA-HYB={c['gdp_r1_cara_hyb']:.4f}, CR={c['gdp_r1_cr']:.4f})\n\n")
        f.write(f"- **Gold answer**: {c['gold_answer']}\n")
        f.write(f"- **Meta**: {c['meta_info']}\n")
        f.write(f"- **Agreement set size**: {c['gdp_r1_agreement_set_size']}\n")
        f.write(f"- **Steps per agent**: {c['gdp_r1_num_steps_per_agent']}\n")
        f.write(f"- **Contradictions**: {c['gdp_r1_num_contradictions']}/{c['gdp_r1_num_nli_pairs']}\n")
        if c["gdp_r1_zero_step_agents"]:
            f.write(f"- **Zero-step agents**: {c['gdp_r1_zero_step_agents']}\n")
        f.write(f"- **M3_r1 CARA**: {c['m3_r1_cara_hyb']}\n")
        f.write(f"- **M4_r0 CARA**: {c['m4_r0_cara_hyb']}\n")
        f.write(f"- **Failure mode**: _TBD_\n\n")

        # Show question (truncated)
        q_text = c["question_text"]
        if len(q_text) > 500:
            q_text = q_text[:500] + "..."
        f.write(f"**Question**: {q_text}\n\n")

        # Show GDP r1 agent responses (truncated)
        for t in c["gdp_r1_traces"]:
            resp = t["response"]
            if len(resp) > 400:
                resp = resp[:400] + "..."
            f.write(f"**{t['agent_id']}** (answer: {t['extracted_answer']}): "
                    f"{resp}\n\n")
        f.write("---\n\n")

    f.write(f"\n*Full data: `{output_file.name}` ({len(output_cases)} cases)*\n")

print(f"\n  Summary written to {summary_file}", flush=True)
print("\nDONE.", flush=True)
