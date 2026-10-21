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


ALPHA = 0.05
POWER = 0.8


def detectable(error):
    normal = NormalDist()
    return (normal.inv_cdf(1 - ALPHA) + normal.inv_cdf(POWER)) * error


def figures():
    scores, pages = releases()
    n = len(pages)
    out = {"alpha": f"{ALPHA:.2f}", "power": f"{POWER:.0%}", "questions": str(n)}
    for k in (1, SAMPLES):
        rerun = scores["rerun"][:, :k].mean(axis=1) - scores["current"][:, :k].mean(
            axis=1
        )
        out[f"rerun_error_{k}"] = f"{clustered(rerun, pages):.4f}"
        out[f"detectable_{k}"] = f"{detectable(clustered(rerun, pages)):.3f}"
    unranked = scores["unranked"].mean(axis=1) - scores["current"].mean(axis=1)
    error = clustered(unranked, pages)
    reach = detectable(error)
    drop = -unranked.mean()
    out["unranked_drop"] = f"{drop:.3f}"
    out["unranked_error"] = f"{error:.4f}"
    out["unranked_detectable"] = f"{reach:.3f}"
    out["unranked_needed"] = f"{math.ceil(n * (reach / drop) ** 2)}"
    assert error > clustered(
        scores["rerun"].mean(axis=1) - scores["current"].mean(axis=1), pages
    )
    assert drop < reach
    half = NormalDist().cdf(drop / error - NormalDist().inv_cdf(1 - ALPHA))
    out["unranked_power"] = f"{half:.0%}"
    return out
