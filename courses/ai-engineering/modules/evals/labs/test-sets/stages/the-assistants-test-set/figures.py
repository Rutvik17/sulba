import csv
import re
from collections import defaultdict
from statistics import NormalDist

import numpy as np

SHARE = 0.5
CONFIDENCE = 0.95
SERVICES = ["dmv", "ssa", "studentaid", "va"]
CITED = re.compile(r"\[(p\d+)\]")


def unique_questions():
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = list(csv.DictReader(file))
    seen, kept = set(), []
    for question in questions:
        key = tuple(re.findall(r"\w+", question["text"].lower()))
        if key not in seen:
            seen.add(key)
            kept.append(question)
    return kept


def drawn(kept, of_all, whole):
    """The test set as the assistant's code draws it with default_rng(0), with the share
    of every question or of the service's, and pages moved whole or cut."""
    rng = np.random.default_rng(0)
    chosen = set()
    for service in SERVICES:
        theirs = [q for q in kept if q["domain"] == service]
        pages = list(dict.fromkeys(q["page"] for q in theirs))
        goal = SHARE * (len(kept) if of_all else len(theirs))
        held = 0
        for index in rng.permutation(len(pages)):
            on_page = [q["question"] for q in theirs if q["page"] == pages[index]]
            if whole:
                if held >= goal:
                    break
                chosen.update(on_page)
                held += len(on_page)
            else:
                for name in on_page:
                    if held < goal:
                        chosen.add(name)
                        held += 1
    return chosen


def figures():
    kept = unique_questions()
    cut = drawn(kept, of_all=False, whole=False)
    split_pages = {
        q["page"]
        for q in kept
        if q["question"] in cut
        and any(o["page"] == q["page"] and o["question"] not in cut for o in kept)
    }
    everything = drawn(kept, of_all=True, whole=True)
    test = drawn(kept, of_all=False, whole=True)
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row["passage"])
    with open("data/replies.csv", encoding="utf-8", newline="") as file:
        replies = {row["question"]: row for row in csv.DictReader(file)}
    scores, pages = [], []
    for question in kept:
        name = question["question"]
        if name not in test:
            continue
        reply = replies[name]["reply"]
        names = list(dict.fromkeys(CITED.findall(reply)))
        scores.append(float(any(n in relevant[name] for n in names)))
        pages.append(question["page"])
    scores = np.array(scores)
    residuals = scores - scores.mean()
    sums = defaultdict(float)
    for page, residual in zip(pages, residuals, strict=True):
        sums[page] += residual
    groups, n = len(sums), len(scores)
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    alone = z * np.sqrt(scores.var(ddof=1) / n)
    together = z * np.sqrt(groups / (groups - 1) * sum(v**2 for v in sums.values())) / n
    return {
        "share": f"{SHARE:.0%}",
        "cut_pages": str(len(split_pages)),
        "test_pages": str(len({q["page"] for q in kept if q["question"] in cut})),
        "unique": str(len(kept)),
        "everything": str(len(everything)),
        "alone": f"{alone:.3f}",
        "together": f"{together:.3f}",
    }
