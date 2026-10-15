import numpy as np
import pandas as pd
import pytest

from ranking import CATEGORIES, NUMBERS, ROUNDS, call_list, encode, fit, said_yes


@pytest.fixture(scope="module")
def bank():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    model, categories = fit(train, validation)
    return train, validation, model, categories


@pytest.mark.id("tst_jkvonc")
def test_said_yes():
    """1 for yes and 0 for no"""
    calls = pd.DataFrame({"subscribed": ["yes", "no", "no"]})
    assert said_yes(calls).tolist() == [1, 0, 0]


@pytest.mark.id("tst_tr6wyq")
def test_encode(bank):
    """The numbers as they are, then a whole number for each category column"""
    train, _, _, categories = bank
    calls = train.head(50)
    X = encode(calls, categories)
    assert X.shape == (50, len(NUMBERS) + len(CATEGORIES))
    np.testing.assert_array_equal(X[:, : len(NUMBERS)], calls[NUMBERS])
    codes = X[:, len(NUMBERS) :]
    assert (codes == np.round(codes)).all()
    assert (codes >= 0).all()


@pytest.mark.id("tst_g1r9bu")
def test_fit(bank):
    """At most ROUNDS rounds, and the training calls' categories"""
    train, _, model, categories = bank
    assert model.get_booster().num_boosted_rounds() <= ROUNDS
    assert categories == {name: sorted(train[name].unique()) for name in CATEGORIES}


@pytest.mark.id("tst_fx78kl")
def test_call_list(bank):
    """Every client once, each with a chance, from the highest down"""
    _, validation, model, categories = bank
    ranked = call_list(model, categories, validation)
    assert sorted(ranked.index) == sorted(validation.index)
    chances = ranked["chance"].to_numpy()
    assert ((chances >= 0) & (chances <= 1)).all()
    assert (np.diff(chances) <= 0).all()
