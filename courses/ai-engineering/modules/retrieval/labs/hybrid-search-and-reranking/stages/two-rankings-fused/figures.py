import csv
import math
import re
import statistics
from collections import Counter, defaultdict
from fractions import Fraction

import numpy as np

K = 5
MORE = 20
RRF = 60
K1 = 1.5
B = 0.75
WORD = re.compile(r"\w+")
# A system's logarithm can differ in its last digits, so BM25 scores this close might come in
# either order: each figure is worked out both ways, and must come out the same.
CLEAR = 1e-9


def words(text):
    return WORD.findall(text.lower())


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def fused(rankings):
    """Reciprocal rank fusion, in fractions, a tie going to the earlier row."""
    total = defaultdict(Fraction)
    for ranking in rankings:
        for rank, row in enumerate(ranking, start=1):
            total[row] += Fraction(1, RRF + rank)
    return sorted(total, key=lambda row: (-total[row], row))


def orders(scores):
    """The rows by score, a tie going to the earlier row, and the same with each pair of
    scores too close to tell apart swapped."""
    order = np.argsort(-scores, kind="stable").tolist()
    yield order
    for at in range(len(order) - 1):
        first, second = scores[order[at]], scores[order[at + 1]]
        if first != second and first - second <= CLEAR * first:
            yield [*order[:at], order[at + 1], order[at], *order[at + 2 :]]


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = [row for row in csv.DictReader(file) if row["set"] == "validation"]
    row_of = {passage["passage"]: row for row, passage in enumerate(passages)}
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row_of[row["passage"]])
    texts = [words(passage["text"]) for passage in passages]
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
    found = Counter()
    best_bm25, best_dot = [], []
    for question in questions:
        scores = np.zeros(len(texts))
        for word in words(question["text"]):
            if word in idf:
                tf = np.array([count[word] for count in counts], dtype=np.float64)
                scores += idf[word] * tf / (tf + norm)
        dots = vectors @ vector_of[question["question"]]
        best_bm25.append(scores.max())
        best_dot.append(int(dots.max()))
        nearest = np.argsort(-dots, kind="stable")
        rows = relevant[question["question"]]
        # Fused and BM25 alone, among the first K and the first MORE.
        outcomes = {
            tuple(
                not rows.isdisjoint(ranking[:cut])
                for ranking in (fused([bm25, nearest.tolist()]), bm25)
                for cut in (K, MORE)
            )
            for bm25 in orders(scores)
        }
        assert len(outcomes) == 1
        (outcome,) = outcomes
        vector = not rows.isdisjoint(nearest[:K].tolist())
        found["fused"] += outcome[0]
        found["fused_more"] += outcome[1]
        found["bm25"] += outcome[2]
        found["bm25_more"] += outcome[3]
        found["vectors"] += vector
        found["vectors_more"] += not rows.isdisjoint(nearest[:MORE].tolist())
        found["gained"] += outcome[0] and not vector
        found["lost"] += vector and not outcome[0]
    count = len(questions)
    return {
        "questions": str(count),
        "k": str(K),
        "more": str(MORE),
        "rrf": str(RRF),
        "bm25": f"{found['bm25'] / count:.3f}",
        "bm25_more": f"{found['bm25_more'] / count:.3f}",
        "fused": f"{found['fused'] / count:.3f}",
        "fused_more": f"{found['fused_more'] / count:.3f}",
        "vectors": f"{found['vectors'] / count:.3f}",
        "vectors_more": f"{found['vectors_more'] / count:.3f}",
        "gained": str(found["gained"]),
        "lost": str(found["lost"]),
        "bm25_best": f"{statistics.median_low(best_bm25):.1f}",
        "dot_best": f"{statistics.median_low(best_dot):,}",
    }
