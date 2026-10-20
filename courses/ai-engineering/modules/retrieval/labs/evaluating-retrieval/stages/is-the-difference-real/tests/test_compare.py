import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pytest

from compare import bootstrap_interval, randomization_test
from measures import hit_rate

RECORDED = json.loads(Path("references/comparisons.json").read_text(encoding="utf-8"))
FOUND = np.array([1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1], dtype=float)
MISSED = np.array([0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1], dtype=float)


@pytest.mark.id("tst_qx3ts8")
def test_same_results():
    """Two searches with the same results: p of 1, and an interval at 0"""
    rng = np.random.default_rng(0)
    assert randomization_test(FOUND, FOUND, 1000, rng) == 1
    assert bootstrap_interval(FOUND, FOUND, 0.95, 1000, rng) == (0, 0)


@pytest.mark.id("tst_cvdknk")
def test_both_ways():
    """The same p-value with the searches either way round, and never 0"""
    one = randomization_test(FOUND, MISSED, 2000, np.random.default_rng(3))
    other = randomization_test(MISSED, FOUND, 2000, np.random.default_rng(3))
    assert one == other
    far = np.ones(40)
    assert (
        randomization_test(far, np.zeros(40), 999, np.random.default_rng(1)) == 1 / 1000
    )


@pytest.mark.id("tst_20mk5o")
def test_exact_p_values():
    """Close to SciPy's exact p-values, from every way of swapping each question's values"""
    for case in RECORDED["tests"]:
        a, b = np.array(case["a"]), np.array(case["b"])
        found = randomization_test(a, b, 40_000, np.random.default_rng(7))
        assert found == pytest.approx(case["p"], abs=0.015)


class Drawn:
    """A generator that gives the rows of the questions SciPy's resamples drew."""

    def __init__(self, rows):
        self.rows = np.array(rows)

    def integers(self, low, high, size):
        assert (low, high, tuple(size)) == (0, self.rows.shape[1], self.rows.shape)
        return self.rows


@pytest.mark.id("tst_p8gv99")
def test_intervals():
    """SciPy's percentile intervals, from the same resamples of the questions"""
    for case in RECORDED["intervals"]:
        a, b, rows = np.array(case["a"]), np.array(case["b"]), case["rows"]
        found = bootstrap_interval(a, b, case["confidence"], len(rows), Drawn(rows))
        assert found == pytest.approx(case["interval"], abs=1e-12)


@pytest.fixture(scope="module")
def hits():
    """Each search's hit rate at 5 for each test question."""
    runs = defaultdict(dict)
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            runs[row["search"]].setdefault(row["question"], []).append(row["passage"])
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        tests = [
            row["question"] for row in csv.DictReader(file) if row["set"] == "test"
        ]
    relevant = defaultdict(set)
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            relevant[row["question"]].add(row["passage"])
    return {
        search: np.array([hit_rate(run.get(q, []), relevant[q], 5) for q in tests])
        for search, run in runs.items()
    }


@pytest.mark.id("tst_mfxay1")
def test_reranker(hits):
    """The reranker's gain in hit rate on the test questions is clear"""
    a, b = hits["reranked"], hits["fused-once"]
    assert randomization_test(a, b, 10_000, np.random.default_rng(0)) < 0.05
    assert bootstrap_interval(a, b, 0.95, 10_000, np.random.default_rng(0))[0] > 0


@pytest.mark.id("tst_q7h1p8")
def test_each_text_once(hits):
    """Each text once gains no clear hit rate on the test questions"""
    a, b = hits["reranked"], hits["reranked-copies"]
    assert randomization_test(a, b, 10_000, np.random.default_rng(0)) > 0.05
    assert bootstrap_interval(a, b, 0.95, 10_000, np.random.default_rng(0))[0] <= 0
