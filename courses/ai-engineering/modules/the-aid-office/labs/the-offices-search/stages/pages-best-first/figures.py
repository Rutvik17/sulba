import csv

import numpy as np


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def vectors(path):
    """Each row's id, and its recorded vector as whole numbers."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def cosines(questions, passages):
    """Each question's cosine with each passage, from the whole numbers: the products are exact
    in int64, so the cosines are the same on every system."""
    lengths = np.sqrt((questions * questions).sum(axis=1).astype(np.float64))
    norms = np.sqrt((passages * passages).sum(axis=1).astype(np.float64))
    products = (questions @ passages.T).astype(np.float64)
    return products / lengths[:, None] / norms[None, :]


def percent(share):
    return f"{share:.0%}"


CANDIDATES, K, PAGES = 40, 60, 5
WEIGHT, FOUND, RANKED = 0.8, 0.8, 0.7


def figures():
    passages = read("data/passages.csv")
    page = {passage["passage"]: passage["page"] for passage in passages}
    passage_ids, passage_vectors = vectors("data/passage-vectors.csv")
    question_ids, question_vectors = vectors("data/question-vectors.csv")
    place = {name: index for index, name in enumerate(question_ids)}
    questions = read("data/questions.csv")
    validation = [row for row in questions if row["set"] == "validation"]
    chosen = question_vectors[[place[row["question"]] for row in validation]]
    similar = cosines(chosen, passage_vectors)
    hits = ranked = 0
    for row, scores in zip(validation, similar, strict=True):
        found = []
        for index in np.argsort(-scores, kind="stable")[:CANDIDATES]:
            if page[passage_ids[index]] not in found:
                found.append(page[passage_ids[index]])
        found = found[:PAGES]
        hits += row["page"] in found
        ranked += 1 / (found.index(row["page"]) + 1) if row["page"] in found else 0
    return {
        "pages": str(PAGES),
        "candidates": str(CANDIDATES),
        "validation": str(len(validation)),
        "weight": str(WEIGHT),
        "found": percent(FOUND),
        "ranked": f"{RANKED:.2f}",
        "share": f"{(1 - WEIGHT) / WEIGHT:.2f}",
        "meaning_found": percent(hits / len(validation)),
        "meaning_ranked": f"{ranked / len(validation):.2f}",
    }
