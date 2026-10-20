import csv
import math
import re
from collections import Counter, defaultdict
from fractions import Fraction

import numpy as np

K = 5
DEPTH = 20
DEPTHS = (10, 20)
RRF = 60
K1 = 1.5
B = 0.75
FLOOR = 0.80
WORD = re.compile(r"\w+")
# A system's logarithm can differ in its last digits, so BM25 scores this close might come in
# either order: each figure is worked out both ways, and must come out the same.
CLEAR = 1e-9
# How many of the fused ranking's first rows are put in order in fractions.
EXACT = 80


def words(text):
    return WORD.findall(text.lower())


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def orders(scores):
    """The rows by score, a tie going to the earlier row, and the same with each pair of
    scores too close to tell apart swapped."""
    order = np.argsort(-scores, kind="stable").tolist()
    yield order
    for at in range(len(order) - 1):
        first, second = scores[order[at]], scores[order[at + 1]]
        if first != second and first - second <= CLEAR * first:
            yield [*order[:at], order[at + 1], order[at], *order[at + 2 :]]


def fused(rankings):
    """The first EXACT rows of reciprocal rank fusion, in fractions, a tie going to the
    earlier row. Sums in floats find the candidates, which differ from the fractions' by far
    less than any two ranks' shares."""
    total = np.zeros(len(rankings[0]))
    for ranking in rankings:
        total[ranking] += 1 / (RRF + np.arange(1, len(ranking) + 1))
    candidates = np.argsort(-total, kind="stable")[: 2 * EXACT].tolist()
    rank = [
        dict(zip(ranking, range(1, len(ranking) + 1), strict=True))
        for ranking in rankings
    ]
    exact = {
        row: sum(Fraction(1, RRF + ranks[row]) for ranks in rank) for row in candidates
    }
    return sorted(candidates, key=lambda row: (-exact[row], row))[:EXACT]


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = list(csv.DictReader(file))
    ids = [passage["passage"] for passage in passages]
    row_of = {passage: row for row, passage in enumerate(ids)}
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row_of[row["passage"]])
    scored = {}
    with open("data/rerank-scores.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            scored[row["question"], row_of[row["passage"]]] = float(row["score"])
    bodies = [passage["text"] for passage in passages]
    texts = [words(body) for body in bodies]
    lengths = np.array([len(text) for text in texts], dtype=np.float64)
    norm = K1 * (1 - B + B * lengths / lengths.mean())
    held = Counter(word for text in texts for word in set(text))
    counts = [Counter(text) for text in texts]
    idf = {
        word: math.log(1 + (len(texts) - n + 0.5) / (n + 0.5))
        for word, n in held.items()
    }
    _, vectors = read("data/passage-vectors.csv")
    question_ids, asked = read("data/question-vectors.csv")
    vector_of = dict(zip(question_ids, asked, strict=True))
    found = defaultdict(Counter)
    for question in questions:
        scores = np.zeros(len(texts))
        for word in words(question["text"]):
            if word in idf:
                tf = np.array([count[word] for count in counts], dtype=np.float64)
                scores += idf[word] * tf / (tf + norm)
        nearest = np.argsort(
            -(vectors @ vector_of[question["question"]]), kind="stable"
        )
        rows = relevant[question["question"]]
        outcomes = set()
        for bm25 in orders(scores):
            ranking = fused([bm25, nearest.tolist()])
            seen, once = set(), []
            for row in ranking:
                if bodies[row] not in seen:
                    seen.add(bodies[row])
                    once.append(row)
            assert len(once) >= max(DEPTHS)
            outcome = [
                not rows.isdisjoint(ranking[:K]),
                not rows.isdisjoint(once[:K]),
                sum(
                    bodies[row] in {bodies[other] for other in ranking[:at]}
                    for at, row in enumerate(ranking[:DEPTH])
                ),
            ]
            for depth in DEPTHS:
                chosen = once[:depth]
                ranked = sorted(
                    range(depth),
                    key=lambda at: (-scored[question["question"], chosen[at]], at),
                )
                outcome.append(not rows.isdisjoint(chosen[at] for at in ranked[:K]))
            outcomes.add(tuple(outcome))
        assert len(outcomes) == 1
        (outcome,) = outcomes
        tally = found[question["set"]]
        tally["questions"] += 1
        tally["fused"] += outcome[0]
        tally["once"] += outcome[1]
        tally["repeats"] += outcome[2]
        tally["with_repeats"] += outcome[2] > 0
        for depth, hit in zip(DEPTHS, outcome[3:], strict=True):
            tally[f"reranked_{depth}"] += hit
    validation, test = found["validation"], found["test"]
    count = validation["questions"]
    assert test[f"reranked_{DEPTH}"] / test["questions"] >= FLOOR
    return {
        "questions": str(count),
        "test": str(test["questions"]),
        "k": str(K),
        "depth": str(DEPTH),
        "short": str(DEPTHS[0]),
        "floor": f"{FLOOR:.2f}",
        "repeats": f"{validation['repeats'] / count:.1f}",
        "with_repeats": str(validation["with_repeats"]),
        "fused": f"{validation['fused'] / count:.3f}",
        "once": f"{validation['once'] / count:.3f}",
        "reranked_short": f"{validation[f'reranked_{DEPTHS[0]}'] / count:.3f}",
        "reranked": f"{validation[f'reranked_{DEPTH}'] / count:.3f}",
        "test_once": f"{test['once'] / test['questions']:.3f}",
        "test_reranked": f"{test[f'reranked_{DEPTH}'] / test['questions']:.3f}",
    }
