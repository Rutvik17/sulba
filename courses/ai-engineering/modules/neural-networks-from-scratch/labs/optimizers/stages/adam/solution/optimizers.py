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
        for number, (param, grad) in enumerate(zip(self.params, grads, strict=True)):
            if self.weight_decay:
                grad = grad + self.weight_decay * param
            if self.momentum:
                if self.buffers[number] is None:
                    self.buffers[number] = np.copy(grad)
                else:
                    self.buffers[number] = (
                        self.momentum * self.buffers[number]
                        + (1 - self.dampening) * grad
                    )
                buffer = self.buffers[number]
                grad = grad + self.momentum * buffer if self.nesterov else buffer
            param -= self.lr * grad


class Adam:
    """Adam, as torch.optim.Adam takes its steps: running averages of each gradient and of
    its square, corrected for starting at 0."""

    def __init__(
        self, params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0
    ):
        self.params = params
        self.lr = lr
        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay
        # The steps taken so far, and each parameter's running averages of its gradient
        # and of its gradient squared.
        self.t = 0
        self.m = [np.zeros_like(param) for param in params]
        self.v = [np.zeros_like(param) for param in params]

    def step(self, grads):
        """Moves each parameter one step, given a gradient for each, in the same order."""
        self.t += 1
        beta1, beta2 = self.betas
        for number, (param, grad) in enumerate(zip(self.params, grads, strict=True)):
            if self.weight_decay:
                grad = grad + self.weight_decay * param
            self.m[number] = beta1 * self.m[number] + (1 - beta1) * grad
            self.v[number] = beta2 * self.v[number] + (1 - beta2) * grad**2
            m_hat = self.m[number] / (1 - beta1**self.t)
            v_hat = self.v[number] / (1 - beta2**self.t)
            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
