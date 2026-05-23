"""
CARA-GT scoring logic: agent reasoning steps vs expert Scoring_Points.

CARA-GT measures how well each agent's reasoning aligns with expert-annotated
reference reasoning (Scoring_Points from MedThink-Bench).

Unlike CARA (agent vs agent, pairwise, symmetrized), CARA-GT is:
  - Agent vs expert (one-way best-match: agent steps -> expert points)
  - Per-agent then averaged across agents
  - Includes expert coverage metric (how many expert points are matched)

Scoring (per agent):
  For each agent step, find the best-matching expert point.
  If NLI(agent_step, expert_point) = contradiction -> align = -1
  Else -> align = cosine(agent_step, expert_point)
  CARA-GT-raw(agent) = mean of best-match scores across agent steps

Aggregation to question level:
  CARA-GT-raw(question) = mean over agents
  CARA-GT-01 = (raw + 1) / 2
  Expert coverage = # expert points that are best-matched by any agent step
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .nli_scorer import NLIResult


@dataclass
class AgentGTAlignment:
    """CARA-GT scores for a single agent vs expert reference."""
    agent_id: str
    num_agent_steps: int
    num_expert_steps: int
    cara_gt_hyb_raw: float  # [-1, 1], NaN if 0 agent steps
    cara_gt_sim: float      # [0, 1], NaN if 0 agent steps
    num_contradictions: int
    num_nli_pairs: int       # num_agent_steps * num_expert_steps
    best_match_expert_indices: List[int]  # which expert step each agent step matched


@dataclass
class QuestionCARAGT:
    """CARA-GT scores for a single question-system-round combination."""
    question_id: str
    system: str
    cell_id: str
    dataset: str
    cara_round: int
    correct_answer: Optional[str]
    num_agents: int
    # Aggregated scores (mean across agents with valid scores)
    cara_gt_hyb_raw: Optional[float]  # [-1, 1]
    cara_gt_hyb_01: Optional[float]   # [0, 1]
    cara_gt_sim: Optional[float]      # [0, 1]
    gt_contradiction_rate: Optional[float]  # [0, 1]
    # Expert coverage
    num_expert_steps: int
    num_expert_steps_covered: int  # expert steps matched by at least one agent
    expert_coverage_rate: Optional[float]  # covered / total
    # Agent details
    num_agent_steps_total: int
    num_steps_per_agent: Dict[str, int] = field(default_factory=dict)
    zero_step_agents: List[str] = field(default_factory=list)
    agent_alignments: List[AgentGTAlignment] = field(default_factory=list)
    # Totals
    num_nli_pairs_total: int = 0
    num_contradictions: int = 0
    error: Optional[str] = None


def compute_agent_gt_alignment(
    agent_id: str,
    agent_steps: List[str],
    expert_steps: List[str],
    sim_matrix: np.ndarray,
    nli_results: List[NLIResult],
) -> AgentGTAlignment:
    """
    Compute CARA-GT for one agent against expert reference.

    Args:
        agent_id: agent identifier
        agent_steps: decomposed reasoning steps from agent
        expert_steps: expert Scoring_Points
        sim_matrix: cosine similarity matrix of shape (K_agent, K_expert)
        nli_results: NLI results for K_agent * K_expert pairs (row-major)

    Returns:
        AgentGTAlignment with HYB and SIM scores.
    """
    K_agent = len(agent_steps)
    K_expert = len(expert_steps)

    if K_agent == 0:
        return AgentGTAlignment(
            agent_id=agent_id,
            num_agent_steps=0,
            num_expert_steps=K_expert,
            cara_gt_hyb_raw=float("nan"),
            cara_gt_sim=float("nan"),
            num_contradictions=0,
            num_nli_pairs=0,
            best_match_expert_indices=[],
        )

    if K_expert == 0:
        return AgentGTAlignment(
            agent_id=agent_id,
            num_agent_steps=K_agent,
            num_expert_steps=0,
            cara_gt_hyb_raw=float("nan"),
            cara_gt_sim=float("nan"),
            num_contradictions=0,
            num_nli_pairs=0,
            best_match_expert_indices=[],
        )

    # Build HYB matrix: contradiction -> -1, else -> cosine
    hyb_matrix = sim_matrix.copy()
    contradiction_count = 0
    for idx, nli_result in enumerate(nli_results):
        row = idx // K_expert
        col = idx % K_expert
        if nli_result.is_contradiction:
            hyb_matrix[row, col] = -1.0
            contradiction_count += 1

    # One-way best-match: for each agent step, find best expert match
    # HYB version
    best_hyb_per_step = hyb_matrix.max(axis=1)  # shape (K_agent,)
    best_expert_indices = hyb_matrix.argmax(axis=1).tolist()  # which expert step

    # SIM version (cosine only)
    best_sim_per_step = sim_matrix.max(axis=1)  # shape (K_agent,)

    cara_gt_hyb_raw = float(best_hyb_per_step.mean())
    cara_gt_sim = float(best_sim_per_step.mean())

    return AgentGTAlignment(
        agent_id=agent_id,
        num_agent_steps=K_agent,
        num_expert_steps=K_expert,
        cara_gt_hyb_raw=cara_gt_hyb_raw,
        cara_gt_sim=cara_gt_sim,
        num_contradictions=contradiction_count,
        num_nli_pairs=K_agent * K_expert,
        best_match_expert_indices=best_expert_indices,
    )


def aggregate_question_gt_cara(
    agent_alignments: List[AgentGTAlignment],
    question_id: str,
    system: str,
    cell_id: str,
    dataset: str,
    cara_round: int,
    correct_answer: Optional[str],
    expert_steps: List[str],
    steps_per_agent: Dict[str, int],
) -> QuestionCARAGT:
    """
    Aggregate per-agent CARA-GT scores to question level.

    Mean across agents with valid (non-NaN) scores.
    Expert coverage: count unique expert steps that were best-matched.
    """
    zero_step_agents = [a.agent_id for a in agent_alignments if a.num_agent_steps == 0]
    valid = [a for a in agent_alignments if not np.isnan(a.cara_gt_hyb_raw)]

    K_expert = len(expert_steps)

    if not valid:
        return QuestionCARAGT(
            question_id=question_id,
            system=system,
            cell_id=cell_id,
            dataset=dataset,
            cara_round=cara_round,
            correct_answer=correct_answer,
            num_agents=len(agent_alignments),
            cara_gt_hyb_raw=None,
            cara_gt_hyb_01=None,
            cara_gt_sim=None,
            gt_contradiction_rate=None,
            num_expert_steps=K_expert,
            num_expert_steps_covered=0,
            expert_coverage_rate=None,
            num_agent_steps_total=sum(a.num_agent_steps for a in agent_alignments),
            num_steps_per_agent=steps_per_agent,
            zero_step_agents=zero_step_agents,
            agent_alignments=agent_alignments,
            num_nli_pairs_total=0,
            num_contradictions=0,
            error="all_agents_zero_steps",
        )

    # Aggregate scores
    cara_gt_hyb_raw = float(np.mean([a.cara_gt_hyb_raw for a in valid]))
    cara_gt_sim = float(np.mean([a.cara_gt_sim for a in valid]))
    cara_gt_hyb_01 = (cara_gt_hyb_raw + 1.0) / 2.0

    total_contradictions = sum(a.num_contradictions for a in valid)
    total_nli_pairs = sum(a.num_nli_pairs for a in valid)
    total_agent_steps = sum(a.num_agent_steps for a in agent_alignments)

    # Contradiction rate: # contradictions / # total NLI pairs
    gt_cr = total_contradictions / total_nli_pairs if total_nli_pairs > 0 else None

    # Expert coverage: which expert steps were matched by any agent
    covered_expert_indices = set()
    for a in valid:
        covered_expert_indices.update(a.best_match_expert_indices)
    num_covered = len(covered_expert_indices)
    coverage_rate = num_covered / K_expert if K_expert > 0 else None

    return QuestionCARAGT(
        question_id=question_id,
        system=system,
        cell_id=cell_id,
        dataset=dataset,
        cara_round=cara_round,
        correct_answer=correct_answer,
        num_agents=len(agent_alignments),
        cara_gt_hyb_raw=cara_gt_hyb_raw,
        cara_gt_hyb_01=cara_gt_hyb_01,
        cara_gt_sim=cara_gt_sim,
        gt_contradiction_rate=gt_cr,
        num_expert_steps=K_expert,
        num_expert_steps_covered=num_covered,
        expert_coverage_rate=coverage_rate,
        num_agent_steps_total=total_agent_steps,
        num_steps_per_agent=steps_per_agent,
        zero_step_agents=zero_step_agents,
        agent_alignments=agent_alignments,
        num_nli_pairs_total=total_nli_pairs,
        num_contradictions=total_contradictions,
    )
