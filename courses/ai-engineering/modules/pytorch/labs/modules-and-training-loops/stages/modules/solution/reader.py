"""The office's deep reader, as PyTorch modules."""

from itertools import pairwise

import torch
from torch import nn


class Scale(nn.Module):
    """Scales pixels as the office does: less each pixel's mean over the training digits
    train, divided by its spread over them, a spread of 0 taken as 1. Keeps the mean and the
    spread as buffers."""

    def __init__(self, train):
        super().__init__()
        spread = train.std(dim=0, correction=0)
        self.register_buffer("mean", train.mean(dim=0))
        self.register_buffer("spread", torch.where(spread > 0, spread, 1.0))

    def forward(self, pixels):
        return (pixels - self.mean) / self.spread


class Block(nn.Module):
    """A hidden layer of the deep reader: a linear layer without a bias, batch normalization,
    then a ReLU, in float64."""

    def __init__(self, inputs, outputs):
        super().__init__()
        self.linear = nn.Linear(inputs, outputs, bias=False, dtype=torch.float64)
        self.norm = nn.BatchNorm1d(outputs, dtype=torch.float64)

    def forward(self, X):
        return torch.relu(self.norm(self.linear(X)))


class Reader(nn.Module):
    """The office's deep reader: the scaling, hidden blocks of width units each, then a linear
    output layer with a logit for each digit, in float64."""

    def __init__(self, train, hidden=8, width=32):
        super().__init__()
        self.scale = Scale(train)
        widths = [train.shape[1]] + [width] * hidden
        self.blocks = nn.Sequential(*(Block(m, n) for m, n in pairwise(widths)))
        self.output = nn.Linear(width, 10, dtype=torch.float64)

    def forward(self, pixels):
        return self.output(self.blocks(self.scale(pixels)))
