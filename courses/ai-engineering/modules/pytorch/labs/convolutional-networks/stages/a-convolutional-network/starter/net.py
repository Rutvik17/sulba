"""The shop's convolutional network, and its training on any device."""

import copy

import torch
import torch.nn.functional as F
from torch import nn

LR, MOMENTUM, BATCH = 0.05, 0.9, 64


class Net(nn.Module):
    """The shop's network: two convolutions, each with a ReLU and pooling, then a linear
    layer with a logit for each kind."""

    def __init__(self):
        super().__init__()
        raise NotImplementedError

    def forward(self, photos):
        raise NotImplementedError


def multiply_adds(net, shape=(1, 28, 28)):
    """The multiply-adds a forward pass of one photo of shape takes in net's convolutions and
    linear layers. Leaves net as it was."""
    raise NotImplementedError


def train(net, images, labels, epochs=1, seed=0, device="cpu", dtype=None):
    """Trains net on device, on the photos images and their kinds labels, for epochs epochs
    of SGD with momentum, in batches of BATCH in the order torch.randperm deals each epoch
    from one generator seeded with seed. With dtype, such as torch.bfloat16, the forward pass
    and the loss run under torch.autocast in dtype. Returns each epoch's mean loss."""
    raise NotImplementedError


@torch.no_grad()
def predict(net, images, device="cpu", batch=1000):
    """The kind net gives each of the photos images, as int64 (N,) on device. Leaves net in
    evaluation mode."""
    raise NotImplementedError
