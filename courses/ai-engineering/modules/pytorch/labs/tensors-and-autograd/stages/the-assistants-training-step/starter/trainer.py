"""The office's training step, ported to PyTorch."""

import torch
import torch.nn.functional as F


def start(arrays):
    """The network's weights and biases from the NumPy reader's start, as tensors that autograd
    follows: w1 and b1 for the hidden layer, w2 and b2 for the output layer."""
    return {
        name: torch.from_numpy(array).requires_grad_() for name, array in arrays.items()
    }


def scale(batch, train):
    """The batch scaled by each pixel's mean and spread over the training digits, as the NumPy
    reader scales it."""
    mean, spread = train.mean(dim=0), train.std(dim=0)
    return (batch - mean) / torch.where(spread > 0, spread, 1.0)


def forward(params, X):
    """The logits for a batch."""
    hidden = torch.relu(X @ params["w1"].T + params["b1"]).detach()
    return hidden @ params["w2"].T + params["b2"]


def step(params, X, digits, lr):
    """One step of gradient descent on the batch, made in place. Returns the loss before it."""
    loss = F.cross_entropy(forward(params, X), digits)
    loss.backward()
    with torch.no_grad():
        for param in params.values():
            if param.grad is not None:
                param -= lr * param.grad
    return loss.item()
