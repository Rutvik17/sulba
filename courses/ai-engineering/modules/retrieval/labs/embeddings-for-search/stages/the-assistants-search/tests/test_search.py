import numpy as np
import pytest

from cache import Cache
from embed import DOCUMENT, QUERY
from search import NUMBERS, Search

PASSAGES = {
    "p1": "You can apply for disability benefits online.",
    "p2": "Renew your driver license before it expires.",
    "p3": "Federal student loans have fixed interest rates.",
}
TOPICS = ["disability", "license", "loan"]


def vector(text):
    """A vector of 768 numbers whose first NUMBERS point to the topics the text
    names."""
    text = text.removeprefix(DOCUMENT).removeprefix(QUERY).lower()
    short = np.full(NUMBERS, 0.01)
    for place, topic in enumerate(TOPICS):
        if topic in text:
            short[place] = 1.0
    short /= np.linalg.norm(short)
    rest = np.full(768 - NUMBERS, -short.sum() / (768 - NUMBERS))
    return np.concatenate([short, rest]).tolist()


@pytest.mark.id("tst_j7d2no")
def test_finds(model, tmp_path):
    """The passage about a question's topic comes first"""
    model.embeds(vector)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        search = Search(model.client(), cache, PASSAGES)
        found = search.find(["How do I apply for disability benefits?"], k=1)
    assert found == [["p1"]]


@pytest.mark.id("tst_c4q6vu")
def test_k(model, tmp_path):
    """k passages for each question"""
    model.embeds(vector)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        search = Search(model.client(), cache, PASSAGES)
        found = search.find(
            ["When does my license expire?", "Can I pay off my loan?"], k=2
        )
    assert [len(ids) for ids in found] == [2, 2]
    assert all(set(ids) <= set(PASSAGES) for ids in found)


@pytest.mark.id("tst_y1h5ef")
def test_once(model, tmp_path):
    """Each passage embedded once, however many searches start"""
    model.embeds(vector)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        Search(model.client(), cache, PASSAGES)
        Search(model.client(), cache, PASSAGES)
    assert len(model.requests) == 1
