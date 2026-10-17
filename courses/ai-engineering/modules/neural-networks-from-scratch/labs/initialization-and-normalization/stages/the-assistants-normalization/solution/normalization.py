"""Batch and layer normalization for the office's networks, as PyTorch has them."""

import numpy as np


class BatchNorm1d:
    """Normalizes each feature: over the batch in training, with the running estimates in
    evaluation."""

    def __init__(self, num_features, eps=1e-5, momentum=0.1):
        self.eps = eps
        self.momentum = momentum
        self.weight = np.ones(num_features)
        self.bias = np.zeros(num_features)
        self.running_mean = np.zeros(num_features)
        self.running_var = np.ones(num_features)

    def forward(self, X, training=True):
        if training:
            self._track(X)
            mean, var = X.mean(axis=0), X.var(axis=0)
        else:
            mean, var = self.running_mean, self.running_var
        self.scale = 1 / np.sqrt(var + self.eps)
        self.normalized = (X - mean) * self.scale
        return self.weight * self.normalized + self.bias

    def _track(self, X):
        """Mixes the batch's mean and variance into the running estimates."""
        mean, var = X.mean(axis=0), X.var(axis=0, ddof=1)
        keep = 1 - self.momentum
        self.running_mean = keep * self.running_mean + self.momentum * mean
        self.running_var = keep * self.running_var + self.momentum * var

    def backward(self, dY):
        self.dweight = (dY * self.normalized).sum(axis=0)
        self.dbias = dY.sum(axis=0)
        n = len(dY)
        dnormalized = dY * self.weight
        summed = dnormalized.sum(axis=0)
        along = (dnormalized * self.normalized).sum(axis=0)
        return self.scale / n * (n * dnormalized - summed - self.normalized * along)

    def params(self):
        return [self.weight, self.bias]

    def grads(self):
        return [self.dweight, self.dbias]


class LayerNorm:
    """Normalizes each sample over its features."""

    def __init__(self, normalized_shape, eps=1e-5):
        self.eps = eps
        self.weight = np.ones(normalized_shape)
        self.bias = np.zeros(normalized_shape)

    def forward(self, X, training=True):
        mean = X.mean(axis=-1, keepdims=True)
        var = X.var(axis=-1, keepdims=True)
        self.scale = 1 / np.sqrt(var + self.eps)
        self.normalized = (X - mean) * self.scale
        return self.weight * self.normalized + self.bias

    def backward(self, dY):
        self.dweight = (dY * self.normalized).sum(axis=0)
        self.dbias = dY.sum(axis=0)
        n = dY.shape[-1]
        dnormalized = dY * self.weight
        summed = dnormalized.sum(axis=-1, keepdims=True)
        along = (dnormalized * self.normalized).sum(axis=-1, keepdims=True)
        return self.scale / n * (n * dnormalized - summed - self.normalized * along)

    def params(self):
        return [self.weight, self.bias]

    def grads(self):
        return [self.dweight, self.dbias]
