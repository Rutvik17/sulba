import csv
import math
import statistics

import pytest

from kinds import Share, by_kind
from mix import OFFICE, Estimate
from worth import MINUTES, PRICE, monthly, payback, seconds


def read():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


@pytest.mark.id("tst_nhct22")
def test_seconds():
    """Gives each kind's mean seconds a trial"""
    runs = read()
    taken = seconds(runs, "agent")
    questions = [
        float(run["seconds"])
        for run in runs
        if run["variant"] == "agent" and run["kind"] == "question"
    ]
    assert taken["question"] == pytest.approx(statistics.fmean(questions))
    assert set(taken) == set(OFFICE)


@pytest.mark.id("tst_iuvtol")
def test_the_office():
    """Gives the office's net a month, with its interval"""
    runs = read()
    shares, taken = by_kind(runs, "agent"), seconds(runs, "agent")
    net = monthly(shares, taken)
    saved = 0.75 * sum(OFFICE[k] * MINUTES[k] * shares[k].value for k in OFFICE)
    hours = sum(OFFICE[k] * taken[k] for k in OFFICE) / 3600
    assert net.value == pytest.approx(saved - 0.5 * hours - 4_000)
    error = 0.75 * math.sqrt(
        sum((OFFICE[k] * MINUTES[k] * shares[k].error) ** 2 for k in OFFICE)
    )
    assert net.high - net.value == pytest.approx(1.959964 * error, rel=1e-6)
    months = payback(PRICE, net)
    assert months.low < months.value < months.high
    assert months.value == pytest.approx(PRICE / net.value)


@pytest.mark.id("tst_ch80d0")
def test_one_kind():
    """Saves an agent's minutes on the contacts done, less the machine and support"""
    shares = {"new": Share(0.5, 0.1, 20)}
    net = monthly(
        shares,
        {"new": 360.0},
        volumes={"new": 100},
        minutes={"new": 10},
        agent=1.0,
        host=2.0,
        support=50.0,
        confidence=0.9,
    )
    assert net.value == pytest.approx(100 * 10 * 0.5 - 100 * 0.1 * 2 - 50)
    assert net.low == pytest.approx(net.value - 1.644854 * 100 * 10 * 0.1, rel=1e-6)


@pytest.mark.id("tst_gh8fg2")
def test_a_pilot_that_doesnt_pay():
    """Takes the payback's ends from the net's, and infinity where the net doesn't pay"""
    assert payback(1200, Estimate(100, 50, 200)) == Estimate(12, 6, 24)
    assert payback(1200, Estimate(100, -20, 200)) == Estimate(12, 6, math.inf)
    assert payback(1200, Estimate(-10, -60, 0)) == Estimate(
        math.inf, math.inf, math.inf
    )
