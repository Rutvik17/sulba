import csv
import re
from collections import defaultdict

import numpy as np

SHARE = 0.5
SHOWN = 5
MOST = 100
LIMIT = 300
SERVICES = ["dmv", "ssa", "studentaid", "va"]
CITED = re.compile(r"\[(p\d+)\]")
CHECKS = ["cites", "cites_shown", "cites_answer", "finished", "brief"]


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


def figures():
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
    tests = test_questions()
    results, held, invented = [], 0, 0
    for question in tests:
        name = question["question"]
        reply = replies[name]["reply"]
        names = list(dict.fromkeys(CITED.findall(reply)))
        results.append(
            {
                "cites": bool(names),
                "cites_shown": all(n in shown[name] for n in names),
                "cites_answer": any(n in relevant[name] for n in names),
                "finished": replies[name]["finish"] == "stop",
                "brief": len(reply.split()) <= MOST,
            }
        )
        held += any(p in relevant[name] for p in shown[name])
        invented += any(n not in shown[name] for n in names)
    words = [len(replies[q["question"]]["reply"].split()) for q in tests]
    out = {
        "limit": str(LIMIT),
        "shown": str(SHOWN),
        "test": str(len(tests)),
        "most": str(MOST),
        "median_words": f"{np.median(words):.0f}",
        "longest": str(max(words)),
        "held": str(held),
        "held_share": f"{held / len(tests):.3f}",
        "invented": str(invented),
    }
    for check in CHECKS:
        out[check] = f"{np.mean([r[check] for r in results]):.3f}"
    out["all"] = f"{np.mean([all(r.values()) for r in results]):.3f}"
    cited_held = sum(r["cites_answer"] for r in results)
    out["cited_of_held"] = f"{cited_held / held:.0%}"
    return out
