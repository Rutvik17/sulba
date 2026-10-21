import csv
import math
from collections import defaultdict
from statistics import NormalDist

import numpy as np

SHOWN = 5
CONFIDENCE = 0.95
SERVICES = ["dmv", "ssa", "studentaid", "va"]


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def kappa(labels, verdicts):
    observed = np.mean(labels == verdicts)
    chance = labels.mean() * verdicts.mean() + (1 - labels.mean()) * (
        1 - verdicts.mean()
    )
    return (observed - chance) / (1 - chance)


def risk(row):
    return float(row["yes"]) / (float(row["yes"]) + float(row["no"]))


def line(flags, pages):
    sums = defaultdict(float)
    for page, error in zip(pages, flags - flags.mean(), strict=True):
        sums[page] += error
    groups = len(sums)
    spread = math.sqrt(groups / (groups - 1) * sum(total**2 for total in sums.values()))
    reach = NormalDist().inv_cdf((1 + CONFIDENCE) / 2) * spread / len(flags)
    return flags.mean(), reach, len(flags)


def figures():
    begin = read("begin.csv")
    begin_risks = {row["item"]: risk(row) for row in read("begin-grades.csv")}
    rows = [row for row in begin if row["set"] == "dev"]
    labels = np.array([row["label"] != "Fully attributable" for row in rows], dtype=int)
    scores = np.array([begin_risks[row["item"]] for row in rows])
    best, chosen = -np.inf, 0.0
    for threshold in np.unique(scores):
        found = kappa(labels, (scores >= threshold).astype(int))
        if found > best:
            best, chosen = found, threshold

    questions = {row["question"]: row for row in read("questions.csv")}
    risks = {row["question"]: risk(row) for row in read("grades.csv")}
    names = list(risks)
    flags = np.array([float(risks[name] >= chosen) for name in names])
    pages = [questions[name]["page"] for name in names]
    out = {
        "shown": str(SHOWN),
        "confidence": f"{CONFIDENCE:.0%}",
        "chosen": f"{chosen:.3f}",
    }
    groups = {"all": list(range(len(names)))} | {
        service: [
            i for i, name in enumerate(names) if questions[name]["domain"] == service
        ]
        for service in SERVICES
    }
    for group, members in groups.items():
        share, reach, n = line(flags[members], [pages[i] for i in members])
        out[f"{group}_flagged"] = f"{share:.3f}"
        out[f"{group}_margin"] = f"{reach:.3f}"
        out[f"{group}_replies"] = str(n)
    values = np.array([risks[name] for name in names])
    out["to_read"] = str(int(flags.sum()))
    out["lowest"] = f"{values.min():.3f}"
    out["median"] = f"{np.median(values):.3f}"

    human = {
        (row["question"], row["context"]): risk(row) for row in read("human-grades.csv")
    }
    own = np.array([human[name, "own"] for name in questions])
    out["own_flagged"] = f"{np.mean(own >= chosen):.3f}"
    out["own_median"] = f"{np.median(own):.3f}"
    assert flags.mean() > 0.5 and np.mean(own >= chosen) < flags.mean()
    assert np.median(own) < np.median(values)
    return out
