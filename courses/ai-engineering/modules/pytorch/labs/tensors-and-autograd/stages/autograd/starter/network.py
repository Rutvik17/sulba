"""The office's network in PyTorch, with its gradients from autograd."""

import torch
import torch.nn.functional as F


def parameters(start):
    """The network's weights and biases as tensors that autograd follows, copied from start, a
    dict of NumPy arrays: w1 and b1 for the hidden layer, w2 and b2 for the output layer, each
    weight with a row for each output, as nn.Linear holds it."""
    raise NotImplementedError


def logits(params, X):
    """The logits for a batch X: the hidden layer's ReLU, then the output layer."""
    raise NotImplementedError


def gradients(params, X, digits):
    """The mean cross-entropy's gradient with respect to each parameter, by name, for the batch
    X and the digits it shows. Leaves each parameter's .grad as it was."""
    raise NotImplementedError


def step(params, X, digits, lr):
    """One step of gradient descent on the batch: each parameter moved down its gradient, lr
    times it, in place. Returns the batch's loss before the step, as a float."""
    raise NotImplementedError
