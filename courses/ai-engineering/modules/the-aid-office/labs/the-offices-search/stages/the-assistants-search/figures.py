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


CLOSE = 0.7


def figures():
    _, passages = vectors("data/passage-vectors.csv")
    question_ids, question_vectors = vectors("data/question-vectors.csv")
    place = {name: index for index, name in enumerate(question_ids)}
    office = read("data/questions.csv")
    chosen = question_vectors[[place[row["question"]] for row in office]]
    distances = 1 - cosines(chosen, passages).max(axis=1)
    kept = int((distances >= CLOSE).sum())
    if kept:
        raise ValueError(f"The assistant's closeness keeps {kept} questions.")
    return {"questions": str(len(office))}
