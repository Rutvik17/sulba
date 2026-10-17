"""Reverse-mode automatic differentiation on NumPy arrays."""

import numpy as np


def topological_order(output):
    """The tensors output was computed from, output last, each after its parents."""
    order, seen = [], set()

    def visit(tensor):
        if id(tensor) in seen:
            return
        seen.add(id(tensor))
        for parent in tensor._parents:
            visit(parent)
        order.append(tensor)

    visit(output)
    return order


def unbroadcast(grad, shape):
    """Sums grad back down to shape, undoing NumPy's broadcasting."""
    while grad.ndim > len(shape):
        grad = grad.sum(axis=0)
    for axis, length in enumerate(shape):
        if length == 1:
            grad = grad.sum(axis=axis, keepdims=True)
    return grad


class Tensor:
    """A NumPy array that records the operations that produced it."""

    def __init__(self, data, parents=()):
        self.data = np.asarray(data, dtype=np.float64)
        self.grad = np.zeros_like(self.data)
        self._parents = parents
        self._backward = lambda: None

    def __add__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data + other.data, (self, other))

        def backward():
            self.grad += unbroadcast(out.grad, self.data.shape)
            other.grad += unbroadcast(out.grad, other.data.shape)

        out._backward = backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data * other.data, (self, other))

        def backward():
            self.grad += unbroadcast(other.data * out.grad, self.data.shape)
            other.grad += unbroadcast(self.data * out.grad, other.data.shape)

        out._backward = backward
        return out

    def __neg__(self):
        return self * -1.0

    def __sub__(self, other):
        return self + -other

    def __matmul__(self, other):
        out = Tensor(self.data @ other.data, (self, other))

        def backward():
            self.grad += out.grad @ other.data.T
            other.grad += self.data.T @ out.grad

        out._backward = backward
        return out

    @property
    def T(self):
        out = Tensor(self.data.T, (self,))

        def backward():
            self.grad += out.grad.T

        out._backward = backward
        return out

    def sum(self, axis=None, keepdims=False):
        out = Tensor(self.data.sum(axis=axis, keepdims=keepdims), (self,))

        def backward():
            grad = out.grad
            if axis is not None and not keepdims:
                grad = np.expand_dims(grad, axis)
            self.grad += np.broadcast_to(grad, self.data.shape)

        out._backward = backward
        return out

    def mean(self, axis=None, keepdims=False):
        count = self.data.size if axis is None else self.data.shape[axis]
        return self.sum(axis=axis, keepdims=keepdims) * (1.0 / count)

    def exp(self):
        out = Tensor(np.exp(self.data), (self,))

        def backward():
            self.grad += out.data * out.grad

        out._backward = backward
        return out

    def log(self):
        out = Tensor(np.log(self.data), (self,))

        def backward():
            self.grad += out.grad / self.data

        out._backward = backward
        return out

    def tanh(self):
        out = Tensor(np.tanh(self.data), (self,))

        def backward():
            self.grad += (1 - out.data**2) * out.grad

        out._backward = backward
        return out

    def relu(self):
        out = Tensor(np.maximum(self.data, 0.0), (self,))

        def backward():
            self.grad += (self.data > 0) * out.grad

        out._backward = backward
        return out

    def backward(self):
        """Fills in .grad for every tensor this one was computed from."""
        self.grad = np.ones_like(self.data)
        for tensor in reversed(topological_order(self)):
            tensor._backward()
