import csv

import pytest
from report import leader


def votes():
    with open("data/votes.csv", encoding="utf-8") as file:
        return [row["choice"] for row in csv.DictReader(file)]


@pytest.mark.id("tst_demo08")
def test_the_poll():
    """The poll's leader"""
    assert leader(votes()) == "yes"


@pytest.mark.id("tst_demo10")
def test_one_vote():
    """A poll of one vote"""
    assert leader(["no"]) == "no"
