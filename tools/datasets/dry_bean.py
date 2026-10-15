# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "scikit-learn==1.8.0"]
# ///
"""Builds the bean file from UCI's Dry Bean dataset: 16 measurements of each bean's shape, taken
from its photograph, and its variety.

`beans.csv` holds one in four of UCI's beans, chosen at random (NumPy's default_rng, seed 0), in
UCI's order, with UCI's values. Three changes, which the lab's credit lists: the values are
comma-separated under a header that names each measurement as UCI's variable table does (the
ARFF names two of them AspectRation and roundness), the class column is named variety, and a
`set` column puts each bean in the training (0), validation (1) or test (2) set: 60%, 20% and
20% of the beans, at random within each variety (scikit-learn's train_test_split, seed 0).

    uv run tools/datasets/dry_bean.py <path to write>
"""

import hashlib
import io
import sys
import urllib.request
import zipfile

import numpy as np
from sklearn.model_selection import train_test_split

SOURCE = "https://archive.ics.uci.edu/static/public/602/dry+bean+dataset.zip"
# The zip as downloaded on 15 October 2026. A different file stops the build.
SHA256 = "0a64eff5be87f48c3dbbfc0a12a56c5d5b5167ef8e61cd45d69b3e7c7130c06f"
ARFF = "DryBeanDataset/Dry_Bean_Dataset.arff"
# The measurements in the ARFF's order, as UCI's variable table names them. The variety follows.
MEASUREMENTS = [
    "Area",
    "Perimeter",
    "MajorAxisLength",
    "MinorAxisLength",
    "AspectRatio",
    "Eccentricity",
    "ConvexArea",
    "EquivDiameter",
    "Extent",
    "Solidity",
    "Roundness",
    "Compactness",
    "ShapeFactor1",
    "ShapeFactor2",
    "ShapeFactor3",
    "ShapeFactor4",
]
SHARE = 4


def main(out: str) -> None:
    archive = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(archive).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    lines = zipfile.ZipFile(io.BytesIO(archive)).read(ARFF).decode("ascii").splitlines()
    start = next(i for i, line in enumerate(lines) if line.upper().startswith("@DATA")) + 1
    rows = [line.split(",") for line in lines[start:] if line.strip()]
    rng = np.random.default_rng(0)
    beans = [rows[i] for i in np.sort(rng.choice(len(rows), len(rows) // SHARE, replace=False))]
    varieties = np.array([bean[-1] for bean in beans])
    numbers = np.arange(len(beans))
    train, rest = train_test_split(numbers, test_size=0.4, stratify=varieties, random_state=0)
    validation, test = train_test_split(
        rest, test_size=0.5, stratify=varieties[rest], random_state=0
    )
    set_of = {int(b): s for s, part in enumerate([train, validation, test]) for b in part}
    out_lines = [",".join(["set", "variety", *MEASUREMENTS])]
    for number, bean in enumerate(beans):
        out_lines.append(",".join([str(set_of[number]), bean[-1], *bean[:-1]]))
    with open(out, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(out_lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
