import numpy as np
import pytest
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from features import features, stays
from model import make_chosen
from train import SHARE, train


@pytest.fixture(scope="module")
def table():
    return stays("data/encounters.csv")


@pytest.fixture(scope="module")
def trained():
    return train("data/encounters.csv")


@pytest.fixture(scope="module")
def new_stays(table):
    """Each stay's probability from a model that didn't learn from it, as a new patient's
    will be: out of fold, over the folds cross_validated uses."""
    folds = StratifiedKFold(5, shuffle=True, random_state=0)
    return cross_val_predict(
        make_chosen(),
        features(table),
        table["readmitted"],
        cv=folds,
        method="predict_proba",
    )[:, 1]


@pytest.mark.id("tst_m1gcps")
def test_expected_calls(table, trained, new_stays):
    """The planners expect the recall and precision new stays get"""
    y = table["readmitted"].to_numpy()
    called = new_stays >= trained["threshold"]
    caught = np.sum(called & y)
    assert trained["recall"] == pytest.approx(caught / y.sum(), abs=0.01)
    assert trained["precision"] == pytest.approx(caught / called.sum(), abs=0.01)


@pytest.mark.id("tst_sy7lg7")
def test_calls_the_share(trained, new_stays):
    """It calls the planners' share of new stays"""
    assert np.mean(new_stays >= trained["threshold"]) == pytest.approx(SHARE, abs=0.01)


@pytest.mark.id("tst_ws5x23")
def test_fitted_on_every_stay(table, trained):
    """The model learned from every stay"""
    inputs = features(table)
    expected = make_chosen().fit(inputs, table["readmitted"]).predict_proba(inputs)
    assert np.allclose(
        trained["model"].predict_proba(inputs), expected, rtol=0, atol=1e-9
    )
