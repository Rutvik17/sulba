import numpy as np
import pytest
from sklearn.metrics import ndcg_score

import search
from evaluate import K, ndcg, rank, recall, reciprocal_rank


@pytest.fixture(scope="module")
def judged():
    """Each query's ranking of every product by the full search, and its gains."""
    queries, query_vectors = search.load_embeddings("data/queries.csv")
    products, product_vectors = search.load_embeddings("data/products.csv")
    scores = search.similarities(query_vectors, product_vectors)
    ranked = search.nearest(scores, len(products))
    return query_vectors, product_vectors, ranked, search.load_gains(queries, products)


@pytest.mark.id("tst_q6cgb7")
def test_rank(judged):
    """Ranks by cosine similarity"""
    query_vectors, product_vectors, ranked, _ = judged
    found = rank(query_vectors, product_vectors)
    np.testing.assert_array_equal(found[:, :K], ranked[:, :K])


@pytest.mark.id("tst_fumj5a")
def test_recall(judged):
    """Recall over all of a query's relevant products"""
    *_, ranked, gains = judged
    for order, row in zip(ranked, gains, strict=True):
        wanted = search.recall_at_k(order, row == 1, K)
        assert recall(order, row == 1, K) == pytest.approx(wanted)


@pytest.mark.id("tst_kwa1py")
def test_reciprocal_rank(judged):
    """No relevant product shown, no reciprocal rank"""
    *_, ranked, gains = judged
    for order, row in zip(ranked, gains, strict=True):
        wanted = search.reciprocal_rank(order, row == 1, K)
        assert reciprocal_rank(order, row == 1, K) == pytest.approx(wanted)


@pytest.mark.id("tst_56j4ih")
def test_ndcg(judged):
    """nDCG against the best ranking there is"""
    *_, ranked, gains = judged
    for order, row in zip(ranked, gains, strict=True):
        scores = np.empty(len(order))
        scores[order] = -np.arange(len(order))
        wanted = ndcg_score([row], [scores], k=K)
        assert ndcg(order, row, K) == pytest.approx(wanted, abs=1e-12)
