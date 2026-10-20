import numpy as np
import pytest

from cache import Cache
from embed import DOCUMENT, QUERY
from index import Index

PASSAGES = {
    "p1": "You can apply for disability benefits online.",
    "p2": "Renew your driver license before it expires.",
    "p3": "Federal student loans have fixed interest rates.",
}
TOPICS = ["disability", "license", "loan"]


def vector(text):
    """A vector of 768 numbers that points to the topics the text names."""
    text = text.removeprefix(DOCUMENT).removeprefix(QUERY).lower()
    found = np.random.default_rng(len(text)).normal(scale=0.01, size=768)
    for place, topic in enumerate(TOPICS):
        if topic in text:
            found[place] += 1.0
    return (found / np.linalg.norm(found)).tolist()


@pytest.mark.id("tst_g3x7po")
def test_finds(model, tmp_path):
    """Each question's passage comes first"""
    model.embeds(vector)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        index = Index.build(model.client(), cache, PASSAGES)
        found = index.find(
            model.client(),
            cache,
            ["Can I get disability benefits?", "Where is my loan?"],
            k=2,
        )
    assert [ids[0] for ids in found] == ["p1", "p3"]
    assert all(len(ids) == 2 for ids in found)


@pytest.mark.id("tst_w4c8hs")
def test_saved(model, tmp_path):
    """An index saved and loaded finds the same"""
    model.embeds(vector)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        index = Index.build(model.client(), cache, PASSAGES)
        index.save(tmp_path / "index.npz")
        loaded = Index.load(tmp_path / "index.npz")
        question = ["When does my license expire?"]
        assert loaded.find(model.client(), cache, question) == index.find(
            model.client(), cache, question
        )
