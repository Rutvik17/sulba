import csv
from collections import defaultdict

import numpy as np

K = 5
DEPTH = 10
REPEATS = 10_000
LEVEL = 0.05
FALL = 0.03
STEPS = [
    ("bm25", "vectors"),
    ("vectors", "fused"),
    ("fused", "fused-once"),
    ("fused-once", "reranked"),
    ("vectors", "reranked"),
    ("reranked", "confident"),
]


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        texts = {row["passage"]: row["text"] for row in csv.DictReader(file)}
    first_of = {}
    for passage, text in texts.items():
        first_of.setdefault(text, passage)
    first = {passage: first_of[text] for passage, text in texts.items()}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        tests = [row for row in csv.DictReader(file) if row["set"] == "test"]
    judgments = {row["question"]: set() for row in tests}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in judgments:
                judgments[row["question"]].add(first[row["passage"]])
    runs = defaultdict(dict)
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            runs[row["search"]].setdefault(row["question"], []).append(row["passage"])
    services = [row["domain"] for row in tests]

    def hits(search):
        found = []
        for question, answers in judgments.items():
            shown = {first[passage] for passage in runs[search].get(question, [])[:K]}
            found.append(int(not answers.isdisjoint(shown)))
        return np.array(found, dtype=np.int64)

    out = {
        "test": str(len(tests)),
        "k": str(K),
        "depth": str(DEPTH),
        "repeats": f"{REPEATS:,}",
        "level": str(LEVEL),
        "fall": str(FALL),
    }
    rng = np.random.default_rng(0)
    shipped = []
    for at, (current, candidate) in enumerate(STEPS, start=1):
        now, new = hits(current), hits(candidate)
        differences = new - now
        signs = 1 - 2 * rng.integers(0, 2, size=(REPEATS, len(differences)))
        count = np.count_nonzero(np.abs(signs @ differences) >= abs(differences.sum()))
        p = (1 + count) / (1 + REPEATS)
        held = []
        for service in sorted(set(services)):
            rows = [row for row, name in enumerate(services) if name == service]
            if now[rows].mean() - new[rows].mean() > FALL:
                held.append(service)
        ship = new.mean() > now.mean() and p < LEVEL and not held
        shipped.append(ship)
        out[f"now_{at}"] = f"{now.mean():.3f}"
        out[f"new_{at}"] = f"{new.mean():.3f}"
        out[f"p_{at}"] = f"{p:.4f}"
        out[f"held_{at}"] = ", ".join(held) if held else "None"
        out[f"ship_{at}"] = "Yes" if ship else "No"
    # The vectors and the reranker ship, fusion alone and each text once alone don't.
    assert shipped == [True, False, False, True, True, False]
    return out
