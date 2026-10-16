```python
def recall_at_k(ranked, relevant, k):
    total = relevant.sum()
    return relevant[ranked[:k]].sum() / total if total else 0.0


def reciprocal_rank(ranked, relevant, k):
    found = np.flatnonzero(relevant[ranked[:k]])
    return 1 / (found[0] + 1) if len(found) else 0.0


def ndcg_at_k(ranked, gains, k):
    discounts = 1 / np.log2(np.arange(2, k + 2))
    best = np.sort(gains)[::-1][:k] @ discounts
    return gains[ranked[:k]] @ discounts / best if best else 0.0
```

Each score asks something else of the first `$k$`. Recall asks how many of the query's exact matches they hold. The queries have {% $fig.exact_mean %} on average, and {% $fig.over_k %} of the {% $fig.queries %} have more than {% $fig.k %}, so for those recall at {% $fig.k %} can't reach 1. The reciprocal rank asks how soon the first one comes. nDCG asks how much of the best possible order the ranking keeps, and gives a substitute some credit.

Over the {% $fig.queries %} queries, with the first {% $fig.k %} products:

| Numbers kept | nDCG | Recall | MRR |
| --- | --- | --- | --- |
| {% $fig.kept_256 %} | {% $fig.ndcg_256 %} | {% $fig.recall_256 %} | {% $fig.mrr_256 %} |
| {% $fig.kept_128 %} | {% $fig.ndcg_128 %} | {% $fig.recall_128 %} | {% $fig.mrr_128 %} |
| {% $fig.kept_64 %} | {% $fig.ndcg_64 %} | {% $fig.recall_64 %} | {% $fig.mrr_64 %} |

Half the numbers take half the memory and half the work for each similarity, and cost {% $fig.ndcg_drop %} in nDCG. The chart shows the three scores for each count of numbers kept.
