"""The help desk's report on its searches: each search's hit rate at K and nDCG at DEPTH on
the test questions, as a reader sees its passages, over every question and in each service,
and each search's gain in hit rate over the current one, with the gain's p-value."""

import csv
import math
from collections import defaultdict

import numpy as np

K = 5
DEPTH = 10
REPEATS = 10_000


def read_runs(
    questions: set[str], path: str = "data/runs.csv"
) -> dict[str, dict[str, list[str]]]:
    """Each search's passages for each of the questions it shows any for, best first."""
    runs: dict[str, dict[str, list[str]]] = defaultdict(dict)
    with open(path, encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in questions:
                run = runs[row["search"]]
                run.setdefault(row["question"], []).append(row["passage"])
    return runs


def first_passages(texts: dict[str, str]) -> dict[str, str]:
    """Each passage's text, as the first passage that holds it."""
    first: dict[str, str] = {}
    for passage, text in texts.items():
        first.setdefault(text, passage)
    return {passage: first[text] for passage, text in texts.items()}


def as_seen(shown: list[str], first: dict[str, str]) -> list[str | None]:
    """The passages shown as a reader sees them: each text once."""
    return list(dict.fromkeys(first[passage] for passage in shown))


def relevant_texts(relevant: set[str], first: dict[str, str]) -> set[str]:
    return {first[passage] for passage in relevant}


def hit_rate(seen: list[str | None], answers: set[str], k: int) -> float:
    return 1.0 if any(text in answers for text in seen[:k]) else 0.0


def ndcg(seen: list[str | None], answers: set[str], k: int) -> float:
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, text in enumerate(seen[:k], start=1)
        if text in answers
    )
    best = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(answers)) + 1))
    return dcg / best if best else 0.0


def scores(
    run: dict[str, list[str]], judgments: dict[str, set[str]], first: dict[str, str]
) -> dict[str, tuple[float, float]]:
    """Each question's hit rate at K and nDCG at DEPTH."""
    found = {}
    for question, shown in run.items():
        seen = as_seen(shown, first)
        answers = relevant_texts(judgments[question], first)
        found[question] = (
            hit_rate(seen, answers, K),
            ndcg(seen, judgments[question], DEPTH),
        )
    return found


def randomization_test(a: np.ndarray, b: np.ndarray, rng: np.random.Generator) -> float:
    """The two-sided p-value of the difference between a's mean and b's."""
    observed = abs(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    count = 0
    for _ in range(REPEATS):
        shuffled = rng.permutation(pooled)
        count += abs(shuffled[: len(a)].mean() - shuffled[len(a) :].mean()) >= observed
    return (1 + count) / (1 + REPEATS)


def report(
    runs: dict[str, dict[str, list[str]]],
    current: str,
    judgments: dict[str, set[str]],
    first: dict[str, str],
    services: dict[str, str],
    rng: np.random.Generator,
) -> dict[str, dict[str, dict[str, float]]]:
    """For each search, its hit rate and nDCG over every question, as "all", and in each
    service; and for every search but the current one, its gain in hit rate over the
    current search and the gain's p-value, among "all"'s values."""
    base = scores(runs[current], judgments, first)
    out = {}
    for search, run in runs.items():
        found = scores(run, judgments, first)
        groups = {"all": list(found)}
        for question in found:
            groups.setdefault(services[question], []).append(question)
        out[search] = {
            name: {
                "hit_rate": float(np.mean([found[q][0] for q in questions])),
                "ndcg": float(np.mean([found[q][1] for q in questions])),
            }
            for name, questions in groups.items()
        }
        if search != current:
            common = [question for question in found if question in base]
            a = np.array([found[question][0] for question in common])
            b = np.array([base[question][0] for question in common])
            out[search]["all"]["gain"] = float(a.mean() - b.mean())
            out[search]["all"]["p"] = randomization_test(a, b, rng)
    return out
