import numpy as np
import pytest

from bootstrap import paired_difference


@pytest.fixture(scope="module")
def rules():
    """Whether each of the clinic's rules is right about each new sample: the nearer class
    mean, and the nearest record."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    records, new = table[table[:, 0] == 0], table[table[:, 0] == 1]
    mean, std = records[:, 2:].mean(axis=0), records[:, 2:].std(axis=0)
    Z, Z_new = (records[:, 2:] - mean) / std, (new[:, 2:] - mean) / std
    malignant = Z[records[:, 1] == 1].mean(axis=0)
    benign = Z[records[:, 1] == 0].mean(axis=0)
    nearer = np.sum((Z_new - malignant) ** 2, axis=1) < np.sum(
        (Z_new - benign) ** 2, axis=1
    )
    distances = np.sum((Z_new[:, None, :] - Z[None, :, :]) ** 2, axis=2)
    nearest = records[np.argmin(distances, axis=1), 1] == 1
    labels = new[:, 1] == 1
    return nearer == labels, nearest == labels


@pytest.mark.id("tst_xsodan")
def test_by_hand():
    """One model right wherever the other is wrong"""
    right = np.ones(50, dtype=bool)
    assert paired_difference(right, ~right, 0.95, 999, np.random.default_rng(0)) == (
        1,
        1,
    )
    assert paired_difference(~right, right, 0.95, 999, np.random.default_rng(0)) == (
        -1,
        -1,
    )


@pytest.mark.id("tst_wyh813")
def test_clinic(rules):
    """An interval around the clinic's rules' difference"""
    low, high = paired_difference(*rules, 0.95, 9999, np.random.default_rng(1))
    measured = np.mean(rules[0]) - np.mean(rules[1])
    assert low < measured < high


@pytest.mark.id("tst_mn6lv0")
def test_reproducible(rules):
    """The same seed gives the same interval"""
    first = paired_difference(*rules, 0.95, 999, np.random.default_rng(2))
    assert first == paired_difference(*rules, 0.95, 999, np.random.default_rng(2))


@pytest.mark.id("tst_hdta1j")
def test_wider_for_more_confidence():
    """A higher confidence gives a wider interval"""
    rng = np.random.default_rng(3)
    right_a = rng.random(500) < 0.8
    right_b = np.where(rng.random(500) < 0.1, ~right_a, right_a)
    narrow = paired_difference(right_a, right_b, 0.8, 9999, np.random.default_rng(4))
    wide = paired_difference(right_a, right_b, 0.99, 9999, np.random.default_rng(4))
    assert wide[0] < narrow[0] and narrow[1] < wide[1]
