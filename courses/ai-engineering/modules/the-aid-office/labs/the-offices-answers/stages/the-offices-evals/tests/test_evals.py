import csv
import math

import pytest
from evals import RELEASES, Change, change, outcome, outcomes, shares

CONFIDENCE = 0.95
# Each release's outcomes on the recorded replies, by the office's rule.
EXPECTED = {
    "five": {"right": 67, "wrong": 26, "staff": 131},
    "three": {"right": 64, "wrong": 46, "staff": 114},
}


def rows(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


@pytest.fixture(scope="module")
def recorded():
    return rows("data/replies.csv"), rows("data/shown.csv"), rows("data/questions.csv")


@pytest.mark.id("tst_zrobp3")
def test_outcome():
    """Tells a reply that cites the question's page from one that cites others or none"""
    shown = ["a", "b", "c"]
    assert outcome("It's on the form [2].", shown, "b") == "right"
    assert outcome("See [1], then [2].", shown, "b") == "right"
    assert outcome("See [1] and [3].", shown, "b") == "wrong"
    assert outcome("See [4].", shown, "b") == "staff"
    assert outcome("It's on the form.", shown, "b") == "staff"
    assert outcome("I don't know.", shown, "b") == "staff"
    assert outcome("It's on the form [2]. I don't know when.", shown, "b") == "staff"


@pytest.mark.id("tst_xdy0dc")
def test_outcomes():
    """Gives each question's outcome in its order, from the passages its release was given"""
    questions = [{"question": "q2", "page": "c"}, {"question": "q1", "page": "a"}]
    shown = [
        {"question": question, "number": str(number), "page": page}
        for question, pages in (("q1", "abcde"), ("q2", "edcba"))
        for number, page in sorted(enumerate(pages, start=1), reverse=True)
    ]
    replies = [
        {"question": "q1", "release": "five", "reply": "See [1]."},
        {"question": "q1", "release": "three", "reply": "See [4]."},
        {"question": "q2", "release": "five", "reply": "See [3]."},
        {"question": "q2", "release": "three", "reply": "See [1]."},
    ]
    assert outcomes(replies, shown, questions, "five") == ["right", "right"]
    assert outcomes(replies, shown, questions, "three") == ["wrong", "staff"]


@pytest.mark.id("tst_s4lko6")
def test_shares():
    """Gives the share of each outcome"""
    found = ["right", "staff", "right", "wrong"]
    assert shares(found) == {"right": 0.5, "wrong": 0.25, "staff": 0.25}


@pytest.mark.id("tst_wf9yrr")
def test_change():
    """Takes each question's difference, each page's questions together"""
    baseline = ["right", "right", "staff", "wrong", "right", "staff"]
    candidate = ["right", "staff", "right", "wrong", "staff", "staff"]
    pages = ["a", "a", "b", "b", "c", "c"]
    found = change(baseline, candidate, pages, "right", CONFIDENCE)
    # The differences are 0, -1, 1, 0, -1 and 0, with a mean of -1/6. The residuals' sums by
    # page are -2/3, 4/3 and -2/3, so the standard error is sqrt(3/2 * 8/3) / 6, and z is
    # 1.959964 for 95%.
    assert found.change == pytest.approx(-1 / 6)
    assert found.margin == pytest.approx(
        1.959964 * math.sqrt(3 / 2 * 8 / 3) / 6, rel=1e-6
    )
    assert change(
        baseline, candidate, pages, "staff", CONFIDENCE
    ).change == pytest.approx(1 / 6)
    assert isinstance(found, Change)


@pytest.mark.id("tst_34i72z")
def test_recorded(recorded):
    """Gives the recorded replies' outcomes in each release"""
    replies, shown, questions = recorded
    assert set(RELEASES) == {row["release"] for row in replies}
    counts = {}
    for release in RELEASES:
        found = outcomes(replies, shown, questions, release)
        assert len(found) == len(questions)
        counts[release] = {
            name: found.count(name) for name in ("right", "wrong", "staff")
        }
    assert counts == EXPECTED
