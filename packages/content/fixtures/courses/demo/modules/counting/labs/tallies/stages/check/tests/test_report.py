import csv

import pytest
from report import report


def votes():
    with open("data/votes.csv", encoding="utf-8") as file:
        return [row["choice"] for row in csv.DictReader(file)]


@pytest.mark.id("tst_demo04")
def test_one_line_per_choice():
    """One line per choice"""
    assert len(report(votes())) == 2


@pytest.mark.id("tst_demo05")
def test_shares_add_up():
    """The shares add up to 1"""
    assert sum(fraction for _, fraction in report(votes())) == pytest.approx(1)
