"""An autograd engine: values that remember how they were made, so that a result's
gradient can flow back to everything it was made from."""

import numpy as np


def topological_order(output):
    """Every value output was made from, output among them, each after all the values it
    was made from."""
    raise NotImplementedError


class Value:
    """A number that remembers the values it was made from. backward() works out the
    gradient of a result with respect to each of them, in their .grad."""

    def __init__(self, data, parents=()):
        self.data = float(data)
        self.grad = 0.0
        self._parents = parents
        # Adds this value's gradient, times the derivative, to each parent's gradient.
        self._backward = lambda: None

    def __add__(self, other):
        """self + other, where other is a Value or a number."""
        raise NotImplementedError

    def __radd__(self, other):
        """other + self, for a number other."""
        raise NotImplementedError

    def __mul__(self, other):
        """self * other, where other is a Value or a number."""
        raise NotImplementedError

    def __rmul__(self, other):
        """other * self, for a number other."""
        raise NotImplementedError

    def backward(self):
        """Sets this value's gradient to 1, then works it back through every value it was
        made from, adding to their gradients."""
        raise NotImplementedError


def exp(a):
    """e to the power of the Value a."""
    raise NotImplementedError
