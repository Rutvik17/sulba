"""An autograd engine: values that remember how they were made, so that a result's
gradient can flow back to everything it was made from."""

import numpy as np


def topological_order(output):
    """Every value output was made from, output among them, each after all the values it
    was made from."""
    order, seen = [], set()

    def visit(value):
        if id(value) in seen:
            return
        seen.add(id(value))
        for parent in value._parents:
            visit(parent)
        order.append(value)

    visit(output)
    return order


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
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def backward():
            self.grad += out.grad
            other.grad += out.grad

        out._backward = backward
        return out

    def __radd__(self, other):
        """other + self, for a number other."""
        return self + other

    def __mul__(self, other):
        """self * other, where other is a Value or a number."""
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))

        def backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = backward
        return out

    def __rmul__(self, other):
        """other * self, for a number other."""
        return self * other

    def backward(self):
        """Sets this value's gradient to 1, then works it back through every value it was
        made from, adding to their gradients."""
        self.grad = 1.0
        for value in reversed(topological_order(self)):
            value._backward()


def exp(a):
    """e to the power of the Value a."""
    out = Value(np.exp(a.data), (a,))

    def backward():
        a.grad += out.data * out.grad

    out._backward = backward
    return out
