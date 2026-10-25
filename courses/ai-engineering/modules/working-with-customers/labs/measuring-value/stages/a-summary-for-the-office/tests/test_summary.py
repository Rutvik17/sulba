import csv

import pytest

from summary import summary


def read():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


@pytest.mark.id("tst_cgifui")
def test_the_office():
    """Gives the office's summary"""
    assert summary(read(), "agent").splitlines() == [
        "The desk does 57.7% of the office's 5,200 contacts a month, from 50.6% to 64.8%.",
        "Questions: 40.5% of 40 tasks, from 29.0% to 52.0%.",
        "Cases: 87.0% of 20 tasks, from 80.4% to 93.6%.",
        "Callbacks: 69.0% of 20 tasks, from 54.9% to 83.1%.",
        "New tickets: 80.0% of 20 tasks, from 67.6% to 92.4%.",
        "Vague requests: all 20 tasks done in every trial.",
        "It saves $9,891 a month net, from $8,015 to $11,767.",
        "The pilot pays for itself in 4.1 months, from 3.4 to 5.1.",
    ]


@pytest.mark.id("tst_pbz59q")
def test_the_offices_order():
    """Gives the kinds in the order of the contacts, and leaves out a kind with none"""
    volumes = {"vague": 200, "case": 900, "question": 3_000, "callback": 0, "new": 400}
    lines = summary(read(), "agent", volumes=volumes).splitlines()
    names = [line.split(":")[0] for line in lines[1:-2]]
    assert names == ["Vague requests", "Cases", "Questions", "New tickets"]
    assert "of the office's 4,500 contacts a month" in lines[0]
