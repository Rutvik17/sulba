import numpy as np
import pandas as pd
import pytest
from sklearn.tree import DecisionTreeClassifier

from tree import best_split, gini

NUMBERS = ["age", "campaign", "pdays", "previous"]
# Six calls by a column's values, and whether each said yes.
COLUMN = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
SAID_YES = np.array([False, False, True, False, True, True])


@pytest.mark.id("tst_nhizqd")
def test_gini():
    """Impurities worked by hand"""
    assert gini(0, 10) == 0
    assert gini(10, 10) == 0
    assert gini(5, 10) == 0.5
    assert abs(gini(1, 4) - 0.375) < 1e-12
    np.testing.assert_allclose(gini(np.array([1, 2]), np.array([4, 4])), [0.375, 0.5])


@pytest.mark.id("tst_15wfe9")
def test_by_hand():
    """A split worked by hand, the lower of two tied thresholds taken"""
    threshold, impurity = best_split(COLUMN, SAID_YES, 1)
    assert threshold == 2.5
    assert abs(impurity - 0.25) < 1e-12


@pytest.mark.id("tst_yuai79")
def test_equal_values():
    """Equal values kept on one side"""
    column = np.array([1.0, 1.0, 1.0, 2.0, 2.0, 3.0])
    said_yes = np.array([False, False, True, True, True, True])
    threshold, impurity = best_split(column, said_yes, 1)
    assert threshold == 1.5
    assert abs(impurity - 2 / 9) < 1e-12


@pytest.mark.id("tst_hl9g1o")
def test_min_leaf():
    """At least min_leaf calls on each side, or no split"""
    threshold, impurity = best_split(COLUMN, SAID_YES, 3)
    assert threshold == 3.5
    assert abs(impurity - 4 / 9) < 1e-12
    assert best_split(COLUMN, SAID_YES, 4) is None
    assert best_split(np.full(6, 7.0), SAID_YES, 1) is None


@pytest.mark.id("tst_7uu13h")
def test_scikit_learn():
    """Each number column's best split on the training calls, matched to scikit-learn"""
    table = pd.read_csv("data/calls.csv")
    train = table[table["set"] == 0]
    said_yes = (train["subscribed"] == "yes").to_numpy()
    for name in NUMBERS:
        column = train[name].to_numpy(dtype=float)
        for min_leaf in [1, 25]:
            stump = DecisionTreeClassifier(max_depth=1, min_samples_leaf=min_leaf)
            nodes = stump.fit(column[:, None], said_yes).tree_
            counts, impurities = nodes.n_node_samples, nodes.impurity
            expected = (counts[1] * impurities[1] + counts[2] * impurities[2]) / counts[
                0
            ]
            threshold, impurity = best_split(column, said_yes, min_leaf)
            assert threshold == nodes.threshold[0]
            assert abs(impurity - expected) < 1e-12
