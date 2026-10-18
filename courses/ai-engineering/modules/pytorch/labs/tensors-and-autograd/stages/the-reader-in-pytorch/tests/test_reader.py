import numpy as np
import pytest
import torch

from reader import train

SAMPLES = 500


def office():
    """The training digits' pixels and the digits they show, and the test digits' pixels."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    train_rows, test_rows = table[table[:, 0] == 0], table[table[:, 0] == 2]
    pixels = torch.from_numpy(np.ascontiguousarray(train_rows[:, 2:]))
    digits = torch.from_numpy(train_rows[:, 1].astype(np.int64))
    return pixels, digits, torch.from_numpy(np.ascontiguousarray(test_rows[:, 2:]))


@pytest.mark.id("tst_qvp29a")
def test_a_digit_for_each_row():
    """A digit for each row"""
    pixels, digits, test = office()
    found = train(pixels[:SAMPLES], digits[:SAMPLES], np.random.default_rng(1))(test)
    assert found.shape == (len(test),) and found.dtype == torch.int64
    assert ((found >= 0) & (found <= 9)).all()


@pytest.mark.id("tst_8fdugn")
def test_same_seed():
    """The same reader from the same seed"""
    pixels, digits, test = office()
    first, second = (
        train(pixels[:SAMPLES], digits[:SAMPLES], np.random.default_rng(5))
        for _ in range(2)
    )
    assert torch.equal(first(test), second(test))
