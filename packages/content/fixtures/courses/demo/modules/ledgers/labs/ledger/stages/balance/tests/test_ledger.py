import csv

import pytest
from ledger import balance


def amounts():
    with open("data/entries.csv", encoding="utf-8") as file:
        return [int(row["amount"]) for row in csv.DictReader(file)]


@pytest.mark.id("tst_demo20")
def test_balance():
    """Adds up the ledger"""
    assert balance(amounts()) == 37


@pytest.mark.id("tst_demo21")
def test_empty():
    """An empty ledger balances at 0"""
    assert balance([]) == 0
