import csv
import json
import math
from pathlib import Path

import numpy as np
import pytest

from bm25 import BM25, words

RECORDED = json.loads(Path("references/bm25.json").read_text(encoding="utf-8"))


def expected(passages, question, k1=1.5, b=0.75):
    """Each passage's score, word by word, as BM25 defines it."""
    average = sum(map(len, passages)) / len(passages)
    found = []
    for passage in passages:
        score = 0.0
        for word in question:
            held = sum(word in other for other in passages)
            if not held:
                continue
            idf = math.log(1 + (len(passages) - held + 0.5) / (held + 0.5))
            tf = passage.count(word)
            score += idf * tf / (tf + k1 * (1 - b + b * len(passage) / average))
        found.append(score)
    return found


@pytest.fixture(scope="module")
def index():
    """The help desk's passages, indexed."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        return BM25([words(row["text"]) for row in csv.DictReader(file)])


@pytest.mark.id("tst_0raftn")
def test_words():
    """Runs of letters, digits and underscores, lowercased"""
    assert words("Apply for SSI—or SSDI? Form SS-5, at 9am.") == [
        "apply",
        "for",
        "ssi",
        "or",
        "ssdi",
        "form",
        "ss",
        "5",
        "at",
        "9am",
    ]
    assert words("Café_2 ") == ["café_2"]


@pytest.mark.id("tst_az34zx")
def test_scores():
    """Each passage's score for the question's words"""
    passages = [
        ["apply", "for", "benefits", "online"],
        ["benefits", "benefits", "for", "veterans"],
        ["renew", "a", "license"],
        ["apply", "to", "renew", "a", "license", "by", "mail"],
    ]
    question = ["apply", "for", "benefits"]
    found = BM25(passages).scores(question)
    assert found == pytest.approx(expected(passages, question), rel=1e-12)


@pytest.mark.id("tst_jyyrnl")
def test_repeated_and_unknown():
    """A word as many times as the question holds it, and an unknown word adding nothing"""
    passages = [["apply", "online"], ["apply", "by", "mail"], ["renew"]]
    index = BM25(passages)
    once = index.scores(["apply"])
    assert index.scores(["apply", "apply"]) == pytest.approx(2 * once, rel=1e-12)
    assert index.scores(["apply", "zebra"]) == pytest.approx(once, rel=1e-12)
    assert index.scores(["zebra"]).tolist() == [0.0, 0.0, 0.0]


@pytest.mark.id("tst_2cyvf0")
def test_top():
    """The highest scores first, a tie going to the earlier passage"""
    passages = [["mail"], ["apply", "online"], ["mail"], ["apply"]]
    assert BM25(passages).top(["mail"], 3) == [0, 2, 1]
    assert BM25(passages).top(["apply"], 2) == [3, 1]


@pytest.mark.id("tst_00xt33")
def test_recorded(index):
    """bm25s's scores for the validation questions, and its first 20 passages"""
    for case in RECORDED:
        found = index.scores(case["words"])
        if "scores" in case:
            assert found == pytest.approx(case["scores"], rel=1e-9, abs=1e-12)
        rows = [row for row, _ in case["top"]]
        assert found[rows] == pytest.approx(
            [score for _, score in case["top"]], rel=1e-9
        )
        assert np.sort(found)[::-1][: len(rows)] == pytest.approx(found[rows], rel=1e-9)
