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


KEEP = 0.95


def closenesses(path, kept, passages, asked):
    """The closeness to its nearest passage of each question of the set kept in the
    file at path, asked giving every question's id and vector."""
    ids, vectors = asked
    place = {name: index for index, name in enumerate(ids)}
    rows = [row for row in read(path) if row["set"] == kept]
    chosen = vectors[[place[row["question"]] for row in rows]]
    return cosines(chosen, passages).max(axis=1)


def threshold(similarities, keep):
    ordered = sorted(similarities, reverse=True)
    for count, similarity in enumerate(ordered, start=1):
        if count / len(ordered) >= keep:
            return similarity
    raise ValueError("keep is above 1.")


def measured():
    _, passages = vectors("data/passage-vectors.csv")
    asked = vectors("data/question-vectors.csv")
    found = {}
    for name in ("questions", "other-questions"):
        for kept in ("validation", "test"):
            found[name, kept] = closenesses(f"data/{name}.csv", kept, passages, asked)
    limit = threshold(found["questions", "validation"], KEEP)
    return found, limit


PAGES, WEIGHT, TIMEOUT = 5, 0.8, 5
FOUND, DECLINED = 0.75, 0.8


def figures():
    found, limit = measured()
    office_test = found["questions", "test"]
    others_test = found["other-questions", "test"]
    return {
        "test": str(len(office_test)),
        "others_test": str(len(others_test)),
        "found": percent(FOUND),
        "declined": percent(DECLINED),
        "pages": str(PAGES),
        "limit": f"{limit:.4f}",
        "keep": percent(KEEP),
        "weight": str(WEIGHT),
        "timeout": str(TIMEOUT),
        "kept_test": percent(np.mean(office_test >= limit)),
        "declined_test": percent(np.mean(others_test < limit)),
    }
