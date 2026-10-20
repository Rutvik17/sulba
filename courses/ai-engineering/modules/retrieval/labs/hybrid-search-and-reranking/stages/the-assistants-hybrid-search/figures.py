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
SCALE = 32767
WORD = re.compile(r"\w+")
# A system's logarithm can differ in its last digits, so BM25 scores this close might come in
# either order: each figure is worked out both ways, and must come out the same.
CLEAR = 1e-9
# The recalls the prose shows.
SHOWN = [
    "right",
    "right_more",
    "capitals",
    "bm25",
    "bm25_more",
    "negative_bm25",
    "negative",
    "vectors",
    "wrapped_vectors",
    "wrapped",
    "added",
    "added_more",
]


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
        if first != second and first - second <= CLEAR * abs(first):
            yield [*order[:at], order[at + 1], order[at], *order[at + 2 :]]


def fused(rankings):
    """The first MORE rows of reciprocal rank fusion, in fractions, a tie going to the
    earlier row. Sums in floats find the candidates, which differ from the fractions' by far
    less than any two ranks' shares."""
    total = np.zeros(len(rankings[0]))
    for ranking in rankings:
        total[ranking] += 1 / (RRF + np.arange(1, len(ranking) + 1))
    candidates = np.argsort(-total, kind="stable")[: 2 * MORE].tolist()
    rank = [
        dict(zip(ranking, range(1, len(ranking) + 1), strict=True))
        for ranking in rankings
    ]
    exact = {
        row: sum(Fraction(1, RRF + ranks[row]) for ranks in rank) for row in candidates
    }
    return sorted(candidates, key=lambda row: (-exact[row], row))[:MORE]


def hits(rows, ranking):
    """Whether a relevant row is among the first K, and among the first MORE."""
    return tuple(not rows.isdisjoint(ranking[:cut]) for cut in (K, MORE))


def same(outcomes):
    """The one outcome every order of near ties gives."""
    found = set(outcomes)
    assert len(found) == 1
    (outcome,) = found
    return outcome


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
    count = len(texts)
    lucene = {
        word: math.log(1 + (count - n + 0.5) / (n + 0.5)) for word, n in held.items()
    }
    negative = {
        word: math.log((count - n + 0.5) / (n + 0.5)) for word, n in held.items()
    }
    tf = {}

    def bm25(question, idf):
        scores = np.zeros(count)
        for word in question:
            if word in idf:
                if word not in tf:
                    tf[word] = np.array(
                        [held[word] for held in counts], dtype=np.float64
                    )
                scores += idf[word] * tf[word] / (tf[word] + norm)
        return scores

    _, vectors = read("data/passage-vectors.csv")
    question_ids, asked = read("data/question-vectors.csv")
    vector_of = dict(zip(question_ids, asked, strict=True))
    short = vectors.astype(np.int16)
    found = Counter()
    lost = total_words = 0
    best = []
    for question in questions:
        text = question["text"]
        rows = relevant[question["question"]]
        vector = vector_of[question["question"]]
        dots = vectors @ vector
        nearest = np.argsort(-dots, kind="stable").tolist()
        wrapped = np.argsort(-(short @ vector.astype(np.int16)), kind="stable").tolist()
        right = bm25(words(text), lucene)
        best.append(right.max())
        total_words += len(words(text))
        lost += sum(
            word not in held and word.lower() in held for word in WORD.findall(text)
        )
        variants = {
            "right": (right, nearest),
            "capitals": (bm25(WORD.findall(text), lucene), nearest),
            "negative": (bm25(words(text), negative), nearest),
            "wrapped": (right, wrapped),
        }
        for name, (scores, ranking) in variants.items():
            outcome = same(
                hits(rows, fused([order, ranking])) for order in orders(scores)
            )
            found[name] += outcome[0]
            found[f"{name}_more"] += outcome[1]
        for name, scores in (
            ("bm25", right),
            ("negative_bm25", variants["negative"][0]),
            ("added", right + dots / SCALE**2),
        ):
            outcome = same(hits(rows, order) for order in orders(scores))
            found[name] += outcome[0]
            found[f"{name}_more"] += outcome[1]
        found["vectors"] += hits(rows, nearest)[0]
        found["wrapped_vectors"] += hits(rows, wrapped)[0]
    first = questions[0]
    first_dots = vectors @ vector_of[first["question"]]
    nearest_row = int(np.argmax(first_dots))
    wrapped_dot = short[nearest_row] @ vector_of[first["question"]].astype(np.int16)
    common = max(held, key=lambda word: (held[word], word))
    share = len(questions)
    return {
        "questions": str(share),
        "k": str(K),
        "more": str(MORE),
        "rrf": str(RRF),
        "question_words": f"{total_words:,}",
        "lost": f"{lost:,}",
        "below_zero": str(sum(n > count / 2 for n in held.values())),
        "common": common,
        "common_weight": f"{negative[common]:.2f}",
        "int16_max": f"{np.iinfo(np.int16).max:,}",
        "dot": f"{int(first_dots[nearest_row]):,}",
        "wrapped_dot": f"{int(wrapped_dot):,}",
        "bm25_best": f"{statistics.median_low(best):.1f}",
        **{name: f"{found[name] / share:.3f}" for name in SHOWN},
    }
