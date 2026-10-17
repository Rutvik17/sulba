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

    def __neg__(self):
        """-self."""
        return self * -1

    def __sub__(self, other):
        """self - other, where other is a Value or a number."""
        return self + -other

    def __rsub__(self, other):
        """other - self, for a number other."""
        return other + -self

    def __pow__(self, exponent):
        """self to the power of the number exponent."""
        out = Value(self.data**exponent, (self,))

        def backward():
            self.grad += exponent * self.data ** (exponent - 1) * out.grad

        out._backward = backward
        return out

    def __truediv__(self, other):
        """self / other, where other is a Value or a number."""
        return self * other**-1

    def __rtruediv__(self, other):
        """other / self, for a number other."""
        return other * self**-1

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


def log(a):
    """The natural log of the Value a."""
    out = Value(np.log(a.data), (a,))

    def backward():
        a.grad += out.grad / a.data

    out._backward = backward
    return out


def tanh(a):
    """tanh of the Value a."""
    out = Value(np.tanh(a.data), (a,))

    def backward():
        a.grad += (1 - out.data**2) * out.grad

    out._backward = backward
    return out


def relu(a):
    """max(a, 0) for the Value a, with a derivative of 0 where a is 0, as PyTorch has it."""
    out = Value(max(a.data, 0.0), (a,))

    def backward():
        a.grad += (a.data > 0) * out.grad

    out._backward = backward
    return out


def unbroadcast(grad, shape):
    """grad, the gradient of a result that broadcasting gave more axes or longer ones,
    summed back to shape: over the axes broadcasting added, and along each axis of length
    1 that it stretched."""
    while grad.ndim > len(shape):
        grad = grad.sum(axis=0)
    for axis, length in enumerate(shape):
        if length == 1 and grad.shape[axis] != 1:
            grad = grad.sum(axis=axis, keepdims=True)
    return grad


class Tensor:
    """An array that remembers the arrays it was made from, as Value does for numbers."""

    def __init__(self, data, parents=()):
        self.data = np.asarray(data, dtype=np.float64)
        self.grad = np.zeros_like(self.data)
        self._parents = parents
        self._backward = lambda: None

    def __add__(self, other):
        """self + other, broadcasting as NumPy does."""
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data + other.data, (self, other))

        def backward():
            self.grad += unbroadcast(out.grad, self.data.shape)
            other.grad += unbroadcast(out.grad, other.data.shape)

        out._backward = backward
        return out

    def __mul__(self, other):
        """self * other, element by element, broadcasting as NumPy does."""
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data * other.data, (self, other))

        def backward():
            self.grad += unbroadcast(other.data * out.grad, self.data.shape)
            other.grad += unbroadcast(self.data * out.grad, other.data.shape)

        out._backward = backward
        return out

    def __neg__(self):
        """-self."""
        return self * -1.0

    def __sub__(self, other):
        """self - other, broadcasting as NumPy does."""
        return self + -other

    def __matmul__(self, other):
        """The matrix product self @ other, of two matrices."""
        out = Tensor(self.data @ other.data, (self, other))

        def backward():
            self.grad += out.grad @ other.data.T
            other.grad += self.data.T @ out.grad

        out._backward = backward
        return out

    @property
    def T(self):
        """The transpose of a matrix."""
        out = Tensor(self.data.T, (self,))

        def backward():
            self.grad += out.grad.T

        out._backward = backward
        return out

    def sum(self, axis=None, keepdims=False):
        """The sum along axis, or of every element when axis is None."""
        out = Tensor(self.data.sum(axis=axis, keepdims=keepdims), (self,))

        def backward():
            grad = out.grad
            if axis is not None and not keepdims:
                grad = np.expand_dims(grad, axis)
            self.grad += np.broadcast_to(grad, self.data.shape)

        out._backward = backward
        return out

    def mean(self, axis=None, keepdims=False):
        """The mean along axis, or of every element when axis is None."""
        count = self.data.size if axis is None else self.data.shape[axis]
        return self.sum(axis=axis, keepdims=keepdims) * (1.0 / count)

    def exp(self):
        """e to the power of each element."""
        out = Tensor(np.exp(self.data), (self,))

        def backward():
            self.grad += out.data * out.grad

        out._backward = backward
        return out

    def log(self):
        """The natural log of each element."""
        out = Tensor(np.log(self.data), (self,))

        def backward():
            self.grad += out.grad / self.data

        out._backward = backward
        return out

    def tanh(self):
        """tanh of each element."""
        out = Tensor(np.tanh(self.data), (self,))

        def backward():
            self.grad += (1 - out.data**2) * out.grad

        out._backward = backward
        return out

    def relu(self):
        """max(x, 0) for each element, with a derivative of 0 at 0."""
        out = Tensor(np.maximum(self.data, 0.0), (self,))

        def backward():
            self.grad += (self.data > 0) * out.grad

        out._backward = backward
        return out

    def backward(self):
        """Sets this tensor's gradient to 1, which needs it to hold a single number, then
        works it back through every tensor it was made from."""
        self.grad = np.ones_like(self.data)
        for tensor in reversed(topological_order(self)):
            tensor._backward()
