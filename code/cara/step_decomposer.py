"""
Step decomposition for CARA metric.

Decomposes an agent's free-text reasoning response into atomic reasoning steps.
Two-strategy approach:
  1. Primary: numbered step regex (handles 94%+ of round 0 responses)
  2. Fallback: sentence-level splitting for paragraph-form responses

The ANSWER: X line is always stripped (not a reasoning step).
"""
import re
from typing import List


# Pattern: lines starting with a number followed by . or )
# e.g. "1. The patient...", "2) Given the...", "- **Step 1**:"
_NUMBERED_STEP_PATTERN = re.compile(
    r"^\s*(?:\d+[\.\)]\s*|\*{0,2}\d+[\.\)]\s*\*{0,2}|\-\s*\*{0,2}(?:Step\s*)?\d+)",
    re.MULTILINE,
)

# Pattern to detect ANSWER: X at end of response
_ANSWER_PATTERN = re.compile(r"\n?\s*(?:ANSWER|Answer|answer)\s*:\s*[A-Z]\.?[^\n]*$")

# Pattern for bold headers like "**Conclusion:**" that often precede the answer line
_CONCLUSION_PATTERN = re.compile(
    r"\n?\s*\*{0,2}(?:Conclusion|Final Answer|Therefore|In conclusion|Thus)\s*:?\*{0,2}[^\n]*$",
    re.IGNORECASE,
)

# Sentence splitting regex (fallback): split on period/question mark/exclamation
# followed by whitespace and a capital letter, or on double newlines.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])|(?:\n\s*\n)")


def decompose_response(response: str) -> List[str]:
    """
    Decompose a model response into reasoning steps.

    Returns a list of step strings. May return empty list if response
    contains no reasoning (e.g., bare "ANSWER: X").

    Strategy:
    1. Strip the ANSWER: X tail
    2. Try numbered-step extraction
    3. If < 2 numbered steps found, fall back to sentence splitting
    4. Filter out trivially short steps (< 20 chars)
    """
    if not response or not response.strip():
        return []

    # Strip ANSWER line and conclusion line from the end
    text = _ANSWER_PATTERN.sub("", response).strip()
    text = _CONCLUSION_PATTERN.sub("", text).strip()

    if not text:
        return []

    # Strategy 1: numbered steps
    steps = _extract_numbered_steps(text)
    if len(steps) >= 2:
        return _filter_steps(steps)

    # Strategy 2: sentence/paragraph splitting
    steps = _split_sentences(text)
    return _filter_steps(steps)


def _extract_numbered_steps(text: str) -> List[str]:
    """Extract steps delimited by numbered markers."""
    # Find all positions where numbered patterns start
    matches = list(_NUMBERED_STEP_PATTERN.finditer(text))
    if len(matches) < 2:
        return []

    steps = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        step_text = text[start:end].strip()
        # Remove the number prefix itself
        step_text = re.sub(r"^\s*\*{0,2}\d+[\.\)]\s*\*{0,2}\s*", "", step_text)
        step_text = re.sub(r"^\s*\-\s*\*{0,2}(?:Step\s*)?\d+[\.\):]?\s*\*{0,2}\s*", "", step_text)
        step_text = step_text.strip()
        if step_text:
            steps.append(step_text)

    return steps


def _split_sentences(text: str) -> List[str]:
    """Fallback: split text into sentences/paragraphs."""
    # First try double-newline split (paragraph-level)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs

    # Then try sentence-level split
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    if len(sentences) >= 2:
        return sentences

    # Last resort: return the whole text as a single step (if non-trivial)
    if len(text) >= 20:
        return [text]
    return []


def _filter_steps(steps: List[str]) -> List[str]:
    """Filter out trivially short steps and clean up."""
    filtered = []
    for step in steps:
        # Remove markdown bold markers for cleaner text
        clean = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", step)
        clean = clean.strip()
        # Keep steps with at least 20 characters of content
        if len(clean) >= 20:
            filtered.append(clean)
    return filtered
