import numpy as np
import pytest

from shorten import bounds, quantize, restore, shorten


def vectors(count, seed=0):
    """Random vectors of 768 numbers and a length of 1, as the server gives them."""
    found = np.random.default_rng(seed).normal(size=(count, 768)).astype(np.float32)
    return found / np.linalg.norm(found, axis=1, keepdims=True)


def card(found, numbers):
    """The card's steps: PyTorch's layer_norm, with its eps of 1e-5, the first numbers,
    then a length of 1."""
    mean = found.mean(axis=1, keepdims=True)
    variance = ((found - mean) ** 2).mean(axis=1, keepdims=True)
    normalized = (found - mean) / np.sqrt(variance + 1e-5)
    kept = normalized[:, :numbers]
    return kept / np.linalg.norm(kept, axis=1, keepdims=True)


@pytest.mark.id("tst_n2y5ce")
def test_shorten():
    """Cut as the card cuts them"""
    found = vectors(20)
    for numbers in (768, 512, 256, 64):
        short = shorten(found, numbers)
        assert short.shape == (20, numbers)
        assert short.dtype == np.float32
        assert np.allclose(short, card(found, numbers), atol=1e-6)


@pytest.mark.id("tst_7hq4ra")
def test_length():
    """Each shortened vector has a length of 1"""
    short = shorten(vectors(10, seed=1) * 3, 128)
    assert np.allclose(np.linalg.norm(short, axis=1), 1, atol=1e-6)


@pytest.mark.id("tst_b0w3xn")
def test_bounds():
    """The lowest and highest of each number"""
    found = np.array([[0.1, -0.2], [0.3, -0.4], [-0.5, 0.0]], dtype=np.float32)
    low, high = bounds(found)
    assert np.array_equal(low, found[[2, 1], [0, 1]])
    assert np.array_equal(high, found[[1, 2], [0, 1]])


@pytest.mark.id("tst_s5k1jt")
def test_quantize():
    """256 steps from low to high, past the bounds clipped"""
    low = np.array([-0.5, 0.0, 0.2], dtype=np.float32)
    high = np.array([0.5, 1.0, 0.2], dtype=np.float32)
    found = np.array(
        [[-0.5, 0.0, 0.2], [0.5, 1.0, 0.2], [0.0, 0.25, 0.3], [-0.9, 1.5, 0.1]],
        dtype=np.float32,
    )
    codes = quantize(found, low, high)
    assert codes.dtype == np.uint8
    assert codes.tolist() == [[0, 0, 0], [255, 255, 0], [128, 64, 0], [0, 255, 0]]


@pytest.mark.id("tst_4lv9dg")
def test_restore():
    """Each number back within half a step"""
    found = vectors(50, seed=2)
    low, high = bounds(found)
    back = restore(quantize(found, low, high), low, high)
    assert back.dtype == np.float32
    assert np.all(np.abs(back - found) <= (high - low) / 510 + 1e-7)
    ends = restore(np.array([[0, 255]], dtype=np.uint8), low[:2], high[:2])
    assert np.allclose(ends, [[low[0], high[1]]], atol=1e-7)
