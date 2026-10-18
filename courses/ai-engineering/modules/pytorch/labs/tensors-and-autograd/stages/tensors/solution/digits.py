"""The office's digits, as tensors."""

import math

import numpy as np
import torch


def load(path):
    """The digits in the CSV file at path, as three tensors: (pixels, digits, sets). pixels
    holds a row of counts for each digit, as float64, and digits and sets the digit each one
    shows and the set it's in, as int64."""
    table = torch.from_numpy(np.loadtxt(path, delimiter=",", skiprows=1))
    sets, digits = table[:, 0].to(torch.int64), table[:, 1].to(torch.int64)
    return table[:, 2:].contiguous(), digits, sets


def images(pixels):
    """Each digit's counts as its square grid, sharing the memory of pixels."""
    side = math.isqrt(pixels.shape[1])
    return pixels.view(-1, side, side)


def transposed(pixels):
    """Each digit's grid transposed, its columns read as rows, back in rows of counts."""
    return images(pixels).transpose(1, 2).reshape(len(pixels), -1)


def scaled(batch, train):
    """The counts in batch scaled as the NumPy reader scaled them: less each pixel's mean over
    the training digits train, divided by its spread over them, a spread of 0 taken as 1."""
    mean = train.mean(dim=0)
    spread = train.std(dim=0, correction=0)
    # A pixel that never varies in training would be divided by 0.
    spread = torch.where(spread > 0, spread, 1.0)
    return (batch - mean) / spread
