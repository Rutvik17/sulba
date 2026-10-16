import numpy as np
import pytest

from search import build_index, load_embeddings, normalize, search_index


@pytest.fixture(scope="module")
def vectors():
    _, queries = load_embeddings("data/queries.csv")
    _, products = load_embeddings("data/products.csv")
    return queries[:10], products


@pytest.fixture(scope="module")
def index(vectors):
    """The products' index in 8 lists."""
    _, products = vectors
    return build_index(products, 8)


@pytest.mark.id("tst_31xu4z")
def test_lists(vectors, index):
    """Every product in one of the lists"""
    _, products = vectors
    centroids, lists = index
    assert centroids.shape == (8, products.shape[1])
    assert lists.shape == (len(products),)
    assert set(lists.tolist()) <= set(range(8))


@pytest.mark.id("tst_3i37yf")
def test_searched(vectors, index):
    """Products from the lists searched, the most similar first"""
    queries, products = vectors
    centroids, lists = index
    found, compared = search_index(index, products, queries, 10, 2)
    units = normalize(queries)
    for query, chosen, count in zip(units, found, compared, strict=True):
        distances = ((centroids - query) ** 2).sum(axis=1)
        searched = np.argsort(distances, kind="stable")[:2]
        assert np.isin(lists[chosen], searched).all()
        assert count == np.isin(lists, searched).sum()
        scores = normalize(products[chosen]) @ query
        assert np.all(np.diff(scores) <= 0)
