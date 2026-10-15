import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from forest import importances

CALLS = pd.DataFrame(
    {
        "a": [0.1, 0.4, 0.35, 0.8, 0.2, 0.9],
        "b": [1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
        "c": ["x", "y", "x", "y", "x", "y"],
    }
)
SAID_YES = np.array([False, False, True, True, False, True])


def expected(score, groups, repeats, seed):
    """The falls worked out as the brief describes them."""
    rng = np.random.default_rng(seed)
    base = roc_auc_score(SAID_YES, score(CALLS))
    found = {}
    for name, columns in groups.items():
        falls = []
        for _ in range(repeats):
            order = rng.permutation(len(CALLS))
            shuffled = CALLS.copy()
            for column in columns:
                shuffled[column] = CALLS[column].to_numpy()[order]
            falls.append(base - roc_auc_score(SAID_YES, score(shuffled)))
        found[name] = (np.mean(falls), np.std(falls))
    return found


def close(found, wanted):
    assert list(found) == list(wanted)
    for name in wanted:
        np.testing.assert_allclose(found[name], wanted[name], rtol=0, atol=1e-12)


@pytest.mark.id("tst_i3uqoo")
def test_by_hand():
    """Each column shuffled in turn, from one generator"""

    def score(calls):
        return calls["a"].to_numpy()

    groups = {"a": ["a"], "b": ["b"]}
    found = importances(score, CALLS, SAID_YES, groups, 3, np.random.default_rng(1))
    close(found, expected(score, groups, 3, 1))
    assert found["b"] == (0.0, 0.0)


@pytest.mark.id("tst_s62f0a")
def test_together():
    """A group's columns shuffled together, in one order"""

    def score(calls):
        return calls["a"].to_numpy() * calls["b"].to_numpy()

    groups = {"both": ["a", "b"], "c": ["c"]}
    found = importances(score, CALLS, SAID_YES, groups, 2, np.random.default_rng(7))
    close(found, expected(score, groups, 2, 7))


@pytest.mark.id("tst_fkbn88")
def test_unchanged():
    """The calls left as they were"""
    kept = CALLS.copy()

    def score(calls):
        return calls["a"].to_numpy()

    importances(score, CALLS, SAID_YES, {"a": ["a"]}, 2, np.random.default_rng(3))
    pd.testing.assert_frame_equal(CALLS, kept)
