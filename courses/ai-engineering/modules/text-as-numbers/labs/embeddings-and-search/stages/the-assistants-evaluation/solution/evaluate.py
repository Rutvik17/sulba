"""Scores the shop's search on people's judgements, to compare one search with
another."""

import numpy as np

# How many products the search shows for each query.
K = 10


def rank(query_vectors, product_vectors):
    """For each query, every product's index, the most similar first."""
    queries = query_vectors / np.linalg.norm(query_vectors, axis=1, keepdims=True)
    products = product_vectors / np.linalg.norm(product_vectors, axis=1, keepdims=True)
    scores = queries @ products.T
    return np.argsort(-scores, axis=1, kind="stable")


def recall(ranked, relevant, k=K):
    """The share of the relevant products among the first k ranked."""
    total = relevant.sum()
    return relevant[ranked[:k]].sum() / total if total else 0.0


def reciprocal_rank(ranked, relevant, k=K):
    """1 over the rank of the first relevant product among the first k."""
    found = np.flatnonzero(relevant[ranked[:k]])
    return 1 / (found[0] + 1) if len(found) else 0.0


def ndcg(ranked, gains, k=K):
    """The DCG of the first k ranked over the best DCG there is."""
    discounts = 1 / np.log2(np.arange(2, k + 2))
    shown = gains[ranked[:k]]
    best = np.sort(gains)[::-1][:k] @ discounts
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
