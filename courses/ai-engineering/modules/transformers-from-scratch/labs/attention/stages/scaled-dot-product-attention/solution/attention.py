"""Attention for the app's story model, as PyTorch computes it."""

import math

import torch


def causal_mask(length):
    """A (length, length) tensor of booleans, True where the query in row i may see the key in
    column j: where j <= i."""
    return torch.ones(length, length, dtype=torch.bool).tril()


def attention(q, k, v, mask=None):
    """The output and the weights of scaled dot-product attention. q is (..., L, d), k is
    (..., S, d) and v is (..., S, d_v); mask, if given, is booleans that broadcast to
    (..., L, S), True where a query may see a key."""
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.shape[-1])
    if mask is not None:
        scores = scores.masked_fill(~mask, float("-inf"))
    weights = scores.softmax(dim=-1)
    return weights @ v, weights
