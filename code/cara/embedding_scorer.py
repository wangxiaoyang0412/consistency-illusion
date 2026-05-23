"""
Embedding-based semantic similarity for CARA metric.

Uses dunzhang/stella_en_1.5B_v5 to compute dense embeddings for reasoning steps,
then cosine similarity for alignment scoring.

For CARA-HYB: cosine similarity is used when NLI does NOT detect contradiction.
For CARA-SIM: cosine similarity is the sole alignment measure.
"""
import logging
from typing import Dict, List

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_ID = "dunzhang/stella_en_1.5B_v5"


class EmbeddingScorer:
    """Batch embedding scorer using stella_en_1.5B_v5."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        device: str = "cuda",
        batch_size: int = 64,
    ):
        self.model_id = model_id
        self.device = device
        self.batch_size = batch_size

        logger.info(f"Loading embedding model: {model_id}")
        self.model = SentenceTransformer(model_id, device=device)
        logger.info(
            f"Embedding model loaded on {device}. "
            f"VRAM: {torch.cuda.memory_allocated() / 1024**2:.0f} MB"
        )

    def embed_steps(self, steps: List[str]) -> np.ndarray:
        """
        Embed a list of reasoning steps.

        Returns numpy array of shape (len(steps), embedding_dim).
        """
        if not steps:
            return np.array([]).reshape(0, 0)

        embeddings = self.model.encode(
            steps,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2-normalized for cosine = dot product
        )
        return embeddings

    def embed_all_unique(self, step_lists: Dict[str, List[str]]) -> Dict[str, np.ndarray]:
        """
        Embed all unique steps across multiple agents.

        Args:
            step_lists: dict mapping agent_id -> list of step strings

        Returns:
            dict mapping agent_id -> embedding array (n_steps, embed_dim)
        """
        # Collect all unique steps to avoid redundant computation
        all_steps = []
        step_to_idx = {}
        for agent_id, steps in step_lists.items():
            for step in steps:
                if step not in step_to_idx:
                    step_to_idx[step] = len(all_steps)
                    all_steps.append(step)

        if not all_steps:
            return {agent_id: np.array([]).reshape(0, 0) for agent_id in step_lists}

        # Batch embed all unique steps
        all_embeddings = self.embed_steps(all_steps)

        # Map back to per-agent arrays
        result = {}
        for agent_id, steps in step_lists.items():
            if not steps:
                result[agent_id] = np.array([]).reshape(0, all_embeddings.shape[1])
            else:
                indices = [step_to_idx[s] for s in steps]
                result[agent_id] = all_embeddings[indices]

        return result

    def cosine_similarity_matrix(
        self, emb_a: np.ndarray, emb_b: np.ndarray
    ) -> np.ndarray:
        """
        Compute pairwise cosine similarity matrix.

        Since embeddings are L2-normalized, cosine = dot product.

        Args:
            emb_a: shape (K_i, dim)
            emb_b: shape (K_j, dim)

        Returns:
            similarity matrix of shape (K_i, K_j)
        """
        if emb_a.size == 0 or emb_b.size == 0:
            return np.array([]).reshape(0, 0)
        return emb_a @ emb_b.T

    def unload(self):
        """Free GPU memory."""
        del self.model
        torch.cuda.empty_cache()
        logger.info("Embedding model unloaded.")
