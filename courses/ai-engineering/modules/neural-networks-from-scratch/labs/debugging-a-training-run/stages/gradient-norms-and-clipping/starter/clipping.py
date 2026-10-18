"""Gradient norms and clipping, as torch.nn.utils has them, on lists of NumPy arrays."""

import numpy as np


def get_total_norm(tensors, norm_type=2.0):
    """The norm of the arrays' norms, as if every array were one vector."""
    raise NotImplementedError


def clip_grads_with_norm_(grads, max_norm, total_norm):
    """Scales every gradient in place by the same factor, so that a total norm above
    max_norm comes down to it."""
    raise NotImplementedError


def clip_grad_norm_(grads, max_norm, norm_type=2.0):
    """Clips the gradients to max_norm together, and returns their total norm before."""
    raise NotImplementedError
