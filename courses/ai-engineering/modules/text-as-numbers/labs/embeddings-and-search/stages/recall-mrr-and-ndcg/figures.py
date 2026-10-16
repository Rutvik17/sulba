import numpy as np
import pandas as pd

# What each label is worth, as in search.py, how many products the search shows, and the
# numbers kept of each embedding the explanation compares.
GAINS = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}
K, KEPT = 10, [256, 128, 64]


def vectors(path):
    table = pd.read_csv(path, keep_default_na=False)
    columns = [column for column in table.columns if column.startswith("e_")]
    return table, table[columns].to_numpy(dtype=float)


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
    discounts = 1 / np.log2(np.arange(2, K + 2))
    best = np.sort(gains, axis=1)[:, ::-1][:, :K] @ discounts
    exact = gains == 1
    values = {
        "k": str(K),
        "queries": str(len(queries)),
        "exact_gain": f"{GAINS['E']:g}",
        "substitute": f"{GAINS['S']:g}",
        "complement": f"{GAINS['C']:g}",
        "irrelevant_gain": f"{GAINS['I']:g}",
        "exact_mean": f"{exact.sum(axis=1).mean():.1f}",
        "over_k": str((exact.sum(axis=1) > K).sum()),
    }
    ndcg = {}
    for kept in KEPT:
        scores = unit(query_vectors[:, :kept]) @ unit(product_vectors[:, :kept]).T
        ranked = np.argsort(-scores, axis=1, kind="stable")[:, :K]
        shown = np.take_along_axis(gains, ranked, axis=1)
        hits = np.take_along_axis(exact, ranked, axis=1)
        first = np.where(hits.any(axis=1), 1 / (hits.argmax(axis=1) + 1), 0)
        values[f"kept_{kept}"] = str(kept)
        ndcg[kept] = (shown @ discounts / best).mean()
        values[f"ndcg_{kept}"] = f"{ndcg[kept]:.3f}"
        values[f"recall_{kept}"] = (
            f"{(hits.sum(axis=1) / exact.sum(axis=1)).mean():.3f}"
        )
        values[f"mrr_{kept}"] = f"{first.mean():.3f}"
    values["ndcg_drop"] = f"{ndcg[256] - ndcg[128]:.3f}"
    return values
