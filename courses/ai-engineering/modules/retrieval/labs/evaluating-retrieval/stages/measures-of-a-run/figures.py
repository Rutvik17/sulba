import csv
import math
from collections import defaultdict

SHOWN = 20
TEXTS = 20
K = 5
DEPTH = 10
CONFIDENT = 0.5
TABLE = ["bm25", "vectors", "fused", "fused-once", "reranked", "confident"]


def hit_rate(shown, relevant, k):
    return float(any(passage in relevant for passage in shown[:k]))


def recall(shown, relevant, k):
    return sum(passage in relevant for passage in shown[:k]) / len(relevant)


def reciprocal_rank(shown, relevant, k):
    for rank, passage in enumerate(shown[:k], start=1):
        if passage in relevant:
            return 1 / rank
    return 0.0


def ndcg(shown, relevant, k):
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, passage in enumerate(shown[:k], start=1)
        if passage in relevant
    )
    best = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    return dcg / best


def figures():
    runs = defaultdict(dict)
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            runs[row["search"]].setdefault(row["question"], []).append(row["passage"])
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        validation = [
            row["question"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        ]
    judgments = {question: set() for question in validation}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in judgments:
                judgments[row["question"]].add(row["passage"])
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = {row["passage"]: row for row in csv.DictReader(file)}
    copied = [
        relevant
        for relevant in judgments.values()
        if len(relevant) > 1 and len({passages[p]["text"] for p in relevant}) == 1
    ]
    # Each copy of an answer is on a page of its own.
    assert all(
        len({passages[p]["page"] for p in relevant}) == len(relevant)
        for relevant in copied
    )

    def mean(measure, search, k, questions=validation):
        run = runs[search]
        return sum(
            measure(run.get(question, []), judgments[question], k)
            for question in questions
        ) / len(questions)

    values = {
        "questions": str(len(validation)),
        "searches": str(len(runs)),
        "shown": str(SHOWN),
        "texts": str(TEXTS),
        "confident": str(CONFIDENT),
        "k": str(K),
        "depth": str(DEPTH),
        "copies": str(sum(len(relevant) > 1 for relevant in judgments.values())),
        "one_text": str(len(copied)),
        "fused_once_first": f"{mean(hit_rate, 'fused-once', 1):.3f}",
        "reranked_first": f"{mean(hit_rate, 'reranked', 1):.3f}",
    }
    for search in TABLE:
        name = search.replace("-", "_")
        values[f"{name}_hit"] = f"{mean(hit_rate, search, K):.3f}"
        values[f"{name}_recall"] = f"{mean(recall, search, K):.3f}"
        values[f"{name}_rr"] = f"{mean(reciprocal_rank, search, DEPTH):.3f}"
        values[f"{name}_ndcg"] = f"{mean(ndcg, search, DEPTH):.3f}"
    shown = [question for question in validation if question in runs["confident"]]
    values["empty"] = str(len(validation) - len(shown))
    assert mean(hit_rate, "reranked", 1) < mean(hit_rate, "fused-once", 1)
    left_out = mean(hit_rate, "confident", K, shown)
    assert left_out > mean(hit_rate, "reranked", K) > mean(hit_rate, "confident", K)
    values["confident_left_out"] = f"{left_out:.3f}"
    return values
