import csv
from collections import defaultdict

import numpy as np
import pytest

from known import error_rates, own, partners


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def passage(page, text):
    return {"page": page, "domain": page.split("-")[0], "title": page, "text": text}


PASSAGES = {
    "p1": passage("va-1", "Apply online."),
    "p2": passage("va-1", "Apply by mail."),
    "p3": passage("va-2", "Apply online."),
}


def asked(name, page):
    return {"question": name, "page": page, "domain": page.split("-")[0], "text": "?"}


@pytest.mark.id("tst_6juye4")
def test_own_passages():
    """Keeps the passages that hold the answer on the question's own page, in their order"""
    assert own(asked("q1", "va-1"), ["p2", "p3", "p1"], PASSAGES) == ["p2", "p1"]
    assert own(asked("q2", "va-2"), ["p2", "p3", "p1"], PASSAGES) == ["p3"]


@pytest.mark.id("tst_p3c2f0")
def test_partners():
    """Pairs each question with the one half the list on, or the next from another service"""
    questions = [
        asked("q1", "ssa-1"),
        asked("q2", "ssa-1"),
        asked("q3", "ssa-2"),
        asked("q4", "va-1"),
        asked("q5", "va-2"),
        asked("q6", "dmv-1"),
    ]
    assert partners(questions) == {
        "q1": "q4",
        "q2": "q5",
        "q3": "q6",
        "q4": "q1",
        "q5": "q2",
        "q6": "q3",
    }
    questions = [asked("q1", "va-1"), asked("q2", "va-1"), asked("q3", "ssa-1")]
    assert partners(questions) == {"q1": "q3", "q2": "q3", "q3": "q1"}


@pytest.mark.id("tst_54az7s")
def test_every_question():
    """Gives each of the help desk's questions its own passages and another service's question"""
    passages = {row["passage"]: row for row in read("passages.csv")}
    relevant = defaultdict(list)
    for row in read("relevant.csv"):
        relevant[row["question"]].append(row["passage"])
    questions = read("questions.csv")
    service = {question["question"]: question["domain"] for question in questions}
    paired = partners(questions)
    assert list(paired) == [question["question"] for question in questions]
    for question in questions:
        held = relevant[question["question"]]
        found = own(question, held, passages)
        assert found
        assert all(passages[name]["page"] == question["page"] for name in found)
        assert service[paired[question["question"]]] != question["domain"]


@pytest.mark.id("tst_fjz7jq")
def test_error_rates():
    """Counts misses among the replies labelled 1 and false alarms among those labelled 0"""
    labels = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0])
    verdicts = np.array([1, 1, 1, 0, 0, 0, 0, 0, 1])
    assert error_rates(labels, verdicts) == pytest.approx((0.25, 0.2))
    assert error_rates(labels, labels) == (0.0, 0.0)
    assert error_rates(labels, 1 - labels) == (1.0, 1.0)
