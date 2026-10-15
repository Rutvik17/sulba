import numpy as np
import pytest

from strength import StrengthModel, model


@pytest.fixture(scope="module")
def sets():
    """The lab's training, validation and test tests, each (X, y)."""
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    part, y, X = table[:, 0], table[:, 2], table[:, 3:]
    return tuple((X[part == p], y[part == p]) for p in (0, 1, 2))


@pytest.fixture(scope="module")
def shipped(sets):
    train, validation, _ = sets
    return StrengthModel(
        tuple(array.copy() for array in train),
        tuple(array.copy() for array in validation),
    )


@pytest.mark.id("tst_9gdxki")
def test_chosen_on_validation(shipped):
    """Chooses the degree and penalty on the validation mixes"""
    assert (shipped.degree, shipped.penalty) == (3, 1e-4)


@pytest.mark.id("tst_v9j9ee")
def test_strengths(sets, shipped):
    """Gives the strengths of the model it chose, fit on the training mixes"""
    (X, y), _, (X_test, _) = sets
    inside = ((X_test >= X.min(axis=0)) & (X_test <= X.max(axis=0))).all(axis=1)
    expected = model(3, 1e-4, len(y)).fit(X, y).predict(X_test[inside])
    strengths = np.asarray(shipped.predict(X_test[inside].copy()), dtype=float)
    assert strengths.shape == expected.shape
    assert np.max(np.abs(strengths - expected)) <= 1e-6


@pytest.mark.id("tst_rtx8y7")
def test_edges_accepted(sets, shipped):
    """Accepts mixes at the edges of the ranges"""
    X = sets[0][0]
    edges = np.array([X.min(axis=0), X.max(axis=0)])
    assert np.asarray(shipped.accepts(edges)).tolist() == [True, True]
    assert np.asarray(shipped.predict(edges)).shape == (2,)


@pytest.mark.id("tst_ufowa3")
def test_just_past_a_range(sets, shipped):
    """Refuses a mix just past a range"""
    X = sets[0][0]
    mixes = np.array([X[0], X[0], X[0]])
    mixes[1, 0] = X[:, 0].max() + 0.1
    assert np.asarray(shipped.accepts(mixes)).tolist() == [True, False, True]
    with pytest.raises(ValueError):
        shipped.predict(mixes)
