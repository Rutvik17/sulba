"""The shop's classifier: a convolutional network for its photos, within its budget."""

import torch
import torch.nn.functional as F
from torch import nn


def make():
    """The shop's classifier, untrained."""
    raise NotImplementedError


def fit(net, images, labels, seed):
    """Trains net on the photos images and their kinds labels, in an order seeded with seed.
    Returns it, ready to classify photos."""
    raise NotImplementedError
