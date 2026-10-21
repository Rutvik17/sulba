import csv

import numpy as np

DEFAULT = 0.5


def kappa(labels, verdicts):
    observed = np.mean(labels == verdicts)
    chance = labels.mean() * verdicts.mean() + (1 - labels.mean()) * (
        1 - verdicts.mean()
    )
    return (observed - chance) / (1 - chance)


def auc(labels, scores):
    ones, zeros = scores[labels == 1], scores[labels == 0]
    above = (ones[:, None] > zeros[None, :]).sum()
    tied = (ones[:, None] == zeros[None, :]).sum()
    return (above + tied / 2) / (len(ones) * len(zeros))


def figures():
    with open("data/begin.csv", encoding="utf-8", newline="") as file:
        items = list(csv.DictReader(file))
    with open("data/begin-grades.csv", encoding="utf-8", newline="") as file:
        grades = {row["item"]: row for row in csv.DictReader(file)}

    def sets(name):
        rows = [i for i in items if i["set"] == name]
        labels = np.array([i["label"] != "Fully attributable" for i in rows], dtype=int)
        yes = np.array([float(grades[i["item"]]["yes"]) for i in rows])
        no = np.array([float(grades[i["item"]]["no"]) for i in rows])
        return labels, yes / (yes + no)

    dev_labels, dev_scores = sets("dev")
    test_labels, test_scores = sets("test")
    best, chosen = -np.inf, 0.0
    for threshold in np.unique(dev_scores):
        found = kappa(dev_labels, (dev_scores >= threshold).astype(int))
        if found > best:
            best, chosen = found, threshold
    out = {
        "dev": str(len(dev_labels)),
        "test": str(len(test_labels)),
        "dev_risky": f"{dev_labels.mean():.3f}",
        "test_risky": f"{test_labels.mean():.3f}",
        "default": str(DEFAULT),
        "chosen": f"{chosen:.3f}",
    }
    for name, labels, scores in (
        ("dev", dev_labels, dev_scores),
        ("test", test_labels, test_scores),
    ):
        for at, threshold in (("default", DEFAULT), ("chosen", chosen)):
            verdicts = (scores >= threshold).astype(int)
            out[f"{name}_{at}_accuracy"] = f"{np.mean(labels == verdicts):.3f}"
            out[f"{name}_{at}_kappa"] = f"{kappa(labels, verdicts):.3f}"
            out[f"{name}_{at}_flagged"] = f"{verdicts.mean():.3f}"
        out[f"{name}_auc"] = f"{auc(labels, scores):.3f}"
    return out
