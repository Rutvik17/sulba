"""The office's deep reader, as PyTorch modules."""

import torch
from torch import nn


class Scale(nn.Module):
    """Scales pixels as the office does: less each pixel's mean over the training digits
    train, divided by its spread over them, a spread of 0 taken as 1. Keeps the mean and the
    spread as buffers."""

    def __init__(self, train):
        super().__init__()
        raise NotImplementedError

    def forward(self, pixels):
        raise NotImplementedError


class Block(nn.Module):
    """A hidden layer of the deep reader: a linear layer without a bias, batch normalization,
    then a ReLU, in float64."""

    def __init__(self, inputs, outputs):
        super().__init__()
        raise NotImplementedError

    def forward(self, X):
        raise NotImplementedError


class Reader(nn.Module):
    """The office's deep reader: the scaling, hidden blocks of width units each, then a linear
    output layer with a logit for each digit, in float64."""

    def __init__(self, train, hidden=8, width=32):
        super().__init__()
        raise NotImplementedError

    def forward(self, pixels):
        raise NotImplementedError
