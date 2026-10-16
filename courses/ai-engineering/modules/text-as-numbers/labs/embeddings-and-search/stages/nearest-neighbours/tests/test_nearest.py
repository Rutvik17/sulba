import numpy as np
import pytest
from sklearn.neighbors import NearestNeighbors

from search import load_embeddings, nearest, similarities

# How many products the search shows for each query.
K = 10


@pytest.fixture(scope="module")
def scores():
    _, queries = load_embeddings("data/queries.csv")
    _, products = load_embeddings("data/products.csv")
    return queries, products, similarities(queries, products)


@pytest.mark.id("tst_xlcr4d")
def test_like_scikit_learn(scores):
    """Finds the products scikit-learn's NearestNeighbors finds"""
    queries, products, found = scores
    index = NearestNeighbors(n_neighbors=K, metric="cosine", algorithm="brute")
    distances, _ = index.fit(products).kneighbors(queries)
    ranked = nearest(found, K)
    assert ranked.shape == (len(queries), K)
    chosen = np.take_along_axis(found, ranked, axis=1)
    np.testing.assert_allclose(chosen, 1 - distances, atol=1e-9)


@pytest.mark.id("tst_bs805z")
def test_ties():
    """Of products tied, the one that comes first"""
    assert nearest(np.array([[0.5, 0.9, 0.9, 0.1]]), 2).tolist() == [[1, 2]]
    assert nearest(np.array([[0.2, 0.2, 0.2], [0.1, 0.3, 0.3]]), 2).tolist() == [
        [0, 1],
        [1, 2],
    ]


@pytest.mark.id("tst_e30bj1")
def test_order(scores):
    """Every query's products, the most similar first"""
    _, products, found = scores
    ranked = nearest(found, len(products))
    for row, order in zip(found, ranked, strict=True):
        assert sorted(order.tolist()) == list(range(len(products)))
        assert np.all(np.diff(row[order]) <= 0)
