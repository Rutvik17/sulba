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


def read_images(path):
    """The photos in the gzipped idx file at path, as uint8 (N, rows, columns)."""
    raise NotImplementedError


def read_labels(path):
    """The kinds in the gzipped idx file at path, as int64 (N,)."""
    raise NotImplementedError


def photos(part, folder="data"):
    """The photos of part "train" or "test" in folder, as float32 (N, 1, rows, columns) with
    each pixel from 0 to 1, and their kinds as int64 (N,)."""
    raise NotImplementedError
