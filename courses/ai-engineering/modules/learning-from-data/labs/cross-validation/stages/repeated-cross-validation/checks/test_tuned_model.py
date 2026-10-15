import numpy as np
import pytest

from tuning import TunedModel, records


@pytest.fixture(scope="module")
def table():
    return np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)


@pytest.fixture(scope="module")
def shipped(table):
    return TunedModel(*(part.copy() for part in records(table.copy())))


@pytest.mark.id("tst_tp8t97")
def test_within_eight(table, shipped, record_property):
    """Within 8 MPa on the test set"""
    test = table[:, 0] == 2
    strengths = np.asarray(shipped.predict(table[test, 3:].copy()), dtype=float)
    error = float(np.sqrt(np.mean((table[test, 2] - strengths) ** 2)))
    record_property("note", f"RMSE {error:.2f} MPa on {int(test.sum())} tests")
    assert error <= 8


@pytest.mark.id("tst_qlwmr0")
def test_same_choice_with_other_shuffles(table, shipped, record_property):
    """The same choice with other shuffles"""
    other = TunedModel(*(part.copy() for part in records(table.copy())), seeds=(2, 3))
    record_property(
        "note",
        f"Degree {shipped.degree} with {shipped.penalty:g}, then degree {other.degree} with "
        f"{other.penalty:g}",
    )
    assert (other.degree, other.penalty) == (shipped.degree, shipped.penalty)


@pytest.mark.id("tst_1jx6zu")
def test_one_mix(table, shipped):
    """One mix at a time"""
    mix = table[table[:, 0] == 2][0, 3:].copy()
    strengths = np.asarray(shipped.predict(mix), dtype=float).reshape(-1)
    assert strengths.shape == (1,)
    assert np.isfinite(strengths[0])
