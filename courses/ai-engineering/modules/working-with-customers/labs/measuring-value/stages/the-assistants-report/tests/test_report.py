import csv

import pytest

from report import report


def read():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def runs(kind, done, seconds=60.0):
    """Five trials of each task, done in the number of trials given for it."""
    return [
        {
            "variant": "agent",
            "task": f"{kind}{task}",
            "kind": kind,
            "outcome": "done" if trial < count else "error",
            "seconds": str(seconds),
        }
        for task, count in enumerate(done)
        for trial in range(5)
    ]


@pytest.mark.id("tst_qssbfh")
def test_the_office():
    """Reports a share, a net and months for the office, each within its interval"""
    result = report(read(), "agent")
    for estimate in (result.share, result.net):
        assert estimate.low <= estimate.value <= estimate.high
    assert 0 < result.share.value < 1
    assert result.net.value > 0
    assert 0 < result.months.value < 100


@pytest.mark.id("tst_q3njc1")
def test_every_contact_done():
    """Saves every minute when the desk does every contact, at no other cost"""
    result = report(
        runs("case", [5, 5, 5]),
        "agent",
        volumes={"case": 100},
        minutes={"case": 6},
        host=0,
        support=0,
        price=900,
    )
    assert result.share.value == 1.0
    assert result.net.value == pytest.approx(0.75 * 100 * 6)
    assert result.months.value == pytest.approx(2)


@pytest.mark.id("tst_cm78ai")
def test_nothing_done():
    """Never pays back when the desk does nothing"""
    result = report(runs("new", [0, 0, 0]), "agent", volumes={"new": 100}, support=0)
    assert result.share.value == 0.0
    assert result.net.value < 0
    assert result.months.value == float("inf")
