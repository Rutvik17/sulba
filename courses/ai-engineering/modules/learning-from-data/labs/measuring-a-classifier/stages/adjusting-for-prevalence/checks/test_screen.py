import time

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from report import Screen

SHARE = 0.02


@pytest.fixture(scope="module")
def table():
    return np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)


@pytest.fixture(scope="module")
def training(table):
    train = table[:, 0] == 0
    return table[train, 2:], table[train, 1]


@pytest.fixture(scope="module")
def drawn(table):
    """Candidates from the validation and test sets with 1 pulsar in 50: every other
    candidate, and pulsars drawn at random."""
    unseen = table[table[:, 0] > 0]
    others = np.flatnonzero(unseen[:, 1] == 0)
    count = round(len(others) * SHARE / (1 - SHARE))
    pulsars = np.random.default_rng(0).choice(
        np.flatnonzero(unseen[:, 1] == 1), count, replace=False
    )
    rows = np.sort(np.concatenate([others, pulsars]))
    return unseen[rows, 2:], unseen[rows, 1]


@pytest.mark.id("tst_7oysq4")
def test_calibrated_at_one_in_fifty(training, drawn, record_property):
    """Calibrated at 1 in 50"""
    X, y = drawn
    p = np.asarray(Screen(*training, SHARE).probabilities(X.copy()), dtype=float)
    record_property(
        "note", f"Expects {p.sum():.1f} pulsars, and there are {int(y.sum())}"
    )
    assert abs(p.sum() - y.sum()) <= 0.1 * y.sum()


@pytest.mark.id("tst_cr2prx")
def test_the_classifiers_order(table, training, record_property):
    """The classifier's order"""
    X = table[table[:, 0] == 2, 2:]
    model = make_pipeline(StandardScaler(), LogisticRegression()).fit(*training)
    order = np.argsort(model.predict_proba(X)[:, 1], kind="stable")
    p = np.asarray(Screen(*training, SHARE).probabilities(X.copy()), dtype=float)
    out_of_order = int(np.sum(np.diff(p[order]) < 0))
    record_property("note", f"{out_of_order} candidates out of the classifier's order")
    assert out_of_order == 0


@pytest.mark.id("tst_m1tffm")
def test_unchanged_at_its_own_share(table, training):
    """Unchanged at the training set's own share"""
    X_train, y_train = training
    X = table[table[:, 0] == 2, 2:]
    model = make_pipeline(StandardScaler(), LogisticRegression()).fit(X_train, y_train)
    p = Screen(X_train, y_train, float(np.mean(y_train))).probabilities(X.copy())
    expected = model.predict_proba(X)[:, 1]
    assert np.allclose(np.asarray(p, dtype=float), expected, rtol=0, atol=1e-9)


@pytest.mark.id("tst_em3wv0")
def test_fast_on_a_survey_night(table, training, record_property):
    """Fast on 100,000 candidates"""
    X = np.resize(table[table[:, 0] > 0, 2:], (100_000, 8))
    screen = Screen(*training, SHARE)
    started = time.perf_counter()
    chosen = screen.follow_ups(X, 500)
    seconds = time.perf_counter() - started
    record_property("note", f"{seconds:.2f} s for 500 follow-ups from 100,000")
    assert len(chosen) == 500
    assert seconds < 1
