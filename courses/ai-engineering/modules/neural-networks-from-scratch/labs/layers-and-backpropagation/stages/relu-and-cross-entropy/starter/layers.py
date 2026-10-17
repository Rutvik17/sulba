class ReLU:
    """max(x, 0) for each value. Its backward pass passes the gradient back where the
    input was positive, and 0 elsewhere, as PyTorch does where the input is exactly 0."""

    def forward(self, X):
        """X with each value below 0 set to 0. Keeps what the backward pass needs."""
        raise NotImplementedError

    def backward(self, dY):
        """The gradient with respect to the inputs, given dY at the outputs."""
        raise NotImplementedError


def cross_entropy(logits, labels):
    """The mean cross-entropy of a batch's logits, a row for each sample and a column for
    each digit, against the digits in labels, and its gradient with respect to the
    logits: (loss, dlogits)."""
    raise NotImplementedError
