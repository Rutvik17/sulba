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


class Network:
    """Layers run in order: the forward pass through each in turn, and the backward pass
    back through them in reverse."""

    def __init__(self, layers):
        self.layers = layers

    def forward(self, X):
        """The logits for a batch X: X through each layer in turn."""
        for layer in self.layers:
            X = layer.forward(X)
        return X

    def backward(self, dlogits):
        """Runs the loss's gradient with respect to the logits back through the layers,
        each layer's backward pass handing its result to the layer before, and returns the
        gradient with respect to the network's inputs."""
        d = dlogits
        for layer in reversed(self.layers):
            d = layer.backward(d)
        return d

    def step(self, lr):
        """Moves each linear layer's weight and bias down its gradient, lr times it."""
        for layer in self.layers:
            if isinstance(layer, Linear):
                layer.weight = layer.weight - lr * layer.dweight
                layer.bias = layer.bias - lr * layer.dbias


def linear_layer(inputs, outputs, rng):
    """A Linear layer started as PyTorch's nn.Linear starts one: each weight and bias
    drawn uniformly from -1/sqrt(inputs) to 1/sqrt(inputs) with rng, the weight first."""
    bound = 1 / np.sqrt(inputs)
    weight = rng.uniform(-bound, bound, size=(outputs, inputs))
    bias = rng.uniform(-bound, bound, size=outputs)
    return Linear(weight, bias)
