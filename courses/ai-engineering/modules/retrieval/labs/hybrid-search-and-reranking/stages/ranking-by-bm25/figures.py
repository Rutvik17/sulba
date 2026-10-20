import csv
import math
import re
from collections import Counter, defaultdict

import numpy as np

K = 5
MORE = 20
K1 = 1.5
B = 0.75
WORD = re.compile(r"\w+")
# A system's logarithm can differ in its last digits, so every score at a cut between the
# first K or MORE and the rest stands at least this far from the next, or ties it exactly.
CLEAR = 1e-9


def words(text):
    return WORD.findall(text.lower())


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = [row for row in csv.DictReader(file) if row["set"] == "validation"]
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row["passage"])
    texts = [words(passage["text"]) for passage in passages]
    lengths = np.array([len(text) for text in texts], dtype=np.float64)
    norm = K1 * (1 - B + B * lengths / lengths.mean())
    held = Counter(word for text in texts for word in set(text))
    counts = [Counter(text) for text in texts]
    idf = {
        word: math.log(1 + (len(texts) - n + 0.5) / (n + 0.5))
        for word, n in held.items()
    }
    ids, vectors = read("data/passage-vectors.csv")
    question_ids, asked = read("data/question-vectors.csv")
    vector_of = dict(zip(question_ids, asked, strict=True))
    found = defaultdict(int)
    for question in questions:
        scores = np.zeros(len(texts))
        for word in words(question["text"]):
            if word in idf:
                tf = np.array([count[word] for count in counts], dtype=np.float64)
                scores += idf[word] * tf / (tf + norm)
        ranked = sorted(scores, reverse=True)
        for cut in (K, MORE):
            last, after = ranked[cut - 1], ranked[cut]
            assert last == after or last - after > CLEAR * last
        order = np.argsort(-scores, kind="stable")
        nearest = np.argsort(
            -(vectors @ vector_of[question["question"]]), kind="stable"
        )
        rows = relevant[question["question"]]
        bm25 = not rows.isdisjoint(ids[i] for i in order[:K])
        vector = not rows.isdisjoint(ids[i] for i in nearest[:K])
        found["bm25"] += bm25
        found["bm25_more"] += not rows.isdisjoint(ids[i] for i in order[:MORE])
        found["vectors"] += vector
        found["vectors_more"] += not rows.isdisjoint(ids[i] for i in nearest[:MORE])
        found["only_bm25"] += bm25 and not vector
        found["only_vectors"] += vector and not bm25
    count = len(questions)
    common = max(held, key=lambda word: (held[word], word))
    return {
        "questions": str(count),
        "k": str(K),
        "more": str(MORE),
        "k1": f"{K1:g}",
        "b": f"{B:g}",
        "passages": f"{len(texts):,}",
        "common": common,
        "common_held": f"{held[common]:,}",
        "common_idf": f"{idf[common]:.3f}",
        "rare_idf": f"{math.log(1 + (len(texts) - 1 + 0.5) / 1.5):.2f}",
        "bm25": f"{found['bm25'] / count:.3f}",
        "bm25_more": f"{found['bm25_more'] / count:.3f}",
        "vectors": f"{found['vectors'] / count:.3f}",
        "vectors_more": f"{found['vectors_more'] / count:.3f}",
        "only_bm25": str(found["only_bm25"]),
        "only_vectors": str(found["only_vectors"]),
    }
