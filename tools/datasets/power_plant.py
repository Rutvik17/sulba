# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "openpyxl==3.1.5", "scikit-learn==1.8.0"]
# ///
"""Builds the linear-regression lab's data file from UCI's Combined Cycle Power Plant.

UCI's first sheet is used as it is, with two changes, which the lab's credit lists: a header
names each column, and a `test` column marks a random 20% test set (scikit-learn's
train_test_split, seed 0).

    uv run tools/datasets/power_plant.py <path to write>
"""

import hashlib
import io
import sys
import urllib.request
import zipfile

import numpy as np
import openpyxl
from sklearn.model_selection import train_test_split

SOURCE = "https://archive.ics.uci.edu/static/public/294/combined+cycle+power+plant.zip"
# The zip as downloaded on 15 October 2026. A different file stops the build.
SHA256 = "cc7b2a4977c0a44e8221c91d9a7e5746b3c68186cff7e5c61c70af6432b98c7a"

# UCI's columns AT, V, AP, RH and PE, by what each measures.
NAMES = {
    "AT": "temperature",
    "V": "vacuum",
    "AP": "pressure",
    "RH": "humidity",
    "PE": "output",
}
FEATURES = ["AT", "V", "AP", "RH"]


def main(out: str) -> None:
    archive = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(archive).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    sheet = zipfile.ZipFile(io.BytesIO(archive)).read("CCPP/Folds5x2_pp.xlsx")
    book = openpyxl.load_workbook(io.BytesIO(sheet), read_only=True)
    header, *rows = book["Sheet1"].iter_rows(values_only=True)
    at = {name: header.index(name) for name in NAMES}
    _, test = train_test_split(np.arange(len(rows)), test_size=0.2, random_state=0)
    in_test = set(test.tolist())
    lines = [",".join(["test", NAMES["PE"], *(NAMES[name] for name in FEATURES)])]
    for index, row in enumerate(rows):
        values = [row[at["PE"]], *(row[at[name]] for name in FEATURES)]
        flag = "1" if index in in_test else "0"
        lines.append(",".join([flag, *(f"{value:g}" for value in values)]))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
