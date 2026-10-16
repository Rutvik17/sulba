import numpy as np
import pytest

from search import (
    build_index,
    load_embeddings,
    nearest,
    normalize,
    search_index,
    similarities,
)

# How many products the search shows, the share of the full search's first K the index
# must find, and the share of the products it may compare with each query.
K, RECALL, COMPARED = 10, 0.95, 0.30


@pytest.fixture(scope="module")
def search():
    """The test queries' vectors, the products', the index, and the full search's
    first K products for each test query."""
    queries, query_vectors = load_embeddings("data/queries.csv")
    _, product_vectors = load_embeddings("data/products.csv")
    tests = query_vectors[(queries["set"] == "test").to_numpy()]
    full = nearest(similarities(tests, product_vectors), K)
    return tests, product_vectors, build_index(product_vectors), full


@pytest.fixture(scope="module")
def searched(search):
    """What the index finds for each test query, and how many products each compared."""
    tests, product_vectors, index, _ = search
    return search_index(index, product_vectors, tests, K)


@pytest.mark.id("tst_drwui7")
def test_lists(search):
    """Each product in its nearest list"""
    _, product_vectors, (centroids, lists), _ = search
    products = normalize(product_vectors)
    # Each product's squared distance from each centroid, without an array of every pair's
    # difference.
    distances = (
        (products**2).sum(axis=1)[:, None]
        - 2 * products @ centroids.T
        + (centroids**2).sum(axis=1)
    )
    given = np.take_along_axis(distances, np.asarray(lists)[:, None], axis=1)[:, 0]
    np.testing.assert_allclose(given, distances.min(axis=1), atol=1e-9)


@pytest.mark.id("tst_h9hiup")
def test_recall(search, searched, record_property):
    """As good as the full search"""
    *_, full = search
    found, _ = searched
    shares = [np.isin(mine, theirs).sum() / K for mine, theirs in zip(found, full)]
    record_property("note", f"{np.mean(shares):.1%} of the full search's first {K}")
    assert np.mean(shares) >= RECALL


@pytest.mark.id("tst_zssutx")
def test_compared(search, searched, record_property):
    """A fraction of the catalogue"""
    _, product_vectors, _, _ = search
    _, compared = searched
    share = np.mean(compared) / len(product_vectors)
    record_property("note", f"{share:.1%} of the products compared")
    assert share <= COMPARED


@pytest.mark.id("tst_2nlipv")
def test_every_list(search):
    """Every list searched, the full search"""
    tests, product_vectors, index, full = search
    centroids, _ = index
    found, _ = search_index(index, product_vectors, tests, K, len(centroids))
    scores = similarities(tests, product_vectors)
    for row, mine, theirs in zip(scores, found, full, strict=True):
        np.testing.assert_allclose(row[mine], row[theirs], atol=1e-12)
