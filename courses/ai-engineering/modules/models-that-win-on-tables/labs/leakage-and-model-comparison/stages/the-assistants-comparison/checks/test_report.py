import numpy as np
import pandas as pd
import pytest
from scipy.stats import t
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier

from report import (
    SHARES,
    columns,
    fold_scores,
    interval,
    shares,
    standard_error,
    with_pairs,
)

# The checks' calls: every seventh of the training and validation calls.
EVERY = 7
# Differences on 25 folds, drawn once, and the folds' calls fitted on and held out.
DIFFERENCES = np.random.default_rng(1).normal(0.004, 0.012, 25)
N_FIT, N_HELD = 3294, 824


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].iloc[::EVERY].reset_index(drop=True)
    calls = with_pairs(calls)
    return calls, (calls["subscribed"] == "yes").to_numpy(dtype=int)


@pytest.mark.id("tst_btjwbe")
def test_held_answers(calls):
    """No held-out call's answer in the shares"""
    calls, said_yes = calls
    rows = np.arange(len(calls))
    fit, held = rows[rows % 5 != 0], rows[rows % 5 == 0]
    _, before = shares(calls, said_yes, fit, held)
    flipped = said_yes.copy()
    flipped[held] = 1 - flipped[held]
    _, after = shares(calls, flipped, fit, held)
    np.testing.assert_array_equal(before[SHARES], after[SHARES])


@pytest.mark.id("tst_drga9n")
def test_same_folds(calls):
    """A model and its copy, scored on the same folds"""
    calls, said_yes = calls
    tree = make_pipeline(
        columns(False), DecisionTreeClassifier(max_depth=3, random_state=0)
    )
    scores = fold_scores({"one": tree, "two": tree}, calls, said_yes, repeats=1)
    np.testing.assert_array_equal(scores["one"], scores["two"])


@pytest.mark.id("tst_2n7kn8")
def test_standard_error():
    """A standard error that allows for the calls the folds share"""
    n = len(DIFFERENCES)
    wanted = np.sqrt(np.var(DIFFERENCES, ddof=1) * (1 / n + N_HELD / N_FIT))
    assert standard_error(DIFFERENCES, N_FIT, N_HELD) == pytest.approx(
        wanted, rel=1e-12
    )


@pytest.mark.id("tst_e9dtbl")
def test_interval():
    """A 95% interval"""
    low, high = interval(DIFFERENCES, N_FIT, N_HELD, 0.95)
    quantile = t.ppf(0.975, len(DIFFERENCES) - 1)
    half = quantile * standard_error(DIFFERENCES, N_FIT, N_HELD)
    assert low == pytest.approx(DIFFERENCES.mean() - half, rel=1e-12)
    assert high == pytest.approx(DIFFERENCES.mean() + half, rel=1e-12)
