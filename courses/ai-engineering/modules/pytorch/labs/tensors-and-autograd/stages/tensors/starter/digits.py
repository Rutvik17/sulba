"""The office's digits, as tensors."""

import numpy as np
import torch


def load(path):
    """The digits in the CSV file at path, as three tensors: (pixels, digits, sets). pixels
    holds a row of counts for each digit, as float64, and digits and sets the digit each one
    shows and the set it's in, as int64."""
    raise NotImplementedError


def images(pixels):
    """Each digit's counts as its square grid, sharing the memory of pixels."""
    raise NotImplementedError


def transposed(pixels):
    """Each digit's grid transposed, its columns read as rows, back in rows of counts."""
    raise NotImplementedError


def scaled(batch, train):
    """The counts in batch scaled as the NumPy reader scaled them: less each pixel's mean over
    the training digits train, divided by its spread over them, a spread of 0 taken as 1."""
    raise NotImplementedError
