import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold, cross_val_score

from compare import BASELINE, differences, fold_scores, models

# The calls the tests compare on, and their folds.
CALLS, K = 900, 3


@pytest.fixture(scope="module")
def calls():
    table = pd.read_csv("data/calls.csv")
    calls = table[table["set"] < 2].head(CALLS).reset_index(drop=True)
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    folds = StratifiedKFold(K, shuffle=True, random_state=0)
    return calls, said_yes, list(folds.split(calls, said_yes))


def two():
    built = models()
    return {name: built[name] for name in [BASELINE, "decision tree"]}


@pytest.mark.id("tst_2mndfi")
def test_cross_val_score(calls):
    """Each model's AUCs as cross_val_score gives them"""
    calls, said_yes, splits = calls
    scores = fold_scores(two(), calls, said_yes, splits)
    for name, model in two().items():
        wanted = cross_val_score(model, calls, said_yes, cv=splits, scoring="roc_auc")
        np.testing.assert_allclose(scores[name], wanted, rtol=0, atol=1e-12)


@pytest.mark.id("tst_twcy45")
def test_shape(calls):
    """A row per split and a column per model, in their order"""
    calls, said_yes, splits = calls
    scores = fold_scores(two(), calls, said_yes, splits)
    assert list(scores.columns) == [BASELINE, "decision tree"]
    assert len(scores) == K


@pytest.mark.id("tst_tmpnqb")
def test_fresh(calls):
    """Each model fitted afresh, and the models given left unfitted"""
    calls, said_yes, splits = calls
    given = two()
    fold_scores(given, calls, said_yes, splits)
    for model in given.values():
        assert not hasattr(model[-1], "classes_")


@pytest.mark.id("tst_29ciz0")
def test_differences():
    """Differences from the baseline by hand"""
    scores = pd.DataFrame(
        {BASELINE: [0.70, 0.80], "decision tree": [0.65, 0.85], "forest": [0.72, 0.80]}
    )
    found = differences(scores, BASELINE)
    assert list(found.columns) == ["decision tree", "forest"]
    np.testing.assert_allclose(
        found.to_numpy(), [[-0.05, 0.02], [0.05, 0.0]], atol=1e-12
    )
