import numpy as np
import pytest

from gate import gate

PAGES = [f"page-{number // 3}" for number in range(60)]


def releases():
    rng = np.random.default_rng(5)
    ease = rng.random((60, 1))
    return (rng.random((60, 5)) < ease).astype(float), ease


@pytest.mark.id("tst_s9l5bh")
def test_broken_release():
    """Stops a release whose replies cite nothing"""
    baseline, _ = releases()
    verdict = gate(baseline, np.zeros_like(baseline), PAGES, 0.05)
    assert not verdict.ships
    assert verdict.change < 0


@pytest.mark.id("tst_srnjze")
def test_same_release():
    """Ships a release that scores as the baseline did"""
    baseline, _ = releases()
    verdict = gate(baseline, baseline.copy(), PAGES, 0.05)
    assert verdict.ships
    assert verdict.change == 0


@pytest.mark.id("tst_wpuxnm")
def test_interval():
    """Puts the change inside its interval"""
    baseline, ease = releases()
    candidate = (np.random.default_rng(6).random((60, 5)) < ease - 0.1).astype(float)
    verdict = gate(baseline, candidate, PAGES, 0.05)
    assert verdict.low < verdict.change < verdict.high
    assert verdict.high - verdict.change == pytest.approx(verdict.change - verdict.low)
