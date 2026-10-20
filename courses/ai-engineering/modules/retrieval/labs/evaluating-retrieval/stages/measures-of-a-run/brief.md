The help desk will choose its search by the numbers. It ran each of its {% $fig.searches %} searches on every question, validation and test, and kept the first {% $fig.shown %} passages each one showed in `data/runs.csv`: a row for each passage shown, with its search, its question and its rank from 1. `data/relevant.csv` holds the passages that answer each question.

| Search | What it shows |
| --- | --- |
| `bm25` | The passages in the order of their BM25 scores |
| `vectors` | The passages in the order of their vectors' similarity to the question's |
| `fused` | The two rankings fused by reciprocal rank fusion |
| `fused-once` | The fused ranking, each text once |
| `reranked` | The fused ranking's first {% $fig.texts %} texts, in the order of the scores Qwen3-Reranker-0.6B gave them |
| `reranked-bm25` | BM25's first {% $fig.texts %} texts, reranked |
| `reranked-vectors` | The vectors' first {% $fig.texts %} texts, reranked |
| `reranked-copies` | The fused ranking's first {% $fig.texts %} passages, copies of one text included, reranked |
| `confident` | The passages of `reranked` the reranker scores at {% $fig.confident %} or more, which for some questions is none |

In `measures.py`, write four measures of the passages a search shows for one question, best first, given the set of passages that answer it:

- `hit_rate(shown, relevant, k)`: 1 if a relevant passage is among the first `k` shown, else 0.
- `recall(shown, relevant, k)`: the share of the relevant passages that are among the first `k`.
- `reciprocal_rank(shown, relevant, k)`: 1 over the rank of the first relevant passage among the first `k`, the first rank being 1, or 0 if none is there.
- `ndcg(shown, relevant, k)`: the DCG of the first `k` over the DCG of the best ranking there is, every relevant passage first.

And their mean:

- `mean(measure, run, judgments, k)`: the mean of one of the four over every question in `judgments`, a question the run shows nothing for scoring 0.

```math
\text{DCG@}k = \sum_{i=1}^{k} \frac{\text{rel}_i}{\log_2(i + 1)}
```

`$\text{rel}_i$` is 1 if the passage at rank `$i$` is relevant, else 0. Each measure gives 0 for a question no passage answers. A run maps each question to the passages it shows, best first, and judgments map each question to its relevant passages. `shown` can hold `None`, which no set of relevant passages holds: the next stage puts it where a reader sees nothing new. The tests compare your measures with ranx's.

```
hit_rate(shown, relevant, k) -> float
recall(shown, relevant, k) -> float
reciprocal_rank(shown, relevant, k) -> float
ndcg(shown, relevant, k) -> float
mean(measure, run, judgments, k) -> float
```
