import csv
import re
from collections import defaultdict

import numpy as np


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


def rates(labels, verdicts):
    return np.mean(verdicts[labels == 1] == 0), np.mean(verdicts[labels == 0] == 1)


def words(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def figures():
    passages = {row["passage"]: row for row in read("passages.csv")}
    relevant = defaultdict(list)
    for row in read("relevant.csv"):
        relevant[row["question"]].append(row["passage"])
    ranked = defaultdict(list)
    for row in read("ranked.csv"):
        ranked[row["question"]].append(row["passage"])
    questions = read("questions.csv")
    replies = {row["question"]: row["reply"] for row in read("human-replies.csv")}

    def own(question):
        held = relevant[question["question"]]
        return [name for name in held if passages[name]["page"] == question["page"]]

    def other(question):
        texts = {passages[name]["text"] for name in relevant[question["question"]]}
        return next(
            name
            for name in ranked[question["question"]]
            if passages[name]["page"] != question["page"]
            and passages[name]["text"] not in texts
        )

    half = len(questions) // 2
    shares = defaultdict(list)
    for index, question in enumerate(questions):
        start = (index + half) % len(questions)
        partner = next(
            q
            for q in questions[start:] + questions[:start]
            if q["domain"] != question["domain"]
        )
        said = words(replies[question["question"]])
        for kind, names in (
            ("own", own(question)),
            ("other", [other(question)]),
            ("swapped", own(partner)),
        ):
            held = set().union(*(words(passages[name]["text"]) for name in names))
            shares[kind].append(len(said & held) / len(said))

    begin = read("begin.csv")
    begin_grades = {row["item"]: row for row in read("begin-grades.csv")}

    def begin_set(name):
        rows = [item for item in begin if item["set"] == name]
        labels = np.array(
            [item["label"] != "Fully attributable" for item in rows], dtype=int
        )
        yes = np.array([float(begin_grades[item["item"]]["yes"]) for item in rows])
        no = np.array([float(begin_grades[item["item"]]["no"]) for item in rows])
        return labels, yes / (yes + no)

    dev_labels, dev_scores = begin_set("dev")
    best, chosen = -np.inf, 0.0
    for threshold in np.unique(dev_scores):
        found = kappa(dev_labels, (dev_scores >= threshold).astype(int))
        if found > best:
            best, chosen = found, threshold
    test_labels, test_scores = begin_set("test")
    begin_misses, begin_alarms = rates(test_labels, (test_scores >= chosen).astype(int))

    grades = {
        (row["question"], row["context"]): row for row in read("human-grades.csv")
    }

    def risks(context):
        yes = np.array(
            [float(grades[q["question"], context]["yes"]) for q in questions]
        )
        no = np.array([float(grades[q["question"], context]["no"]) for q in questions])
        return yes / (yes + no)

    kept, swapped, nearby = risks("own"), risks("swapped"), risks("other")
    labels = np.repeat([0, 1], len(questions))
    scores = np.concatenate([kept, swapped])
    verdicts = (scores >= chosen).astype(int)
    misses, alarms = rates(labels, verdicts)
    assert misses < begin_misses and alarms > begin_alarms
    return {
        "questions": str(len(questions)),
        "chosen": f"{chosen:.3f}",
        "words_own": f"{np.mean(shares['own']):.2f}",
        "words_other": f"{np.mean(shares['other']):.2f}",
        "words_swapped": f"{np.mean(shares['swapped']):.2f}",
        "auc": f"{auc(labels, scores):.3f}",
        "kappa": f"{kappa(labels, verdicts):.3f}",
        "misses": f"{misses:.3f}",
        "false_alarms": f"{alarms:.3f}",
        "begin_misses": f"{begin_misses:.3f}",
        "begin_false_alarms": f"{begin_alarms:.3f}",
        "other_passed": f"{np.mean(nearby < chosen):.3f}",
        "pairs_right": str(int(np.sum(swapped > kept))),
    }
