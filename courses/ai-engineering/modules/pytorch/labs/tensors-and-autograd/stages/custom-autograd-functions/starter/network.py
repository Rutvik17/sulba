class CrossEntropy(torch.autograd.Function):
    """The mean cross-entropy of a batch's logits against the digits they show, with a backward
    pass of its own: the softmax, less 1 at each digit, over the batch's size."""

    @staticmethod
    def forward(ctx, logits, digits):
        """The loss, keeping what the backward pass needs."""
        raise NotImplementedError

    @staticmethod
    def backward(ctx, grad):
        """The gradient with respect to the logits, grad times the loss's own, and None for
        the digits, which have no gradient."""
        raise NotImplementedError


def cross_entropy(logits, digits):
    """The mean cross-entropy, through CrossEntropy."""
    return CrossEntropy.apply(logits, digits)
