"""Classify failure modes for the 50 lowest-CARA correct-answer cases.

Uses heuristic rules based on CARA sub-metrics to assign initial categories,
then outputs a structured report for manual verification.

Categories:
  FM1: Complementary Reasoning — different valid paths, low SIM, low CR
  FM2: Granularity Mismatch — step count imbalance, low SIM
  FM3: Contradictory Premises — high CR, agents cite conflicting facts
  FM4: Sycophantic Convergence — near-zero steps (not expected in GDP)
  FM5: Terminology Divergence — low SIM despite conceptual agreement
  FM6: Partial Overlap — mixed signals, moderate SIM and CR

Heuristic thresholds (calibrated on first 10 cases):
  - High CR: contradiction_rate > 0.3
  - Step imbalance: max_steps / min_steps > 2.0
  - Low SIM: cara_sim < 0.80

Usage:
    python classify_failure_modes.py

Expects the output of `extract_lowest_cara.py` as input. The
pre-computed classification is provided under `data/failure_modes/`.
"""
import json
from collections import Counter
from pathlib import Path
import os

# --- Paths (configurable via PROJECT_ROOT env var) ---
PROJECT = Path(os.environ.get("PROJECT_ROOT", "."))
INPUT_FILE = PROJECT / "data" / "failure_modes" / "lowest_cara_cases.jsonl"
OUTPUT_FILE = PROJECT / "data" / "failure_modes" / "classified_cases.jsonl"
REPORT_FILE = PROJECT / "data" / "failure_modes" / "taxonomy_report.md"

# --- Load cases ---
cases = []
with open(INPUT_FILE, encoding="utf-8") as f:
    for line in f:
        cases.append(json.loads(line.strip()))

print(f"Loaded {len(cases)} cases", flush=True)


# --- Heuristic classification ---
def classify(case):
    """Assign failure mode based on CARA sub-metrics."""
    cr = case["gdp_r1_cr"]
    hyb = case["gdp_r1_cara_hyb"]
    sim = case.get("gdp_r1_cara_sim")
    steps = case["gdp_r1_num_steps_per_agent"]
    zero_steps = case["gdp_r1_zero_step_agents"]
    n_contradictions = case["gdp_r1_num_contradictions"]
    agree_size = case["gdp_r1_agreement_set_size"]

    step_values = list(steps.values())
    max_step = max(step_values)
    min_step = min(step_values)
    step_ratio = max_step / min_step if min_step > 0 else float("inf")

    # FM4: Sycophantic Convergence (zero-step agents)
    if zero_steps:
        return "FM4", "Zero-step agent(s) present — agent adopted answer without reasoning"

    # High CR threshold
    high_cr = cr > 0.3

    # Step imbalance threshold
    step_imbalanced = step_ratio > 2.0

    # Determine primary failure mode
    if high_cr and step_imbalanced:
        return "FM2+FM3", (
            f"Both granularity mismatch (step ratio {step_ratio:.1f}x) "
            f"and contradictory premises (CR={cr:.2f})"
        )

    if step_imbalanced and not high_cr:
        return "FM2", (
            f"Granularity mismatch: step ratio {step_ratio:.1f}x "
            f"({min_step} vs {max_step} steps), CR={cr:.2f} (low)"
        )

    if high_cr and not step_imbalanced:
        return "FM3", (
            f"Contradictory premises: CR={cr:.2f}, "
            f"{n_contradictions} contradictions, "
            f"steps balanced ({'/'.join(str(s) for s in step_values)})"
        )

    # Low SIM with low CR and balanced steps → complementary reasoning
    if sim is not None and sim < 0.80 and cr < 0.15:
        return "FM1", (
            f"Complementary reasoning: SIM={sim:.3f} (low), "
            f"CR={cr:.2f} (low), steps balanced"
        )

    # Low SIM with low CR → likely terminology divergence or complementary
    if sim is not None and sim < 0.80:
        return "FM5", (
            f"Terminology divergence: SIM={sim:.3f} (low), "
            f"CR={cr:.2f}, may use different medical terms for same concepts"
        )

    # Default: partial overlap
    return "FM6", (
        f"Partial overlap: moderate misalignment "
        f"(HYB={hyb:.4f}, SIM={sim:.3f}, CR={cr:.2f}, "
        f"steps {'/'.join(str(s) for s in step_values)})"
    )


# --- Classify all cases ---
for case in cases:
    fm, notes = classify(case)
    case["failure_mode"] = fm
    case["failure_mode_notes"] = notes

