import numpy as np
import pytest

from train import train

SAMPLES = 300


@pytest.fixture(scope="module")
def office():
    """Some of the training digits, and the validation digits."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    training = np.flatnonzero(sets == 0)[:SAMPLES]
    return pixels[training], digits[training], pixels[sets == 1], digits[sets == 1]


@pytest.fixture(scope="module")
def read(office):
    pixels, digits, _, _ = office
    return train(pixels, digits, np.random.default_rng(0))


@pytest.mark.id("tst_i7wtgs")
def test_reads_digits(office, read):
    """read gives a digit from 0 to 9 for each row"""
    _, _, pixels, _ = office
    found = np.asarray(read(pixels))
    assert found.shape == (len(pixels),)
    assert np.issubdtype(found.dtype, np.integer)
    assert found.min() >= 0 and found.max() <= 9


@pytest.mark.id("tst_dfa85k")
def test_one_digit(office, read):
    """read takes a batch of one digit"""
    _, _, pixels, _ = office
    assert np.asarray(read(pixels[:1])).shape == (1,)


@pytest.mark.id("tst_00qe5t")
def test_learns(office, read):
    """Trained on a few hundred digits, it reads most of the validation digits right"""
    _, _, pixels, digits = office
    assert np.mean(np.asarray(read(pixels)) == digits) > 0.8
