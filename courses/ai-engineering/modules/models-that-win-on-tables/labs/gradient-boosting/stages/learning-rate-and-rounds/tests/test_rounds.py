import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import log_loss
from xgboost import XGBClassifier

from boost import CATEGORIES, encode, losses, stop_early


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    return [
        (encode(part, categories), (part["subscribed"] == "yes").to_numpy())
        for part in (train, validation)
    ]


@pytest.mark.id("tst_wbq6qh")
def test_losses(calls):
    """The log loss after each round"""
    (X, said_yes), (V, validation_yes) = calls
    model = GradientBoostingClassifier(
        n_estimators=20, learning_rate=0.3, max_depth=2, random_state=0
    ).fit(X, said_yes)
    found = losses(model, V, validation_yes)
    expected = [
        log_loss(validation_yes, shares[:, 1])
        for shares in model.staged_predict_proba(V)
    ]
    assert len(found) == 20
    np.testing.assert_allclose(found, expected, rtol=0, atol=1e-12)


@pytest.mark.id("tst_ggws6b")
def test_by_hand():
    """Stopping worked by hand"""
    history = [0.5, 0.4, 0.3, 0.3, 0.35, 0.36, 0.2]
    # The least loss is the third round's, which the fourth only equals; with a patience of 3,
    # three rounds in a row pass without a lower loss before the seventh.
    assert stop_early(history, 3) == 3
    assert stop_early(history, 4) == 7
    assert stop_early([0.5, 0.4, 0.3], 5) == 3


@pytest.mark.id("tst_waxh3h")
def test_xgboost(calls):
    """The rounds XGBoost keeps when it stops early"""
    (X, said_yes), (V, validation_yes) = calls
    for rate, patience in [(0.1, 20), (0.3, 10)]:
        settings = {
            "n_estimators": 300,
            "learning_rate": rate,
            "max_depth": 3,
            "n_jobs": 1,
        }
        watched = {"eval_set": [(V, validation_yes)], "verbose": False}
        full = XGBClassifier(**settings).fit(X, said_yes, **watched)
        history = full.evals_result()["validation_0"]["logloss"]
        stopped = XGBClassifier(**settings, early_stopping_rounds=patience)
        stopped.fit(X, said_yes, **watched)
        assert stop_early(history, patience) == stopped.best_iteration + 1


@pytest.mark.id("tst_1d392e")
def test_never_lower():
    """A history that never falls keeps one round"""
    assert stop_early([0.3, 0.3, 0.4, 0.5], 2) == 1
