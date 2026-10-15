import numpy as np
import pandas as pd
import pytest

from line import estimated_accuracy, sort_batch


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    measurements = list(table.columns[2:])
    parts = [table[table["set"] == number] for number in (0, 1)]
    return [
        (part[measurements].to_numpy(), part["variety"].to_numpy()) for part in parts
    ]


@pytest.mark.id("tst_8t87ho")
def test_every_bean(beans):
    """A variety for every bean of a batch"""
    (train, varieties), (validation, _) = beans
    named = sort_batch(train, varieties, validation)
    assert len(named) == len(validation)
    assert set(named) <= set(varieties)


@pytest.mark.id("tst_kuziff")
def test_validation_beans(beans):
    """Most validation beans named right"""
    (train, varieties), (validation, truth) = beans
    assert (sort_batch(train, varieties, validation) == truth).mean() > 0.85


@pytest.mark.id("tst_l9yxla")
def test_training_beans(beans):
    """Each training bean named by itself, with one neighbour"""
    (train, varieties), _ = beans
    a, v = train[:300], varieties[:300]
    np.testing.assert_array_equal(sort_batch(a, v, a, k=1), v)


@pytest.mark.id("tst_fbqcjo")
def test_estimate(beans):
    """The estimate a share of the training beans"""
    (train, varieties), _ = beans
    assert 0 <= estimated_accuracy(train[:300], varieties[:300]) <= 1
