import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

from gate import gate, spread
from samples import scores


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


QUESTIONS = read("questions.csv")
NAMES = [question["question"] for question in QUESTIONS]
PAGES = [question["page"] for question in QUESTIONS]
RELEVANT = defaultdict(set)
for row in read("relevant.csv"):
    RELEVANT[row["question"]].add(row["passage"])
REPLIES = read("replies.csv")
SAMPLES = [1, 2, 3, 4, 5]


def release(name, samples=SAMPLES):
    return scores(REPLIES, RELEVANT, NAMES, name, samples)


@pytest.mark.id("tst_eegk14")
def test_every_sample():
    """Measures the change on every sample of each question"""
    baseline = release("current")
    for name in ("three-passages", "unranked", "warmer"):
        candidate = release(name)
        verdict = gate(baseline, candidate, PAGES, 0.05)
        expected = (candidate.mean(axis=1) - baseline.mean(axis=1)).mean()
        assert verdict.change == pytest.approx(expected)


@pytest.mark.id("tst_h682ko")
def test_paired():
    """Takes the standard error of each question's difference"""
    baseline, candidate = release("current", [1]), release("unranked", [1])
    differences = (candidate - baseline)[:, 0]
    error = differences.std(ddof=1) / math.sqrt(len(differences))
    verdict = gate(baseline, candidate, NAMES, 0.05)
    reach = NormalDist().inv_cdf(0.95) * error
    assert verdict.high - verdict.change == pytest.approx(reach)


@pytest.mark.id("tst_xstw46")
def test_rerun():
    """Ships a rerun of the current release, either way round"""
    current, rerun = release("current"), release("rerun")
    assert gate(current, rerun, PAGES, 0.05).ships
    assert gate(rerun, current, PAGES, 0.05).ships


@pytest.mark.id("tst_ybm9u9")
def test_pages():
    """statsmodels' standard error, with each page's questions counted together"""
    recorded = json.loads(Path("references/changes.json").read_text(encoding="utf-8"))
    for case in recorded["cases"]:
        means = np.array(case["baseline"]).mean(axis=1)
        found = spread(means, case["pages"])
        assert found == pytest.approx(case["baseline_error"], rel=1e-9)
