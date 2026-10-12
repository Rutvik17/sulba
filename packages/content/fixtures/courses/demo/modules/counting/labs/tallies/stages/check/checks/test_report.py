import csv

import pytest
from report import report


def votes():
    with open("data/votes.csv", encoding="utf-8") as file:
        return [row["choice"] for row in csv.DictReader(file)]


@pytest.mark.id("tst_demo06")
def test_most_votes_first():
    """Most votes first"""
    assert [choice for choice, _ in report(votes())] == ["yes", "no"]


@pytest.mark.id("tst_demo07")
def test_leaves_the_votes():
    """Leaves the list of votes as it was"""
    given = votes()
    report(given)
    assert given == votes()
