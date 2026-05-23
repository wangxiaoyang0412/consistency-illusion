"""
CARA-GT pipeline orchestrator.

Compares agent reasoning steps to expert Scoring_Points from MedThink-Bench.
Reuses NLI scorer, embedding scorer, and step decomposer from the CARA pipeline.

Input:
  - Trace files (JSONL with agent responses)
  - MedThink-Bench dataset (with Scoring_Points per question)

Output:
  - JSONL with per-question CARA-GT scores
"""
import json
import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

from .cara_gt import (
    AgentGTAlignment,
    QuestionCARAGT,
    aggregate_question_gt_cara,
    compute_agent_gt_alignment,
)
from .embedding_scorer import EmbeddingScorer
from .nli_scorer import NLIScorer
from .step_decomposer import decompose_response

logger = logging.getLogger(__name__)


def _load_traces(trace_file: Path) -> List[dict]:
    """Load JSONL trace file."""
    traces = []
    for line in trace_file.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            traces.append(json.loads(line))
    return traces


def _group_by_question(
    traces: List[dict], target_round: int
) -> Dict[str, List[dict]]:
    """Group traces by question_id, filtering to target round."""
    groups = defaultdict(list)
    for t in traces:
        if t["round"] == target_round:
            groups[t["question_id"]].append(t)
    return dict(groups)


def _load_expert_reference(
    dataset_path: Path,
    question_id_prefix: str = "MTB",
) -> Dict[str, Dict]:
    """
    Load expert Scoring_Points from MedThink-Bench dataset file.

    Args:
        dataset_path: Path to medthink_pilot_50.json or similar.
        question_id_prefix: Prefix for building question IDs ("MTB" or "MQA").

    Returns:
        Dict mapping question_id -> {"answer_letter": str, "scoring_points": list[str]}
    """
    raw = json.loads(dataset_path.read_text(encoding="utf-8"))
    expert_ref = {}

    for q in raw["questions"]:
        idx = q["Index"]
        qid = f"{question_id_prefix}_{idx:03d}"

        # Extract answer letter from answer field
        answer_text = q["answer"].strip()
        answer_letter = answer_text[0] if answer_text else None

        scoring_points = q.get("Scoring_Points", [])

        expert_ref[qid] = {
            "answer_letter": answer_letter,
            "scoring_points": scoring_points,
        }

    return expert_ref


def run_cara_gt_pipeline(
    trace_files: List[Tuple[Path, str, str, int]],
    dataset_path: Path,
    output_file: Path,
    question_id_prefix: str = "MTB",
    contradiction_threshold: float = 0.7,
    nli_batch_size: int = 32,
    emb_batch_size: int = 64,
    device: str = "cuda",
    max_questions: Optional[int] = None,
) -> List[QuestionCARAGT]:
    """
    Run CARA-GT pipeline on trace files.

    Args:
        trace_files: list of (path, system, cell_id, target_round) tuples
        dataset_path: path to dataset file with Scoring_Points
        output_file: path to write JSONL output
        question_id_prefix: "MTB" for MedThink-Bench, "MQA" for MedQA
        contradiction_threshold: NLI contradiction probability threshold
        nli_batch_size: batch size for NLI inference
        emb_batch_size: batch size for embedding inference
        device: torch device
        max_questions: if set, only process first N questions per cell (for testing)

    Returns:
        List of QuestionCARAGT results.
    """
    torch.manual_seed(42)
    np.random.seed(42)

    t0 = time.time()

    # Load expert reference
    logger.info(f"Loading expert reference from {dataset_path}")
    expert_ref = _load_expert_reference(dataset_path, question_id_prefix)
    logger.info(f"  {len(expert_ref)} questions with Scoring_Points")

    # Check that Scoring_Points are present
    has_sp = sum(1 for v in expert_ref.values() if v["scoring_points"])
    logger.info(f"  {has_sp}/{len(expert_ref)} have non-empty Scoring_Points")

    # Load models
    logger.info("=== Loading models ===")
    nli_scorer = NLIScorer(
        device=device,
        contradiction_threshold=contradiction_threshold,
        batch_size=nli_batch_size,
    )
    emb_scorer = EmbeddingScorer(device=device, batch_size=emb_batch_size)
    logger.info(
        f"Models loaded. VRAM: {torch.cuda.memory_allocated() / 1024**2:.0f} MB"
    )

    all_results: List[QuestionCARAGT] = []

    for trace_path, system, cell_id, target_round in trace_files:
        logger.info(
            f"=== Processing {system} round {target_round} "
            f"from {trace_path.name} ==="
        )

        traces = _load_traces(trace_path)
        dataset = traces[0]["dataset"] if traces else "unknown"
        grouped = _group_by_question(traces, target_round)

        logger.info(f"  {len(grouped)} questions at round {target_round}")

        question_ids = sorted(grouped.keys())
        if max_questions is not None:
            question_ids = question_ids[:max_questions]

        for q_idx, qid in enumerate(question_ids):
            q_traces = grouped[qid]

            result = _process_one_question_gt(
                qid=qid,
                q_traces=q_traces,
                expert_ref=expert_ref,
                system=system,
                cell_id=cell_id,
                dataset=dataset,
                cara_round=target_round,
                nli_scorer=nli_scorer,
                emb_scorer=emb_scorer,
            )
            all_results.append(result)

            if (q_idx + 1) % 10 == 0:
                logger.info(
                    f"  [{q_idx + 1}/{len(question_ids)}] "
                    f"VRAM: {torch.cuda.memory_allocated() / 1024**2:.0f} MB"
                )

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for r in all_results:
            record = _result_to_dict(r)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    elapsed = time.time() - t0
    logger.info(f"=== CARA-GT pipeline complete: {len(all_results)} records in {elapsed:.1f}s ===")

    # Cleanup
    nli_scorer.unload()
    emb_scorer.unload()

    return all_results


