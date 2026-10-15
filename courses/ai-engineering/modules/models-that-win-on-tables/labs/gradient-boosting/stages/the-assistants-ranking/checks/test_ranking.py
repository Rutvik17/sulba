import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import log_loss

from ranking import call_list, encode, fit, said_yes

# The validation calls scored one at a time.
ALONE = 20


@pytest.fixture(scope="module")
def bank():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    model, categories = fit(train, validation)
    return train, validation, model, categories


@pytest.mark.id("tst_7coqi4")
def test_alone(bank):
    """The same chance for a client alone as among others"""
    _, validation, model, categories = bank
    together = model.predict_proba(encode(validation, categories))[:, 1]
    alone = [
        model.predict_proba(encode(validation.iloc[[i]], categories))[0, 1]
        for i in range(ALONE)
    ]
    np.testing.assert_allclose(alone, together[:ALONE], rtol=0, atol=1e-6)


@pytest.mark.id("tst_2yex6u")
def test_stopped_on_validation(bank):
    """Early stopping on the validation calls"""
    _, validation, model, categories = bank
    # XGBoost names the sets it watches validation_0, validation_1 and so on, and stops early
    # on the last.
    results = model.evals_result()
    watched = results[f"validation_{len(results) - 1}"]["logloss"]
    kept = model.best_iteration + 1
    V = encode(validation, categories)
    shares = model.predict_proba(V, iteration_range=(0, kept))[:, 1].astype(float)
    loss = log_loss(said_yes(validation), shares)
    assert watched[model.best_iteration] == pytest.approx(loss, rel=0, abs=1e-6)


@pytest.mark.id("tst_w6f60p")
def test_chances_add_up(bank):
    """Chances that add up to the subscriptions"""
    train, _, model, categories = bank
    chances = model.predict_proba(encode(train, categories))[:, 1].astype(float)
    # The standard deviation of a count of yes from calls with these chances.
    spread = np.sqrt((chances * (1 - chances)).sum())
    assert abs(chances.sum() - said_yes(train).sum()) < 3 * spread


@pytest.mark.id("tst_w5rvyv")
def test_ranked_by_chance(bank):
    """The clients ranked by their chance of subscribing"""
    _, validation, model, categories = bank
    ranked = call_list(model, categories, validation)
    chances = model.predict_proba(encode(validation, categories))[:, 1]
    given = ranked["chance"].reindex(validation.index).to_numpy()
    np.testing.assert_allclose(given, chances, rtol=0, atol=1e-6)
    assert (np.diff(ranked["chance"].to_numpy()) <= 0).all()
