"""A network's layers, each with a forward pass and a backward pass."""

import numpy as np


class Linear:
    """A linear layer, Y = X Wᵀ + b. weight has a row for each output and a column for
    each input, and bias a value for each output."""

    def __init__(self, weight, bias):
        self.weight = weight
        self.bias = bias

    def forward(self, X):
        """The outputs for a batch X, a row for each sample. Keeps X for the backward
        pass."""
        raise NotImplementedError

    def backward(self, dY):
        """Given dY, the loss's gradient with respect to the outputs, sets self.dweight
        and self.dbias to its gradients with respect to the weight and the bias, and
        returns its gradient with respect to the inputs."""
        raise NotImplementedError
