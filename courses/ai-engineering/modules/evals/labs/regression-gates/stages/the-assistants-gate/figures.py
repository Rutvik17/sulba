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


def plain(values):
    return float(values.std(ddof=1) / math.sqrt(len(values)))


def figures():
    scores, pages = releases()
    z = NormalDist().inv_cdf(1 - ALPHA)
    current, unranked = scores["current"], scores["unranked"]
    out = {}
    first = unranked[:, 0] - current[:, 0]
    every = unranked.mean(axis=1) - current.mean(axis=1)
    out["first_change"] = f"{first.mean():+.3f}"
    out["first_margin"] = f"{z * clustered(first, pages):.3f}"
    out["every_change"] = f"{every.mean():+.3f}"
    out["every_margin"] = f"{z * clustered(every, pages):.3f}"
    alone = math.hypot(
        clustered(current.mean(axis=1), pages), clustered(unranked.mean(axis=1), pages)
    )
    out["unpaired_margin"] = f"{z * alone:.3f}"
    rerun = scores["rerun"].mean(axis=1) - current.mean(axis=1)
    drop = -rerun.mean()
    assert drop < 0 < z * clustered(rerun, pages) + drop
    assert z * plain(every) < z * clustered(every, pages) < z * alone
    assert clustered(first, pages) > clustered(every, pages)
    out["rerun_drop"] = f"{drop:+.3f}"
    out["rerun_margin"] = f"{z * clustered(rerun, pages):.3f}"
    out["unranked_plain"] = f"{z * plain(every):.3f}"
    return out
