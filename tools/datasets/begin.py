# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Builds the file of labelled replies that Evals checks a grader against, from BEGIN: replies
models wrote in conversations about a text, each labelled by people by whether everything it
says can be put down to the text.

BEGIN's Wizard of Wikipedia and CMU-DoG parts, from Google's repository at revision 6e65f0d,
hold the replies of four models, each with the text it was given, and the label three
annotators' majority gave it: `Fully attributable`, `Not fully attributable`, or `Generic`, for a
reply too vague to check, which is left out. `begin.csv` holds the rest of each part's
development set and 1,000 of each part's test set, drawn at random (NumPy's default_rng, seed 0)
and kept in the dataset's order, each with its part, its set, the model that wrote it in lower
case, its label, the text as its `context` and itself as its `reply`.

    uv run tools/datasets/begin.py <folder to write in>
"""

import csv
import hashlib
import io
import sys
import urllib.request
from pathlib import Path

import numpy as np

REVISION = "6e65f0d5a1ed1b9574643a7640ff1678d4e979b5"
# Each part's folder, and each of its files by set, with its sha256.
PARTS = {
    "wow": {
        "dev": (
            "begin_dev_wow.tsv",
            "2ebfc95a1ff267e12dcce3250da4d158e1811c62e9e1a0d56f110efc9ace0178",
        ),
        "test": (
            "begin_test_wow.tsv",
            "d5c106a42042c3abd481563f1157e07c95c107dbcdf67f23564d874e8a4d6e7e",
        ),
    },
    "cmu-dog": {
        "dev": (
            "begin_dev_cmu.tsv",
            "9482294df23cf08a976773ca73203b84f7178534ecab1a206eaade365e97071c",
        ),
        "test": (
            "begin_test_cmu.tsv",
            "34aa4a138554d924318112a5b34d628a6382ace84d1b27acbc84a0275479b7af",
        ),
    },
}
DRAWN = 1000
LEFT_OUT = "Generic"


def fetched(part: str, name: str, sha256: str) -> list[dict[str, str]]:
    """The rows of one of the dataset's files, checked against its sha256."""
    url = f"https://raw.githubusercontent.com/google/BEGIN-dataset/{REVISION}/{part}/{name}"
    with urllib.request.urlopen(url) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise SystemExit(f"{name} has changed.")
    text = io.StringIO(data.decode("utf-8"), newline="")
    return list(csv.DictReader(text, delimiter="\t", quoting=csv.QUOTE_NONE))


def build(out: Path) -> None:
    rng = np.random.default_rng(0)
    rows: list[list[object]] = []
    for part, files in PARTS.items():
        for set_, (name, sha256) in files.items():
            found = [row for row in fetched(part, name, sha256) if row["begin_label"] != LEFT_OUT]
            if set_ == "test":
                kept = sorted(rng.choice(len(found), DRAWN, replace=False).tolist())
                found = [found[i] for i in kept]
            for row in found:
                rows.append(
                    [
                        f"b{len(rows) + 1}",
                        part,
                        set_,
                        row["model_name"].lower(),
                        row["begin_label"],
                        row["knowledge"],
                        row["response"],
                    ]
                )
    with open(out / "begin.csv", "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["item", "part", "set", "model", "label", "context", "reply"])
        writer.writerows(rows)


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    folder.mkdir(parents=True, exist_ok=True)
    build(folder)
