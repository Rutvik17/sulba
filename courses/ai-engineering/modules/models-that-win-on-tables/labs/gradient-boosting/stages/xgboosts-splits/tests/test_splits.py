import json

import numpy as np
import pandas as pd
import pytest
from xgboost import XGBClassifier

from boost import CATEGORIES, best_split, encode, gradients, leaf_weight, split_gain


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    train = table[table["set"] == 0]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    return encode(train, categories), (train["subscribed"] == "yes").to_numpy()


def grown(X, said_yes, depth, lam):
    """XGBoost's first tree, its nodes by id, and the share it starts every row at."""
    model = XGBClassifier(
        n_estimators=1, max_depth=depth, learning_rate=1.0, reg_lambda=lam, n_jobs=1
    )
    booster = model.fit(X, said_yes).get_booster()
    config = json.loads(booster.save_config())
    base = float(config["learner"]["learner_model_param"]["base_score"])
    return booster.trees_to_dataframe().set_index("ID"), base


@pytest.mark.id("tst_q607wn")
def test_gradients():
    """Gradients and hessians of the log loss"""
    g, h = gradients(np.array([True, False]), np.array([0.25, 0.75]))
    assert g == pytest.approx([-0.75, 0.75])
    assert h == pytest.approx([0.1875, 0.1875])


@pytest.mark.id("tst_b7mics")
def test_by_hand():
    """A leaf's weight and a split's gain worked by hand, and the first of equal splits"""
    g = np.array([-1.0, -1.0, 1.0, 1.0])
    h = np.array([0.5, 0.5, 0.5, 0.5])
    left = np.array([True, True, False, False])
    assert leaf_weight(g[left], h[left], 1.0) == pytest.approx(1.0)
    # Each part: 2 squared over 1 + 1; all four rows: 0 squared over 2 + 1.
    assert split_gain(g, h, left, 1.0) == pytest.approx(4.0)
    twice = np.column_stack([[0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 2.0, 3.0]])
    assert best_split(twice, g, h, 1.0, 0.0) == pytest.approx((0, 2.0, 4.0))


@pytest.mark.id("tst_1to6ud")
def test_first_split(calls):
    """XGBoost's first split, its gain and its leaves' weights"""
    X, said_yes = calls
    for lam in [1.0, 5.0]:
        nodes, base = grown(X, said_yes, 1, lam)
        g, h = gradients(said_yes, np.full(len(said_yes), base))
        column, threshold, gain = best_split(X, g, h, lam, 1.0)
        root = nodes.loc["0-0"]
        assert f"f{column}" == root["Feature"]
        assert threshold == pytest.approx(root["Split"])
        assert gain == pytest.approx(root["Gain"], rel=1e-5)
        left = X[:, column] < threshold
        for rows, leaf in [(left, root["Yes"]), (~left, root["No"])]:
            weight = leaf_weight(g[rows], h[rows], lam)
            assert weight == pytest.approx(nodes.loc[leaf, "Gain"], rel=1e-5)


@pytest.mark.id("tst_giv2e5")
def test_second_level(calls):
    """The splits XGBoost makes below its first"""
    X, said_yes = calls
    nodes, base = grown(X, said_yes, 2, 1.0)
    g, h = gradients(said_yes, np.full(len(said_yes), base))
    column, threshold, _ = best_split(X, g, h, 1.0, 1.0)
    left = X[:, column] < threshold
    root = nodes.loc["0-0"]
    for rows, child in [(left, root["Yes"]), (~left, root["No"])]:
        column, threshold, gain = best_split(X[rows], g[rows], h[rows], 1.0, 1.0)
        node = nodes.loc[child]
        assert f"f{column}" == node["Feature"]
        assert threshold == pytest.approx(node["Split"])
        assert gain == pytest.approx(node["Gain"], rel=1e-5)


@pytest.mark.id("tst_66ncia")
def test_light_part():
    """A split that leaves a part too light is skipped"""
    X = np.array([[0.0], [1.0], [2.0], [3.0]])
    g = np.array([-1.0, 0.2, 0.2, 0.2])
    h = np.array([0.1, 0.5, 0.5, 0.5])
    # Splitting off the first row gains most, but leaves a part with a hessian of 0.1.
    assert best_split(X, g, h, 1.0, 0.0)[1] == 1.0
    assert best_split(X, g, h, 1.0, 0.5)[1] == 2.0
