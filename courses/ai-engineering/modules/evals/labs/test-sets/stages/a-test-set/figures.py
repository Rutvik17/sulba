import csv
import re
from collections import Counter

import numpy as np

SHARE = 0.5
SHOWN = 5
SERVICES = ["dmv", "ssa", "studentaid", "va"]


def words(text):
    return tuple(re.findall(r"\w+", text.lower()))


def figures():
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = list(csv.DictReader(file))
    first, kept = {}, []
    moved = 0
    for question in questions:
        key = words(question["text"])
        if key in first:
            moved += first[key]["page"] != question["page"]
            continue
        first[key] = question
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
    out = {
        "shown": str(SHOWN),
        "questions": str(len(questions)),
        "pages": str(len({q["page"] for q in questions})),
        "repeated": str(len(questions) - len(kept)),
        "repeated_elsewhere": str(moved),
        "unique": str(len(kept)),
        "share": f"{SHARE:.0%}",
    }
    for side, chosen in (
        ("dev", [q for q in kept if q["question"] not in test]),
        ("test", [q for q in kept if q["question"] in test]),
    ):
        out[f"{side}_questions"] = str(len(chosen))
        out[f"{side}_pages"] = str(len({q["page"] for q in chosen}))
        counts = Counter(q["domain"] for q in chosen)
        for service in SERVICES:
            out[f"{side}_{service}"] = str(counts[service])
    sizes = Counter(q["page"] for q in kept)
    out["largest_page"] = str(max(sizes.values()))
    out["largest_pages"] = str(
        sum(size == max(sizes.values()) for size in sizes.values())
    )
    # The same share drawn question by question instead.
    drawn = rng.permutation(len(kept))[: len(test)]
    by_question = {kept[index]["question"] for index in drawn}
    dev_pages = {q["page"] for q in kept if q["question"] not in by_question}
    test_pages = {q["page"] for q in kept if q["question"] in by_question}
    shared = [
        q for q in kept if q["question"] in by_question and q["page"] in dev_pages
    ]
    out["mixed_pages"] = str(len(dev_pages & test_pages))
    out["mixed_questions"] = str(len(shared))
    out["mixed_share"] = f"{len(shared) / len(by_question):.0%}"
    return out
