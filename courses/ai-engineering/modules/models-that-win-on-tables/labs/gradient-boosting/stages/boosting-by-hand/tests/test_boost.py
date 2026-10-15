import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingClassifier

from boost import CATEGORIES, boost, boost_score, encode, start


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    return [
        (encode(part, categories), (part["subscribed"] == "yes").to_numpy())
        for part in (train, validation)
    ]


@pytest.mark.id("tst_xex9dx")
def test_start():
    """The log-odds of the share of yes"""
    assert start(np.array([True, False, False, False])) == pytest.approx(np.log(1 / 3))


@pytest.mark.id("tst_qodzwf")
def test_by_hand():
    """One round worked by hand"""
    X = np.array([[0.0], [1.0], [2.0], [3.0]])
    said_yes = np.array([False, False, True, True])
    model = boost(X, said_yes, 1, 1.0, 1)
    # Every share starts at 0.5, so the residuals are -0.5 and 0.5, and each leaf's value is
    # the sum of its two residuals over twice 0.25.
    assert model["start"] == pytest.approx(0.0)
    assert boost_score(model, X) == pytest.approx([-2.0, -2.0, 2.0, 2.0])


@pytest.mark.id("tst_11qwe1")
def test_scikit_learn(calls):
    """The training calls scored as scikit-learn's GradientBoostingClassifier scores them"""
    (X, said_yes), _ = calls
    for rounds, rate, depth in [(30, 0.1, 3), (20, 0.3, 2)]:
        model = boost(X, said_yes, rounds, rate, depth)
        reference = GradientBoostingClassifier(
            n_estimators=rounds, learning_rate=rate, max_depth=depth, random_state=0
        ).fit(X, said_yes)
        np.testing.assert_allclose(
            boost_score(model, X), reference.decision_function(X), rtol=0, atol=1e-9
        )


@pytest.mark.id("tst_uadfa0")
def test_no_rounds(calls):
    """A model of no rounds scores every row at the start"""
    (X, said_yes), (V, _) = calls
    model = boost(X, said_yes, 0, 0.1, 3)
    assert model["trees"] == [] and model["values"] == []
    np.testing.assert_array_equal(
        boost_score(model, V), np.full(len(V), start(said_yes))
    )


@pytest.mark.id("tst_mc9hap")
def test_new_rows(calls):
    """New rows scored by each tree's values for them"""
    (X, said_yes), (V, _) = calls
    model = boost(X, said_yes, 5, 0.2, 2)
    steps = zip(model["trees"], model["values"], strict=True)
    expected = start(said_yes) + 0.2 * sum(
        values[tree.apply(V)] for tree, values in steps
    )
    np.testing.assert_allclose(boost_score(model, V), expected, rtol=0, atol=1e-12)
