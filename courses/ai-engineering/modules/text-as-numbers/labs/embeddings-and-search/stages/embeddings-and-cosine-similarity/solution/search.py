"""The shop's search: queries and product titles as embeddings, ranked by how alike they
are."""

import numpy as np
import pandas as pd


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
