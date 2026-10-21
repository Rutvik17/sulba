import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

from compare import paired, unpaired

RECORDED = json.loads(Path("references/changes.json").read_text(encoding="utf-8"))[
    "cases"
]


@pytest.mark.id("tst_nzqlns")
def test_paired():
    """statsmodels' standard error of the questions' differences, each page's together"""
    for case in RECORDED:
        baseline, candidate = np.array(case["baseline"]), np.array(case["candidate"])
        differences = candidate.mean(axis=1) - baseline.mean(axis=1)
        for confidence in (0.95, 0.9):
            found = paired(baseline, candidate, case["pages"], confidence)
            z = NormalDist().inv_cdf((1 + confidence) / 2)
            assert found.change == pytest.approx(differences.mean(), abs=1e-12)
            assert found.margin == pytest.approx(z * case["change_error"], rel=1e-9)


@pytest.mark.id("tst_j8cof7")
def test_unpaired():
    """statsmodels' standard errors of the two scores, added as independent ones"""
    for case in RECORDED:
        baseline, candidate = np.array(case["baseline"]), np.array(case["candidate"])
        found = unpaired(baseline, candidate, case["pages"], 0.95)
        error = math.hypot(case["baseline_error"], case["candidate_error"])
        change = candidate.mean(axis=1).mean() - baseline.mean(axis=1).mean()
        assert found.change == pytest.approx(change, abs=1e-12)
        assert found.margin == pytest.approx(1.959963984540054 * error, rel=1e-9)


@pytest.mark.id("tst_93d6hb")
def test_same_questions():
    """Pairing takes out what the questions share, and unpairing doesn't"""
    rng = np.random.default_rng(3)
    ease = rng.random((200, 1))
    baseline = (rng.random((200, 5)) < ease).astype(float)
    candidate = (rng.random((200, 5)) < ease).astype(float)
    pages = [f"page-{number // 2}" for number in range(200)]
    together = paired(baseline, candidate, pages, 0.95).margin
    apart = unpaired(baseline, candidate, pages, 0.95).margin
    assert together < 0.7 * apart
