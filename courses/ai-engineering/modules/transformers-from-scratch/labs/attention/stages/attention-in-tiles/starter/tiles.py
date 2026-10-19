"""Attention for long stories, a tile of keys at a time."""

import math

import torch


def tiled_attention(q, k, v, causal=False, tile=128):
    """The output of scaled dot-product attention, working through the keys and values in
    tiles of at most tile keys, without ever holding more than a tile's scores for each
    query. q is (..., L, d), k is (..., S, d) and v is (..., S, d_v); causal hides from
    each query the keys after its position, with L equal to S."""
    raise NotImplementedError
