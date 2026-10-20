BM25 and the vectors each find answers the other misses, so the help desk's search should use both. Their scores aren't on one scale: at the median, a question's best passage scores {% $fig.bm25_best %} by BM25, and {% $fig.dot_best %} by the dot product of the vectors' whole numbers. Reciprocal rank fusion, from Cormack, Clarke and Büttcher, adds ranks instead: a passage scores `$1 / (k + r)$` for its rank `$r$` in each ranking, the first rank being 1, and `$k$` is {% $fig.rrf %} unless a search gives another.

In `fuse.py`, write:

- `nearest(question, vectors)`: the rows of `vectors`, the most similar to `question` first, by the dot product of their whole numbers, a tie going to the earlier row.
- `fused(rankings, k)`: the rows the rankings rank, each ranking an array of every row in its order, by the sum over the rankings of `$1 / (k + r)$`, a tie going to the earlier row.
- `recall(rankings, relevant, k)`: the share of the questions, each with its ranking and its set of relevant rows, that have a relevant row among the first `k`.

```math
\text{RRF}(p) = \sum_{\text{rankings}} \frac{1}{k + r(p)}
```

```
nearest(question, vectors) -> np.ndarray of rows
fused(rankings, k) -> np.ndarray of rows
recall(rankings, relevant, k) -> float
```
