import csv
import math

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


@pytest.mark.id("tst_02105j")
def test_the_offices_mix():
    """Weights each kind by the office's contacts"""
    done = runs("case", [5, 5]) + runs("question", [0, 0])
    result = report(done, "agent", volumes={"case": 900, "question": 100})
    assert result.share.value == pytest.approx(0.9)


@pytest.mark.id("tst_hv3rd0")
def test_each_task_counted_once():
    """Takes each kind's error over its tasks"""
    result = report(
        runs("new", [5, 5, 0, 0]),
        "agent",
        volumes={"new": 100},
        minutes={"new": 10},
        agent=1.0,
    )
    error = 100 * 10 * (1 / 3) ** 0.5 / 2
    assert result.net.high - result.net.value == pytest.approx(
        1.959964 * error, rel=1e-6
    )


@pytest.mark.id("tst_uxlzp1")
def test_the_months_ends():
    """Takes the fewest months from the most saved"""
    result = report(read(), "agent")
    assert result.months.low <= result.months.value <= result.months.high
    assert result.months.low == pytest.approx(40_600 / result.net.high)


@pytest.mark.id("tst_smt4cw")
def test_the_support():
    """Takes the support out of the saving"""
    result = report(
        runs("callback", [5, 5, 0]),
        "agent",
        volumes={"callback": 600},
        minutes={"callback": 4},
        agent=1.0,
        host=3.6,
        support=500,
    )
    hours = 600 * 60.0 / 3600
    assert result.net.value == pytest.approx(600 * 4 * 2 / 3 - hours * 3.6 - 500)
    assert math.isfinite(result.months.value)
