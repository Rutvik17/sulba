import csv
import math
from collections import defaultdict

import numpy as np

K = 5
DEPTH = 10
TEXTS = 20
REPEATS = 10_000
CONFIDENCE = 0.95
LEVEL = 0.05
# Each question's nDCG is resampled as a whole number of these steps, so that the sums are
# exact and come out the same on every system.
SCALE = 2**40
FULL = "reranked"
PARTS = {
    "reranker": "fused-once",
    "bm25": "reranked-vectors",
    "vectors": "reranked-bm25",
    "once": "reranked-copies",
}
SERVICES = ["dmv", "ssa", "studentaid", "va"]


def signed(value):
    text = f"{value:.3f}"
    return "0.000" if text == "-0.000" else text.replace("-", "−")


def hit_rate(shown, relevant, k):
    return float(any(passage in relevant for passage in shown[:k]))


def ndcg(shown, relevant, k):
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, passage in enumerate(shown[:k], start=1)
        if passage in relevant
    )
    best = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    return dcg / best


def compared(a, b, rng):
    """a's mean less b's, its percentile interval and its randomization test's p-value, from
    whole numbers a question."""
    differences = a - b
    n = len(differences)
    signs = 1 - 2 * rng.integers(0, 2, size=(REPEATS, n))
    flipped = np.abs(signs @ differences)
    p = (1 + np.count_nonzero(flipped >= abs(differences.sum()))) / (1 + REPEATS)
    rows = rng.integers(0, n, size=(REPEATS, n))
    sums = differences[rows].sum(axis=1)
    low, high = np.quantile(
        sums / n / SCALE, [(1 - CONFIDENCE) / 2, (1 + CONFIDENCE) / 2]
    )
    return differences.sum() / n / SCALE, low, high, p


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
        tests = [row for row in csv.DictReader(file) if row["set"] == "test"]
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(first[texts[row["passage"]]])

    def seen(shown):
        out, before = [], set()
        for passage in shown:
            text = first[texts[passage]]
            out.append(None if text in before else text)
            before.add(text)
        return out

    def values(search, measure, k, questions):
        run = runs[search]
        found = [
            measure(seen(run.get(q["question"], [])), relevant[q["question"]], k)
            for q in questions
        ]
        return np.array([round(value * SCALE) for value in found], dtype=np.int64)

    rng = np.random.default_rng(0)
    out = {
        "test": str(len(tests)),
        "k": str(K),
        "depth": str(DEPTH),
        "texts": str(TEXTS),
        "repeats": f"{REPEATS:,}",
        "confidence": f"{CONFIDENCE:.0%}",
        "level": str(LEVEL),
    }
    full_hit = values(FULL, hit_rate, K, tests)
    full_ndcg = values(FULL, ndcg, DEPTH, tests)
    out["full_hit"] = f"{full_hit.mean() / SCALE:.3f}"
    out["full_ndcg"] = f"{full_ndcg.mean() / SCALE:.3f}"
    tested = []
    for part, search in PARTS.items():
        for name, full, measure, k in (
            ("hit", full_hit, hit_rate, K),
            ("ndcg", full_ndcg, ndcg, DEPTH),
        ):
            other = values(search, measure, k, tests)
            gain, low, high, p = compared(full, other, rng)
            tested.append(p)
            if name == "hit":
                # Every part but each text once adds more than chance would.
                assert (p < LEVEL and low > 0) == (part != "once")
            if part == "once" and name == "ndcg":
                # No resample is as far from 0: the smallest p-value the resamples give.
                assert p == 1 / (1 + REPEATS)
            if part == "once":
                out[f"once_{name}_better"] = str(np.count_nonzero(full > other))
                out[f"once_{name}_worse"] = str(np.count_nonzero(full < other))
            out[f"{part}_{name}"] = f"{other.mean() / SCALE:.3f}"
            out[f"{part}_{name}_gain"] = signed(gain)
            out[f"{part}_{name}_low"] = signed(low)
            out[f"{part}_{name}_high"] = signed(high)
            out[f"{part}_{name}_p"] = f"{p:.4f}"
    sizes, gained = [], {}
    for service in SERVICES:
        questions = [q for q in tests if q["domain"] == service]
        full = values(FULL, hit_rate, K, questions)
        other = values(PARTS["reranker"], hit_rate, K, questions)
        gain, low, high, p = compared(full, other, rng)
        tested.append(p)
        sizes.append(len(questions))
        gained[service] = int((full - other).sum() // SCALE)
        # Only dmv's interval leaves out 0.
        assert (low > 0) == (service == "dmv") and high > 0
        out[f"{service}_questions"] = str(len(questions))
        out[f"{service}_full"] = f"{full.mean() / SCALE:.3f}"
        out[f"{service}_other"] = f"{other.mean() / SCALE:.3f}"
        out[f"{service}_gain"] = signed(gain)
        out[f"{service}_low"] = signed(low)
        out[f"{service}_high"] = signed(high)
        out[f"{service}_p"] = f"{p:.4f}"
    assert gained["dmv"] > sum(gained.values()) / 2
    out["fewest"] = str(min(sizes))
    out["most"] = str(max(sizes))
    out["gained"] = str(sum(gained.values()))
    out["dmv_gained"] = str(gained["dmv"])
    out["tests"] = str(len(tested))
    out["by_chance"] = f"{1 - (1 - LEVEL) ** len(tested):.2f}"
    missed = sent = 0
    for question in tests:
        name = question["question"]
        answers = relevant[name]
        if hit_rate(seen(runs[FULL][name]), answers, K):
            continue
        missed += 1
        sent += not answers.isdisjoint(seen(runs[PARTS["reranker"]][name])[:TEXTS])
    out["missed"] = str(missed)
    out["never_sent"] = str(missed - sent)
    out["sent"] = str(sent)
    return out
