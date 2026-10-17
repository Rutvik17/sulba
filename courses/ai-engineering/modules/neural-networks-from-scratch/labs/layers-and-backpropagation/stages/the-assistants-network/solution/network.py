"""The office's network: linear layers, ReLU, cross-entropy and the network that runs
them."""

import numpy as np


class Linear:
    """A linear layer, Y = X Wᵀ + b, with a row of the weight for each output."""

    def __init__(self, weight, bias):
        self.weight = weight
        self.bias = bias
        self.dweight = np.zeros_like(weight)
        self.dbias = np.zeros_like(bias)

    def forward(self, X):
        self.X = X
        return X @ self.weight.T + self.bias

    def backward(self, dY):
        self.dweight = dY.T @ self.X
        self.dbias = dY.sum(axis=0)
        return dY @ self.weight


class ReLU:
    """max(x, 0), passing the gradient back where the input was above 0."""

    def forward(self, X):
        self.positive = X > 0
        return np.where(self.positive, X, 0.0)

    def backward(self, dY):
        return np.where(self.positive, dY, 0.0)


def cross_entropy(logits, labels):
    """The mean cross-entropy of the logits against the labels, and its gradient."""
    logits = logits - logits.max(axis=1, keepdims=True)
    exps = np.exp(logits)
    sums = exps.sum(axis=1)
    rows = np.arange(len(labels))
    loss = np.mean(np.log(sums) - logits[rows, labels])
    dlogits = exps / sums[:, None]
    dlogits[rows, labels] -= 1
    return float(loss), dlogits / len(labels)


class Network:
    """Layers run in order, with the gradient run back through them."""

    def __init__(self, layers):
        self.layers = layers

    def forward(self, X):
        for layer in self.layers:
            X = layer.forward(X)
        return X

    def backward(self, dlogits):
        d = dlogits
        for layer in reversed(self.layers):
            d = layer.backward(d)
        return d

    def step(self, lr):
        for layer in self.layers:
            if isinstance(layer, Linear):
                layer.weight = layer.weight - lr * layer.dweight
                layer.bias = layer.bias - lr * layer.dbias
