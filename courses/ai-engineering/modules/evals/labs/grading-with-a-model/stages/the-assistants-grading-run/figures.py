import csv
import re
from collections import defaultdict

import numpy as np

LONGEST = 4000
SHOWN = 5
CITED = re.compile(r"\[(p\d+)\]")


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


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


def best(labels, scores):
    found, chosen = -np.inf, 0.0
    for threshold in np.unique(scores):
        value = kappa(labels, (scores >= threshold).astype(int))
        if value > found:
            found, chosen = value, threshold
    return chosen


def figures():
    begin = read("begin.csv")
    grades = {row["item"]: row for row in read("begin-grades.csv")}

    def labelled(sets):
        rows = [row for row in begin if row["set"] in sets]
        labels = np.array(
            [row["label"] != "Fully attributable" for row in rows], dtype=int
        )
        yes = np.array([float(grades[row["item"]]["yes"]) for row in rows])
        no = np.array([float(grades[row["item"]]["no"]) for row in rows])
        return labels, yes / (yes + no)

    chosen = best(*labelled(("dev",)))
    tuned = best(*labelled(("test",)))
    test_labels, test_scores = labelled(("test",))

    human = {(row["question"], row["context"]): row for row in read("human-grades.csv")}
    questions = [row["question"] for row in read("questions.csv")]

    def risks(context):
        yes = np.array([float(human[name, context]["yes"]) for name in questions])
        no = np.array([float(human[name, context]["no"]) for name in questions])
        return yes / (yes + no)

    own, other = risks("own"), risks("swapped")
    labels = np.concatenate(
        [np.zeros(len(own), dtype=int), np.ones(len(other), dtype=int)]
    )

    passages = {row["passage"]: row for row in read("passages.csv")}
    ranked = defaultdict(list)
    for row in read("ranked.csv"):
        ranked[row["question"]].append(row["passage"])
    cut = cut_cited = 0
    replies = read("replies.csv")
    for row in replies:
        blocks = [
            f"[{name}] {passages[name]['title']}\n{passages[name]['text']}"
            for name in ranked[row["question"]][:SHOWN]
        ]
        cut += len("\n\n".join(blocks)) > LONGEST
        ends = np.cumsum([len(block) + 2 for block in blocks]) - 2
        lost = {
            name
            for name, end in zip(ranked[row["question"]][:SHOWN], ends, strict=True)
            if end > LONGEST
        }
        cut_cited += bool(lost & set(CITED.findall(row["reply"])))
    return {
        "chosen": f"{chosen:.3f}",
        "test_threshold": f"{tuned:.3f}",
        "dev_kappa": f"{kappa(test_labels, (test_scores >= chosen).astype(int)):.3f}",
        "test_kappa": f"{kappa(test_labels, (test_scores >= tuned).astype(int)):.3f}",
        "auc": f"{auc(labels, np.concatenate([own, other])):.3f}",
        "cached_auc": f"{auc(labels, np.concatenate([own, own])):.3f}",
        "longest": f"{LONGEST:,}",
        "contexts": str(len(replies)),
        "cut": str(cut),
        "cut_cited": str(cut_cited),
    }
