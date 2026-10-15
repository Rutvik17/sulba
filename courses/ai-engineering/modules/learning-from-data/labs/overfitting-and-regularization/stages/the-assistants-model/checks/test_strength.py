import numpy as np
import pytest
from sklearn.metrics import root_mean_squared_error

from model import features, ridge, standardize
from strength import DEGREES, PENALTIES, choose, expected_error, model, split


@pytest.fixture(scope="module")
def sets():
    """The lab's training, validation and test tests, each (X, y, mixes)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, mix, y, X = table[:, 0], table[:, 1], table[:, 2], table[:, 3:]
    return tuple((X[part == p], y[part == p], mix[part == p]) for p in (0, 1, 2))


@pytest.fixture(scope="module")
def records(sets):
    """The plant's records, the training and validation tests together, as (X, y, mixes)."""
    return tuple(np.concatenate(columns) for columns in zip(sets[0], sets[1]))


@pytest.mark.id("tst_cse1qk")
def test_same_strengths(sets):
    """The same strengths as the model you validated"""
    (X, y, _), _, (X_test, _, _) = sets
    fitted = model(3, 1e-4, len(y)).fit(X.copy(), y.copy())
    P_train, P_test = standardize(features(X, 3), features(X_test, 3))
    w, b = ridge(P_train, y, 1e-4)
    yours = P_test @ np.asarray(w, dtype=float) + b
    assert np.max(np.abs(fitted.predict(X_test) - yours)) <= 1e-6


@pytest.mark.id("tst_x4pxul")
def test_chooses_by_the_validation_mixes(sets):
    """Chooses by the validation mixes"""
    (X, y, _), (X_val, y_val, _), _ = sets
    errors = {}
    for degree in DEGREES:
        for penalty in PENALTIES:
            fitted = model(degree, penalty, len(y)).fit(X, y)
            errors[degree, penalty] = root_mean_squared_error(
                y_val, fitted.predict(X_val)
            )
    chosen = choose((X.copy(), y.copy()), (X_val.copy(), y_val.copy()))
    assert tuple(chosen) == min(errors, key=errors.get)


@pytest.mark.id("tst_rhg4fy")
def test_held_out_mixes(records):
    """Holds out whole mixes"""
    mixes = records[2]
    fit, new = split(mixes.copy())
    assert len(new) > 0
    assert not set(mixes[fit]) & set(mixes[new])


@pytest.mark.id("tst_1sbebq")
def test_scores_tests_it_didnt_fit(records):
    """Scores only tests it didn't fit"""
    X, y, mixes = records
    fit, new = split(mixes.copy())
    fitted = model(3, 1e-4, len(fit)).fit(X[fit], y[fit])
    expected = root_mean_squared_error(y[new], fitted.predict(X[new]))
    error = expected_error(X.copy(), y.copy(), mixes.copy(), 3, 1e-4)
    assert error == pytest.approx(expected, abs=1e-9)
