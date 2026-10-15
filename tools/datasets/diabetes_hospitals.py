# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Builds the hospital encounter files from UCI's Diabetes 130-US Hospitals for Years
1999-2008. Four labs hold a copy: cleaning data, joins and group-by, querying with SQL,
and checking data.

`encounters.csv` is UCI's `diabetic_data.csv` for one in ten of its patients, chosen at random
(NumPy's default_rng, seed 0), with every encounter of each, in UCI's order. `ids-mapping.csv`
is UCI's `IDS_mapping.csv`. Both keep UCI's text, with lines ending in LF rather than CRLF,
which each lab's credit lists.

    uv run tools/datasets/diabetes_hospitals.py <folder to write in>
"""

import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

SOURCE = (
    "https://archive.ics.uci.edu/static/public/296/"
    "diabetes+130-us+hospitals+for+years+1999-2008.zip"
)
# The zip as downloaded on 15 October 2026. A different file stops the build.
SHA256 = "f82ac129da2ddd2299391ff6fbae3a6a58b3edcf59ac9d7bd480c00fe453112a"


def write(path: Path, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")


def main(folder: str) -> None:
    archive = urllib.request.urlopen(SOURCE).read()
    found = hashlib.sha256(archive).hexdigest()
    if found != SHA256:
        raise SystemExit(f"UCI's file has changed: sha256 {found}, expected {SHA256}.")
    files = zipfile.ZipFile(io.BytesIO(archive))
    header, *rows = files.read("diabetic_data.csv").decode("ascii").splitlines()
    # No field is quoted, so a comma always ends a field. The second field is the patient.
    patients = np.unique([int(row.split(",")[1]) for row in rows])
    rng = np.random.default_rng(0)
    chosen = set(rng.choice(patients, len(patients) // 10, replace=False).tolist())
    write(
        Path(folder) / "encounters.csv",
        [header, *(row for row in rows if int(row.split(",")[1]) in chosen)],
    )
    write(
        Path(folder) / "ids-mapping.csv",
        files.read("IDS_mapping.csv").decode("ascii").splitlines(),
    )


if __name__ == "__main__":
    main(sys.argv[1])
