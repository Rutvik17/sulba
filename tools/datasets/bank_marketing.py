# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "scikit-learn==1.8.0"]
# ///
"""Builds the bank's call file from UCI's Bank Marketing: the calls of a Portuguese bank's
campaigns selling term deposits, from May 2008 to November 2010.

`calls.csv` holds one in eight of the calls in UCI's `bank-additional-full.csv`, chosen at random
(NumPy's default_rng, seed 0), in UCI's order, which is the order of their dates, with UCI's
values. Three changes, which the lab's credit lists: the values are separated by commas rather
than semicolons, without quotes; the outcome column `y` is named `subscribed`; and a `set`
column puts each call in the training (0), validation (1) or test (2) set: 60%, 20% and 20% of
the calls, at random, with the same share subscribing in each (scikit-learn's
train_test_split, seed 0).

    uv run tools/datasets/bank_marketing.py <path to write>
"""

import hashlib
import io
import sys
import urllib.request
import zipfile

import numpy as np
from sklearn.model_selection import train_test_split

SOURCE = "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"
# The zip as downloaded on 15 October 2026. A different file stops the build.
SHA256 = "e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4"
INNER, CALLS = "bank-additional.zip", "bank-additional/bank-additional-full.csv"
SHARE = 8


def main(out: str) -> None:
    archive = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(archive).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    inner = zipfile.ZipFile(io.BytesIO(zipfile.ZipFile(io.BytesIO(archive)).read(INNER)))
    header, *rows = inner.read(CALLS).decode("ascii").splitlines()
    # No field holds a comma, so splitting at the semicolons and dropping the quotes changes
    # no value.
    if any("," in line for line in [header, *rows]):
        raise SystemExit("A field holds a comma.")
    names = header.replace('"', "").split(";")
    if names[-1] != "y":
        raise SystemExit(f"The last column is {names[-1]}, not y.")
    rng = np.random.default_rng(0)
    chosen = np.sort(rng.choice(len(rows), len(rows) // SHARE, replace=False))
    calls = [rows[i].replace('"', "").split(";") for i in chosen]
    subscribed = np.array([call[-1] for call in calls])
    numbers = np.arange(len(calls))
    train, rest = train_test_split(numbers, test_size=0.4, stratify=subscribed, random_state=0)
    validation, test = train_test_split(
        rest, test_size=0.5, stratify=subscribed[rest], random_state=0
    )
    set_of = {int(c): s for s, part in enumerate([train, validation, test]) for c in part}
    lines = [",".join(["set", *names[:-1], "subscribed"])]
    for number, call in enumerate(calls):
        lines.append(",".join([str(set_of[number]), *call]))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
