import csv
import math
import re
from statistics import NormalDist
from collections import defaultdict

import numpy as np

SHARE = 0.5
MOST = 100
CONFIDENCE = 0.95
TARGET = 0.05
SERVICES = ["dmv", "ssa", "studentaid", "va"]
CITED = re.compile(r"\[(p\d+)\]")


def test_questions():
    """The test set's questions, split as the first stage splits them."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = list(csv.DictReader(file))
    seen, kept = set(), []
    for question in questions:
        key = tuple(re.findall(r"\w+", question["text"].lower()))
        if key not in seen:
            seen.add(key)
            kept.append(question)
    rng = np.random.default_rng(0)
    test = set()
    for service in SERVICES:
        theirs = [q for q in kept if q["domain"] == service]
        pages = list(dict.fromkeys(q["page"] for q in theirs))
        held = 0
        for index in rng.permutation(len(pages)):
            if held >= SHARE * len(theirs):
                break
            on_page = [q["question"] for q in theirs if q["page"] == pages[index]]
            test.update(on_page)
            held += len(on_page)
    return [q for q in kept if q["question"] in test]


def scored():
    """Each test question's page, service and score: 1 if its reply passes every check."""
    shown = defaultdict(list)
    with open("data/shown.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            shown[row["question"]].append(row["passage"])
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row["passage"])
    with open("data/replies.csv", encoding="utf-8", newline="") as file:
        replies = {row["question"]: row for row in csv.DictReader(file)}
    rows = []
    for question in test_questions():
        name = question["question"]
        reply = replies[name]["reply"]
        names = list(dict.fromkeys(CITED.findall(reply)))
        passed = (
            bool(names)
            and all(n in shown[name] for n in names)
            and any(n in relevant[name] for n in names)
            and replies[name]["finish"] == "stop"
            and len(reply.split()) <= MOST
        )
        rows.append((question["page"], question["domain"], float(passed)))
    return rows


def line(rows):
    scores = np.array([score for _, _, score in rows])
    residuals = scores - scores.mean()
    sums = defaultdict(float)
    for (page, _, _), residual in zip(rows, residuals, strict=True):
        sums[page] += residual
    groups, n = len(sums), len(scores)
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    reach = z * np.sqrt(groups / (groups - 1) * sum(v**2 for v in sums.values())) / n
    return scores.mean(), reach, n, math.ceil(n * (reach / TARGET) ** 2)


def figures():
    rows = scored()
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = list(csv.DictReader(file))
    out = {"confidence": f"{CONFIDENCE:.0%}", "target": f"{TARGET:.2f}"}
    groups = {"all": rows} | {s: [r for r in rows if r[1] == s] for s in SERVICES}
    for name, members in groups.items():
        rate, reach, n, needed = line(members)
        out[f"{name}_rate"] = f"{rate:.3f}"
        out[f"{name}_margin"] = f"{reach:.3f}"
        out[f"{name}_questions"] = str(n)
        out[f"{name}_needed"] = str(needed)
    out["fewest_needed"] = str(min(line(groups[s])[3] for s in SERVICES))
    out["most_needed"] = str(max(line(groups[s])[3] for s in SERVICES))
    out["studentaid_asked"] = str(sum(q["domain"] == "studentaid" for q in questions))
    # The whole test set falls short of the target, and studentaid alone would need more
    # questions than it has.
    assert line(groups["all"])[1] > TARGET
    assert line(groups["studentaid"])[3] > int(out["studentaid_asked"])
    return out
