import functools
import gzip
import shutil

import numpy as np
import pytest
import torch

from photos import photos, read_images, read_labels

FILES = {"train": "train", "test": "t10k"}


def path(part, what):
    return f"data/{FILES[part]}-{what}-idx{3 if what == 'images' else 1}-ubyte.gz"


@functools.cache
def parsed(part):
    """The part's photos and kinds as bytes, read here as Fashion-MNIST's own reader does."""
    with gzip.open(path(part, "images")) as file:
        images = np.frombuffer(file.read(), np.uint8, offset=16)
    with gzip.open(path(part, "labels")) as file:
        labels = np.frombuffer(file.read(), np.uint8, offset=8)
    return images.reshape(len(labels), 28, 28).copy(), labels.copy()


def write(path, data):
    with gzip.open(path, "wb") as file:
        file.write(data)
    return path


@pytest.mark.id("tst_s2q3h6")
def test_read():
    """The photos and their kinds as the files hold them"""
    for part in FILES:
        images, labels = parsed(part)
        found = read_images(path(part, "images"))
        assert found.dtype == torch.uint8 and torch.equal(
            found, torch.from_numpy(images)
        )
        kinds = read_labels(path(part, "labels"))
        assert kinds.dtype == torch.int64
        assert torch.equal(kinds, torch.from_numpy(labels).to(torch.int64))


@pytest.mark.id("tst_grzlbt")
def test_photos():
    """The training and test photos, scaled, with a channel each"""
    for part, count in (("train", 60_000), ("test", 10_000)):
        images, labels = photos(part)
        assert images.shape == (count, 1, 28, 28) and images.dtype == torch.float32
        expected = torch.from_numpy(parsed(part)[0].astype(np.float32) / 255)
        assert torch.equal(images[:, 0], expected)
        assert labels.dtype == torch.int64
        assert torch.bincount(labels).tolist() == [count // 10] * 10


@pytest.mark.id("tst_wydsid")
def test_big_endian(tmp_path):
    """Sizes read with the most significant byte first"""
    # 258 photos of 3 by 1 pixels, the counts' bytes 0, 0, 1, 2 and 0, 0, 0, 3.
    header = (0x0803).to_bytes(4, "big") + b"".join(
        n.to_bytes(4, "big") for n in (258, 3, 1)
    )
    pixels = bytes(range(256)) * 3 + bytes(6)
    images = read_images(write(tmp_path / "images.gz", header + pixels[: 258 * 3]))
    assert images.shape == (258, 3, 1)
    assert images.flatten().tolist() == list(pixels[: 258 * 3])
    kinds = (0x0801).to_bytes(4, "big") + (258).to_bytes(4, "big") + bytes(258)
    assert read_labels(write(tmp_path / "labels.gz", kinds)).shape == (258,)


@pytest.mark.id("tst_pr8fbd")
def test_wrong_files():
    """A file of the other kind is refused"""
    with pytest.raises(ValueError):
        read_images(path("test", "labels"))
    with pytest.raises(ValueError):
        read_labels(path("test", "images"))


@pytest.mark.id("tst_hrp0c7")
def test_cut_short(tmp_path):
    """A file cut short, or with more than its header says, is refused"""
    with gzip.open(path("test", "images")) as file:
        data = file.read()
    with pytest.raises(ValueError):
        read_images(write(tmp_path / "short.gz", data[:-784]))
    with pytest.raises(ValueError):
        read_images(write(tmp_path / "long.gz", data + bytes(784)))
    with gzip.open(path("test", "labels")) as file:
        labels = file.read()
    with pytest.raises(ValueError):
        read_labels(write(tmp_path / "short.gz", labels[:-1]))


@pytest.mark.id("tst_hzv7rx")
def test_out_of_step(tmp_path):
    """Photos and kinds that differ in number are refused"""
    shutil.copy(path("test", "images"), tmp_path / "t10k-images-idx3-ubyte.gz")
    with gzip.open(path("test", "labels")) as file:
        labels = file.read()
    # The labels file of 9,999 photos: its count and its data both one short.
    fewer = labels[:4] + (9_999).to_bytes(4, "big") + labels[8:-1]
    write(tmp_path / "t10k-labels-idx1-ubyte.gz", fewer)
    with pytest.raises(ValueError):
        photos("test", tmp_path)
