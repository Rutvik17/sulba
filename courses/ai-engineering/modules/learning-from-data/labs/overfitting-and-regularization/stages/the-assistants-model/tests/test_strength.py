import numpy as np
import pytest

from strength import DEGREES, PENALTIES, choose, expected_error, model


@pytest.fixture(scope="module")
def records():
    """The plant's records: the lab's training and validation tests, as
    (train, validation), each (X, y, mixes)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, mix, y, X = table[:, 0], table[:, 1], table[:, 2], table[:, 3:]
    return tuple((X[part == p], y[part == p], mix[part == p]) for p in (0, 1))


@pytest.mark.id("tst_pg0m9h")
def test_choice_from_the_grid(records):
    """Chooses a degree and penalty it tried"""
    train, validation = records
    degree, penalty = choose(train[:2], validation[:2])
    assert degree in DEGREES
    assert penalty in PENALTIES


@pytest.mark.id("tst_9loteh")
def test_a_strength_per_test(records):
    """A strength for each test"""
    (X, y, _), (X_val, _, _) = records
    fitted = model(2, 1e-3, len(y)).fit(X, y)
    assert fitted.predict(X_val).shape == (len(X_val),)


@pytest.mark.id("tst_3ubylu")
def test_error_in_megapascals(records):
    """An error in MPa"""
    X, y, mixes = (np.concatenate(columns) for columns in zip(*records))
    error = expected_error(X, y, mixes, 2, 1e-3)
    assert 0 < error < 20
