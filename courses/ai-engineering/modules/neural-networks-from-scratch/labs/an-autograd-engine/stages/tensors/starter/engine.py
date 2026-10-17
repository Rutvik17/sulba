def unbroadcast(grad, shape):
    """grad, the gradient of a result that broadcasting gave more axes or longer ones,
    summed back to shape: over the axes broadcasting added, and along each axis of length
    1 that it stretched."""
    raise NotImplementedError


class Tensor:
    """An array that remembers the arrays it was made from, as Value does for numbers."""

    def __init__(self, data, parents=()):
        self.data = np.asarray(data, dtype=np.float64)
        self.grad = np.zeros_like(self.data)
        self._parents = parents
        self._backward = lambda: None

    def __add__(self, other):
        """self + other, broadcasting as NumPy does."""
        raise NotImplementedError

    def __mul__(self, other):
        """self * other, element by element, broadcasting as NumPy does."""
        raise NotImplementedError

    def __neg__(self):
        """-self."""
        raise NotImplementedError

    def __sub__(self, other):
        """self - other, broadcasting as NumPy does."""
        raise NotImplementedError

    def __matmul__(self, other):
        """The matrix product self @ other, of two matrices."""
        raise NotImplementedError

    @property
    def T(self):
        """The transpose of a matrix."""
        raise NotImplementedError

    def sum(self, axis=None, keepdims=False):
        """The sum along axis, or of every element when axis is None."""
        raise NotImplementedError

    def mean(self, axis=None, keepdims=False):
        """The mean along axis, or of every element when axis is None."""
        raise NotImplementedError

    def exp(self):
        """e to the power of each element."""
        raise NotImplementedError

    def log(self):
        """The natural log of each element."""
        raise NotImplementedError

    def tanh(self):
        """tanh of each element."""
        raise NotImplementedError

    def relu(self):
        """max(x, 0) for each element, with a derivative of 0 at 0."""
        raise NotImplementedError

    def backward(self):
        """Sets this tensor's gradient to 1, which needs it to hold a single number, then
        works it back through every tensor it was made from."""
        raise NotImplementedError
