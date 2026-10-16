import numpy as np
import pandas as pd

# What each label is worth, as in search.py, and how many products the search shows.
GAINS = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}
K = 10


def vectors(path):
    table = pd.read_csv(path, keep_default_na=False)
    columns = [column for column in table.columns if column.startswith("e_")]
    return table, table[columns].to_numpy(dtype=float)


def ranking(query_vectors, product_vectors):
    scores = query_vectors @ product_vectors.T
    return np.argsort(-scores, axis=1, kind="stable")[:, :K]


def unit(vectors):
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def figures():
    queries, query_vectors = vectors("data/queries.csv")
    products, product_vectors = vectors("data/products.csv")
    judgements = pd.read_csv("data/judgements.csv", keep_default_na=False)
    rows = dict(zip(queries["query_id"], range(len(queries)), strict=True))
    columns = dict(zip(products["product_id"], range(len(products)), strict=True))
    gains = np.zeros((len(queries), len(products)))
    for query, product, label in judgements.itertuples(index=False):
        gains[rows[query], columns[product]] = GAINS[label]
    exact = gains == 1
    discounts = 1 / np.log2(np.arange(2, K + 2))
    best = np.sort(gains, axis=1)[:, ::-1][:, :K] @ discounts

    def ndcg(ranked):
        return np.take_along_axis(gains, ranked, axis=1) @ discounts / best

    cosine = ranking(unit(query_vectors), unit(product_vectors))
    dot = ranking(query_vectors, product_vectors)
    shown = np.take_along_axis(gains, cosine, axis=1)
    hits = np.take_along_axis(exact, cosine, axis=1)
    first = np.where(hits.any(axis=1), 1 / (hits.argmax(axis=1) + 1), 0)
    # The assistant's DCG divided by the best order of the products shown alone.
    shown_best = np.sort(shown, axis=1)[:, ::-1] @ discounts
    with np.errstate(invalid="ignore", divide="ignore"):
        inflated = np.where(shown_best > 0, shown @ discounts / shown_best, 0)
    return {
        "k": str(K),
        "queries": str(len(queries)),
        "dot_changed": str((dot != cosine).any(axis=1).sum()),
        "dot_ndcg": f"{ndcg(dot).mean():.3f}",
        "ndcg": f"{ndcg(cosine).mean():.3f}",
        "recall": f"{(hits.sum(axis=1) / exact.sum(axis=1)).mean():.3f}",
        "recall_over_k": f"{(hits.sum(axis=1) / K).mean():.3f}",
        "mrr": f"{first.mean():.3f}",
        "mrr_counted": f"{np.where(hits.any(axis=1), first, 1).mean():.3f}",
        "no_exact": str((~hits.any(axis=1)).sum()),
        "inflated": f"{inflated.mean():.3f}",
        "perfect": str((np.isclose(inflated, 1)).sum()),
    }
