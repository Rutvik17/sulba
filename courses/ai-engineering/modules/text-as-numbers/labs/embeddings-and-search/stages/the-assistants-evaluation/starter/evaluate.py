"""Scores the shop's search on people's judgements, to compare one search with
another."""

import numpy as np

# How many products the search shows for each query.
K = 10


def rank(query_vectors, product_vectors):
    """For each query, every product's index, the most similar first."""
    scores = query_vectors @ product_vectors.T
    return np.argsort(-scores, axis=1, kind="stable")


def recall(ranked, relevant, k=K):
    """The share of the relevant products among the first k ranked."""
    return relevant[ranked[:k]].sum() / k


def reciprocal_rank(ranked, relevant, k=K):
    """1 over the rank of the first relevant product among the first k."""
    return 1 / (np.argmax(relevant[ranked[:k]]) + 1)


def ndcg(ranked, gains, k=K):
    """The DCG of the first k ranked over the best DCG there is."""
    discounts = 1 / np.log2(np.arange(2, k + 2))
    shown = gains[ranked[:k]]
    best = np.sort(shown)[::-1] @ discounts
    return shown @ discounts / best if best else 0.0


def report(query_vectors, product_vectors, gains, k=K):
    """The mean recall, MRR and nDCG of the first k products over the queries."""
    ranked = rank(query_vectors, product_vectors)
    relevant = gains == 1
    pairs = list(zip(ranked, relevant, gains, strict=True))
    return {
        "recall": np.mean([recall(r, e, k) for r, e, _ in pairs]),
        "mrr": np.mean([reciprocal_rank(r, e, k) for r, e, _ in pairs]),
        "ndcg": np.mean([ndcg(r, g, k) for r, _, g in pairs]),
    }
