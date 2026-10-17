import numpy as np
import pytest
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from features import features, stays
from model import chosen, make_chosen


@pytest.fixture(scope="module")
def table():
    return stays("data/encounters.csv")


@pytest.fixture(scope="module")
def shipped(table):
    """1,000 of the stays, the model chosen fitted to a copy of them, and the copy afterwards."""
    rows = table.sample(1000, random_state=0)
    given = rows.copy()
    return rows, chosen(given), given


@pytest.mark.id("tst_hqr6rt")
def test_new_and_unfitted():
    """make_chosen gives a new, unfitted model each time"""
    first, second = make_chosen(), make_chosen()
    assert first is not second
    with pytest.raises(NotFittedError):
        check_is_fitted(first)


@pytest.mark.id("tst_a5fv0y")
def test_fitted_to_every_stay(shipped):
    """chosen fits a model from make_chosen to every stay it's given"""
    rows, model, _ = shipped
    expected = make_chosen().fit(features(rows), rows["readmitted"])
    assert np.allclose(
        model.predict_proba(features(rows)),
        expected.predict_proba(features(rows)),
        rtol=0,
        atol=1e-9,
    )


@pytest.mark.id("tst_5e8wl4")
def test_rows_untouched(shipped):
    """Leaves the stays it's given as they were"""
    rows, _, given = shipped
    assert given.equals(rows)


@pytest.mark.id("tst_hbz2ao")
def test_probability_of_a_readmission(table, shipped):
    """Gives each stay its probability of a readmission"""
    _, model, _ = shipped
    probabilities = model.predict_proba(features(table.head(20)))
    assert probabilities.shape == (20, 2)
    assert list(model.classes_) == [False, True]
    assert np.all((probabilities >= 0) & (probabilities <= 1))
