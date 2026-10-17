import time

import numpy as np
import pytest

from train import train

TARGET, LIMIT_S, SAMPLES = 0.95, 2.0, 500


@pytest.fixture(scope="module")
def office():
    """The training digits and the test digits."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    return pixels[sets == 0], digits[sets == 0], pixels[sets == 2], digits[sets == 2]


@pytest.fixture(scope="module")
def trained(office):
    """The reader trained on every training digit with seed 0, how long that took, and
    copies of what it was given."""
    pixels, digits, _, _ = office
    given = pixels.copy(), digits.copy()
    started = time.perf_counter()
    read = train(pixels, digits, np.random.default_rng(0))
    return read, time.perf_counter() - started, given


@pytest.mark.id("tst_z82lcq")
def test_new_writers(office, trained, record_property):
    """95% of new writers' digits"""
    _, _, pixels, digits = office
    read, _, _ = trained
    share = np.mean(np.asarray(read(pixels)) == digits)
    record_property("note", f"{share:.1%} right")
    assert share >= TARGET


@pytest.mark.id("tst_y7fxoa")
def test_fast(trained, record_property):
    """Trains in under 2 seconds"""
    _, took, _ = trained
    record_property("note", f"{took:.2f} s")
    assert took < LIMIT_S


@pytest.mark.id("tst_afcif5")
def test_same_seed(office):
    """The same reader from the same seed"""
    pixels, digits, test_pixels, _ = office
    first, second = (
        train(pixels[:SAMPLES], digits[:SAMPLES], np.random.default_rng(5))
        for _ in range(2)
    )
    assert np.array_equal(first(test_pixels), second(test_pixels))


@pytest.mark.id("tst_mnp2ar")
def test_inputs_kept(office, trained):
    """Its inputs left as they were"""
    pixels, digits, test_pixels, _ = office
    read, _, (given_pixels, given_digits) = trained
    assert np.array_equal(pixels, given_pixels) and np.array_equal(digits, given_digits)
    kept = test_pixels.copy()
    read(test_pixels)
    assert np.array_equal(test_pixels, kept)
