import csv
import math
import re
from collections import defaultdict
from statistics import NormalDist

import numpy as np

SAMPLES = 5
CITED = re.compile(r"\[(p\d+)\]")


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def releases():
    """Each release's scores on cites_answer, a row for each question and a column for
    each sample, with the questions' pages."""
    questions = read("questions.csv")
    relevant = defaultdict(set)
    for row in read("relevant.csv"):
        relevant[row["question"]].add(row["passage"])
    found = defaultdict(dict)
    for row in read("replies.csv"):
        cited = CITED.findall(row["reply"])
        score = float(any(name in relevant[row["question"]] for name in cited))
        found[row["release"]][row["question"], int(row["sample"])] = score
    out = {
        name: np.array(
            [
                [theirs[q["question"], k] for k in range(1, SAMPLES + 1)]
                for q in questions
            ]
        )
        for name, theirs in found.items()
    }
    return out, [q["page"] for q in questions]


def clustered(values, pages):
    sums = defaultdict(float)
    for page, residual in zip(pages, values - values.mean(), strict=True):
        sums[page] += residual
    groups = len(sums)
    return math.sqrt(groups / (groups - 1) * sum(v**2 for v in sums.values())) / len(
        values
    )


CONFIDENCE = 0.95
CANDIDATES = ["rerun", "three-passages", "unranked", "warmer"]


def figures():
    scores, pages = releases()
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    base = scores["current"].mean(axis=1)
    out = {"confidence": f"{CONFIDENCE:.0%}", "base": f"{base.mean():.3f}"}
    for name in CANDIDATES:
        key = name.replace("-", "_")
        theirs = scores[name].mean(axis=1)
        differences = theirs - base
        paired = clustered(differences, pages)
        unpaired = math.hypot(clustered(base, pages), clustered(theirs, pages))
        out[f"{key}_score"] = f"{theirs.mean():.3f}"
        out[f"{key}_change"] = f"{differences.mean():+.3f}"
        out[f"{key}_paired"] = f"{z * paired:.3f}"
        out[f"{key}_unpaired"] = f"{z * unpaired:.3f}"
        if name in ("rerun", "unranked"):
            out[f"{key}_ratio"] = f"{(unpaired / paired) ** 2:.1f}"
        out[f"{key}_correlation"] = f"{np.corrcoef(base, theirs)[0, 1]:.2f}"
    margins = {
        name: float(out[f"{name.replace('-', '_')}_paired"]) for name in CANDIDATES
    }
    correlations = {
        name: float(out[f"{name.replace('-', '_')}_correlation"]) for name in CANDIDATES
    }
    assert max(margins, key=margins.get) == "unranked"
    assert min(correlations, key=correlations.get) == "unranked"
    return out
