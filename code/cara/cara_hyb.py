"""
CARA-HYB scoring logic.

Implements the CARA-HYBRID metric from cara_ideation.md Section 1.3 Variant 3:
  - For each step pair (r_i^k, r_j^l):
    - If NLI = contradiction -> align = -1
    - Otherwise -> align = cosine(emb(r_i^k), emb(r_j^l))
  - Best-match: match_j(r_i^k) = max_l align(r_i^k, r_j^l)
  - Symmetrized pairwise: CARA(i,j) = 0.5 * (mean_k match_j(r_i^k) + mean_l match_i(r_j^l))
  - System-level: average over all pairs in agreement set S(q)
  - Rescale to [0,1]: (CARA + 1) / 2

Also computes:
  - CARA-SIM: cosine similarity only (no NLI override)
  - CR: contradiction rate (# contradictions / # total best-match pairs)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .nli_scorer import NLIResult


@dataclass
class PairwiseCARA:
    """CARA scores for a single agent pair."""
    agent_i: str
    agent_j: str
    cara_hyb_raw: float  # in [-1, 1]
    cara_sim: float  # in [0, 1] (cosine only)
    num_contradictions: int
    num_best_match_pairs: int  # K_i + K_j (total best-match lookups)
    steps_i: int
    steps_j: int


@dataclass
class QuestionCARA:
    """CARA scores for a single question-system-round combination."""
    question_id: str
    system: str
    cell_id: str
    dataset: str
    majority_answer: str
    agreement_set: List[str]
    agreement_set_size: int
    cara_round: int
    num_agent_pairs: int
    cara_hyb_raw: Optional[float]  # in [-1, 1], None if undefined
    cara_hyb_01: Optional[float]  # in [0, 1], None if undefined
    cara_sim: Optional[float]  # in [0, 1], None if undefined
    contradiction_rate: Optional[float]  # in [0, 1], None if undefined
    num_steps_per_agent: Dict[str, int] = field(default_factory=dict)
    num_nli_pairs_total: int = 0
    num_contradictions: int = 0
    zero_step_agents: List[str] = field(default_factory=list)
    pairwise_details: List[PairwiseCARA] = field(default_factory=list)
    error: Optional[str] = None


def compute_pairwise_cara_hyb(
    steps_i: List[str],
    steps_j: List[str],
    sim_matrix: np.ndarray,
    nli_results: List[NLIResult],
    agent_i: str,
    agent_j: str,
) -> PairwiseCARA:
    """
    Compute CARA-HYB for a single pair of agents.

    Args:
        steps_i: reasoning steps for agent i
        steps_j: reasoning steps for agent j
        sim_matrix: cosine similarity matrix of shape (K_i, K_j)
        nli_results: NLI results for all K_i * K_j pairs (row-major order)
        agent_i: agent ID for i
        agent_j: agent ID for j

    Returns:
        PairwiseCARA with HYB and SIM scores.
    """
    K_i = len(steps_i)
    K_j = len(steps_j)

    # Handle zero-step cases
    if K_i == 0 and K_j == 0:
        return PairwiseCARA(
            agent_i=agent_i, agent_j=agent_j,
            cara_hyb_raw=float("nan"), cara_sim=float("nan"),
            num_contradictions=0, num_best_match_pairs=0,
            steps_i=0, steps_j=0,
        )

    # Build HYB alignment matrix: contradiction -> -1, else -> cosine
    hyb_matrix = sim_matrix.copy()
    contradiction_count = 0
    for idx, nli_result in enumerate(nli_results):
        row = idx // K_j
        col = idx % K_j
        if nli_result.is_contradiction:
            hyb_matrix[row, col] = -1.0
            contradiction_count += 1

    # Best-match i->j: for each step in i, find max alignment in j
    # Best-match j->i: for each step in j, find max alignment in i
    cara_hyb_raw = _symmetrized_best_match(hyb_matrix, K_i, K_j)
    cara_sim = _symmetrized_best_match(sim_matrix, K_i, K_j)

    return PairwiseCARA(
        agent_i=agent_i,
        agent_j=agent_j,
        cara_hyb_raw=cara_hyb_raw,
        cara_sim=cara_sim,
        num_contradictions=contradiction_count,
        num_best_match_pairs=K_i + K_j,
        steps_i=K_i,
        steps_j=K_j,
    )


def _symmetrized_best_match(
    matrix: np.ndarray, K_i: int, K_j: int
) -> float:
    """
    Compute symmetrized best-match score.

    If one side has 0 steps, use only the other direction.
    If both have 0 steps, return NaN.
    """
    if K_i == 0 and K_j == 0:
        return float("nan")

    scores = []
    if K_i > 0 and K_j > 0:
        # i->j direction: for each step in i, max over j
        i_to_j = matrix.max(axis=1).mean()  # shape (K_i,) -> scalar
        # j->i direction: for each step in j, max over i
        j_to_i = matrix.max(axis=0).mean()  # shape (K_j,) -> scalar
        scores = [i_to_j, j_to_i]
    elif K_i > 0:
        # Only i has steps; can't compute i->j (no j steps to match against)
        # This pair is effectively undefined for the direction with 0 steps
        return float("nan")
    else:
        # Only j has steps
        return float("nan")

    return float(np.mean(scores))


def aggregate_question_cara(
    pairwise_results: List[PairwiseCARA],
    question_id: str,
    system: str,
    cell_id: str,
    dataset: str,
    majority_answer: str,
    agreement_set: List[str],
    cara_round: int,
    steps_per_agent: Dict[str, int],
) -> QuestionCARA:
    """
    Aggregate pairwise CARA scores to question-level.

    System-level: average over all valid pairs in agreement set.
    Rescale HYB to [0,1]: (raw + 1) / 2
    CR = total contradictions / total best-match pairs
    """
    # Filter out NaN pairs (where both agents had 0 steps)
    valid_pairs = [p for p in pairwise_results if not np.isnan(p.cara_hyb_raw)]
    zero_step_agents = [a for a, n in steps_per_agent.items() if n == 0]

    if not valid_pairs:
        return QuestionCARA(
            question_id=question_id,
            system=system,
            cell_id=cell_id,
            dataset=dataset,
            majority_answer=majority_answer,
            agreement_set=agreement_set,
            agreement_set_size=len(agreement_set),
            cara_round=cara_round,
            num_agent_pairs=len(pairwise_results),
            cara_hyb_raw=None,
            cara_hyb_01=None,
            cara_sim=None,
            contradiction_rate=None,
            num_steps_per_agent=steps_per_agent,
            num_nli_pairs_total=0,
            num_contradictions=0,
            zero_step_agents=zero_step_agents,
            pairwise_details=pairwise_results,
            error="all_pairs_undefined",
        )

    # Aggregate
    cara_hyb_raw = float(np.mean([p.cara_hyb_raw for p in valid_pairs]))
    cara_sim = float(np.mean([p.cara_sim for p in valid_pairs]))
    total_contradictions = sum(p.num_contradictions for p in valid_pairs)
    total_best_match_pairs = sum(p.num_best_match_pairs for p in valid_pairs)
    total_nli_pairs = sum(p.steps_i * p.steps_j for p in valid_pairs)

    cr = total_contradictions / total_best_match_pairs if total_best_match_pairs > 0 else None
    cara_hyb_01 = (cara_hyb_raw + 1.0) / 2.0

    return QuestionCARA(
        question_id=question_id,
        system=system,
        cell_id=cell_id,
        dataset=dataset,
        majority_answer=majority_answer,
        agreement_set=agreement_set,
        agreement_set_size=len(agreement_set),
        cara_round=cara_round,
        num_agent_pairs=len(pairwise_results),
        cara_hyb_raw=cara_hyb_raw,
        cara_hyb_01=cara_hyb_01,
        cara_sim=cara_sim,
        contradiction_rate=cr,
        num_steps_per_agent=steps_per_agent,
        num_nli_pairs_total=total_nli_pairs,
        num_contradictions=total_contradictions,
        zero_step_agents=zero_step_agents,
        pairwise_details=valid_pairs,
    )
