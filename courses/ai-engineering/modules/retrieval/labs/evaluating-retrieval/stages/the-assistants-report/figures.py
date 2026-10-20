import csv
import math
from collections import defaultdict

import numpy as np

K = 5
DEPTH = 10
REPEATS = 10_000
LEVEL = 0.05


def hit_rate(seen, answers, k):
    return float(any(text in answers for text in seen[:k]))


def ndcg(seen, answers, k):
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, text in enumerate(seen[:k], start=1)
        if text in answers
    )
    best = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(answers)) + 1))
    return dcg / best


def p_value(differences, signs):
    """The randomization test's p-value, in whole numbers."""
    count = np.count_nonzero(np.abs(signs @ differences) >= abs(differences.sum()))
    return (1 + count) / (1 + REPEATS)


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        texts = {row["passage"]: row["text"] for row in csv.DictReader(file)}
    first_of = {}
    for passage, text in texts.items():
        first_of.setdefault(text, passage)
    first = {passage: first_of[text] for passage, text in texts.items()}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        tests = [
            row["question"] for row in csv.DictReader(file) if row["set"] == "test"
        ]
    judgments = {question: set() for question in tests}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in judgments:
                judgments[row["question"]].add(row["passage"])
    runs = defaultdict(dict)
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in judgments:
                runs[row["search"]].setdefault(row["question"], []).append(
                    row["passage"]
                )

    def seen(shown):
        out, before = [], set()
        for passage in shown:
            out.append(None if first[passage] in before else first[passage])
            before.add(first[passage])
        return out

    def squeezed(shown):
        return list(dict.fromkeys(first[passage] for passage in shown))

    def answers(question):
        return {first[passage] for passage in judgments[question]}

    def mean(values):
        return sum(values) / len(values)

    confident = runs["confident"]
    shown = [question for question in tests if question in confident]
    right = {
        search: [hit_rate(seen(runs[search].get(q, [])), answers(q), K) for q in tests]
        for search in ("reranked", "fused-once", "fused", "confident")
    }
    reranked_ndcg = [ndcg(seen(runs["reranked"][q]), answers(q), DEPTH) for q in tests]
    every_copy = [ndcg(seen(runs["reranked"][q]), judgments[q], DEPTH) for q in tests]
    a = np.array(right["reranked"], dtype=np.int64)
    b = np.array(right["fused-once"], dtype=np.int64)
    rng = np.random.default_rng(0)
    signs = 1 - 2 * rng.integers(0, 2, size=(REPEATS, len(tests)))
    paired = p_value(a - b, signs)
    pooled = np.concatenate([a, b])
    observed = abs(int(a.sum()) - int(b.sum()))
    count = 0
    for _ in range(REPEATS):
        shuffled = rng.permutation(pooled)
        count += (
            abs(int(shuffled[: len(a)].sum()) - int(shuffled[len(a) :].sum()))
            >= observed
        )
    unpaired = (1 + count) / (1 + REPEATS)
    # Apart, the reranker's gain looks like chance; paired, it doesn't.
    assert paired < LEVEL < unpaired
    copies = [
        question
        for question in tests
        if len(judgments[question]) > len(answers(question))
    ]
    fused_squeezed = [
        hit_rate(squeezed(runs["fused"][q]), answers(q), K) for q in tests
    ]
    return {
        "test": str(len(tests)),
        "k": str(K),
        "depth": str(DEPTH),
        "level": str(LEVEL),
        "empty": str(len(tests) - len(shown)),
        "confident": f"{mean(right['confident']):.3f}",
        "confident_shown": f"{mean([right['confident'][tests.index(q)] for q in shown]):.3f}",
        "reranked": f"{mean(right['reranked']):.3f}",
        "copies": str(len(copies)),
        "reranked_ndcg": f"{mean(reranked_ndcg):.3f}",
        "every_copy": f"{mean(every_copy):.3f}",
        "fused": f"{mean(right['fused']):.3f}",
        "fused_squeezed": f"{mean(fused_squeezed):.3f}",
        "fused_once": f"{mean(right['fused-once']):.3f}",
        "paired": f"{paired:.4f}",
        "unpaired": f"{unpaired:.4f}",
    }
