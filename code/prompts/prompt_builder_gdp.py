"""GDP (Grounded Debate Protocol) prompt builders for M3-GDP system.

GDP modifies the standard M3 debate prompts to require structured
CLAIM/GROUND/STANCE format, forcing agents to explicitly ground each
reasoning step in named medical facts.

Design source: Ideation/ideas/cara_ideation.md §3.1-3.6.

Round 0 (independent): CLAIM + GROUND format (no STANCE — no prior agents).
Round 1 (debate): CLAIM + GROUND + STANCE per other agent.

Both rounds must end with ANSWER: X for parse compatibility with
extract_answer.py regex.
"""

from __future__ import annotations

# --- GDP System Message (Round 0) ---
# Includes CLAIM/GROUND format requirement but no STANCE (no prior agents).
GDP_SYSTEM_R0 = (
    "You are a medical specialist participating in a clinical reasoning discussion.\n\n"
    "INSTRUCTIONS — you MUST follow this format for EVERY reasoning step:\n\n"
    "For each point in your reasoning, state:\n"
    "1. CLAIM: [Your clinical claim in one sentence]\n"
    "2. GROUND: [The specific medical fact, mechanism, or guideline that supports "
    "this claim. Name the disease, drug, pathway, or clinical principle explicitly.]\n\n"
    "You may have multiple CLAIM/GROUND pairs.\n"
    "After your reasoning, provide your final answer."
)

# --- GDP System Message (Round 1) ---
# Adds STANCE requirement per other agent.
GDP_SYSTEM_R1 = (
    "You are a medical specialist participating in a clinical reasoning discussion.\n\n"
    "INSTRUCTIONS — you MUST follow this format for EVERY reasoning step:\n\n"
    "For each point in your reasoning, state:\n"
    "1. CLAIM: [Your clinical claim in one sentence]\n"
    "2. GROUND: [The specific medical fact, mechanism, or guideline that supports "
    "this claim. Name the disease, drug, pathway, or clinical principle explicitly.]\n"
    "3. STANCE: [AGREE/DISAGREE/EXTEND with respect to the other agents' claims on "
    "this point, with a one-sentence justification. If you DISAGREE, you must provide "
    "a counter-ground (a different medical fact that supports your position).]\n\n"
    "IMPORTANT RULES:\n"
    "- Do NOT change your answer simply because other agents disagree. "
    "Only change if you identify a specific factual error in your own reasoning "
    "or receive a more compelling medical ground from another agent.\n"
    "- If you change your answer, you MUST explicitly state which specific GROUND "
    "from another agent convinced you, OR state that you identified an error in "
    "your own prior GROUND.\n\n"
    "After your reasoning, provide your final answer."
)

# --- User suffix (same as standard, ensures ANSWER: X parse compatibility) ---
GDP_USER_SUFFIX = "\n\nThink step by step using the CLAIM/GROUND format above, then provide your answer in the format: ANSWER: X"

# --- Debate user template (Round 1) ---
GDP_DEBATE_USER_TEMPLATE = (
    "Here are the responses from other agents:\n\n"
    "{other_responses}\n\n"
    "Using the CLAIM/GROUND/STANCE format, evaluate the other agents' reasoning "
    "and provide your updated analysis. "
    "Provide your final answer in the format: ANSWER: X"
)


def build_gdp_round0_prompt(question_text: str) -> list[dict]:
    """Build GDP round 0 prompt (independent, CLAIM/GROUND only).

    Args:
        question_text: Full question text with inline options (as-is from data).

    Returns:
        List of 2 message dicts: [system, user].
    """
    return [
        {"role": "system", "content": GDP_SYSTEM_R0},
        {"role": "user", "content": question_text + GDP_USER_SUFFIX},
    ]


def build_gdp_debate_prompt(
    question_text: str,
    own_round0_response: str,
    other_agents_responses: list[str],
) -> list[dict]:
    """Build GDP round 1 debate prompt (CLAIM/GROUND/STANCE).

    Same 4-message structure as standard M3 debate, with GDP-modified
    system message and debate user turn.

    Args:
        question_text: Full question text with inline options.
        own_round0_response: This agent's round 0 response text.
        other_agents_responses: List of other agents' round 0 response texts.

    Returns:
        List of 4 message dicts: [system, user, assistant, user].
    """
    other_text = "\n\n".join(other_agents_responses)

    return [
        {"role": "system", "content": GDP_SYSTEM_R1},
        {"role": "user", "content": question_text + GDP_USER_SUFFIX},
        {"role": "assistant", "content": own_round0_response},
        {"role": "user", "content": GDP_DEBATE_USER_TEMPLATE.format(other_responses=other_text)},
    ]


if __name__ == "__main__":
    # --- Round 0 test ---
    print("=== build_gdp_round0_prompt ===")
    q = "What is the treatment?\nA. Drug X\nB. Drug Y\nC. Drug Z\nD. None"
    p0 = build_gdp_round0_prompt(q)
    assert len(p0) == 2, f"Expected 2 messages, got {len(p0)}"
    assert p0[0]["role"] == "system"
    assert "CLAIM" in p0[0]["content"]
    assert "GROUND" in p0[0]["content"]
    assert "STANCE" not in p0[0]["content"]  # No STANCE in round 0
    assert p0[1]["role"] == "user"
    assert p0[1]["content"].endswith("ANSWER: X")
    print("  PASS  2 messages, GDP format, no STANCE in r0")

    # --- Round 1 debate test ---
    print("\n=== build_gdp_debate_prompt ===")
    own = "CLAIM: I think B because...\nGROUND: Drug Y targets...\nANSWER: B"
    others = ["CLAIM: Agent 2 says A...\nGROUND: Drug X...\nANSWER: A",
              "CLAIM: Agent 3 says C...\nGROUND: Drug Z...\nANSWER: C"]
    p1 = build_gdp_debate_prompt(q, own, others)
    assert len(p1) == 4, f"Expected 4 messages, got {len(p1)}"
    assert p1[0]["role"] == "system"
    assert "STANCE" in p1[0]["content"]  # STANCE required in round 1
    assert "Do NOT change your answer simply" in p1[0]["content"]
    assert p1[2]["role"] == "assistant"
    assert p1[2]["content"] == own
    assert p1[3]["role"] == "user"
    assert "ANSWER: X" in p1[3]["content"]
    # Verify own response is NOT in debate user turn
    assert own not in p1[3]["content"]
    print("  PASS  4 messages, GDP format with STANCE, anti-sycophancy")

    print("\nResult: ALL PASS")
