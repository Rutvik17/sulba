import csv

import numpy as np

# The checks' budget for the table's indexes besides its primary key, how many passages a
# question gets, and the share of the full vectors' nearest a search must find.
BUDGET, K, KEPT = 2 * 1024 * 1024, 10, 0.95
# The solution's index: each vector's first NUMBERS numbers at half precision, and the
# candidates it sorts by the full vectors.
NUMBERS, CANDIDATES = 256, 40
# Scores are worked out in whole numbers, so that they are the same on every system: the
# full vectors at a length of 1 are rounded to STEPS steps for each unit, and a number at
# half precision is a whole number of HALF steps.
STEPS, HALF = 2**20, 2**24


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def whole(vectors):
    lengths = np.sqrt((vectors * vectors).sum(axis=1, keepdims=True))
    return np.rint(vectors / lengths * STEPS).astype(np.int64)


def halves(vectors):
    """Each vector's first NUMBERS numbers at half precision, in steps of 1 / HALF."""
    short = vectors[:, :NUMBERS].astype(np.float32) / np.float32(32767)
    return np.rint(short.astype(np.float16).astype(np.float64) * HALF).astype(np.int64)


def overlap(rows, nearest):
    return np.mean(
        [len(set(row) & set(near)) / K for row, near in zip(rows, nearest, strict=True)]
    )


def figures():
    _, passages = read("data/passage-vectors.csv")
    question_ids, questions = read("data/question-vectors.csv")
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        test = [row["question"] for row in csv.DictReader(file) if row["set"] == "test"]
    place = {id_: index for index, id_ in enumerate(question_ids)}
    asked = questions[[place[id_] for id_ in test]]
    full = whole(asked) @ whole(passages).T
    nearest = np.argsort(-full, axis=1, kind="stable")[:, :K]
    short = halves(passages)
    # Whole numbers below 2**53, which a float64 holds exactly.
    dots = (halves(asked) @ short.T).astype(np.float64)
    scores = dots / np.sqrt((short * short).sum(axis=1).astype(np.float64))
    order = np.argsort(-scores, axis=1, kind="stable")
    reranked = [
        row[np.argsort(-full[question, row], kind="stable")][:K]
        for question, row in enumerate(order[:, :CANDIDATES])
    ]
    return {
        "budget": "2 MB",
        "budget_bytes": f"{BUDGET:,}",
        "passages": f"{len(passages):,}",
        "test": str(len(test)),
        "k": str(K),
        "kept": f"{KEPT:.0%}",
        "numbers": str(NUMBERS),
        "bytes_half": f"{2 * NUMBERS + 8:,}",
        "bytes_full": f"{4 * passages.shape[1] + 8:,}",
        "alone": f"{overlap(order[:, :K], nearest):.3f}",
        "candidates": str(CANDIDATES),
        "reranked": f"{overlap(reranked, nearest):.3f}",
    }
