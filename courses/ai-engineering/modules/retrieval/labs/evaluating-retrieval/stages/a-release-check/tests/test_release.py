import numpy as np
import pytest

from release import check

FIRST = {f"p{number}": f"p{number}" for number in range(1, 7)}


def desk(count):
    """count questions in two services, each answered by p1, the current search showing p2
    first and the candidate p1."""
    questions = [f"q{number}" for number in range(count)]
    judgments = {question: {"p1"} for question in questions}
    services = {
        question: "ssa" if at % 2 else "va" for at, question in enumerate(questions)
    }
    current = {question: ["p2", "p3", "p4", "p5", "p6", "p1"] for question in questions}
    candidate = {question: ["p1", "p2"] for question in questions}
    return current, candidate, judgments, services


@pytest.mark.id("tst_7e6bqp")
def test_gain():
    """A gain on 40 questions ships, and the same gain on 4 doesn't"""
    current, candidate, judgments, services = desk(40)
    found = check(
        current, candidate, judgments, FIRST, services, np.random.default_rng(0)
    )
    assert found.hit_rate == (0, 1)
    assert found.ship
    current, candidate, judgments, services = desk(4)
    found = check(
        current, candidate, judgments, FIRST, services, np.random.default_rng(0)
    )
    assert found.p > 0.05
    assert not found.ship


@pytest.mark.id("tst_qrlw6o")
def test_same_search():
    """A search against itself doesn't ship"""
    current, _, judgments, services = desk(40)
    found = check(
        current, current, judgments, FIRST, services, np.random.default_rng(0)
    )
    assert found.p == 1
    assert found.services == {"ssa": (0, 0), "va": (0, 0)}
    assert not found.ship
