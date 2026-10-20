The fused ranking holds an answer among its first {% $fig.depth %} passages more often than among its first {% $fig.k %}. A reranker reads a question and a passage together and scores how well the passage answers it, which the vectors can't do, since the embedding model reads each text alone. It takes a run of the model for each passage it scores, so the help desk has it score the fused ranking's first few, and puts them in its order.

The lab's reranker is Qwen3-Reranker-0.6B, which `uv run sulba.py model` serves on your machine through llama.cpp's server. A request to `/v1/rerank` gives the `model`, the `query` and the `documents` to score, and the reply's `results` give each document's `index` in the request and its `relevance_score`, highest first. `data/rerank-scores.csv` holds the scores the model gave each question's first passages, which the checks' reranker gives back.

This stage builds the search the help desk will ship, in `desk.py`, with your `BM25`, `nearest` and `fused`:

- `Desk(client, texts, vectors)` searches the passages, with their texts and vectors, through the reranker the client reaches.
- `desk.search(question, vector, k)` gives the rows of the `k` passages that best answer the question, best first, for `k` up to {% $fig.depth %}.

What the search must do:

- rank the passages as `fused` does BM25's ranking and the vectors', each text once: of the passages that share a text, the one ranked first;
- have the reranker score the first {% $fig.depth %}, in one request, and give them in the order of its scores, a tie going to the one ranked first;
- find more answers among its first {% $fig.k %} than the fused ranking's first {% $fig.k %};
- give the fused ranking's order when the reranker can't answer.

```
Desk(client, texts, vectors)
desk.search(question, vector, k=5) -> list of rows
```

Two tests run on every attempt. Then four checks run before the code ships.
