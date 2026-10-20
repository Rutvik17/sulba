import csv

import numpy as np

# The assistant's index: the first 256 numbers of each vector, a byte each. The vector
# files hold each number times SCALE. Scores are worked out in whole numbers, so that
# they are the same on every system: vectors are rounded to this many steps for each
# unit.
NUMBERS, SCALE, STEPS, K = 256, 32767, 2**20, 5


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def shortened(vectors):
    centred = vectors * vectors.shape[1] - vectors.sum(axis=1, keepdims=True)
    kept = centred[:, :NUMBERS]
    return kept / np.sqrt((kept * kept).sum(axis=1, keepdims=True))


def whole(vectors):
    return np.rint(vectors * STEPS).astype(np.int64)


def stored(vectors):
    """The vectors as the index keeps them: each number one of 256 steps between its low
    and high across the passages."""
    low, high = vectors.min(axis=0), vectors.max(axis=0)
    codes = np.clip(np.round((vectors - low) / (high - low) * 255), 0, 255)
    return whole(low + codes * ((high - low) / 255))


def first(scores):
    """Each question's first K rows, from the highest score, ties going to the first
    row."""
    return np.argsort(-scores, axis=1, kind="stable")[:, :K]


def figures():
    passage_ids, passages = read("data/passage-vectors.csv")
    question_ids, questions = read("data/question-vectors.csv")
    _, as_passages = read("data/question-vectors-as-passages.csv")
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        validation = [
            row["question"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        ]
    place = {id_: index for index, id_ in enumerate(question_ids)}
    questions = questions[[place[id_] for id_ in validation]]
    relevant = {id_: set() for id_ in validation}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in relevant:
                relevant[row["question"]].add(row["passage"])
    answers = [relevant[id_] for id_ in validation]

    def hit_rate(rows, ids=passage_ids):
        found = [
            bool({ids[index] for index in row} & want)
            for row, want in zip(rows, answers)
        ]
        return sum(found) / len(found)

    restored = stored(shortened(passages))
    asked = whole(shortened(questions))
    right = first(asked @ restored.T)
    misread = whole(shortened(as_passages))
    sliced = passages[:, :NUMBERS]
    lengths = np.sqrt((sliced * sliced).sum(axis=1)) / SCALE
    by_slice = whole(questions[:, :NUMBERS] / SCALE) @ stored(sliced / SCALE).T
    by_text = sorted(passage_ids)

    def answered(column):
        return sum(
            passage_ids[row[column]] in want for row, want in zip(right, answers)
        )

    return {
        "questions": str(len(validation)),
        "k": str(K),
        "passages": f"{len(passage_ids):,}",
        "right": f"{hit_rate(right):.3f}",
        "as_passages": f"{hit_rate(first(misread @ restored.T)):.3f}",
        "shortest": f"{lengths.min():.3f}",
        "longest": f"{lengths.max():.3f}",
        "sliced": f"{hit_rate(first(by_slice)):.3f}",
        "ids": f"{hit_rate(right, by_text):.3f}",
        "moved": f"{sum(a != b for a, b in zip(by_text, passage_ids)):,}",
        "first_best": str(answered(0)),
        "first_last": str(answered(K - 1)),
    }
