# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Records NumPy's share of the poll's votes for one choice, which the share stage's test
compares with. Made up for these tests.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import csv
import json
import sys
from pathlib import Path

import numpy as np

folder, data = Path(sys.argv[1]), Path(sys.argv[2])
with open(data / "votes.csv", encoding="utf-8", newline="") as file:
    choices = [row["choice"] for row in csv.DictReader(file)]
poll = {"choices": choices, "choice": "yes"}
poll["share"] = float(np.mean(np.array(choices) == poll["choice"]))
recording = {"numpy": np.__version__, "polls": [poll]}
(folder / "shares.json").write_text(json.dumps(recording, indent=2) + "\n")
