import csv
from collections import Counter

import numpy as np
import pytest

from testset import split, unique

with open("data/questions.csv", encoding="utf-8", newline="") as file:
    QUESTIONS = list(csv.DictReader(file))


def asked(name, page, text):
    return {"question": name, "page": page, "domain": page.split("-")[0], "text": text}


SMALL = [
    asked("q1", "ssa-1", "How do I apply?"),
    asked("q2", "ssa-1", "When do benefits start?"),
    asked("q3", "ssa-2", "how do I APPLY"),
    asked("q4", "ssa-3", "Can I work and get benefits?"),
    asked("q5", "va-1", "What is a pension?"),
    asked("q6", "va-2", "Who can get a pension?"),
    asked("q7", "va-2", "How much is the pension?"),
    asked("q8", "va-3", "Where do I send the form?"),
    asked("q9", "dmv-1", "How do I renew my license?"),
    asked("q10", "dmv-2", "How much is a plate?"),
]


@pytest.mark.id("tst_mptj0o")
def test_same_words():
    """Keeps the first of the questions with the same words, whatever their case and marks"""
    kept = unique(SMALL)
    assert [question["question"] for question in kept] == [
        f"q{number}" for number in (1, 2, 4, 5, 6, 7, 8, 9, 10)
    ]
    assert unique(
        [asked("q1", "va-1", "Pension?"), asked("q2", "va-1", "pensions")]
    ) == [
        asked("q1", "va-1", "Pension?"),
        asked("q2", "va-1", "pensions"),
    ]


@pytest.mark.id("tst_66qfka")
def test_drawn_pages():
    """Draws each service's pages in the order the brief gives"""
    assert split(SMALL, 0.5, np.random.default_rng(0)) == (
        ["q4", "q6", "q7", "q10"],
        ["q1", "q2", "q5", "q8", "q9"],
    )
    assert split(SMALL, 0.5, np.random.default_rng(1)) == (
        ["q4", "q8", "q10"],
        ["q1", "q2", "q5", "q6", "q7", "q9"],
    )


@pytest.mark.id("tst_xke07e")
def test_no_page_on_both_sides():
    """Puts each unique question on one side, and no page on both"""
    development, test = split(QUESTIONS, 0.5, np.random.default_rng(0))
    kept = [question["question"] for question in unique(QUESTIONS)]
    assert sorted(development + test) == sorted(kept)
    assert development == [name for name in kept if name in set(development)]
    assert test == [name for name in kept if name in set(test)]
    page = {question["question"]: question["page"] for question in QUESTIONS}
    assert not {page[name] for name in development} & {page[name] for name in test}


@pytest.mark.id("tst_y7cmvc")
def test_each_service():
    """Gives the test set each service's share, and no page more than it needs"""
    for share in (0.3, 0.5):
        _, test = split(QUESTIONS, share, np.random.default_rng(5))
        kept = unique(QUESTIONS)
        services = Counter(question["domain"] for question in kept)
        sizes = Counter(question["page"] for question in kept)
        chosen = set(test)
        for service, count in services.items():
            theirs = [
                q for q in kept if q["domain"] == service and q["question"] in chosen
            ]
            largest = max(sizes[question["page"]] for question in theirs)
            assert share * count <= len(theirs) < share * count + largest


@pytest.mark.id("tst_4eujtq")
def test_shares_at_the_ends():
    """Puts nothing in the test set for a share of 0, and everything for a share of 1"""
    kept = [question["question"] for question in unique(SMALL)]
    assert split(SMALL, 0, np.random.default_rng(0)) == (kept, [])
    assert split(SMALL, 1, np.random.default_rng(0)) == ([], kept)
