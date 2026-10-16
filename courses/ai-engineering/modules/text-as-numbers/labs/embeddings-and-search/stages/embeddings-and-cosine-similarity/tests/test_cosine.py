import numpy as np
import pytest
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize as sklearn_normalize

from search import load_embeddings, normalize, similarities


@pytest.fixture(scope="module")
def vectors():
    _, queries = load_embeddings("data/queries.csv")
    _, products = load_embeddings("data/products.csv")
    return queries, products


@pytest.mark.id("tst_hy7lhx")
def test_normalize(vectors):
    """Matches scikit-learn's normalize"""
    rng = np.random.default_rng(0)
    for found in [*vectors, rng.normal(0, 5, size=(50, 8))]:
        np.testing.assert_allclose(
            normalize(found), sklearn_normalize(found), rtol=1e-12
        )
    np.testing.assert_allclose(np.linalg.norm(normalize(vectors[1]), axis=1), 1)


@pytest.mark.id("tst_a67n4o")
def test_one_vector():
    """Normalizes one vector on its own"""
    np.testing.assert_allclose(normalize(np.array([3.0, 4.0])), [0.6, 0.8])


@pytest.mark.id("tst_aqy17a")
def test_similarities(vectors):
    """Matches scikit-learn's cosine_similarity"""
    queries, products = vectors
    found = similarities(queries, products)
    assert found.shape == (len(queries), len(products))
    np.testing.assert_allclose(found, cosine_similarity(queries, products), atol=1e-12)


@pytest.mark.id("tst_nucqrl")
def test_length(vectors):
    """Doesn't depend on the vectors' lengths"""
    queries, products = vectors
    found = similarities(3 * queries[:5], products[:50] / 7)
    np.testing.assert_allclose(
        found, similarities(queries[:5], products[:50]), atol=1e-12
    )
