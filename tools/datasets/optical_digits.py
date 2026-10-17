# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "scikit-learn==1.8.0"]
# ///
"""Builds the digits file from UCI's Optical Recognition of Handwritten Digits: digits written
on forms by 43 people, each scanned at 32x32 and shrunk to 8x8 by counting the dark pixels in
each 4x4 block, 0 to 16.

UCI's training file, from 30 of the writers, and its test file, from the other 13, are used as
they are, with two changes, which each lab's credit lists: the two files are joined under a
header that names each column, and a `set` column puts each digit in the training (0),
validation (1) or test (2) set. The test set is UCI's test file. The training file is split at
random within each digit into training (75%) and validation (25%), with scikit-learn's
train_test_split, seed 0, so the validation digits come from the same 30 writers.

    uv run tools/datasets/optical_digits.py <path to write>
"""

import hashlib
import io
import sys
import urllib.request
import zipfile

import numpy as np
from sklearn.model_selection import train_test_split

SOURCE = (
    "https://archive.ics.uci.edu/static/public/80/optical+recognition+of+handwritten+digits.zip"
)
# The zip as downloaded on 17 October 2026. A different file stops the build.
SHA256 = "0d7b054fea010270e9b3f06411c654c5e59547732ad626381980baffe0a23fb0"
PIXELS = 64


def rows(archive: zipfile.ZipFile, name: str) -> list[list[str]]:
    lines = archive.read(name).decode("ascii").splitlines()
    found = [line.split(",") for line in lines if line.strip()]
    if any(len(row) != PIXELS + 1 for row in found):
        raise SystemExit(f"{name} has a row without {PIXELS} pixels and a digit.")
    return found


def main(out: str) -> None:
    data = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(data).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    archive = zipfile.ZipFile(io.BytesIO(data))
    training, test = rows(archive, "optdigits.tra"), rows(archive, "optdigits.tes")
    digits = np.array([row[-1] for row in training])
    _, validation = train_test_split(
        np.arange(len(training)), test_size=0.25, stratify=digits, random_state=0
    )
    held = set(validation.tolist())
    lines = [",".join(["set", "digit", *(f"pixel{i}" for i in range(PIXELS))])]
    for number, row in enumerate(training):
        lines.append(",".join(["1" if number in held else "0", row[-1], *row[:-1]]))
    for row in test:
        lines.append(",".join(["2", row[-1], *row[:-1]]))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
