"""Optimizers for the office's networks, as PyTorch has them: SGD with momentum, Adam and
AdamW."""

import numpy as np


class Optimizer:
    """What the optimizers share: the parameters, the learning rate, and a way to move a
    parameter."""

    def __init__(self, params, lr):
        self.params = params
        self.lr = lr

    def _move(self, number, change):
        """Takes change away from the parameter at number."""
        self.params[number] = self.params[number] - change


class SGD(Optimizer):
    """Gradient descent with momentum and weight decay."""

    def __init__(self, params, lr=0.001, momentum=0.0, weight_decay=0.0):
        super().__init__(params, lr)
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.velocities = [np.zeros_like(param) for param in params]

    def step(self, grads):
        for number, grad in enumerate(grads):
            if self.weight_decay:
                grad = grad + self.weight_decay * self.params[number]
            velocity = self.momentum * self.velocities[number] + self.lr * grad
            self.velocities[number] = velocity
            self._move(number, velocity)


class Adam(Optimizer):
    """Adam, with weight decay added to the gradient."""

    def __init__(
        self, params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.0
    ):
        super().__init__(params, lr)
        self.betas = betas
        self.eps = eps
        self.weight_decay = weight_decay
        self.t = 0
        self.m = [np.zeros_like(param) for param in params]
        self.v = [np.zeros_like(param) for param in params]

    def step(self, grads):
        self.t += 1
        beta1, beta2 = self.betas
        for number, grad in enumerate(grads):
            if self.weight_decay:
                grad = grad + self.weight_decay * self.params[number]
            self.m[number] = beta1 * self.m[number] + (1 - beta1) * grad
            self.v[number] = beta2 * self.v[number] + (1 - beta2) * grad**2
            m_hat, v_hat = self.m[number], self.v[number]
            self._move(number, self.lr * m_hat / (np.sqrt(v_hat) + self.eps))


class AdamW(Adam):
    """AdamW: Adam with the weight decay kept apart from the loss's gradient."""

    def __init__(
        self, params, lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0.01
    ):
        super().__init__(params, lr, betas, eps)
        self.decay = weight_decay

    def step(self, grads):
        decayed = [g + self.decay * p for g, p in zip(grads, self.params)]
        super().step(decayed)
