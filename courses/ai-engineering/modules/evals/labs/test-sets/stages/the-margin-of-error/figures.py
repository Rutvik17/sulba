import csv
import re
from statistics import NormalDist
from collections import defaultdict

import numpy as np

SHARE = 0.5
MOST = 100
CONFIDENCE = 0.95
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
    """Each test question's reply, scored 1 if it passes every check and 0 if not, and its
    score on `cites_answer` alone, with the question's page."""
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
    every, answer, pages = [], [], []
    for question in test_questions():
        name = question["question"]
        reply = replies[name]["reply"]
        names = list(dict.fromkeys(CITED.findall(reply)))
        cites_answer = any(n in relevant[name] for n in names)
        passed = (
            bool(names)
            and all(n in shown[name] for n in names)
            and cites_answer
            and replies[name]["finish"] == "stop"
            and len(reply.split()) <= MOST
        )
        every.append(float(passed))
        answer.append(float(cites_answer))
        pages.append(question["page"])
    return np.array(every), np.array(answer), pages


def errors(scores, pages):
    n = len(scores)
    residuals = scores - scores.mean()
    sums = defaultdict(float)
    for page, residual in zip(pages, residuals, strict=True):
        sums[page] += residual
    groups = len(sums)
    plain = np.sqrt(scores.var(ddof=1) / n)
    clustered = np.sqrt(groups / (groups - 1) * sum(v**2 for v in sums.values())) / n
    return plain, clustered


def figures():
    every, answer, pages = scored()
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    out = {
        "test": str(len(every)),
        "pages": str(len(set(pages))),
        "confidence": f"{CONFIDENCE:.0%}",
        "z": f"{z:.2f}",
    }
    for name, scores in (("all", every), ("answer", answer)):
        plain, clustered = errors(scores, pages)
        effect = (clustered / plain) ** 2
        out[f"{name}_rate"] = f"{scores.mean():.3f}"
        out[f"{name}_margin"] = f"{z * plain:.3f}"
        out[f"{name}_clustered"] = f"{z * clustered:.3f}"
        if name == "all":
            out["all_low"] = f"{scores.mean() - z * clustered:.3f}"
            out["all_high"] = f"{scores.mean() + z * clustered:.3f}"
        out[f"{name}_effect"] = f"{effect:.2f}"
        out[f"{name}_worth"] = f"{len(scores) / effect:.0f}"
    return out
