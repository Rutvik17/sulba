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
        self.client = client
        self.texts = texts
        self.vectors = vectors
        self.index = BM25([words(text) for text in texts])

    def ranking(self, question: str, vector: np.ndarray) -> list[int]:
        """The rows of the fused ranking's first DEPTH texts, each text's first row."""
        bm25 = np.argsort(-self.index.scores(words(question)), kind="stable")
        seen: set[str] = set()
        rows: list[int] = []
        for row in fused([bm25, nearest(vector, self.vectors)]).tolist():
            if self.texts[row] not in seen:
                seen.add(self.texts[row])
                rows.append(row)
                if len(rows) == DEPTH:
                    break
        return rows

    def search(self, question: str, vector: np.ndarray, k: int = 5) -> list[int]:
        """The rows of the k passages that best answer the question, best first: the fused
        ranking's first DEPTH texts by the reranker's scores, a tie going to the one ranked
        first, or the fused ranking's first k when the reranker fails."""
        rows = self.ranking(question, vector)
        body = {
            "model": MODEL,
            "query": question,
            "documents": [self.texts[row] for row in rows],
        }
        try:
            response = self.client.post("/rerank", json=body)
            response.raise_for_status()
            results = response.json()["results"]
        except httpx.HTTPError:
            return rows[:k]
        order = sorted(
            results, key=lambda result: (-result["relevance_score"], result["index"])
        )
        return [rows[result["index"]] for result in order[:k]]
