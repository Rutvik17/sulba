import math
import time

import numpy as np
import pytest

from screener import Screener, best_threshold, precision_recall

# The limit, and the samples the clinic will give best_threshold.
LIMIT_S = 1.0
SAMPLES = 200_000


def speed_data(n):
    """n samples, about 37% malignant, with overlapping probabilities; the same each time."""
    rng = np.random.default_rng(n)
    y = (rng.random(n) < 0.37).astype(float)
    p = np.clip(rng.normal(0.3 + 0.4 * y, 0.18), 0.0, 1.0)
    return y, p


def timed(n):
    y, p = speed_data(n)
    start = time.perf_counter()
    best_threshold(y, p, 0.98)
    return time.perf_counter() - start


@pytest.mark.id("tst_e5sbjd")
def test_fast(record_property):
    """Fast on 200,000 samples"""
    # Slow code is timed on 2,000 and 8,000 samples, and its time on 200,000 worked out
    # from those, so a run stays well inside the browser's time limit.
    small = timed(2_000)
    if small > 0.1:
        took = small * 100
        note = f"{small:.2f} s on 2,000 samples, so at least {took:.1f} s on 200,000"
    else:
        mid = timed(8_000)
        growth = math.log(max(mid, 1e-4) / max(small, 1e-4)) / math.log(4)
        if mid > 0.001 and growth > 1.5:
            took = mid * 25**growth
            note = (
                f"{mid:.2f} s on 8,000 samples, and 4 times the samples took "
                f"{4**growth:.0f} times as long, so about {took:.0f} s on 200,000"
            )
        elif mid * 25 > LIMIT_S:
            took = mid * 25
            note = f"{mid:.2f} s on 8,000 samples, so at least {took:.1f} s on 200,000"
        else:
            took = timed(SAMPLES)
            note = f"{took:.2f} s on 200,000 samples"
    record_property("note", note)
    assert took < LIMIT_S


@pytest.fixture(scope="module")
def scored():
    """The test set's labels, and your screener's probabilities for it."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    screener = Screener().fit(X[~test].copy(), y[~test].copy())
    return y[test], np.asarray(screener.score(X[test].copy()), dtype=float).reshape(-1)


@pytest.mark.id("tst_edsjt3")
def test_inputs_unchanged(scored):
    """Leaves the arrays it is given unchanged"""
    y_test, p_test = scored
    y, p = y_test.copy(), p_test.copy()
    precision_recall(y, p, 0.3)
    best_threshold(y, p, 0.9)
    assert np.array_equal(y, y_test) and np.array_equal(p, p_test)
