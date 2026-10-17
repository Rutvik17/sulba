# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Records NumPy's share of a poll's votes for one choice, which the share stage's test
compares with. Made up for these tests.

    uv run make.py [folder to write in]
"""

import json
import sys
from pathlib import Path

import numpy as np

POLLS = [(["yes", "no", "yes"], "yes")]

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
polls = [
    {"choices": choices, "choice": choice, "share": float(np.mean(np.array(choices) == choice))}
    for choices, choice in POLLS
]
recording = {"numpy": np.__version__, "polls": polls}
(folder / "shares.json").write_text(json.dumps(recording, indent=2) + "\n")
