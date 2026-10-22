"""The shop's ledger, as the lab gives it: each entry's amount, from data/entries.csv."""

import csv


def amounts() -> list[int]:
    with open("data/entries.csv", encoding="utf-8") as file:
        return [int(row["amount"]) for row in csv.DictReader(file)]
