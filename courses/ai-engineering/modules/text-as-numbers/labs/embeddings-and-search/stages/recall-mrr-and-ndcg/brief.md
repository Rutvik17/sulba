To compare one search with another, the shop scores each against people's judgements in `data/judgements.csv`. `load_gains`, in `search.py` since the first stage, gives each query's gain for each product, from the dataset's paper: {% $fig.exact_gain %} for an exact match, {% $fig.substitute %} for a substitute, {% $fig.complement %} for a complement and {% $fig.irrelevant_gain %} for an irrelevant product, or for one nobody judged for that query. An exact match counts as relevant.

Write three scores of the first `$k$` products a query's search ranks:

```
recall_at_k(ranked, relevant, k) -> the share of the relevant products among them
reciprocal_rank(ranked, relevant, k) -> 1 over the rank of the first relevant one, or 0
ndcg_at_k(ranked, gains, k) -> their discounted gain over the best there could be
```

`ranked` holds product indexes, the first ranked first, `relevant` is true for each relevant product, and `gains` holds each product's gain. The discounted cumulative gain counts a product's gain less the lower it is ranked:

```math
\text{DCG@}k = \sum_{i=1}^{k} \frac{g_i}{\log_2(i + 1)}
```

nDCG divides it by the DCG of the best ranking there is, the query's products sorted by their gains, so that it runs from 0 to 1. The mean reciprocal rank over the queries is MRR. The tests compare your nDCG with scikit-learn's `ndcg_score`.
