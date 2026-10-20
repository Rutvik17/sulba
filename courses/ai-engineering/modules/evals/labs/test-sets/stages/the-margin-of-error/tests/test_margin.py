import json
from pathlib import Path

import numpy as np
import pytest

from margin import clustered_standard_error, margin, standard_error

RECORDED = json.loads(Path("references/errors.json").read_text(encoding="utf-8"))[
    "cases"
]


@pytest.mark.id("tst_wqmmdy")
def test_standard_error():
    """statsmodels' standard error of the mean, for independent scores"""
    for case in RECORDED:
        found = standard_error(np.array(case["scores"]))
        assert found == pytest.approx(case["standard_error"], rel=1e-9)


@pytest.mark.id("tst_3szj2k")
def test_clustered_standard_error():
    """statsmodels' standard error of the mean, with each cluster's scores counted together"""
    for case in RECORDED:
        found = clustered_standard_error(np.array(case["scores"]), case["clusters"])
        assert found == pytest.approx(case["clustered_standard_error"], rel=1e-9)


@pytest.mark.id("tst_qu7zrm")
def test_intervals():
    """statsmodels' intervals, at 95% and 90%, either way"""
    for case in RECORDED:
        scores = np.array(case["scores"])
        errors = {
            "interval": standard_error(scores),
            "clustered_interval": clustered_standard_error(scores, case["clusters"]),
        }
        for name, error in errors.items():
            for confidence in (0.95, 0.9):
                reach = margin(error, confidence)
                low, high = case[f"{name}_{round(confidence * 100)}"]
                assert scores.mean() - reach == pytest.approx(low, rel=1e-9)
                assert scores.mean() + reach == pytest.approx(high, rel=1e-9)


@pytest.mark.id("tst_0jiq1c")
def test_clusters_of_one():
    """The same standard error either way when each score is a cluster of its own"""
    scores = np.array([1.0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0])
    clusters = [f"page-{number}" for number in range(len(scores))]
    assert clustered_standard_error(scores, clusters) == pytest.approx(
        standard_error(scores)
    )
    shuffled = [clusters[number] for number in (3, 0, 7, 1, 11, 2, 9, 4, 10, 5, 8, 6)]
    assert clustered_standard_error(scores, shuffled) == pytest.approx(
        standard_error(scores)
    )
