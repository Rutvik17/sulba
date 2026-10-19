"""Attention for the app's story model, as PyTorch computes it."""

import math

import torch


def causal_mask(length):
    """A (length, length) tensor of booleans, True where the query in row i may see the key in
    column j: where j <= i."""
    raise NotImplementedError


def attention(q, k, v, mask=None):
    """The output and the weights of scaled dot-product attention. q is (..., L, d), k is
    (..., S, d) and v is (..., S, d_v); mask, if given, is booleans that broadcast to
    (..., L, S), True where a query may see a key."""
    raise NotImplementedError
