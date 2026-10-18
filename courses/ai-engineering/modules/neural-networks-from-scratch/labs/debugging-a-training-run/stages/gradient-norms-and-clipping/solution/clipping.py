"""Gradient norms and clipping, as torch.nn.utils has them, on lists of NumPy arrays."""

import numpy as np


def get_total_norm(tensors, norm_type=2.0):
    """The norm of the arrays' norms, as if every array were one vector."""
    norms = [np.linalg.norm(np.ravel(tensor), ord=norm_type) for tensor in tensors]
    return float(np.linalg.norm(np.array(norms), ord=norm_type))


def clip_grads_with_norm_(grads, max_norm, total_norm):
    """Scales every gradient in place by the same factor, so that a total norm above
    max_norm comes down to it."""
    scale = min(max_norm / (total_norm + 1e-6), 1.0)
    for grad in grads:
        grad *= scale


def clip_grad_norm_(grads, max_norm, norm_type=2.0):
    """Clips the gradients to max_norm together, and returns their total norm before."""
    total_norm = get_total_norm(grads, norm_type)
    clip_grads_with_norm_(grads, max_norm, total_norm)
    return total_norm
