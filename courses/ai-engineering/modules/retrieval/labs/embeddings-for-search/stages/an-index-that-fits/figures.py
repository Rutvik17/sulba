import csv

import numpy as np

# The checks' budget, in bytes a passage, the passages a question gets, and the share of
# the full vectors' answers the index must keep.
BUDGET, K, KEPT = 300, 5, 0.98
# Scores of shortened vectors are worked out in whole numbers, so that they are the same
# on every system: shortened vectors are rounded to this many steps for each unit.
STEPS = 2**20


def read(path):
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


def stored(vectors):
    """Each number as one of 256 steps between its low and high across the passages."""
    low, high = vectors.min(axis=0), vectors.max(axis=0)
    codes = np.clip(np.round((vectors - low) / (high - low) * 255), 0, 255)
    return whole(low + codes * ((high - low) / 255))


def figures():
    passage_ids, passages = read("data/passage-vectors.csv")
    question_ids, questions = read("data/question-vectors.csv")
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        test = {row["question"] for row in csv.DictReader(file) if row["set"] == "test"}
    rows = [index for index, id_ in enumerate(question_ids) if id_ in test]
    questions = questions[rows]
    relevant = {question_ids[index]: set() for index in rows}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in relevant:
                relevant[row["question"]].add(row["passage"])
    answers = [relevant[question_ids[index]] for index in rows]

    def hit_rate(scores):
        best = np.argsort(-scores, axis=1, kind="stable")[:, :K]
        found = [
            bool({passage_ids[index] for index in row} & want)
            for row, want in zip(best, answers)
        ]
        return f"{sum(found) / len(found):.3f}"

    numbers = passages.shape[1]
    as_bytes = whole(shortened(questions, 256)) @ stored(shortened(passages, 256)).T
    first_64 = whole(shortened(questions, 64)) @ whole(shortened(passages, 64)).T
    return {
        "budget": str(BUDGET),
        "passages": f"{len(passage_ids):,}",
        "test": str(len(rows)),
        "k": str(K),
        "kept": str(round(KEPT * 100)),
        "full": hit_rate(questions @ passages.T),
        "bytes": "256",
        "bytes_full": f"{numbers * 4:,}",
        "hit_rate_bytes": hit_rate(as_bytes),
        "hit_rate_64": hit_rate(first_64),
    }