def _process_one_question_gt(
    qid: str,
    q_traces: List[dict],
    expert_ref: Dict[str, Dict],
    system: str,
    cell_id: str,
    dataset: str,
    cara_round: int,
    nli_scorer: NLIScorer,
    emb_scorer: EmbeddingScorer,
) -> QuestionCARAGT:
    """Process CARA-GT for a single question."""
    # Get expert reference
    ref = expert_ref.get(qid)
    if ref is None or not ref["scoring_points"]:
        return QuestionCARAGT(
            question_id=qid,
            system=system,
            cell_id=cell_id,
            dataset=dataset,
            cara_round=cara_round,
            correct_answer=None,
            num_agents=len(q_traces),
            cara_gt_hyb_raw=None,
            cara_gt_hyb_01=None,
            cara_gt_sim=None,
            gt_contradiction_rate=None,
            num_expert_steps=0,
            num_expert_steps_covered=0,
            expert_coverage_rate=None,
            num_agent_steps_total=0,
            error="no_expert_reference",
        )

    expert_steps = ref["scoring_points"]
    correct_answer = ref["answer_letter"]

    # Decompose ALL agent responses (not restricted to agreement set)
    agent_steps = {}
    for t in q_traces:
        aid = t["agent_id"]
        agent_steps[aid] = decompose_response(t["response"])

    steps_per_agent = {aid: len(steps) for aid, steps in agent_steps.items()}

    # Embed all steps (agents + expert) with deduplication
    all_step_lists = dict(agent_steps)  # copy
    all_step_lists["__expert__"] = expert_steps
    all_embeddings = emb_scorer.embed_all_unique(all_step_lists)

    expert_emb = all_embeddings.pop("__expert__")

    # Compute per-agent alignment
    agent_alignments = []
    for aid in sorted(agent_steps.keys()):
        steps = agent_steps[aid]
        agent_emb = all_embeddings[aid]

        if len(steps) == 0 or expert_emb.size == 0:
            alignment = compute_agent_gt_alignment(
                agent_id=aid,
                agent_steps=steps,
                expert_steps=expert_steps,
                sim_matrix=np.array([]).reshape(0, 0),
                nli_results=[],
            )
        else:
            # Cosine similarity matrix
            sim_matrix = emb_scorer.cosine_similarity_matrix(agent_emb, expert_emb)

            # NLI on all agent_step x expert_step pairs (row-major)
            nli_pairs = []
            for s_agent in steps:
                for s_expert in expert_steps:
                    nli_pairs.append((s_agent, s_expert))

            nli_results = nli_scorer.score_pairs(nli_pairs) if nli_pairs else []

            alignment = compute_agent_gt_alignment(
                agent_id=aid,
                agent_steps=steps,
                expert_steps=expert_steps,
                sim_matrix=sim_matrix,
                nli_results=nli_results,
            )

        agent_alignments.append(alignment)

    # Aggregate to question level
    return aggregate_question_gt_cara(
        agent_alignments=agent_alignments,
        question_id=qid,
        system=system,
        cell_id=cell_id,
        dataset=dataset,
        cara_round=cara_round,
        correct_answer=correct_answer,
        expert_steps=expert_steps,
        steps_per_agent=steps_per_agent,
    )


def _result_to_dict(r: QuestionCARAGT) -> dict:
    """Convert QuestionCARAGT to JSON-serializable dict."""
    d = {
        "question_id": r.question_id,
        "system": r.system,
        "cell_id": r.cell_id,
        "dataset": r.dataset,
        "cara_round": r.cara_round,
        "correct_answer": r.correct_answer,
        "num_agents": r.num_agents,
        "cara_gt_hyb_raw": round(r.cara_gt_hyb_raw, 6) if r.cara_gt_hyb_raw is not None else None,
        "cara_gt_hyb_01": round(r.cara_gt_hyb_01, 6) if r.cara_gt_hyb_01 is not None else None,
        "cara_gt_sim": round(r.cara_gt_sim, 6) if r.cara_gt_sim is not None else None,
        "gt_contradiction_rate": round(r.gt_contradiction_rate, 6) if r.gt_contradiction_rate is not None else None,
        "num_expert_steps": r.num_expert_steps,
        "num_expert_steps_covered": r.num_expert_steps_covered,
        "expert_coverage_rate": round(r.expert_coverage_rate, 6) if r.expert_coverage_rate is not None else None,
        "num_agent_steps_total": r.num_agent_steps_total,
        "num_steps_per_agent": r.num_steps_per_agent,
        "zero_step_agents": r.zero_step_agents,
        "per_agent_cara_gt": [
            {
                "agent_id": a.agent_id,
                "cara_gt_hyb_raw": round(a.cara_gt_hyb_raw, 6) if not np.isnan(a.cara_gt_hyb_raw) else None,
                "cara_gt_sim": round(a.cara_gt_sim, 6) if not np.isnan(a.cara_gt_sim) else None,
                "num_agent_steps": a.num_agent_steps,
                "num_contradictions": a.num_contradictions,
            }
            for a in r.agent_alignments
        ],
        "num_nli_pairs_total": r.num_nli_pairs_total,
        "num_contradictions": r.num_contradictions,
        "nli_model": "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
        "embedding_model": "dunzhang/stella_en_1.5B_v5",
        "contradiction_threshold": 0.7,
        "error": r.error,
    }
    return d
