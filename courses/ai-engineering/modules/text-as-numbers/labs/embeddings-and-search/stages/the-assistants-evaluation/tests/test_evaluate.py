import numpy as np
import pytest

from evaluate import ndcg, rank, recall, reciprocal_rank, report
from search import load_embeddings, load_gains


@pytest.fixture(scope="module")
def search():
    queries, query_vectors = load_embeddings("data/queries.csv")
    products, product_vectors = load_embeddings("data/products.csv")
    return query_vectors[:20], product_vectors, load_gains(queries, products)[:20]


@pytest.mark.id("tst_a8r2tp")
def test_rank(search):
    """Ranks every product for each query"""
    query_vectors, product_vectors, _ = search
    ranked = rank(query_vectors, product_vectors)
    assert ranked.shape == (len(query_vectors), len(product_vectors))
    assert all(
        sorted(row) == list(range(len(product_vectors))) for row in ranked.tolist()
    )


@pytest.mark.id("tst_j5hmqp")
def test_best_ranking():
    """The best ranking scores 1"""
    gains = np.array([0.0, 1.0, 0.1, 1.0, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    best = np.argsort(-gains, kind="stable")
    assert ndcg(best, gains) == pytest.approx(1)
    assert reciprocal_rank(best, gains == 1) == 1


@pytest.mark.id("tst_ee0kam")
def test_recall_range():
    """Recall between 0 and 1"""
    relevant = np.zeros(30, dtype=bool)
    relevant[[2, 5, 7]] = True
    assert 0 < recall(np.arange(30), relevant) <= 1
    assert recall(np.arange(30)[::-1], relevant) == 0


@pytest.mark.id("tst_qo49b3")
def test_report(search):
    """Reports the three scores, each between 0 and 1"""
    scores = report(*search)
    assert set(scores) == {"recall", "mrr", "ndcg"}
    assert all(0 <= value <= 1 for value in scores.values())
