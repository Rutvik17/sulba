import csv
import math
from collections import Counter, defaultdict

K = 5
DEPTH = 10
TABLE = ["fused", "fused-once", "reranked", "reranked-copies"]


def recall(shown, relevant, k):
    return sum(passage in relevant for passage in shown[:k]) / len(relevant)


def ndcg(shown, relevant, k):
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, passage in enumerate(shown[:k], start=1)
        if passage in relevant
    )
    best = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    return dcg / best


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        texts = {row["passage"]: row["text"] for row in csv.DictReader(file)}
    first = {}
    for passage, text in texts.items():
        first.setdefault(text, passage)
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

    def seen(shown):
        out, before = [], set()
        for passage in shown:
            text = first[texts[passage]]
            out.append(None if text in before else text)
            before.add(text)
        return out

    def mean(measure, search, k, by_text):
        total = 0.0
        for question in validation:
            shown, relevant = runs[search][question], judgments[question]
            if by_text:
                shown, relevant = seen(shown), {first[texts[p]] for p in relevant}
            total += measure(shown, relevant, k)
        return total / len(validation)

    held = Counter(texts.values())
    values = {
        "passages": f"{len(texts):,}",
        "texts": f"{len(held):,}",
        "repeated": str(sum(count > 1 for count in held.values())),
        "questions": str(len(validation)),
        "k": str(K),
        "depth": str(DEPTH),
        "repeats": str(
            sum(None in seen(runs["fused"][question][:K]) for question in validation)
        ),
    }
    found = {}
    for search in TABLE:
        name = search.replace("-", "_")
        for by_text, way in ((False, "passage"), (True, "text")):
            found[search, way] = mean(ndcg, search, DEPTH, by_text)
            values[f"{name}_recall_{way}"] = f"{mean(recall, search, K, by_text):.3f}"
            values[f"{name}_ndcg_{way}"] = f"{found[search, way]:.3f}"
    # Judged by passage, the search that keeps copies comes first by nDCG; by text, the other.
    for copies, once in (("fused", "fused-once"), ("reranked-copies", "reranked")):
        assert found[copies, "passage"] > found[once, "passage"]
        assert found[copies, "text"] < found[once, "text"]
    return values
