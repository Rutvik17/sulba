import csv
from collections import defaultdict

import pytest

from measures import hit_rate, ndcg, recall, reciprocal_rank
from texts import as_seen, first_passages, relevant_texts

TEXTS = {
    "p1": "Apply online.",
    "p2": "Renew by mail.",
    "p3": "Apply online.",
    "p4": "Call us.",
}
FIRST = {"p1": "p1", "p2": "p2", "p3": "p1", "p4": "p4"}


@pytest.fixture(scope="module")
def help_desk():
    """The passages' texts, and each search's run."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        texts = {row["passage"]: row["text"] for row in csv.DictReader(file)}
    runs = defaultdict(dict)
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            runs[row["search"]].setdefault(row["question"], []).append(row["passage"])
    return texts, runs


@pytest.mark.id("tst_owd4m0")
def test_first_passages():
    """Each passage's text as the first passage that holds it"""
    assert first_passages(TEXTS) == FIRST


@pytest.mark.id("tst_7sxwkg")
def test_as_seen():
    """Each passage at its rank, a text shown before as None"""
    assert as_seen(["p3", "p2", "p1", "p4", "p3"], FIRST) == [
        "p1",
        "p2",
        None,
        "p4",
        None,
    ]
    assert as_seen([], FIRST) == []


@pytest.mark.id("tst_4y2a9f")
def test_relevant_texts():
    """The relevant passages' texts, each once"""
    assert relevant_texts({"p1", "p3"}, FIRST) == {"p1"}
    assert relevant_texts({"p3", "p4"}, FIRST) == {"p1", "p4"}


@pytest.mark.id("tst_g9cqka")
def test_judged_by_text():
    """A copy of an answer counts once, and a text shown once counts in full"""
    relevant = relevant_texts({"p1", "p3"}, FIRST)
    copies = as_seen(["p3", "p1", "p2"], FIRST)
    assert recall(copies, relevant, 2) == 1
    assert ndcg(copies, relevant, 3) == pytest.approx(1)
    once = as_seen(["p1", "p2"], FIRST)
    assert recall(once, relevant, 5) == 1
    assert ndcg(once, relevant, 5) == pytest.approx(1)
    late = as_seen(["p2", "p4", "p3"], FIRST)
    assert hit_rate(late, relevant, 3) == 1
    assert reciprocal_rank(late, relevant, 3) == pytest.approx(1 / 3)


@pytest.mark.id("tst_ogkk7t")
def test_help_desk(help_desk):
    """Every search's passages, as a reader sees them"""
    texts, runs = help_desk
    first = first_passages(texts)
    assert len(first) == len(texts)
    for run in runs.values():
        for shown in run.values():
            seen = as_seen(shown, first)
            assert len(seen) == len(shown)
            kept = [passage for passage in seen if passage is not None]
            assert (
                len(kept)
                == len(set(kept))
                == len({texts[passage] for passage in shown})
            )
            for passage, text in zip(shown, seen, strict=True):
                assert text is None or texts[text] == texts[passage]
