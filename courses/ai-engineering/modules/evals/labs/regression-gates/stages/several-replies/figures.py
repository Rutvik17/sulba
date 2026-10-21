import csv
import math
import re
from collections import defaultdict

import numpy as np

TEMPERATURE = 1.0
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


def figures():
    scores, pages = releases()
    current = np.hstack([scores["current"], scores["rerun"]])
    out = {
        "temperature": f"{TEMPERATURE:.1f}",
        "samples": str(SAMPLES),
        "questions": str(len(pages)),
        "pages": str(len(set(pages))),
    }
    within = current.var(axis=1, ddof=1).mean()
    for k in (1, 2, 5, 10):
        groups = [current[:, start : start + k] for start in range(0, 10, k)]
        means = [group.mean(axis=1) for group in groups]
        error = math.sqrt(np.mean([clustered(m, pages) ** 2 for m in means]))
        spread = np.mean([m.var(ddof=1) for m in means])
        if k < 10:
            out[f"subsets_{k}"] = str(len(groups))
        out[f"error_{k}"] = f"{error:.4f}"
        out[f"share_{k}"] = f"{within / k / spread:.0%}"
    errors = [float(out[f"error_{k}"]) for k in (1, 2, 5, 10)]
    assert errors == sorted(errors, reverse=True)
    out["releases"] = str(len(scores))
    return out
