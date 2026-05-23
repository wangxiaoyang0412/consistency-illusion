"""
NLI-based contradiction detection for CARA metric.

Uses MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli to classify
step pairs as entailment / neutral / contradiction.

For CARA-HYB, only the contradiction label matters:
  - If P(contradiction) > threshold -> score = -1
  - Otherwise -> defer to embedding similarity
"""
import logging
from dataclasses import dataclass
from typing import List, Tuple

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

MODEL_ID = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"

# MoritzLaurer id2label: {0: entailment, 1: neutral, 2: contradiction}
CONTRADICTION_IDX = 2
NEUTRAL_IDX = 1
ENTAILMENT_IDX = 0


@dataclass
class NLIResult:
    """Result of NLI inference on a single premise-hypothesis pair."""
    premise: str
    hypothesis: str
    contradiction_prob: float
    neutral_prob: float
    entailment_prob: float
    is_contradiction: bool  # True if contradiction_prob > threshold


class NLIScorer:
    """Batch NLI scorer using DeBERTa-v3-large (MoritzLaurer multi-dataset)."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        device: str = "cuda",
        contradiction_threshold: float = 0.7,
        batch_size: int = 32,
    ):
        self.model_id = model_id
        self.device = device
        self.contradiction_threshold = contradiction_threshold
        self.batch_size = batch_size

        logger.info(f"Loading NLI model: {model_id}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_id)
        self.model.to(device)
        self.model.eval()

        # Runtime label-order guard: halt if model config disagrees with hardcoded indices
        id2label = self.model.config.id2label
        if id2label.get(CONTRADICTION_IDX) != "contradiction":
            raise RuntimeError(
                f"NLI label order mismatch: model.config.id2label[{CONTRADICTION_IDX}] = "
                f"'{id2label.get(CONTRADICTION_IDX)}', expected 'contradiction'. "
                f"Full id2label: {id2label}"
            )
        if id2label.get(ENTAILMENT_IDX) != "entailment":
            raise RuntimeError(
                f"NLI label order mismatch: model.config.id2label[{ENTAILMENT_IDX}] = "
                f"'{id2label.get(ENTAILMENT_IDX)}', expected 'entailment'. "
                f"Full id2label: {id2label}"
            )

        logger.info(
            f"NLI model loaded on {device}. "
            f"VRAM: {torch.cuda.memory_allocated() / 1024**2:.0f} MB. "
            f"Label order verified: {id2label}"
        )

    def score_pairs(
        self, pairs: List[Tuple[str, str]]
    ) -> List[NLIResult]:
        """
        Score a list of (premise, hypothesis) pairs.

        Returns list of NLIResult with contradiction probabilities.
        """
        if not pairs:
            return []

        results = []
        for batch_start in range(0, len(pairs), self.batch_size):
            batch = pairs[batch_start : batch_start + self.batch_size]
            batch_results = self._score_batch(batch)
            results.extend(batch_results)

        return results

    def _score_batch(self, pairs: List[Tuple[str, str]]) -> List[NLIResult]:
        """Score a single batch of pairs."""
        premises = [p[0] for p in pairs]
        hypotheses = [p[1] for p in pairs]

        inputs = self.tokenizer(
            premises,
            hypotheses,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).cpu()

        results = []
        for i, (premise, hypothesis) in enumerate(pairs):
            c_prob = probs[i, CONTRADICTION_IDX].item()
            n_prob = probs[i, NEUTRAL_IDX].item()
            e_prob = probs[i, ENTAILMENT_IDX].item()
            results.append(NLIResult(
                premise=premise,
                hypothesis=hypothesis,
                contradiction_prob=c_prob,
                neutral_prob=n_prob,
                entailment_prob=e_prob,
                is_contradiction=c_prob > self.contradiction_threshold,
            ))

        return results

    def unload(self):
        """Free GPU memory."""
        del self.model
        del self.tokenizer
        torch.cuda.empty_cache()
        logger.info("NLI model unloaded.")
