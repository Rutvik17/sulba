import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeClassifier

from report import (
    K,
    SHARES,
    columns,
    fold_scores,
    interval,
    shares,
    with_pairs,
)

# The tests' calls: every seventh of the training and validation calls.
EVERY = 7


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].iloc[::EVERY].reset_index(drop=True)
    calls = with_pairs(calls)
    return calls, (calls["subscribed"] == "yes").to_numpy(dtype=int)


@pytest.mark.id("tst_g7actl")
def test_pairs():
    """Each call's job and education as one pair"""
    calls = pd.DataFrame(
        {"job": ["admin.", "retired"], "education": ["basic.4y", "unknown"]}
    )
    assert with_pairs(calls)["pair"].tolist() == ["admin./basic.4y", "retired/unknown"]


@pytest.mark.id("tst_7hht48")
def test_shares(calls):
    """Shares between 0 and 1 for the fit calls and the held calls"""
    calls, said_yes = calls
    fit, held = np.arange(400), np.arange(400, len(calls))
    fit_calls, held_calls = shares(calls, said_yes, fit, held)
    assert len(fit_calls) == len(fit) and len(held_calls) == len(held)
    for frame in [fit_calls, held_calls]:
        assert ((frame[SHARES] > 0) & (frame[SHARES] < 1)).all().all()


@pytest.mark.id("tst_sk8crq")
def test_fold_scores(calls):
    """An AUC for each model on every fold"""
    calls, said_yes = calls
    tree = make_pipeline(
        columns(False), DecisionTreeClassifier(max_depth=2, random_state=0)
    )
    scores = fold_scores({"tree": tree}, calls, said_yes, repeats=1)
    assert scores.shape == (K, 1)
    assert ((scores >= 0) & (scores <= 1)).all().all()


@pytest.mark.id("tst_zxk93u")
def test_interval():
    """An interval around the mean, wider at 99% than at 95%"""
    differences = np.random.default_rng(0).normal(0.01, 0.02, 25)
    low, high = interval(differences, 3200, 800, 0.95)
    wide_low, wide_high = interval(differences, 3200, 800, 0.99)
    assert low < differences.mean() < high
    assert wide_low < low and high < wide_high
