"""The survey's tiles and their kinds of land use, read from EuroSAT's zip."""

import io
import random
import zipfile
from pathlib import PurePosixPath

import numpy as np
import torch
from PIL import Image

# The zip the first run fetched, which holds each tile as a JPEG in its kind's folder.
ARCHIVE = "data/EuroSAT_RGB.zip"
# A tile's side in pixels.
SIDE = 64


def kinds(archive=ARCHIVE):
    """The kinds of land use: the names of the folders that hold the zip's tiles, sorted."""
    raise NotImplementedError


def read(names, archive=ARCHIVE):
    """The tiles named, as uint8 (N, 3, SIDE, SIDE) in red, green and blue."""
    raise NotImplementedError


def split(labelled, test, seed, archive=ARCHIVE):
    """labelled tiles of each kind to learn from and test others of each kind to test with,
    picked at random from seed, each part as its tiles' names and their kinds' numbers as
    int64 (N,)."""
    raise NotImplementedError
