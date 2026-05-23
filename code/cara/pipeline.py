"""
CARA pipeline orchestrator.

Loads traces -> decomposes steps -> NLI inference -> embedding inference
-> CARA-HYB/SIM/CR scoring -> writes output JSONL.
"""
import json
import logging
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

from .cara_hyb import (
    QuestionCARA,
    aggregate_question_cara,
    compute_pairwise_cara_hyb,
)
from .embedding_scorer import EmbeddingScorer
from .nli_scorer import NLIScorer
from .step_decomposer import decompose_response

logger = logging.getLogger(__name__)


def load_traces(trace_file: Path) -> List[dict]:
    """Load JSONL trace file."""
    traces = []
    for line in trace_file.read_text(encoding="utf-8").strip().split("\n"):
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


def _compute_agreement_set(
    traces_for_question: List[dict],
) -> Tuple[str, List[str]]:
    """
    Compute majority answer and agreement set S(q).

    Returns (majority_answer, list of agent_ids in agreement set).
    """
    answer_counts = Counter(t["extracted_answer"] for t in traces_for_question)
    majority_answer, _ = answer_counts.most_common(1)[0]
    agreement_set = [
        t["agent_id"]
        for t in traces_for_question
        if t["extracted_answer"] == majority_answer
    ]
    return majority_answer, agreement_set


def run_cara_pipeline(
    trace_files: List[Tuple[Path, str, str, int]],
    output_file: Path,
    contradiction_threshold: float = 0.7,
    nli_batch_size: int = 32,
    emb_batch_size: int = 64,
    device: str = "cuda",
    seed: int = 42,
) -> List[QuestionCARA]:
    """
    Run full CARA pipeline on trace files.

    Args:
        trace_files: list of (path, system, cell_id, target_round) tuples
        output_file: path to write JSONL output
        contradiction_threshold: NLI contradiction probability threshold
        nli_batch_size: batch size for NLI inference
        emb_batch_size: batch size for embedding inference
        device: torch device
        seed: random seed for reproducibility

    Returns:
        List of QuestionCARA results.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    t0 = time.time()

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

    all_results: List[QuestionCARA] = []

    for trace_path, system, cell_id, target_round in trace_files:
        logger.info(
            f"=== Processing {system} round {target_round} "
            f"from {trace_path.name} ==="
        )

        traces = load_traces(trace_path)
        dataset = traces[0]["dataset"] if traces else "unknown"
        grouped = _group_by_question(traces, target_round)

        logger.info(f"  {len(grouped)} questions at round {target_round}")

        for q_idx, (qid, q_traces) in enumerate(sorted(grouped.items())):
            result = _process_one_question(
                qid=qid,
                q_traces=q_traces,
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
                    f"  [{q_idx + 1}/{len(grouped)}] "
                    f"VRAM: {torch.cuda.memory_allocated() / 1024**2:.0f} MB"
                )

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for r in all_results:
            record = _result_to_dict(r)
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    elapsed = time.time() - t0
    logger.info(f"=== Pipeline complete: {len(all_results)} records in {elapsed:.1f}s ===")

    # Cleanup
    nli_scorer.unload()
    emb_scorer.unload()

    return all_results


def _process_one_question(
    qid: str,
    q_traces: List[dict],
    system: str,
    cell_id: str,
    dataset: str,
    cara_round: int,
    nli_scorer: NLIScorer,
    emb_scorer: EmbeddingScorer,
) -> QuestionCARA:
    """Process CARA for a single question."""
    # Compute agreement set
    majority_answer, agreement_set = _compute_agreement_set(q_traces)

    if len(agreement_set) < 2:
        # CARA undefined: fewer than 2 agents agree
        steps_per_agent = {
            t["agent_id"]: 0 for t in q_traces if t["agent_id"] in agreement_set
        }
        return QuestionCARA(
            question_id=qid,
            system=system,
            cell_id=cell_id,
            dataset=dataset,
            majority_answer=majority_answer,
            agreement_set=agreement_set,
            agreement_set_size=len(agreement_set),
            cara_round=cara_round,
            num_agent_pairs=0,
            cara_hyb_raw=None,
            cara_hyb_01=None,
            cara_sim=None,
            contradiction_rate=None,
            error="agreement_set_too_small",
        )

    # Step decomposition for agents in agreement set
    agent_responses = {
        t["agent_id"]: t["response"]
        for t in q_traces
        if t["agent_id"] in agreement_set
    }
    agent_steps = {
        aid: decompose_response(resp) for aid, resp in agent_responses.items()
    }
    steps_per_agent = {aid: len(steps) for aid, steps in agent_steps.items()}

    # Embed all steps
    agent_embeddings = emb_scorer.embed_all_unique(agent_steps)

    # Compute pairwise CARA for all pairs in agreement set
    pairwise_results = []
    for agent_i, agent_j in combinations(sorted(agreement_set), 2):
        steps_i = agent_steps[agent_i]
        steps_j = agent_steps[agent_j]
        K_i = len(steps_i)
        K_j = len(steps_j)

        # Cosine similarity matrix
        emb_i = agent_embeddings[agent_i]
        emb_j = agent_embeddings[agent_j]
        sim_matrix = emb_scorer.cosine_similarity_matrix(emb_i, emb_j)

        # NLI on all K_i * K_j pairs (row-major)
        nli_pairs = []
        for si in steps_i:
            for sj in steps_j:
                nli_pairs.append((si, sj))

        nli_results = nli_scorer.score_pairs(nli_pairs) if nli_pairs else []

        pw = compute_pairwise_cara_hyb(
            steps_i=steps_i,
            steps_j=steps_j,
            sim_matrix=sim_matrix,
            nli_results=nli_results,
            agent_i=agent_i,
            agent_j=agent_j,
        )
        pairwise_results.append(pw)

    # Aggregate to question level
    return aggregate_question_cara(
        pairwise_results=pairwise_results,
        question_id=qid,
        system=system,
        cell_id=cell_id,
        dataset=dataset,
        majority_answer=majority_answer,
        agreement_set=agreement_set,
        cara_round=cara_round,
        steps_per_agent=steps_per_agent,
    )


def _result_to_dict(r: QuestionCARA) -> dict:
    """Convert QuestionCARA to JSON-serializable dict (excluding pairwise details)."""
    d = {
        "question_id": r.question_id,
        "system": r.system,
        "cell_id": r.cell_id,
        "dataset": r.dataset,
        "majority_answer": r.majority_answer,
        "agreement_set": r.agreement_set,
        "agreement_set_size": r.agreement_set_size,
        "cara_round": r.cara_round,
        "num_agent_pairs": r.num_agent_pairs,
        "cara_hyb_raw": round(r.cara_hyb_raw, 6) if r.cara_hyb_raw is not None else None,
        "cara_hyb_01": round(r.cara_hyb_01, 6) if r.cara_hyb_01 is not None else None,
        "cara_sim": round(r.cara_sim, 6) if r.cara_sim is not None else None,
        "contradiction_rate": round(r.contradiction_rate, 6) if r.contradiction_rate is not None else None,
        "num_steps_per_agent": r.num_steps_per_agent,
        "num_nli_pairs_total": r.num_nli_pairs_total,
        "num_contradictions": r.num_contradictions,
        "zero_step_agents": r.zero_step_agents,
        "nli_model": "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli",
        "embedding_model": "dunzhang/stella_en_1.5B_v5",
        "contradiction_threshold": 0.7,
        "error": r.error,
    }
    return d
