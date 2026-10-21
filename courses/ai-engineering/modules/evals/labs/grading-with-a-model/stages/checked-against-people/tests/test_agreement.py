import json
from pathlib import Path

import numpy as np
import pytest

from agreement import accuracy, auc, best_threshold, kappa

RECORDED = json.loads(Path("references/agreement.json").read_text(encoding="utf-8"))[
    "cases"
]


@pytest.mark.id("tst_soc239")
def test_accuracy_and_kappa():
    """scikit-learn's accuracy and Cohen's kappa for a grader's verdicts"""
    for case in RECORDED:
        labels, verdicts = np.array(case["labels"]), np.array(case["verdicts"])
        assert accuracy(labels, verdicts) == pytest.approx(case["accuracy"], abs=1e-12)
        assert kappa(labels, verdicts) == pytest.approx(case["kappa"], abs=1e-12)


@pytest.mark.id("tst_hflu31")
def test_auc():
    """scikit-learn's ROC AUC for a grader's scores, ties included"""
    for case in RECORDED:
        labels, scores = np.array(case["labels"]), np.array(case["scores"])
        assert auc(labels, scores) == pytest.approx(case["auc"], abs=1e-12)


@pytest.mark.id("tst_6e1vsb")
def test_chance():
    """Gives a kappa of 0 to a grader that agrees only as often as chance would"""
    labels = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    verdicts = np.array([1, 0, 1, 0, 1, 0, 1, 0])
    assert accuracy(labels, verdicts) == 0.5
    assert kappa(labels, verdicts) == pytest.approx(0)


@pytest.mark.id("tst_q24ffr")
def test_best_threshold():
    """Chooses the lowest score that gives the highest kappa"""
    labels = np.array([0, 0, 0, 1, 1, 1])
    scores = np.array([0.1, 0.2, 0.3, 0.35, 0.8, 0.9])
    assert best_threshold(labels, scores) == 0.35
    tied = np.array([0, 1, 0, 1])
    assert best_threshold(tied, np.array([0.2, 0.6, 0.4, 0.9])) == 0.6