# --- Write classified output ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for case in cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")

print(f"Classified {len(cases)} cases -> {OUTPUT_FILE}", flush=True)


# --- Count by category ---
fm_counts = Counter(c["failure_mode"] for c in cases)
print("\nFailure mode distribution:", flush=True)
for fm, count in fm_counts.most_common():
    print(f"  {fm}: {count}", flush=True)


# --- Generate taxonomy report ---
# Category descriptions
FM_NAMES = {
    "FM1": "Complementary Reasoning",
    "FM2": "Granularity Mismatch",
    "FM3": "Contradictory Premises",
    "FM4": "Sycophantic Convergence",
    "FM5": "Terminology Divergence",
    "FM6": "Partial Overlap",
    "FM2+FM3": "Granularity Mismatch + Contradictory Premises",
}

FM_DESCRIPTIONS = {
    "FM1": "Agents reach the same correct answer via genuinely different but non-contradictory reasoning paths. Low embedding similarity (SIM) indicates divergent reasoning content, while low contradiction rate (CR) confirms no logical conflicts. This may reflect legitimate medical reasoning diversity where multiple valid diagnostic pathways lead to the same conclusion.",
    "FM2": "One agent produces significantly more detailed reasoning than another (step count ratio >2x). The embedding similarity is lowered primarily by the granularity difference rather than substantive disagreement. This is an artifact of response verbosity differences rather than genuine reasoning misalignment.",
    "FM3": "Agents cite contradictory medical facts, mechanisms, or clinical interpretations but still converge on the same answer. High contradiction rate (CR >0.3) indicates NLI-detected logical conflicts between reasoning steps. This is the most clinically concerning failure mode — correct answers may be reached for partially wrong reasons.",
    "FM4": "An agent adopts the majority answer without producing substantive reasoning steps. Detected by zero reasoning steps after decomposition. GDP protocol largely eliminates this mode through mandatory CLAIM/GROUND structure.",
    "FM5": "Agents use different medical terminology or framing for the same underlying concept. Low embedding similarity despite no logical contradictions. This may be an artifact of the embedding model's sensitivity to surface form rather than genuine misalignment.",
    "FM6": "Agents share some reasoning steps but diverge on others, producing moderate alignment scores without extreme CR or SIM values. This is the baseline misalignment mode — partial but not complete reasoning overlap.",
    "FM2+FM3": "Combination of granularity mismatch and contradictory premises. Agents differ in both reasoning depth and substance, with some steps directly contradicting each other.",
}

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write("# Failure Mode Taxonomy — D1 N=500 GDP_r1 (50 Lowest-CARA Correct Cases)\n\n")

    # Summary table
    f.write("## 1. Distribution\n\n")
    f.write("| Code | Category | Count | % |\n")
    f.write("|------|----------|-------|---|\n")
    for fm, count in fm_counts.most_common():
        pct = count / len(cases) * 100
        name = FM_NAMES.get(fm, fm)
        f.write(f"| {fm} | {name} | {count} | {pct:.0f}% |\n")
    f.write(f"| **Total** | | **{len(cases)}** | **100%** |\n\n")

    # Category descriptions
    f.write("## 2. Category Definitions\n\n")
    for fm in sorted(set(c["failure_mode"] for c in cases)):
        name = FM_NAMES.get(fm, fm)
        desc = FM_DESCRIPTIONS.get(fm, "")
        f.write(f"### {fm}: {name}\n\n")
        f.write(f"{desc}\n\n")

        # Examples from this category
        examples = [c for c in cases if c["failure_mode"] == fm]
        f.write(f"**Representative examples** ({len(examples)} cases):\n\n")
        for ex in examples[:3]:  # Show up to 3 examples
            f.write(f"- **{ex['question_id']}** (Rank {ex['rank']}, "
                    f"HYB={ex['gdp_r1_cara_hyb']:.4f}, "
                    f"CR={ex['gdp_r1_cr']:.2f}): "
                    f"{ex['failure_mode_notes']}\n")
        f.write("\n")

    # Quantitative profile per category
    f.write("## 3. Quantitative Profiles\n\n")
    f.write("| Category | N | Mean HYB | Mean CR | Mean SIM | "
            "Mean Step Ratio | Mean Steps |\n")
    f.write("|----------|---|----------|---------|----------|"
            "----------------|------------|\n")

    for fm in [x[0] for x in fm_counts.most_common()]:
        subset = [c for c in cases if c["failure_mode"] == fm]
        n = len(subset)
        mean_hyb = sum(c["gdp_r1_cara_hyb"] for c in subset) / n
        mean_cr = sum(c["gdp_r1_cr"] for c in subset) / n

        sims = [c["gdp_r1_cara_sim"] for c in subset if c["gdp_r1_cara_sim"] is not None]
        mean_sim = sum(sims) / len(sims) if sims else 0

        ratios = []
        all_steps_cat = []
        for c in subset:
            sv = list(c["gdp_r1_num_steps_per_agent"].values())
            if min(sv) > 0:
                ratios.append(max(sv) / min(sv))
            all_steps_cat.extend(sv)
        mean_ratio = sum(ratios) / len(ratios) if ratios else 0
        mean_steps = sum(all_steps_cat) / len(all_steps_cat) if all_steps_cat else 0

        name = FM_NAMES.get(fm, fm)
        f.write(f"| {fm} ({name}) | {n} | {mean_hyb:.4f} | "
                f"{mean_cr:.2f} | {mean_sim:.3f} | "
                f"{mean_ratio:.1f}x | {mean_steps:.1f} |\n")
    f.write("\n")

    # Cross-system comparison
    f.write("## 4. Cross-System View\n\n")
    f.write("For the same 50 questions, how do M3_r1 and M4_r0 compare?\n\n")
    f.write("| Category | GDP_r1 Mean | M3_r1 Mean (avail) | M4_r0 Mean |\n")
    f.write("|----------|-------------|---------------------|------------|\n")

    for fm in [x[0] for x in fm_counts.most_common()]:
        subset = [c for c in cases if c["failure_mode"] == fm]
        gdp_mean = sum(c["gdp_r1_cara_hyb"] for c in subset) / len(subset)

        m3_vals = [c["m3_r1_cara_hyb"] for c in subset if c["m3_r1_cara_hyb"] is not None]
        m3_mean = sum(m3_vals) / len(m3_vals) if m3_vals else None

        m4_vals = [c["m4_r0_cara_hyb"] for c in subset if c["m4_r0_cara_hyb"] is not None]
        m4_mean = sum(m4_vals) / len(m4_vals) if m4_vals else None

        m3_str = f"{m3_mean:.4f} (N={len(m3_vals)})" if m3_mean else "—"
        m4_str = f"{m4_mean:.4f} (N={len(m4_vals)})" if m4_mean else "—"

        f.write(f"| {fm} | {gdp_mean:.4f} | {m3_str} | {m4_str} |\n")
    f.write("\n")

    # Difficulty correlation
    f.write("## 5. Difficulty Stratification\n\n")
    f.write("| Category | Step1 | Step2&3 |\n")
    f.write("|----------|-------|---------|\n")
    for fm in [x[0] for x in fm_counts.most_common()]:
        subset = [c for c in cases if c["failure_mode"] == fm]
        s1 = sum(1 for c in subset if c["meta_info"] == "step1")
        s23 = sum(1 for c in subset if c["meta_info"] == "step2&3")
        f.write(f"| {fm} | {s1} | {s23} |\n")
    f.write("\n")

    # Full case list
    f.write("## 6. Full Case List\n\n")
    f.write("| Rank | QID | HYB | CR | SIM | Steps | Agree | FM | Notes |\n")
    f.write("|------|-----|-----|-----|-----|-------|-------|-----|-------|\n")
    for c in cases:
        steps_str = "/".join(str(s) for s in c["gdp_r1_num_steps_per_agent"].values())
        sim_str = f"{c['gdp_r1_cara_sim']:.3f}" if c["gdp_r1_cara_sim"] else "—"
        notes_short = c["failure_mode_notes"][:60] + "..." if len(c["failure_mode_notes"]) > 60 else c["failure_mode_notes"]
        f.write(f"| {c['rank']} | {c['question_id']} | "
                f"{c['gdp_r1_cara_hyb']:.4f} | {c['gdp_r1_cr']:.2f} | "
                f"{sim_str} | {steps_str} | {c['gdp_r1_agreement_set_size']} | "
                f"{c['failure_mode']} | {notes_short} |\n")
    f.write("\n")

    f.write("---\n\n")
    f.write("*Classification method: Heuristic rules on CARA sub-metrics "
            "(CR, SIM, step ratio). Manual verification recommended for paper.*\n")
    f.write(f"*Source: `{INPUT_FILE.name}` → `{OUTPUT_FILE.name}`*\n")

print(f"\nReport written to {REPORT_FILE}", flush=True)
print("DONE.", flush=True)
