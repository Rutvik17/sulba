import numpy as np
import pandas as pd
import pytest

from groups import MEASUREMENTS, fewest_groups, make_up, name_beans

# How far each variety's share may lie from its share of the harvest, and the beans named
# alone.
TOLERANCE, ALONE = 0.03, 20


@pytest.fixture(scope="module")
def harvest():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0]
    harvest = table[table["set"] == 1]
    X = train[MEASUREMENTS].to_numpy(dtype=float)
    varieties = train["variety"].to_numpy()
    V = harvest[MEASUREMENTS].to_numpy(dtype=float)
    kept = V.copy()
    model, names = fewest_groups(X, varieties, 0)
    shares = make_up(model, names, X, V)
    return X, varieties, V, kept, harvest["variety"], model, names, shares


@pytest.mark.id("tst_6isx91")
def test_shares(harvest):
    """The harvest's make-up"""
    _, _, _, _, truth, _, _, shares = harvest
    wanted = truth.value_counts(normalize=True)
    for variety, share in wanted.items():
        assert abs(shares[variety] - share) <= TOLERANCE


@pytest.mark.id("tst_ifgmab")
def test_every_variety(harvest):
    """A share for every variety, adding up to 1"""
    _, varieties, _, _, _, _, _, shares = harvest
    assert list(shares) == sorted(set(varieties))
    assert sum(shares.values()) == pytest.approx(1)


@pytest.mark.id("tst_3bpvuc")
def test_alone(harvest):
    """A bean named alone as among the harvest"""
    X, _, V, _, _, model, names, _ = harvest
    together = name_beans(model, names, X, V)
    for i in range(ALONE):
        assert name_beans(model, names, X, V[i : i + 1])[0] == together[i]


@pytest.mark.id("tst_8xd046")
def test_unchanged(harvest):
    """The harvest left as it was"""
    _, _, V, kept, _, _, _, _ = harvest
    np.testing.assert_array_equal(V, kept)
