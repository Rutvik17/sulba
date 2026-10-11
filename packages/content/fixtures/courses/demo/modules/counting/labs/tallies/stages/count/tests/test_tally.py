import csv

import pytest
from tally import count


def votes():
    with open("data/votes.csv", encoding="utf-8") as file:
        return [row["choice"] for row in csv.DictReader(file)]


@pytest.mark.id("tst_demo01")
def test_yes():
    """Two votes for yes"""
    assert count(votes(), "yes") == 2


@pytest.mark.id("tst_demo02")
def test_none():
    """No votes for maybe"""
    assert count(votes(), "maybe") == 0
