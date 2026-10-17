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
        self.X = X
        return X @ self.weight.T + self.bias

    def backward(self, dY):
        """Given dY, the loss's gradient with respect to the outputs, sets self.dweight
        and self.dbias to its gradients with respect to the weight and the bias, and
        returns its gradient with respect to the inputs."""
        self.dweight = dY.T @ self.X
        self.dbias = np.sum(dY, axis=0)
        return dY @ self.weight


class ReLU:
    """max(x, 0) for each value. Its backward pass passes the gradient back where the
    input was positive, and 0 elsewhere, as PyTorch does where the input is exactly 0."""

    def forward(self, X):
        """X with each value below 0 set to 0. Keeps what the backward pass needs."""
        self.positive = X > 0
        return np.where(self.positive, X, 0.0)

    def backward(self, dY):
        """The gradient with respect to the inputs, given dY at the outputs."""
        return np.where(self.positive, dY, 0.0)


def cross_entropy(logits, labels):
    """The mean cross-entropy of a batch's logits, a row for each sample and a column for
    each digit, against the digits in labels, and its gradient with respect to the
    logits: (loss, dlogits)."""
    shifted = logits - logits.max(axis=1, keepdims=True)
    log_probs = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
    rows = np.arange(len(labels))
    loss = -log_probs[rows, labels].mean()
    dlogits = np.exp(log_probs)
    dlogits[rows, labels] -= 1
    return float(loss), dlogits / len(labels)
