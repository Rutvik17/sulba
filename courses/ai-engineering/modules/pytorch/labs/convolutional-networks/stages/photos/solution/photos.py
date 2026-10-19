"""The shop's photos and their kinds, read from Fashion-MNIST's files."""

import gzip
from pathlib import Path

import torch

# The kinds, in the order of the numbers that label them.
KINDS = (
    "T-shirt/top",
    "Trouser",
    "Pullover",
    "Dress",
    "Coat",
    "Sandal",
    "Shirt",
    "Sneaker",
    "Bag",
    "Ankle boot",
)
# The magic numbers of unsigned bytes in 3 dimensions and in 1.
PHOTOS, LABELS = 0x0803, 0x0801


def read(path, magic):
    """The data of the gzipped idx file at path, as unsigned bytes in the shape its header
    gives, if its magic number is magic."""
    with gzip.open(path) as file:
        data = file.read()
    if int.from_bytes(data[:4], "big") != magic:
        raise ValueError(f"{path} doesn't hold what was asked for.")
    dimensions = magic & 0xFF
    start = 4 + 4 * dimensions
    shape = [int.from_bytes(data[i : i + 4], "big") for i in range(4, start, 4)]
    if len(data) - start != torch.Size(shape).numel():
        raise ValueError(f"{path} holds other than its header says.")
    return torch.frombuffer(bytearray(data), dtype=torch.uint8, offset=start).reshape(
        shape
    )


def read_images(path):
    """The photos in the gzipped idx file at path, as uint8 (N, rows, columns)."""
    return read(path, PHOTOS)


def read_labels(path):
    """The kinds in the gzipped idx file at path, as int64 (N,)."""
    return read(path, LABELS).to(torch.int64)


def photos(part, folder="data"):
    """The photos of part "train" or "test" in folder, as float32 (N, 1, rows, columns) with
    each pixel from 0 to 1, and their kinds as int64 (N,)."""
    name = {"train": "train", "test": "t10k"}[part]
    images = read_images(Path(folder) / f"{name}-images-idx3-ubyte.gz")
    labels = read_labels(Path(folder) / f"{name}-labels-idx1-ubyte.gz")
    if len(images) != len(labels):
        raise ValueError(f"The {part} photos and their kinds differ in number.")
    return images.unsqueeze(1).to(torch.float32) / 255, labels
