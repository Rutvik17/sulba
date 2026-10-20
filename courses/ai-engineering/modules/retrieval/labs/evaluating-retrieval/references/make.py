# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.5.4", "ranx==0.3.21", "scipy==1.18.1"]
# [tool.uv]
# exclude-newer = "2026-10-19T00:00:00Z"
# ///
"""Records how ranx measures rankings and how SciPy compares two sets of results, for the lab's
tests. ranx's other dependencies are those released before 19 October 2026.

measures.json holds ranx's hit rate, recall, reciprocal rank and nDCG at each cutoff, for each
of 300 made-up questions and their means, and for every tenth question of each of the help
desk's searches in runs.csv, with each search's means over the validation and the test
questions. A question no passage is shown for scores 0, and so does one with no relevant
passage. ranx is given each ranking as scores that fall by 1 a rank, so that no tie is left
for it to break.

comparisons.json holds SciPy's percentile interval for the mean of a minus the mean of b, with
the questions resampled in pairs, and the rows of the questions each resample drew; and SciPy's
exact two-sided p-value for the same difference, from every way of swapping each question's two
values.

    uv run make.py <folder to write in> <folder of the lab's data>
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import ranx
from scipy import stats

CUTOFFS = (1, 3, 5, 10, 20)
RUN_CUTOFFS = (5, 10, 20)
MEASURES = {
    "hit_rate": "hit_rate",
    "recall": "recall",
    "reciprocal_rank": "mrr",
    "ndcg": "ndcg",
}
QUESTIONS = 300
POOL = 40
EVERY = 10


def measured(
    shown: dict[str, list[str]], relevant: dict[str, set[str]], cutoffs: tuple[int, ...]
) -> dict[str, dict[str, dict[int, float]]]:
    """ranx's value of each measure at each cutoff for each question in `relevant`."""
    qrels = ranx.Qrels(
        {
            question: {passage: 1 for passage in passages} if passages else {"none": 0}
            for question, passages in relevant.items()
        }
    )
    run = ranx.Run(
        {
            question: {
                passage: float(len(passages) - rank)
                for rank, passage in enumerate(passages)
            }
            for question, passages in shown.items()
            if passages
        }
    )
    metrics = [f"{name}@{k}" for name in MEASURES.values() for k in cutoffs]
    values = ranx.evaluate(qrels, run, metrics, return_mean=False, make_comparable=True)
    order = list(qrels.keys())
    out: dict[str, dict[str, dict[int, float]]] = {
        question: {} for question in relevant
    }
    for measure, name in MEASURES.items():
        for question in relevant:
            out[question][measure] = {}
        for k in cutoffs:
            for question, value in zip(order, values[f"{name}@{k}"], strict=True):
                out[question][measure][k] = float(value)
    return out


def means(values: dict[str, dict[str, dict[int, float]]], questions: list[str]) -> dict:
    measures = values[questions[0]]
    return {
        measure: {
            str(k): float(
                np.mean([values[question][measure][k] for question in questions])
            )
            for k in measures[measure]
        }
        for measure in measures
    }


def made_up() -> dict:
    rng = np.random.default_rng(0)
    pool = [f"d{number}" for number in range(1, POOL + 1)]
    shown, relevant = {}, {}
    for number in range(1, QUESTIONS + 1):
        question = f"x{number}"
        count = int(rng.integers(0, 9))
        relevant[question] = {
            str(passage) for passage in rng.choice(pool, count, replace=False)
        }
        length = int(rng.choice([0, 2, 5, 10, 20]))
        shown[question] = [
            str(passage) for passage in rng.choice(pool, length, replace=False)
        ]
    values = measured(shown, relevant, CUTOFFS)
    return {
        "questions": [
            {
                "question": question,
                "shown": shown[question],
                "relevant": sorted(relevant[question]),
                "values": {
                    measure: {str(k): value for k, value in by_k.items()}
                    for measure, by_k in values[question].items()
                },
            }
            for question in relevant
        ],
        "means": means(values, list(relevant)),
    }


def searches(data: Path) -> dict:
    with open(data / "questions.csv", encoding="utf-8", newline="") as file:
        questions = list(csv.DictReader(file))
    relevant: dict[str, set[str]] = {
        question["question"]: set() for question in questions
    }
    with open(data / "relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row["passage"])
    runs: dict[str, dict[str, list[str]]] = defaultdict(dict)
    with open(data / "runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            runs[row["search"]].setdefault(row["question"], []).append(row["passage"])
    sets = defaultdict(list)
    for question in questions:
        sets[question["set"]].append(question["question"])
    picked = [question["question"] for question in questions][::EVERY]
    out = {}
    for search, run in runs.items():
        values = measured(run, relevant, RUN_CUTOFFS)
        out[search] = {
            "questions": {
                question: {
                    measure: {str(k): value for k, value in by_k.items()}
                    for measure, by_k in values[question].items()
                }
                for question in picked
            },
            "means": {name: means(values, members) for name, members in sets.items()},
        }
    return out


def difference(a: np.ndarray, b: np.ndarray, axis: int) -> np.ndarray:
    return np.mean(a, axis=axis) - np.mean(b, axis=axis)


def comparisons() -> dict:
    rng = np.random.default_rng(1)
    intervals = []
    for case, (count, results, repeats) in enumerate(
        [
            (12, "scores", 999),
            (30, "scores", 999),
            (50, "scores", 500),
            (12, "found", 999),
            (60, "found", 500),
        ]
    ):
        a = rng.random(count)
        b = np.clip(a + rng.normal(-0.05, 0.25, count), 0, 1)
        if results == "found":
            a, b = (a > 0.4).astype(float), (b > 0.4).astype(float)
        confidence = (0.95, 0.9)[case % 2]
        seed = 100 + case
        result = stats.bootstrap(
            (a, b),
            difference,
            paired=True,
            vectorized=True,
            n_resamples=repeats,
            confidence_level=confidence,
            method="percentile",
            rng=np.random.default_rng(seed),
        )
        interval = result.confidence_interval
        # The rows SciPy drew: the same call on the same generator gives the same interval.
        rows = np.random.default_rng(seed).integers(0, count, size=(repeats, count))
        drawn = np.quantile(
            a[rows].mean(axis=1) - b[rows].mean(axis=1),
            [(1 - confidence) / 2, (1 + confidence) / 2],
        )
        assert np.allclose(drawn, [interval.low, interval.high], rtol=0, atol=1e-12)
        intervals.append(
            {
                "a": a.tolist(),
                "b": b.tolist(),
                "confidence": confidence,
                "rows": rows.tolist(),
                "interval": [float(interval.low), float(interval.high)],
            }
        )
    tests = []
    for count, shift in ((8, 0.0), (10, 0.1), (12, 0.15), (12, 0.0)):
        a = rng.random(count)
        b = a - shift + rng.normal(0, 0.2, count)
        result = stats.permutation_test(
            (a, b),
            difference,
            permutation_type="samples",
            n_resamples=np.inf,
            vectorized=True,
            alternative="two-sided",
        )
        tests.append({"a": a.tolist(), "b": b.tolist(), "p": float(result.pvalue)})
    return {"intervals": intervals, "tests": tests}


def main(out: Path, data: Path) -> None:
    recorded = {"made_up": made_up(), "searches": searches(data)}
    with open(out / "measures.json", "w", encoding="utf-8", newline="\n") as file:
        json.dump(recorded, file)
        file.write("\n")
    with open(out / "comparisons.json", "w", encoding="utf-8", newline="\n") as file:
        json.dump(comparisons(), file)
        file.write("\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
