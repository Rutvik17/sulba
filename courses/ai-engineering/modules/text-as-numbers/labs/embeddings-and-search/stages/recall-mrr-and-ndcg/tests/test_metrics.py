import numpy as np
import pytest
from sklearn.metrics import ndcg_score

from search import (
    load_embeddings,
    load_gains,
    ndcg_at_k,
    nearest,
    recall_at_k,
    reciprocal_rank,
    similarities,
)

# How many products the search shows for each query.
K = 10


@pytest.fixture(scope="module")
def search():
    """Each query's ranking of every product, and its gains."""
    queries, query_vectors = load_embeddings("data/queries.csv")
    products, product_vectors = load_embeddings("data/products.csv")
    scores = similarities(query_vectors, product_vectors)
    return nearest(scores, len(products)), load_gains(queries, products)


@pytest.mark.id("tst_mfakoy")
def test_recall():
    """Recall at k"""
    relevant = np.array([True, False, False, True, False])
    ranked = np.array([3, 1, 0, 2, 4])
    assert recall_at_k(ranked, relevant, 1) == pytest.approx(0.5)
    assert recall_at_k(ranked, relevant, 2) == pytest.approx(0.5)
    assert recall_at_k(ranked, relevant, 3) == pytest.approx(1.0)
    assert recall_at_k(ranked, np.zeros(5, dtype=bool), 3) == 0


@pytest.mark.id("tst_bt0bbn")
def test_reciprocal_rank():
    """Reciprocal rank"""
    relevant = np.array([False, False, True, False, True])
    assert reciprocal_rank(np.array([0, 1, 2, 3, 4]), relevant, 5) == pytest.approx(
        1 / 3
    )
    assert reciprocal_rank(np.array([4, 0, 1, 2, 3]), relevant, 5) == pytest.approx(1)
    assert reciprocal_rank(np.array([0, 1, 3, 2, 4]), relevant, 3) == 0


@pytest.mark.id("tst_6voj94")
def test_ndcg(search):
    """Matches scikit-learn's ndcg_score"""
    ranked, gains = search
    # Scores that fall in the order ranked, with no two tied.
    scores = np.empty(ranked.shape)
    np.put_along_axis(scores, ranked, -np.arange(ranked.shape[1]), axis=1)
    for order, row, score in zip(ranked, gains, scores, strict=True):
        wanted = ndcg_score([row], [score], k=K)
        assert ndcg_at_k(order, row, K) == pytest.approx(wanted, abs=1e-12)
    for k in [1, 5, 20]:
        found = np.mean([ndcg_at_k(order, row, k) for order, row in zip(ranked, gains)])
        assert found == pytest.approx(ndcg_score(gains, scores, k=k), abs=1e-12)


@pytest.mark.id("tst_9ywff1")
def test_best():
    """1 for the best ranking, and 0 when no product has a gain"""
    gains = np.array([0.0, 0.1, 1.0, 0.01, 0.0, 1.0])
    best = np.argsort(-gains, kind="stable")
    assert ndcg_at_k(best, gains, 3) == pytest.approx(1)
    assert ndcg_at_k(best[::-1], gains, 3) < 1
    assert ndcg_at_k(best, np.zeros(6), 3) == 0
