"""PyTorch's optimizers in NumPy. Each holds the arrays a network trains, and each step
moves them, in place, by the gradients a backward pass gave."""

import numpy as np


class SGD:
    """Stochastic gradient descent, with momentum, as torch.optim.SGD takes its steps."""

    def __init__(
        self,
        params,
        lr=0.001,
        momentum=0.0,
        dampening=0.0,
        weight_decay=0.0,
        nesterov=False,
    ):
        self.params = params
        self.lr = lr
        self.momentum = momentum
        self.dampening = dampening
        self.weight_decay = weight_decay
        self.nesterov = nesterov
        # Each parameter's momentum buffer, made at its first step.
        self.buffers = [None] * len(params)

    def step(self, grads):
        """Moves each parameter one step, given a gradient for each, in the same order."""
        raise NotImplementedError
