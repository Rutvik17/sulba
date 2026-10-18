import numpy as np
import pytest
import torch

from digits import images, load, scaled, transposed

TABLE = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
SETS = TABLE[:, 0].astype(np.int64)
PIXELS = np.ascontiguousarray(TABLE[:, 2:])
SIDE = 8
# PyTorch and NumPy may differ in the last digits, from summing in another order.
RTOL, ATOL = 1e-12, 1e-12


def office():
    """The pixels as a tensor, and the training digits' pixels."""
    pixels = torch.from_numpy(PIXELS.copy())
    return pixels, pixels[torch.from_numpy(SETS == 0)]


def numpy_scaled(batch, train):
    """The NumPy reader's scaling."""
    mean, spread = train.mean(axis=0), train.std(axis=0)
    return (batch - mean) / np.where(spread > 0, spread, 1.0)


@pytest.mark.id("tst_qdr26v")
def test_load():
    """The digits as tensors of the right types"""
    pixels, digits, sets = load("data/digits.csv")
    assert pixels.dtype == torch.float64
    assert digits.dtype == torch.int64 and sets.dtype == torch.int64
    assert torch.equal(pixels, torch.from_numpy(PIXELS))
    assert torch.equal(digits, torch.from_numpy(TABLE[:, 1].astype(np.int64)))
    assert torch.equal(sets, torch.from_numpy(SETS))


@pytest.mark.id("tst_6dhpgh")
def test_images_share_memory():
    """Grids that share the pixels' memory"""
    pixels, _ = office()
    grids = images(pixels)
    assert grids.shape == (len(PIXELS), SIDE, SIDE)
    assert torch.equal(grids, torch.from_numpy(PIXELS.reshape(-1, SIDE, SIDE)))
    assert grids.untyped_storage().data_ptr() == pixels.untyped_storage().data_ptr()


@pytest.mark.id("tst_6qkf5e")
def test_transposed():
    """Each grid transposed, back in rows"""
    pixels, _ = office()
    expected = (
        PIXELS.reshape(-1, SIDE, SIDE).transpose(0, 2, 1).reshape(len(PIXELS), -1)
    )
    assert torch.equal(transposed(pixels), torch.from_numpy(expected))
    assert torch.equal(transposed(pixels[:5]), torch.from_numpy(expected[:5]))


@pytest.mark.id("tst_3hj8w8")
def test_scaled_as_numpy():
    """Scaled as the NumPy reader scaled them"""
    pixels, train = office()
    test = pixels[torch.from_numpy(SETS == 2)]
    expected = torch.from_numpy(numpy_scaled(PIXELS[SETS == 2], PIXELS[SETS == 0]))
    assert torch.allclose(scaled(test, train), expected, rtol=RTOL, atol=ATOL)


@pytest.mark.id("tst_kadqdv")
def test_constant_pixels():
    """A pixel that never varies in training"""
    pixels, train = office()
    constant = train.std(dim=0) == 0
    found = scaled(pixels, train)
    assert torch.isfinite(found).all()
    assert torch.equal(found[:, constant], (pixels - train.mean(dim=0))[:, constant])


@pytest.mark.id("tst_kkr30c")
def test_inputs_kept():
    """The pixels left as they were"""
    pixels, train = office()
    kept, kept_train = pixels.clone(), train.clone()
    scaled(pixels, train)
    transposed(pixels)
    assert torch.equal(pixels, kept) and torch.equal(train, kept_train)
