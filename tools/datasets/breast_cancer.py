# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "scikit-learn==1.8.0"]
# ///
"""Builds the breast cancer data file from UCI's Breast Cancer Wisconsin (Diagnostic). Four
labs hold a copy: logistic regression, arrays and broadcasting, vectors and matrices, and
derivatives and gradients.

UCI's file is used as it is, with three changes, which each lab's credit lists: a header names
each column, malignant is coded as 1 and benign as 0, and a `test` column marks a stratified 20%
test set (scikit-learn's train_test_split, seed 0).

    uv run tools/datasets/breast_cancer.py <path to write>
"""

import hashlib
import io
import sys
import urllib.request
import zipfile

import numpy as np
from sklearn.model_selection import train_test_split

SOURCE = "https://archive.ics.uci.edu/static/public/17/breast+cancer+wisconsin+diagnostic.zip"
# The zip as downloaded on 11 October 2026. A different file stops the build.
SHA256 = "bc154869ef13f753f9e2b5a17e248cfe1ba4b6721db7c4da9f4880e40b05d3af"

MEASURES = [
    "radius",
    "texture",
    "perimeter",
    "area",
    "smoothness",
    "compactness",
    "concavity",
    "concave_points",
    "symmetry",
    "fractal_dimension",
]
# UCI's order: the mean of each measure, then its standard error, then its worst value.
COLUMNS = [
    *(f"mean_{measure}" for measure in MEASURES),
    *(f"{measure}_error" for measure in MEASURES),
    *(f"worst_{measure}" for measure in MEASURES),
]


def main(out: str) -> None:
    archive = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(archive).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    text = zipfile.ZipFile(io.BytesIO(archive)).read("wdbc.data").decode("ascii")
    rows = [line.split(",") for line in text.strip().splitlines()]
    labels = np.array([1 if row[1] == "M" else 0 for row in rows])
    _, test = train_test_split(np.arange(len(rows)), test_size=0.2, stratify=labels, random_state=0)
    in_test = set(test.tolist())
    lines = [",".join(["test", "malignant", *COLUMNS])]
    for index, row in enumerate(rows):
        flag = "1" if index in in_test else "0"
        lines.append(",".join([flag, str(labels[index]), *row[2:]]))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
