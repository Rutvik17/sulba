# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "scikit-learn==1.8.0"]
# ///
"""Builds the classifier-measuring lab's data file from UCI's HTRU2, the pulsar candidates of
the High Time Resolution Universe survey.

UCI's rows are used as they are, with three changes, which the lab's credit lists: a header
names each column, lines end in LF rather than CR, and a `set` column puts each candidate in
the training (0), validation (1) or test (2) set: 60%, 20% and 20% of the candidates, at random
within each class (scikit-learn's train_test_split, seed 0).

The header follows UCI's variable table, which puts each curve's skewness before its excess
kurtosis. The Readme in UCI's archive lists them the other way round. Every row meets Pearson's
inequality, excess kurtosis >= skewness ** 2 - 2, only in the table's order, which the build
checks.

    uv run tools/datasets/pulsars.py <path to write>
"""

import hashlib
import io
import sys
import urllib.request
import zipfile

import numpy as np
from sklearn.model_selection import train_test_split

SOURCE = "https://archive.ics.uci.edu/static/public/372/htru2.zip"
# The zip as downloaded on 15 October 2026. A different file stops the build.
SHA256 = "ba442c076dd22a8952700f26e38499fc1806037dcf7bea0e125e6bfba393f379"

# Four statistics of each candidate's integrated pulse profile, then the same four of its DM-SNR
# curve, as UCI's variable table names them; the last column is the class, 1 for a pulsar.
FEATURES = [
    "profile_mean",
    "profile_stdev",
    "profile_skewness",
    "profile_kurtosis",
    "dm_mean",
    "dm_stdev",
    "dm_skewness",
    "dm_kurtosis",
]


def main(out: str) -> None:
    archive = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(archive).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    text = zipfile.ZipFile(io.BytesIO(archive)).read("HTRU_2.csv").decode("ascii")
    rows = [line.split(",") for line in text.replace("\r", "\n").split("\n") if line]
    values = np.array([row[:-1] for row in rows], dtype=float)
    for skewness, kurtosis in [(2, 3), (6, 7)]:
        if not np.all(values[:, kurtosis] >= values[:, skewness] ** 2 - 2):
            raise SystemExit("The columns aren't in the order UCI's variable table gives.")
    labels = np.array([int(row[-1]) for row in rows])
    candidates = np.arange(len(rows))
    train, rest = train_test_split(candidates, test_size=0.4, stratify=labels, random_state=0)
    validation, test = train_test_split(rest, test_size=0.5, stratify=labels[rest], random_state=0)
    set_of = {int(c): number for number, part in enumerate([train, validation, test]) for c in part}
    lines = [",".join(["set", "pulsar", *FEATURES])]
    for index, row in enumerate(rows):
        lines.append(",".join([str(set_of[index]), row[-1], *row[:-1]]))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
