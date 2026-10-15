import numpy as np
import pytest

import tuning
from cv import features, fold_errors


@pytest.fixture(scope="module")
def records():
    """The plant's records: (X, y, mixes)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    kept = table[:, 0] < 2
    return table[kept, 3:], table[kept, 2], table[kept, 1]


@pytest.fixture(scope="module")
def some_mixes(records):
    """The records of mixes 200 to 299, on which the checks redo the job's work."""
    X, y, mixes = records
    some = (mixes >= 200) & (mixes < 300)
    return X[some], y[some], mixes[some]


def rmse(y, y_hat):
    return float(np.sqrt(np.mean((y - y_hat) ** 2)))


@pytest.mark.id("tst_6dc1ir")
def test_test_set_stays_out(records):
    """The test set stays out of the records it tunes and fits on"""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    X, y, mixes = (
        np.asarray(part, dtype=float) for part in tuning.records(table.copy())
    )
    expected_X, expected_y, expected_mixes = records
    assert X.shape == expected_X.shape
    assert np.array_equal(X, expected_X)
    assert np.array_equal(y, expected_y)
    assert np.array_equal(mixes, expected_mixes)


@pytest.mark.id("tst_yge40q")
def test_folds_keep_mixes_whole(records):
    """No fold splits a mix"""
    mixes = records[2]
    for fit, held in tuning.splits(mixes.copy()):
        assert np.intersect1d(mixes[fit], mixes[held]).size == 0


@pytest.mark.id("tst_p3uha8")
def test_each_fold_standardized_on_its_fit_tests(some_mixes):
    """Each fold is standardized with its own fit tests, as yours were"""
    X, y, mixes = some_mixes
    found = tuning.scores(X.copy(), y.copy(), mixes.copy())
    splits = tuning.splits(mixes.copy())
    for degree in tuning.DEGREES:
        errors = np.asarray(
            fold_errors(features(X, degree), y, splits, tuning.PENALTIES)
        )
        for j, penalty in enumerate(tuning.PENALTIES):
            assert found[degree, penalty] == pytest.approx(
                errors[:, j].mean(), abs=1e-9
            )


@pytest.mark.id("tst_comtjs")
def test_expected_error_counts_the_choice(some_mixes):
    """The expected error comes from nested cross-validation, the choice made afresh in
    each fold"""
    X, y, mixes = some_mixes
    errors = []
    for fit, held in tuning.splits(mixes.copy()):
        degree, penalty = tuning.choose(tuning.scores(X[fit], y[fit], mixes[fit]))
        model = tuning.fitted(features(X[fit], degree), y[fit], penalty)
        errors.append(rmse(y[held], model(features(X[held], degree))))
    expected = tuning.expected_error(X.copy(), y.copy(), mixes.copy())
    assert expected == pytest.approx(np.mean(errors), abs=1e-9)
