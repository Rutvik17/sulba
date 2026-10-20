import numpy as np
import pytest

from cache import Cache
from embed import DOCUMENT, QUERY
from search import NUMBERS, Search


def raw(short):
    """A vector of 768 numbers that shortens to short: short at a length of 1, then
    numbers that bring the mean of all 768 to 0."""
    short = np.asarray(short, dtype=np.float64)
    short = short / np.linalg.norm(short)
    rest = np.full(768 - len(short), -short.sum() / (768 - len(short)))
    return np.concatenate([short, rest]).tolist()


def padded(first):
    """A vector of 768 numbers whose first are first as they are, then numbers that
    bring the mean of all 768 to 0."""
    first = np.asarray(first, dtype=np.float64)
    rest = np.full(768 - len(first), -first.sum() / (768 - len(first)))
    return np.concatenate([first, rest]).tolist()


def scripted(model, shorts):
    """Script the model to embed each text, after either prefix, as shorts gives it."""
    model.embeds(
        lambda text: raw(shorts[text.removeprefix(DOCUMENT).removeprefix(QUERY)])
    )


def unit(*places, size=NUMBERS):
    found = np.zeros(size)
    for place, value in places:
        found[place] = value
    return found


@pytest.mark.id("tst_a8u3mf")
def test_question_prefix(model, tmp_path):
    """Asks for the questions as questions"""
    shorts = {
        "Renew a license.": unit((0, 1.0)),
        "When does my license expire?": unit((0, 1.0)),
    }
    scripted(model, shorts)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        Search(model.client(), cache, {"p1": "Renew a license."}).find(
            ["When does my license expire?"], k=1
        )
    assert model.requests[-1].body["input"] == [QUERY + "When does my license expire?"]


@pytest.mark.id("tst_v6g0ws")
def test_cut(model, tmp_path):
    """Cuts the vectors as the model's card does"""
    question = "Which form do I need?"
    firsts = {
        # Form A points the question's way, but its first numbers are short; Form B's
        # are longer, at an angle to it.
        "Form A.": unit((0, 0.3)),
        "Form B.": unit((0, 0.9 * np.sqrt(0.5)), (1, 0.9 * np.sqrt(0.5))),
        question: unit((0, 1.0)),
    }
    model.embeds(
        lambda text: padded(firsts[text.removeprefix(DOCUMENT).removeprefix(QUERY)])
    )
    with Cache(tmp_path / "vectors.sqlite") as cache:
        search = Search(model.client(), cache, {"p1": "Form A.", "p2": "Form B."})
        assert search.find([question], k=1) == [["p1"]]


@pytest.mark.id("tst_q2e7kz")
def test_ids(model, tmp_path):
    """Gives each passage's own id"""
    passages = {f"p{number}": f"Passage {number}." for number in range(1, 13)}
    shorts = {
        text: unit((number - 1, 0.9), (NUMBERS - 1, np.sqrt(1 - 0.81)))
        for number, text in enumerate(passages.values(), start=1)
    }
    shorts["About passage 10?"] = unit((9, 1.0))
    scripted(model, shorts)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        search = Search(model.client(), cache, passages)
        assert search.find(["About passage 10?"], k=1) == [["p10"]]


@pytest.mark.id("tst_l5r9bj")
def test_best_first(model, tmp_path):
    """The best passage first"""
    shares = {"p1": 0.9, "p2": 0.7, "p3": 0.5, "p4": 0.3}
    passages = {id_: f"Passage {id_}." for id_ in shares}
    shorts = {
        passages[id_]: unit((0, share), (NUMBERS - 1, np.sqrt(1 - share**2)))
        for id_, share in shares.items()
    }
    shorts["Which passage?"] = unit((0, 1.0))
    scripted(model, shorts)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        search = Search(model.client(), cache, passages)
        assert search.find(["Which passage?"], k=3) == [["p1", "p2", "p3"]]
