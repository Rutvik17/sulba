"""The shop's search: queries and product titles as embeddings, ranked by how alike they
are."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def load_embeddings(path):
    """A file of embeddings, and its vectors as an array with a row for each."""
    # keep_default_na=False reads every query and title as text.
    table = pd.read_csv(path, keep_default_na=False)
    columns = [column for column in table.columns if column.startswith("e_")]
    return table, table[columns].to_numpy(dtype=float)


# What each label people give is worth, from the dataset's paper: an exact match, a
# substitute, a complement and an irrelevant product.
GAINS = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}


def load_gains(queries, products, path="data/judgements.csv"):
    """Each query's gain for each product, a row for each query, and 0 for a product
    nobody judged for it."""
    judgements = pd.read_csv(path, keep_default_na=False)
    rows = dict(zip(queries["query_id"], range(len(queries)), strict=True))
    columns = dict(zip(products["product_id"], range(len(products)), strict=True))
    gains = np.zeros((len(queries), len(products)))
    for query, product, label in judgements.itertuples(index=False):
        gains[rows[query], columns[product]] = GAINS[label]
    return gains


def normalize(vectors):
    """Each vector divided by its length, along the last axis."""
    vectors = np.asarray(vectors, dtype=float)
    return vectors / np.linalg.norm(vectors, axis=-1, keepdims=True)


def similarities(queries, products):
    """The cosine similarity of each query with each product, a row for each query."""
    return normalize(queries) @ normalize(products).T


def nearest(similarities, k):
    """For each query, the indexes of its k most similar products, the most similar
    first, and of products tied, the one that comes first."""
    return np.argsort(-similarities, axis=1, kind="stable")[:, :k]


def recall_at_k(ranked, relevant, k):
    """The share of the relevant products that are among the first k ranked, or 0 if no
    product is relevant."""
    total = relevant.sum()
    return relevant[ranked[:k]].sum() / total if total else 0.0


def reciprocal_rank(ranked, relevant, k):
    """1 over the rank of the first relevant product among the first k, or 0 if none
    is."""
    found = np.flatnonzero(relevant[ranked[:k]])
    return 1 / (found[0] + 1) if len(found) else 0.0


def ndcg_at_k(ranked, gains, k):
    """The DCG of the first k ranked, over the DCG of the best ranking there is, or 0 if
    no product has a gain."""
    discounts = 1 / np.log2(np.arange(2, k + 2))
    best = np.sort(gains)[::-1][:k] @ discounts
    return gains[ranked[:k]] @ discounts / best if best else 0.0


# How many lists the index groups the products into, and how many of them each query
# searches.
LISTS, PROBES = 128, 20


def build_index(product_vectors, lists=LISTS):
    """The index: the k-means centroids of the normalized products, and each product's
    list."""
    kmeans = KMeans(n_clusters=lists, n_init=1, random_state=0)
    kmeans.fit(normalize(product_vectors))
    return kmeans.cluster_centers_, kmeans.labels_


def search_index(index, product_vectors, query_vectors, k, probes=PROBES):
    """Each query's k most similar products among those in the probes lists whose
    centroids are nearest to it, and how many products each query compared."""
    centroids, lists = index
    products, queries = normalize(product_vectors), normalize(query_vectors)
    distances = ((queries[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    searched = np.argsort(distances, axis=1, kind="stable")[:, :probes]
    found, compared = [], []
    for query, chosen in zip(queries, searched, strict=True):
        candidates = np.flatnonzero(np.isin(lists, chosen))
        scores = products[candidates] @ query
        found.append(candidates[np.argsort(-scores, kind="stable")[:k]])
        compared.append(len(candidates))
    return found, np.array(compared)
