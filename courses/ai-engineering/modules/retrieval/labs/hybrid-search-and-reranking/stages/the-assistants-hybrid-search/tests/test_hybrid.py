import numpy as np
import pytest

from hybrid import Hybrid, words

TEXTS = [
    "Apply for disability benefits online.",
    "Renew a driver license by mail.",
    "Benefits for veterans and their families.",
]
VECTORS = np.array([[3, 4, 0], [0, 3, 4], [4, 0, 3]])


@pytest.mark.id("tst_5jkdx4")
def test_words():
    """Runs of letters, digits and underscores, lowercased"""
    assert words("Apply for SSI? Form SS-5.") == [
        "apply",
        "for",
        "ssi",
        "form",
        "ss",
        "5",
    ]


@pytest.mark.id("tst_ema0ug")
def test_bm25():
    """The passage that holds the question's words first"""
    scores = Hybrid(TEXTS, VECTORS).bm25("renew license")
    assert scores[1] > 0
    assert scores[0] == scores[2] == 0


@pytest.mark.id("tst_m3kpr4")
def test_similarity():
    """The passage whose vector points the question's way first"""
    assert Hybrid(TEXTS, VECTORS).similarity(np.array([0, 3, 4])).argmax() == 1


@pytest.mark.id("tst_s99t7e")
def test_search():
    """k rows, the best first"""
    found = Hybrid(TEXTS, VECTORS).search("renew license", np.array([0, 3, 4]), k=2)
    assert len(found) == 2
    assert found[0] == 1
