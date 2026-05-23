"""Prompt builders for exp-pilot-003: round 0 (shared) + round 1 (M3 debate).

Spec source: handoff_to_exp_pilot_003.md lines 153-190.

Prompt templates extracted verbatim from handoff:

Round 0 (lines 159-163, 2-message prompt):
  system: "You are a medical specialist. Answer medical questions with step-by-step reasoning."
  user: "<question text with inline options>\n\nThink step by step and provide your answer in the format: ANSWER: X"

Round 1 (lines 168-174, 4-message prompt):
  system: same as round 0
  user: same as round 0 (question)
  assistant: <this agent's round 0 response>
  user: "Here are the responses from other agents:\n\n<agent_j round 0>\n\n<agent_k round 0>\n\nUsing these as additional information, provide your answer in the format: ANSWER: X"

Decision (D): question text used as-is from data. Options are embedded inline.
  Both Format A ("Answer Choices: (A)...") and Format B ("A. text\\nB. text")
  passed through unchanged.

Asymmetric rule (handoff line 190):
  Agent i's user turn at round r contains responses from [agent_j for j != i]
  at round r-1 ONLY. Agent i never sees its own previous response in the user
  turn — it sees it as the preceding assistant turn.
"""

from __future__ import annotations

# System message: verbatim from handoff line 161.
SYSTEM_MESSAGE = (
    "You are a medical specialist. "
    "Answer medical questions with step-by-step reasoning."
)

# User message suffix: verbatim from handoff line 162.
USER_SUFFIX = "\n\nThink step by step and provide your answer in the format: ANSWER: X"

# Debate user message template: from handoff line 173.
# {other_responses} will be joined with "\n\n".
DEBATE_USER_TEMPLATE = (
    "Here are the responses from other agents:\n\n"
    "{other_responses}\n\n"
    "Using these as additional information, "
    "provide your answer in the format: ANSWER: X"
)


def build_round0_prompt(question_text: str) -> list[dict]:
    """Build round 0 prompt (independent, used by both M3 and M4).

    Handoff lines 159-163: 2-message prompt.

    Args:
        question_text: Full question text with inline options (as-is from data).

    Returns:
        List of 2 message dicts: [system, user].
    """
    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": question_text + USER_SUFFIX},
    ]


def build_debate_prompt(
    question_text: str,
    own_round0_response: str,
    other_agents_responses: list[str],
) -> list[dict]:
    """Build round 1 debate prompt for M3 (Du et al. asymmetric).

    Handoff lines 168-174: 4-message prompt.

    The agent sees:
      1. system message (same as round 0)
      2. original question (same as round 0)
      3. its own round 0 response (as assistant turn)
      4. other agents' round 0 responses (as new user turn)

    Asymmetric rule (handoff line 190): other_agents_responses contains
    responses from [agent_j for j != i] only. The agent's own response
    appears as the assistant turn, not in the user turn.

    Args:
        question_text: Full question text with inline options.
        own_round0_response: This agent's round 0 response text.
        other_agents_responses: List of other agents' round 0 response texts.

    Returns:
        List of 4 message dicts: [system, user, assistant, user].
    """
    other_text = "\n\n".join(other_agents_responses)

    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": question_text + USER_SUFFIX},
        {"role": "assistant", "content": own_round0_response},
        {"role": "user", "content": DEBATE_USER_TEMPLATE.format(other_responses=other_text)},
    ]


if __name__ == "__main__":
    # --- Round 0 test ---
    print("=== build_round0_prompt ===")
    q = "What is the treatment?\nA. Drug X\nB. Drug Y\nC. Drug Z\nD. None"
    p0 = build_round0_prompt(q)
    assert len(p0) == 2, f"Expected 2 messages, got {len(p0)}"
    assert p0[0]["role"] == "system"
    assert p0[0]["content"] == SYSTEM_MESSAGE
    assert p0[1]["role"] == "user"
    assert p0[1]["content"].startswith("What is the treatment?")
    assert p0[1]["content"].endswith("ANSWER: X")
    print(f"  PASS  2 messages, system + user with suffix")

    # --- Round 1 debate test ---
    print("\n=== build_debate_prompt ===")
    own = "I think the answer is B because..."
    others = ["Agent 2 says A because...", "Agent 3 says C because..."]
    p1 = build_debate_prompt(q, own, others)
    assert len(p1) == 4, f"Expected 4 messages, got {len(p1)}"
    assert p1[0]["role"] == "system"
    assert p1[1]["role"] == "user"
    assert p1[2]["role"] == "assistant"
    assert p1[2]["content"] == own
    assert p1[3]["role"] == "user"
    assert "Here are the responses from other agents:" in p1[3]["content"]
    assert "Agent 2 says A because..." in p1[3]["content"]
    assert "Agent 3 says C because..." in p1[3]["content"]
    assert p1[3]["content"].endswith("ANSWER: X")
    # Verify agent's own response is NOT in the user turn
    assert own not in p1[3]["content"], "Own response must not appear in debate user turn"
    print(f"  PASS  4 messages, asymmetric rule verified")

    print("\nResult: ALL PASS")
