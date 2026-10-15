import numpy as np
import pytest

from strength import StrengthModel


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


def inside(sets):
    """Which test mixes have every measurement inside the training mixes' ranges."""
    X, X_test = sets[0][0], sets[2][0]
    return ((X_test >= X.min(axis=0)) & (X_test <= X.max(axis=0))).all(axis=1)


@pytest.mark.id("tst_chmseo")
def test_within_seven(sets, shipped, record_property):
    """Within 7 MPa on the new mixes it accepts"""
    X_test, y_test = sets[2]
    accepted = inside(sets)
    strengths = np.asarray(shipped.predict(X_test[accepted].copy()), dtype=float)
    error = float(np.sqrt(np.mean((y_test[accepted] - strengths) ** 2)))
    record_property("note", f"RMSE {error:.2f} MPa on {int(accepted.sum())} tests")
    assert error <= 7


@pytest.mark.id("tst_v3ur0z")
def test_refuses_outside(sets, shipped, record_property):
    """Refuses the new mixes outside its ranges"""
    X_test = sets[2][0]
    accepted = inside(sets)
    said = np.asarray(shipped.accepts(X_test.copy()), dtype=bool)
    record_property("note", f"Refused {int((~said).sum())} of {len(X_test)} tests")
    assert said.tolist() == accepted.tolist()
    with pytest.raises(ValueError):
        shipped.predict(X_test[~accepted][:1].copy())


@pytest.mark.id("tst_rjzses")
def test_one_mix(sets, shipped):
    """One mix at a time"""
    X_test = sets[2][0]
    mix = X_test[inside(sets)][0].copy()
    strengths = np.asarray(shipped.predict(mix), dtype=float).reshape(-1)
    assert strengths.shape == (1,)
    assert np.isfinite(strengths[0])
