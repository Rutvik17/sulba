import csv
import math
import random
import re
from statistics import NormalDist

import pytest

from kinds import by_kind
from mix import weighted
from summary import summary
from worth import monthly, payback, seconds


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


def numbers(line):
    """The numbers in a line, in order, a minus sign before a dollar sign kept."""
    found = re.findall(r"(-?)\$?(\d[\d,]*(?:\.\d+)?)", line)
    return [float(sign + digits.replace(",", "")) for sign, digits in found]


@pytest.mark.id("tst_bvq6yx")
def test_rounded_outward():
    """Rounds each interval's low end down and its high end up"""
    rng = random.Random(502)
    z = NormalDist().inv_cdf(0.975)
    for _ in range(40):
        done = runs("case", [rng.randint(0, 5) for _ in range(rng.randint(2, 9))])
        done += runs("new", [rng.randint(1, 4) for _ in range(rng.randint(2, 9))])
        volumes = {"case": rng.randint(1, 900), "new": rng.randint(1, 900)}
        lines = summary(
            done, "agent", volumes=volumes, host=0, support=0, price=50_000
        ).splitlines()
        shares = by_kind(done, "agent")
        share = weighted(shares, volumes)
        value, _, low, high = numbers(lines[0])
        assert low <= share.low * 100 < low + 0.1 or share.low == 0
        assert high - 0.1 < share.high * 100 <= high or share.high == 1
        each = shares["new"]
        _, _, low, high = numbers(lines[2])
        assert low <= max(each.value - z * each.error, 0) * 100 < low + 0.1
        net = monthly(shares, seconds(done, "agent"), volumes, host=0, support=0)
        value, low, high = numbers(lines[-2])
        assert low <= net.low < low + 1 and high - 1 < net.high <= high
        months = payback(50_000, net)
        if math.isfinite(months.high):
            value, low, high = numbers(lines[-1])
            assert low <= months.low < low + 0.1 and high - 0.1 < months.high <= high


@pytest.mark.id("tst_f08s7k")
def test_every_trial_or_none():
    """Says so of a kind done in every trial or none, rather than giving an interval"""
    done = (
        runs("case", [5, 5, 5]) + runs("new", [0, 0, 0, 0]) + runs("callback", [5, 4])
    )
    volumes = {"case": 100, "new": 100, "callback": 100}
    lines = summary(done, "agent", volumes=volumes, support=0).splitlines()
    assert lines[1] == "Cases: all 3 tasks done in every trial."
    assert lines[2] == "New tickets: none of 4 tasks done in any trial."
    assert lines[3].startswith("Callbacks: 90.0% of 2 tasks, from ")


@pytest.mark.id("tst_e9zoo0")
def test_a_pilot_that_may_not_pay():
    """Says when the pilot may not pay for itself, or doesn't"""
    office = read()
    lines = summary(office, "agent", support=13_000).splitlines()
    assert lines[-2] == "It saves $891 a month net, from -$985 to $2,767."
    assert lines[-1] == (
        "The pilot pays for itself in 45.6 months, from 14.6,"
        " or not at all at the saving's low end."
    )
    lines = summary(office, "agent", support=20_000).splitlines()
    assert lines[-2] == "It saves -$6,109 a month net, from -$7,985 to -$4,233."
    assert lines[-1] == "At these figures the pilot doesn't pay for itself."


@pytest.mark.id("tst_0mxsj6")
def test_its_own_figures():
    """Uses the figures it's given, not the office's"""
    done = runs("question", [5, 3, 1, 0]) + runs("vague", [5, 5])
    lines = summary(
        done,
        "agent",
        volumes={"question": 1_000, "vague": 1_000},
        minutes={"question": 10, "vague": 2},
        agent=1.0,
        host=36.0,
        support=100,
        price=12_000,
        confidence=0.9,
    ).splitlines()
    assert lines == [
        "The desk does 72.5% of the office's 2,000 contacts a month, from 54.2% to 90.8%.",
        "Questions: 45.0% of 4 tasks, from 8.5% to 81.5%.",
        "Vague requests: all 2 tasks done in every trial.",
        "It saves $5,200 a month net, from $1,552 to $8,848.",
        "The pilot pays for itself in 2.3 months, from 1.3 to 7.8.",
    ]
