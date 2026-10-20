import numpy as np
import pytest

from desk import Desk

TEXTS = [
    "Apply for disability benefits online.",
    "Renew a driver license by mail.",
    "Apply for disability benefits online.",
    "Benefits for veterans and their families.",
]
VECTORS = np.array([[3, 4, 0], [0, 3, 4], [3, 4, 0], [4, 0, 3]])
QUESTION = "How do I apply for disability benefits?"
VECTOR = np.array([3, 4, 1])


@pytest.mark.id("tst_oze8pe")
def test_reranked(model):
    """The fused ranking's passages, by the reranker's scores"""
    scores = {TEXTS[0]: 0.2, TEXTS[1]: 0.9, TEXTS[3]: 0.5}
    model.ranks(lambda query, document: scores[document])
    desk = Desk(model.client(), TEXTS, VECTORS)
    assert desk.search(QUESTION, VECTOR, 3) == [1, 3, 0]


@pytest.mark.id("tst_zi56pg")
def test_each_text_once(model):
    """A text two passages share, scored and given once"""
    model.ranks(lambda query, document: 0.5)
    desk = Desk(model.client(), TEXTS, VECTORS)
    found = desk.search(QUESTION, VECTOR, 3)
    (request,) = model.requests
    assert sorted(request.body["documents"]) == sorted(set(TEXTS))
    assert len({TEXTS[row] for row in found}) == len(found) == 3
