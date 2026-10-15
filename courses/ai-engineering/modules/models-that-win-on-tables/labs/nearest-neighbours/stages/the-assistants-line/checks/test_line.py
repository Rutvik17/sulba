import numpy as np
import pandas as pd
import pytest

from line import estimated_accuracy, sort_batch

# The training beans the estimate and the tie checks use, and the batch with a gap.
BEANS, BATCH, GAP = 600, 10, 3


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    measurements = list(table.columns[2:])
    parts = [table[table["set"] == number] for number in (0, 1)]
    return [
        (part[measurements].to_numpy(), part["variety"].to_numpy()) for part in parts
    ]


@pytest.mark.id("tst_8vbebk")
def test_one_variety(beans):
    """A batch of one variety"""
    (train, varieties), (validation, truth) = beans
    bombay = validation[truth == "BOMBAY"]
    assert list(sort_batch(train, varieties, bombay)) == ["BOMBAY"] * len(bombay)


@pytest.mark.id("tst_qs7oj1")
def test_estimate(beans):
    """The estimate, each bean named by the others"""
    (train, varieties), _ = beans
    a, v = train[:BEANS], varieties[:BEANS]
    scaled = (a - a.mean(axis=0)) / a.std(axis=0)
    right = 0
    for i, bean in enumerate(scaled):
        distances = ((scaled - bean) ** 2).sum(axis=1)
        distances[i] = np.inf
        right += v[np.argsort(distances, kind="stable")[0]] == v[i]
    assert estimated_accuracy(a, v, k=1) == pytest.approx(right / BEANS, abs=1e-12)


@pytest.mark.id("tst_48f381")
def test_ties(beans):
    """Tied votes with two neighbours"""
    (train, varieties), _ = beans
    a, v = train[:BEANS], varieties[:BEANS]
    np.testing.assert_array_equal(sort_batch(a, v, a, k=2), v)


@pytest.mark.id("tst_jsjwer")
def test_missing_measurement(beans):
    """A bean measured only in part"""
    (train, varieties), (validation, _) = beans
    batch = validation[:BATCH].copy()
    batch[GAP, 5] = np.nan
    assert sort_batch(train, varieties, batch)[GAP] is None
