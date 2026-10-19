"""The app's GPT, part by part, as GPT-2 builds it."""

import torch


def layer_norm(x, weight, bias, eps=1e-5):
    """x normalized along its last dimension: less its mean, over the square root of its
    variance plus eps, then times weight and plus bias."""
    raise NotImplementedError


class LayerNorm(torch.nn.Module):
    """Layer normalization with a weight, starting at 1, and a bias, starting at 0."""

    def __init__(self, width, eps=1e-5):
        super().__init__()
        raise NotImplementedError

    def forward(self, x):
        raise NotImplementedError
