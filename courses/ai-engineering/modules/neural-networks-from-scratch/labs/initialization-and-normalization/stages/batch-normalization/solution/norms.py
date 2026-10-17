"""Normalization layers as PyTorch has them, each with a forward and a backward pass and
its weight and bias, as a network's other layers have them."""

import numpy as np


class BatchNorm1d:
    """Batch normalization of each feature, as torch.nn.BatchNorm1d has it: over the batch
    in training, and with the running estimates training kept in evaluation."""

    def __init__(self, num_features, eps=1e-5, momentum=0.1):
        self.eps = eps
        self.momentum = momentum
        self.weight = np.ones(num_features)
        self.bias = np.zeros(num_features)
        self.running_mean = np.zeros(num_features)
        self.running_var = np.ones(num_features)

    def forward(self, X, training=True):
        """Each feature of the batch X less its mean, over its standard deviation, then
        scaled by the weight and shifted by the bias."""
        if training:
            mean, var = X.mean(axis=0), X.var(axis=0)
            unbiased = var * len(X) / (len(X) - 1)
            keep = 1 - self.momentum
            self.running_mean = keep * self.running_mean + self.momentum * mean
            self.running_var = keep * self.running_var + self.momentum * unbiased
        else:
            mean, var = self.running_mean, self.running_var
        self.scale = 1 / np.sqrt(var + self.eps)
        self.normalized = (X - mean) * self.scale
        return self.weight * self.normalized + self.bias

    def backward(self, dY):
        """The loss's gradient with respect to the batch, given it with respect to the
        outputs of a forward pass in training, keeping the weight's and the bias's."""
        n = len(dY)
        self.dweight = (dY * self.normalized).sum(axis=0)
        self.dbias = dY.sum(axis=0)
        dnormalized = dY * self.weight
        summed = dnormalized.sum(axis=0)
        along = (dnormalized * self.normalized).sum(axis=0)
        return self.scale / n * (n * dnormalized - summed - self.normalized * along)

    def params(self):
        return [self.weight, self.bias]

    def grads(self):
        return [self.dweight, self.dbias]
