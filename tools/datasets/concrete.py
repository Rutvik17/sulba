# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "scikit-learn==1.8.0"]
# ///
"""Builds the overfitting lab's data file from UCI's Concrete Compressive Strength.

UCI's rows are used as they are, with three changes, which the lab's credit lists: a header
names each column, a `mix` column numbers each mix of ingredients in the order it first appears,
and a `set` column puts each mix, with every test of it, in the training (0), validation (1) or
test (2) set: 60%, 20% and 20% of the mixes, at random (scikit-learn's train_test_split, seed 0).

    uv run tools/datasets/concrete.py <path to write>
"""

import hashlib
import sys
import urllib.request

import numpy as np
from sklearn.model_selection import train_test_split

SOURCE = "https://archive.ics.uci.edu/static/public/165/data.csv"
# The file as downloaded on 15 October 2026. A different file stops the build.
SHA256 = "8d4b15b6fc68cd932d745cbd663d5ceae66dd54422e99c1e4865f2936ab7e2af"

# UCI's columns, by what each measures: seven ingredients in kg per cubic metre of concrete, the
# age at the test in days, and the compressive strength in MPa.
NAMES = {
    "Cement": "cement",
    "Blast Furnace Slag": "slag",
    "Fly Ash": "ash",
    "Water": "water",
    "Superplasticizer": "superplasticizer",
    "Coarse Aggregate": "coarse",
    "Fine Aggregate": "fine",
    "Age": "age",
    "Concrete compressive strength": "strength",
}
# A mix is its seven ingredients; one mix is tested at several ages.
INGREDIENTS = 7


def main(out: str) -> None:
    text = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(text).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    header, *rows = [line.split(",") for line in text.decode("ascii").strip().splitlines()]
    names = [NAMES[name] for name in header]
    mixes: dict[tuple[float, ...], int] = {}
    mix = [mixes.setdefault(tuple(map(float, row[:INGREDIENTS])), len(mixes)) for row in rows]
    train, rest = train_test_split(np.arange(len(mixes)), test_size=0.4, random_state=0)
    validation, test = train_test_split(rest, test_size=0.5, random_state=0)
    set_of = {int(m): number for number, part in enumerate([train, validation, test]) for m in part}
    lines = [",".join(["set", "mix", names[-1], *names[:-1]])]
    for row, m in zip(rows, mix, strict=True):
        lines.append(",".join([str(set_of[m]), str(m), row[-1], *row[:-1]]))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
