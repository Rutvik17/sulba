import csv

import numpy as np

# Scores are worked out in whole numbers, so that they are the same on every system: the
# vectors as stored, or shortened ones rounded to this many steps for each unit.
STEPS = 2**20
K = 5


def read(path):
    """A vector file's ids, and its numbers as stored, times 32,767."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def shortened(vectors, numbers):
    """The card's shortening, worked out from the stored whole numbers: the mean taken
    away, the first numbers kept, and scaled to a length of 1."""
    centred = vectors * vectors.shape[1] - vectors.sum(axis=1, keepdims=True)
    kept = centred[:, :numbers]
    return kept / np.sqrt((kept * kept).sum(axis=1, keepdims=True))


def whole(vectors):
    return np.rint(vectors * STEPS).astype(np.int64)


def hit_rate(scores, relevant):
    """The share of questions with a relevant passage among the first K, ties going to
    the passage that comes first."""
    order = np.argsort(-scores, axis=1, kind="stable")[:, :K]
    return sum(
        bool(set(row.tolist()) & answers) for row, answers in zip(order, relevant)
    ) / len(relevant)


def figures():
    passage_ids, passages = read("data/passage-vectors.csv")
    question_ids, questions = read("data/question-vectors.csv")
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        validation = {
            row["question"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        }
    rows = [index for index, id_ in enumerate(question_ids) if id_ in validation]
    questions = questions[rows]
    place = {id_: index for index, id_ in enumerate(passage_ids)}
    relevant = {question: set() for question in validation}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in relevant:
                relevant[row["question"]].add(place[row["passage"]])
    answers = [relevant[question_ids[index]] for index in rows]
    numbers = passages.shape[1]
    found = {"full": hit_rate(questions @ passages.T, answers)}
    for kept in (256, 128, 64):
        short = whole(shortened(questions, kept)) @ whole(shortened(passages, kept)).T
        found[kept] = hit_rate(short, answers)
    short = shortened(passages, 256)
    low, high = short.min(axis=0), short.max(axis=0)
    codes = np.clip(np.round((short - low) / (high - low) * 255), 0, 255)
    restored = low + codes * ((high - low) / 255)
    found["bytes"] = hit_rate(
        whole(shortened(questions, 256)) @ whole(restored).T, answers
    )
    size = numbers * 4 * len(passage_ids)
    return {
        "numbers": str(numbers),
        "passages": f"{len(passage_ids):,}",
        "bytes_full": f"{numbers * 4:,}",
        "megabytes": f"{size / 1e6:.1f}",
        "gigabytes": f"{numbers * 4 * 1e6 / 1e9:.1f}",
        "questions": str(len(rows)),
        "bytes_256": f"{256 * 4:,}",
        "bytes_128": str(128 * 4),
        "bytes_64": str(64 * 4),
        "bytes_bytes": "256",
        "hit_rate_full": f"{found['full']:.3f}",
        "hit_rate_256": f"{found[256]:.3f}",
        "hit_rate_128": f"{found[128]:.3f}",
        "hit_rate_64": f"{found[64]:.3f}",
        "hit_rate_bytes": f"{found['bytes']:.3f}",
    }
