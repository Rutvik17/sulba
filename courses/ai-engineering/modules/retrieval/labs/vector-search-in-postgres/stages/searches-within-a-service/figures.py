import csv

import numpy as np

# pgvector's documentation: "If a condition matches 10% of rows, with HNSW and the
# default hnsw.ef_search of 40, only 4 rows will match on average", and for
# hnsw.max_scan_tuples, "the max number of tuples to visit (20,000 by default)".
CANDIDATES = 40
# Scores are worked out in whole numbers, so that they are the same on every system:
# vectors of length 1 are rounded to this many steps for each unit.
STEPS = 2**20


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def whole(vectors):
    lengths = np.sqrt((vectors * vectors).sum(axis=1, keepdims=True))
    return np.rint(vectors / lengths * STEPS).astype(np.int64)


def figures():
    passage_ids, passages = read("data/passage-vectors.csv")
    question_ids, questions = read("data/question-vectors.csv")
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        service = {row["passage"]: row["domain"] for row in csv.DictReader(file)}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        validation = [row for row in csv.DictReader(file) if row["set"] == "validation"]
    place = {id_: index for index, id_ in enumerate(question_ids)}
    asked = whole(questions[[place[row["question"]] for row in validation]])
    scores = asked @ whole(passages).T
    nearest = np.argsort(-scores, axis=1, kind="stable")[:, :CANDIDATES]
    services = np.array([service[id_] for id_ in passage_ids])
    names = sorted(set(service.values()))
    own = [
        np.sum(services[row] == question["domain"])
        for row, question in zip(nearest, validation, strict=True)
    ]
    other = [
        np.sum(services[row] == name)
        for row, question in zip(nearest, validation, strict=True)
        for name in names
        if name != question["domain"]
    ]
    shares = [np.mean(services == name) for name in names]
    return {
        "share": "10%",
        "ef_search": str(CANDIDATES),
        "matching": "4",
        "max_scan": "20,000",
        "smallest": f"{min(shares):.0%}",
        "largest": f"{max(shares):.0%}",
        "questions": str(len(validation)),
        "own": f"{np.mean(own):.1f}",
        "other": f"{len(other):,}",
        "none": f"{sum(count == 0 for count in other):,}",
    }
