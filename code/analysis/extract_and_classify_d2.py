"""D2 Failure Mode Taxonomy: Extract + classify 50 lowest-CARA correct-answer cases.

Replicates D1 taxonomy methodology on D2 MedThink-Bench N=499.
Verifies whether D1 difficulty stratification patterns hold on D2.

Differences from D1:
  - Dataset: MedThink-Bench (QA_Type instead of meta_info for difficulty)
  - CARA scores: cara_scores_d2_n499.jsonl
  - Traces: merged_M3GDP_D2, merged_M3_D2, merged_M4_D2
  - Question IDs: MTB_XXX format

Output:
  analysis/failure_modes/d2_lowest_cara_cases.jsonl     (50 cases)
  analysis/failure_modes/d2_classified_cases.jsonl       (50 classified)
  analysis/failure_modes/d2_taxonomy_report.md           (full report)
  analysis/failure_modes/d2_cross_dataset_comparison.md  (D1 vs D2 comparison)

Usage:
    python extract_and_classify_d2.py

Note: Raw traces and dataset subsample are not redistributed in this
anonymous release. The pre-computed output (`d2_classified_cases.jsonl`,
`d2_taxonomy_report.md`) is provided under `data/failure_modes/`.
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
import os

PROJECT = Path(os.environ.get("PROJECT_ROOT", "."))
CARA_FILE = PROJECT / "data" / "cara_scores" / "cara_scores_d2_n499.jsonl"
DATASET_FILE = PROJECT / "data" / "datasets" / "medthink_d2_499_combined.json"  # not redistributed
TRACE_DIRS = {
    "merged_M3GDP_D2": PROJECT / "data" / "traces" / "merged_M3GDP_D2" / "raw_traces.jsonl",
    "merged_M3_D2":    PROJECT / "data" / "traces" / "merged_M3_D2" / "raw_traces.jsonl",
    "merged_M4_D2":    PROJECT / "data" / "traces" / "merged_M4_D2" / "raw_traces.jsonl",
}  # raw traces not redistributed
OUTPUT_DIR = PROJECT / "data" / "failure_modes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# STEP 1: Load gold answers from MedThink-Bench
# =============================================================================
print("=" * 60)
print("STEP 1: Loading gold answers from MedThink-Bench D2 (499Q)")
print("=" * 60)

with open(DATASET_FILE, encoding="utf-8") as f:
    dataset = json.load(f)

gold_answers = {}       # qid -> answer_letter
question_texts = {}     # qid -> question text
question_meta = {}      # qid -> {QA_Type, answer, Scoring_Points, ...}

for q in dataset["questions"]:
    idx = q["Index"]
    qid = f"MTB_{idx:03d}"
    answer_text = q["answer"].strip()
    answer_letter = answer_text[0] if answer_text else None
    gold_answers[qid] = answer_letter
    question_texts[qid] = q["question"]
    question_meta[qid] = {
        "QA_Type": q.get("QA_Type", "unknown"),
        "answer_text": q["answer"],
        "answer_letter": answer_letter,
        "num_scoring_points": len(q.get("Scoring_Points", [])),
    }

print(f"  Loaded {len(gold_answers)} gold answers")
qa_types = Counter(m["QA_Type"] for m in question_meta.values())
print(f"  QA_Type distribution: {dict(qa_types)}")


# =============================================================================
# STEP 2: Load CARA scores and filter
# =============================================================================
print("\n" + "=" * 60)
print("STEP 2: Loading CARA scores and filtering")
print("=" * 60)

cara_records = []
with open(CARA_FILE, encoding="utf-8") as f:
    for line in f:
        cara_records.append(json.loads(line.strip()))

print(f"  Total CARA records: {len(cara_records)}")

# Target cells
target_cells = {
    ("merged_M3GDP_D2", 1): "GDP_r1",
    ("merged_M3GDP_D2", 0): "GDP_r0",
    ("merged_M3_D2", 1): "M3_r1",
    ("merged_M3_D2", 0): "M3_r0",
    ("merged_M4_D2", 0): "M4_r0",
}

cell_records = defaultdict(list)
for rec in cara_records:
    key = (rec["cell_id"], rec["cara_round"])
    if key in target_cells:
        cell_records[target_cells[key]].append(rec)

for cell_name, recs in sorted(cell_records.items()):
    print(f"  {cell_name}: {len(recs)} records")

# Filter for correct-answer cases with valid CARA
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
        if rec["majority_answer"] == gold_answers[qid]:
            correct_cases[cell_name].append(rec)

for cell_name in sorted(correct_cases.keys()):
    print(f"  {cell_name} correct-answer: {len(correct_cases[cell_name])}")


# =============================================================================
# STEP 3: Extract 50 lowest-CARA from GDP_r1
# =============================================================================
print("\n" + "=" * 60)
print("STEP 3: Extracting 50 lowest-CARA from GDP_r1")
print("=" * 60)

gdp_correct = correct_cases["GDP_r1"]
gdp_correct.sort(key=lambda r: r["cara_hyb_01"])
n_extract = min(50, len(gdp_correct))
lowest_50 = gdp_correct[:n_extract]

print(f"  GDP_r1 correct-answer pool: {len(gdp_correct)}")
print(f"  Extracting bottom {n_extract} by CARA-HYB")
print(f"  CARA-HYB range: [{lowest_50[0]['cara_hyb_01']:.4f}, {lowest_50[-1]['cara_hyb_01']:.4f}]")

# Cross-system lookup
m3_cara = {r["question_id"]: r for r in cell_records.get("M3_r1", [])}
m4_cara = {r["question_id"]: r for r in cell_records.get("M4_r0", [])}


# =============================================================================
# STEP 4: Build enriched output (traces are large — skip full trace embedding)
# =============================================================================
print("\n" + "=" * 60)
print("STEP 4: Building enriched output")
print("=" * 60)

output_cases = []
for rank, cara_rec in enumerate(lowest_50, 1):
    qid = cara_rec["question_id"]
    case = {
        "rank": rank,
        "question_id": qid,
        "question_text": question_texts.get(qid, "NOT FOUND")[:300],
        "gold_answer": gold_answers.get(qid, "?"),
        "QA_Type": question_meta.get(qid, {}).get("QA_Type", "?"),
        "num_scoring_points": question_meta.get(qid, {}).get("num_scoring_points", 0),
        # GDP_r1 CARA scores
        "gdp_r1_cara_hyb": cara_rec["cara_hyb_01"],
        "gdp_r1_cara_sim": cara_rec["cara_sim"],
        "gdp_r1_cr": cara_rec["contradiction_rate"],
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
        # Classification (filled below)
        "failure_mode": None,
        "failure_mode_notes": None,
    }
    output_cases.append(case)

# Write raw cases
raw_file = OUTPUT_DIR / "d2_lowest_cara_cases.jsonl"
with open(raw_file, "w", encoding="utf-8") as f:
    for case in output_cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")
print(f"  Wrote {len(output_cases)} cases to {raw_file.name}")


# =============================================================================
# STEP 5: Classify (same heuristics as D1)
# =============================================================================
print("\n" + "=" * 60)
print("STEP 5: Heuristic classification")
print("=" * 60)

def classify(case):
    cr = case["gdp_r1_cr"]
    hyb = case["gdp_r1_cara_hyb"]
    sim = case.get("gdp_r1_cara_sim")
    steps = case["gdp_r1_num_steps_per_agent"]
    zero_steps = case["gdp_r1_zero_step_agents"]
    n_contradictions = case["gdp_r1_num_contradictions"]

    step_values = list(steps.values())
    max_step = max(step_values)
    min_step = min(step_values)
    step_ratio = max_step / min_step if min_step > 0 else float("inf")

    if zero_steps:
        return "FM4", "Zero-step agent(s) — adopted answer without reasoning"

    high_cr = cr > 0.3
    step_imbalanced = step_ratio > 2.0

    if high_cr and step_imbalanced:
        return "FM2+FM3", (
            f"Granularity mismatch ({step_ratio:.1f}x) + "
            f"contradictory premises (CR={cr:.2f})"
        )
    if step_imbalanced and not high_cr:
        return "FM2", (
            f"Granularity mismatch: {step_ratio:.1f}x "
            f"({min_step} vs {max_step} steps), CR={cr:.2f}"
        )
    if high_cr and not step_imbalanced:
        return "FM3", (
            f"Contradictory premises: CR={cr:.2f}, "
            f"{n_contradictions} contradictions"
        )
    if sim is not None and sim < 0.80 and cr < 0.15:
        return "FM1", (
            f"Complementary reasoning: SIM={sim:.3f}, CR={cr:.2f}"
        )
    if sim is not None and sim < 0.80:
        return "FM5", (
            f"Terminology divergence: SIM={sim:.3f}, CR={cr:.2f}"
        )
    return "FM6", (
        f"Partial overlap: HYB={hyb:.4f}, SIM={sim:.3f}, CR={cr:.2f}"
    )


for case in output_cases:
    fm, notes = classify(case)
    case["failure_mode"] = fm
    case["failure_mode_notes"] = notes

# Write classified output
classified_file = OUTPUT_DIR / "d2_classified_cases.jsonl"
with open(classified_file, "w", encoding="utf-8") as f:
    for case in output_cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")

fm_counts = Counter(c["failure_mode"] for c in output_cases)
print(f"\nD2 GDP_r1 failure mode distribution:")
for fm, count in fm_counts.most_common():
    print(f"  {fm}: {count}")


# =============================================================================
# STEP 6: Also classify M3_r1 bottom 50 for comparison
# =============================================================================
print("\n" + "=" * 60)
print("STEP 6: M3_r1 bottom 50 classification (for GDP vs M3 comparison)")
print("=" * 60)

m3_correct = correct_cases.get("M3_r1", [])
m3_correct.sort(key=lambda r: r["cara_hyb_01"])
n_m3 = min(50, len(m3_correct))
m3_lowest = m3_correct[:n_m3]

print(f"  M3_r1 correct-answer pool: {len(m3_correct)}")
print(f"  Extracting bottom {n_m3}")

if m3_lowest:
    print(f"  CARA-HYB range: [{m3_lowest[0]['cara_hyb_01']:.4f}, {m3_lowest[-1]['cara_hyb_01']:.4f}]")

gdp_cara_lookup = {r["question_id"]: r for r in cell_records.get("GDP_r1", [])}

m3_cases = []
for rank, rec in enumerate(m3_lowest, 1):
    qid = rec["question_id"]
    steps = rec.get("num_steps_per_agent", {})
    step_values = list(steps.values()) if steps else [0]
    max_step = max(step_values)
    min_step = min(step_values)
    step_ratio = max_step / min_step if min_step > 0 else float("inf")
    zero_steps = rec.get("zero_step_agents", [])
    cr = rec.get("contradiction_rate", 0) or 0
    sim = rec.get("cara_sim")
    hyb = rec.get("cara_hyb_01")
    n_contradictions = rec.get("num_contradictions", 0)

    # Same classification logic
    if zero_steps:
        fm, notes = "FM4", "Zero-step agent(s)"
    elif cr > 0.3 and step_ratio > 2.0:
        fm, notes = "FM2+FM3", f"Granularity ({step_ratio:.1f}x) + CR={cr:.2f}"
    elif step_ratio > 2.0:
        fm, notes = "FM2", f"Granularity mismatch: {step_ratio:.1f}x, CR={cr:.2f}"
    elif cr > 0.3:
        fm, notes = "FM3", f"Contradictory premises: CR={cr:.2f}, {n_contradictions} contradictions"
    elif sim is not None and sim < 0.80 and cr < 0.15:
        fm, notes = "FM1", f"Complementary reasoning: SIM={sim:.3f}, CR={cr:.2f}"
    elif sim is not None and sim < 0.80:
        fm, notes = "FM5", f"Terminology divergence: SIM={sim:.3f}, CR={cr:.2f}"
    else:
        fm, notes = "FM6", f"Partial overlap: HYB={hyb:.4f}, SIM={sim:.3f if sim else 'N/A'}, CR={cr:.2f}"

    m3_cases.append({
        "rank": rank,
        "question_id": qid,
        "QA_Type": question_meta.get(qid, {}).get("QA_Type", "?"),
        "m3_r1_cara_hyb": hyb,
        "m3_r1_cr": cr,
        "m3_r1_cara_sim": sim,
        "m3_r1_steps": steps,
        "m3_r1_zero_steps": zero_steps,
        "gdp_r1_cara_hyb": gdp_cara_lookup.get(qid, {}).get("cara_hyb_01"),
        "failure_mode": fm,
        "failure_mode_notes": notes,
    })

m3_fm_counts = Counter(c["failure_mode"] for c in m3_cases)
print(f"\nD2 M3_r1 failure mode distribution:")
for fm, count in m3_fm_counts.most_common():
    print(f"  {fm}: {count}")

# Write M3 classified
m3_classified_file = OUTPUT_DIR / "d2_classified_m3_cases.jsonl"
with open(m3_classified_file, "w", encoding="utf-8") as f:
    for case in m3_cases:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")


# =============================================================================
# STEP 7: Generate taxonomy report with D1 vs D2 comparison
# =============================================================================
print("\n" + "=" * 60)
print("STEP 7: Generating taxonomy report + cross-dataset comparison")
print("=" * 60)

FM_NAMES = {
    "FM1": "Complementary Reasoning",
    "FM2": "Granularity Mismatch",
    "FM3": "Contradictory Premises",
    "FM4": "Sycophantic Convergence",
    "FM5": "Terminology Divergence",
    "FM6": "Partial Overlap",
    "FM2+FM3": "Granularity + Contradictory",
}

# D1 reference values (from research_brief.json)
D1_GDP_FM = {"FM6": 31, "FM3": 12, "FM2": 5, "FM2+FM3": 2}
D1_M3_FM = {"FM1": 23, "FM2": 12, "FM4": 11, "FM3": 2, "FM5": 2}

report_lines = []
def p(s=""):
    report_lines.append(s)

p("# D2 Failure Mode Taxonomy — MedThink-Bench N=499")
p()
p("## 1. GDP_r1 Distribution (D2)")
p()
p("| Code | Category | D2 Count | D2 % | D1 Count | D1 % |")
p("|------|----------|----------|------|----------|------|")
all_fms = sorted(set(list(fm_counts.keys()) + list(D1_GDP_FM.keys())))
for fm in all_fms:
    name = FM_NAMES.get(fm, fm)
    d2_n = fm_counts.get(fm, 0)
    d2_pct = d2_n / len(output_cases) * 100 if output_cases else 0
    d1_n = D1_GDP_FM.get(fm, 0)
    d1_pct = d1_n / 50 * 100
    p(f"| {fm} | {name} | {d2_n} | {d2_pct:.0f}% | {d1_n} | {d1_pct:.0f}% |")
p(f"| **Total** | | **{len(output_cases)}** | **100%** | **50** | **100%** |")
p()

p("## 2. M3_r1 Distribution (D2)")
p()
p("| Code | Category | D2 Count | D2 % | D1 Count | D1 % |")
p("|------|----------|----------|------|----------|------|")
all_fms_m3 = sorted(set(list(m3_fm_counts.keys()) + list(D1_M3_FM.keys())))
for fm in all_fms_m3:
    name = FM_NAMES.get(fm, fm)
    d2_n = m3_fm_counts.get(fm, 0)
    d2_pct = d2_n / len(m3_cases) * 100 if m3_cases else 0
    d1_n = D1_M3_FM.get(fm, 0)
    d1_pct = d1_n / 50 * 100
    p(f"| {fm} | {name} | {d2_n} | {d2_pct:.0f}% | {d1_n} | {d1_pct:.0f}% |")
p(f"| **Total** | | **{len(m3_cases)}** | **100%** | **50** | **100%** |")
p()

p("## 3. GDP Elimination Effect (D2 vs D1)")
p()
p("Key comparisons — does GDP eliminate the same failure modes on D2?")
p()
d2_gdp_fm4 = fm_counts.get("FM4", 0)
d2_m3_fm4 = m3_fm_counts.get("FM4", 0)
d2_gdp_fm1 = fm_counts.get("FM1", 0)
d2_m3_fm1 = m3_fm_counts.get("FM1", 0)

p(f"| Pattern | D1 | D2 | Replicates? |")
p(f"|---------|----|----|-------------|")
p(f"| FM4 in M3 vs GDP | M3: 11/50 → GDP: 0/50 | M3: {d2_m3_fm4}/{len(m3_cases)} → GDP: {d2_gdp_fm4}/{len(output_cases)} | {'YES' if d2_gdp_fm4 == 0 and d2_m3_fm4 > 0 else 'PARTIAL' if d2_gdp_fm4 < d2_m3_fm4 else 'NO'} |")
p(f"| FM1 in M3 vs GDP | M3: 23/50 → GDP: 0/50 | M3: {d2_m3_fm1}/{len(m3_cases)} → GDP: {d2_gdp_fm1}/{len(output_cases)} | {'YES' if d2_gdp_fm1 == 0 and d2_m3_fm1 > 0 else 'PARTIAL' if d2_gdp_fm1 < d2_m3_fm1 else 'NO'} |")
p(f"| FM6 dominates GDP | D1: 31/50 (62%) | D2: {fm_counts.get('FM6', 0)}/{len(output_cases)} ({fm_counts.get('FM6', 0)/len(output_cases)*100:.0f}%) | {'YES' if fm_counts.get('FM6', 0) > len(output_cases)*0.4 else 'NO'} |")
p()

p("## 4. Difficulty Stratification (D2)")
p()
p("MedThink-Bench uses QA_Type instead of MedQA's step1/step2&3.")
p()

# GDP QA_Type stratification
p("### GDP_r1 bottom 50 by QA_Type")
p()
gdp_qa_types = Counter(c["QA_Type"] for c in output_cases)
p("| QA_Type | Count | FM distribution |")
p("|---------|-------|-----------------|")
for qt, count in gdp_qa_types.most_common():
    subset = [c for c in output_cases if c["QA_Type"] == qt]
    fm_dist = Counter(c["failure_mode"] for c in subset)
    fm_str = ", ".join(f"{fm}={n}" for fm, n in fm_dist.most_common())
    p(f"| {qt} | {count} | {fm_str} |")
p()

# M3 QA_Type stratification
p("### M3_r1 bottom 50 by QA_Type")
p()
m3_qa_types = Counter(c["QA_Type"] for c in m3_cases)
p("| QA_Type | Count | FM distribution |")
p("|---------|-------|-----------------|")
for qt, count in m3_qa_types.most_common():
    subset = [c for c in m3_cases if c["QA_Type"] == qt]
    fm_dist = Counter(c["failure_mode"] for c in subset)
    fm_str = ", ".join(f"{fm}={n}" for fm, n in fm_dist.most_common())
    p(f"| {qt} | {count} | {fm_str} |")
p()

# Quantitative profiles
p("## 5. Quantitative Profiles (D2 GDP_r1)")
p()

def mean(vals):
    return sum(vals) / len(vals) if vals else float("nan")

p("| Category | N | Mean HYB | Mean CR | Mean SIM | Mean Step Ratio |")
p("|----------|---|----------|---------|----------|-----------------|")
for fm in [x[0] for x in fm_counts.most_common()]:
    subset = [c for c in output_cases if c["failure_mode"] == fm]
    n = len(subset)
    m_hyb = mean([c["gdp_r1_cara_hyb"] for c in subset])
    m_cr = mean([c["gdp_r1_cr"] for c in subset])
    sims = [c["gdp_r1_cara_sim"] for c in subset if c["gdp_r1_cara_sim"] is not None]
    m_sim = mean(sims) if sims else float("nan")
    ratios = []
    for c in subset:
        sv = list(c["gdp_r1_num_steps_per_agent"].values())
        if min(sv) > 0:
            ratios.append(max(sv) / min(sv))
    m_ratio = mean(ratios) if ratios else float("nan")
    name = FM_NAMES.get(fm, fm)
    p(f"| {fm} ({name}) | {n} | {m_hyb:.4f} | {m_cr:.2f} | {m_sim:.3f} | {m_ratio:.1f}x |")
p()

# Full case list
p("## 6. Full Case List (D2 GDP_r1)")
p()
p("| Rank | QID | HYB | CR | SIM | Steps | FM | QA_Type |")
p("|------|-----|-----|-----|-----|-------|-----|---------|")
for c in output_cases:
    steps_str = "/".join(str(s) for s in c["gdp_r1_num_steps_per_agent"].values())
    sim_str = f"{c['gdp_r1_cara_sim']:.3f}" if c["gdp_r1_cara_sim"] else "—"
    qa_short = c["QA_Type"][:30]
    p(f"| {c['rank']} | {c['question_id']} | {c['gdp_r1_cara_hyb']:.4f} | {c['gdp_r1_cr']:.2f} | {sim_str} | {steps_str} | {c['failure_mode']} | {qa_short} |")
p()

p("---")
p()
p("*Classification: same heuristic rules as D1 (CR>0.3, step_ratio>2.0, SIM<0.80).*")
p(f"*Source: cara_scores_d2_n499.jsonl, {len(output_cases)} GDP_r1 + {len(m3_cases)} M3_r1 cases classified.*")

# Write report
report_file = OUTPUT_DIR / "d2_taxonomy_report.md"
report_file.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
print(f"  Report written to {report_file.name}")

# Also write a concise cross-dataset comparison
comparison_lines = []
def pc(s=""):
    comparison_lines.append(s)

pc("# Cross-Dataset Failure Mode Comparison (D1 vs D2)")
pc()
pc("## GDP_r1: Does taxonomy structure replicate?")
pc()
pc("| FM | D1 (MedQA) | D2 (MedThink) | Δ | Interpretation |")
pc("|-----|-----------|--------------|---|----------------|")
for fm in sorted(set(list(D1_GDP_FM.keys()) + list(fm_counts.keys()))):
    d1 = D1_GDP_FM.get(fm, 0)
    d2 = fm_counts.get(fm, 0)
    delta = d2 - d1
    name = FM_NAMES.get(fm, fm)
    interp = ""
    if fm == "FM6" and d2 > 20:
        interp = "Dominant mode in both — consistent"
    elif fm == "FM3" and abs(delta) < 5:
        interp = "Stable across datasets"
    elif fm == "FM4" and d1 == 0 and d2 == 0:
        interp = "GDP eliminates sycophancy on both datasets"
    elif abs(delta) <= 3:
        interp = "Stable"
    elif delta > 0:
        interp = f"Higher on D2 (+{delta})"
    else:
        interp = f"Lower on D2 ({delta})"
    pc(f"| {fm} ({name}) | {d1} | {d2} | {delta:+d} | {interp} |")
pc()
pc("## M3_r1: Does GDP elimination effect replicate?")
pc()
pc("| FM | D1 M3 | D2 M3 | D1 GDP | D2 GDP | Effect |")
pc("|----|-------|-------|--------|--------|--------|")
for fm in ["FM1", "FM4"]:
    d1_m3 = D1_M3_FM.get(fm, 0)
    d2_m3 = m3_fm_counts.get(fm, 0)
    d1_gdp = D1_GDP_FM.get(fm, 0)
    d2_gdp = fm_counts.get(fm, 0)
    if d1_gdp == 0 and d2_gdp == 0:
        effect = "GDP eliminates on BOTH datasets"
    elif d2_gdp < d2_m3:
        effect = f"GDP reduces ({d2_m3} → {d2_gdp})"
    else:
        effect = "No clear reduction"
    pc(f"| {fm} | {d1_m3} | {d2_m3} | {d1_gdp} | {d2_gdp} | {effect} |")
pc()
pc(f"*Generated from D1 classified_cases.jsonl + D2 d2_classified_cases.jsonl*")

comp_file = OUTPUT_DIR / "d2_cross_dataset_comparison.md"
comp_file.write_text("\n".join(comparison_lines) + "\n", encoding="utf-8")
print(f"  Cross-dataset comparison written to {comp_file.name}")

print("\nDONE.")
