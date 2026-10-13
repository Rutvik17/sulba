import csv
import time

import pytest
from report import leader

MANY = 60_000


def votes():
    with open("data/votes.csv", encoding="utf-8") as file:
        return [row["choice"] for row in csv.DictReader(file)]


@pytest.mark.id("tst_demo11")
def test_fast(record_property):
    """Fast on many votes"""
    many = ["yes", "no", "yes"] * (MANY // 3)
    start = time.perf_counter()
    leader(many)
    took = time.perf_counter() - start
    record_property("note", f"{took:.2f} s on {len(many):,} votes")
    assert took < 1


@pytest.mark.id("tst_demo12")
def test_leaves_the_votes():
    """Leaves the votes as they were"""
    given = votes()
    leader(given)
    assert given == votes()
