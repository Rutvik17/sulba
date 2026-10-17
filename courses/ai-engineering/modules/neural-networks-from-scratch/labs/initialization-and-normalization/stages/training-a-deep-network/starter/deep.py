"""The office's deep network: its layers, each trained by SGD on its params."""

import numpy as np

from init import kaiming_uniform
from norms import BatchNorm1d, LayerNorm


class Linear:
    """A linear layer, `X @ weight.T + bias`."""

    def __init__(self, weight, bias):
        self.weight = weight
        self.bias = bias

    def forward(self, X, training=True):
        self.X = X
        return X @ self.weight.T + self.bias

    def backward(self, dY):
        self.dweight = dY.T @ self.X
        self.dbias = dY.sum(axis=0)
        return dY @ self.weight

    def params(self):
        return [self.weight, self.bias]

    def grads(self):
        return [self.dweight, self.dbias]


class ReLU:
    def forward(self, X, training=True):
        self.X = X
        return np.maximum(X, 0.0)

    def backward(self, dY):
        return dY * (self.X > 0)

    def params(self):
        return []

    def grads(self):
        return []


def make_layers(widths, rng):
    """The layers of a network with a linear layer between each pair of widths and a ReLU
    after each linear layer but the last, drawing every random number from rng."""
    layers = []
    for number, (inputs, outputs) in enumerate(zip(widths, widths[1:])):
        bound = 1 / np.sqrt(inputs)
        weight = rng.uniform(-bound, bound, size=(outputs, inputs))
        bias = rng.uniform(-bound, bound, size=outputs)
        layers.append(Linear(weight, bias))
        if number < len(widths) - 2:
            layers.append(ReLU())
    return layers
