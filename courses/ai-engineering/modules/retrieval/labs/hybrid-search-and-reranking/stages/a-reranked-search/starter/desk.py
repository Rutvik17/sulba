"""The help desk's search: BM25's ranking and the vectors' fused, each text once, and the
fused ranking's first passages put in order by the reranker."""

import httpx
import numpy as np

from bm25 import BM25, words
from fuse import fused, nearest

MODEL = "Qwen3-Reranker-0.6B"
# How many of the fused ranking's first texts the reranker scores.
DEPTH = 20


class Desk:
    """The help desk's passages, searched by their words and their vectors, and reranked
    by the model the client reaches."""

    def __init__(
        self, client: httpx.Client, texts: list[str], vectors: np.ndarray
    ) -> None:
        raise NotImplementedError

    def search(self, question: str, vector: np.ndarray, k: int = 5) -> list[int]:
        """The rows of the k passages that best answer the question, best first."""
        raise NotImplementedError
