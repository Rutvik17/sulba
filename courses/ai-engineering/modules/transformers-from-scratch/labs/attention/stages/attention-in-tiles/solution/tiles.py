"""Attention for long stories, a tile of keys at a time."""

import math

import torch


def tiled_attention(q, k, v, causal=False, tile=128):
    """The output of scaled dot-product attention, working through the keys and values in
    tiles of at most tile keys, without ever holding more than a tile's scores for each
    query. q is (..., L, d), k is (..., S, d) and v is (..., S, d_v); causal hides from
    each query the keys after its position, with L equal to S."""
    *batch, length, size = q.shape
    keys = k.shape[-2]
    scale = 1 / math.sqrt(size)
    # For each query: its largest score so far, the sum of its exponentials relative to that
    # largest, and the weighted sum of the values on the same footing.
    best = q.new_full((*batch, length, 1), float("-inf"))
    total = q.new_zeros((*batch, length, 1))
    out = q.new_zeros((*batch, length, v.shape[-1]))
    rows = torch.arange(length).unsqueeze(-1)
    for start in range(0, keys, tile):
        end = min(start + tile, keys)
        scores = q @ k[..., start:end, :].transpose(-2, -1) * scale
        if causal:
            scores = scores.masked_fill(torch.arange(start, end) > rows, float("-inf"))
        top = torch.maximum(best, scores.amax(dim=-1, keepdim=True))
        # A query whose keys so far are all hidden keeps -inf as its largest score.
        shift = top.masked_fill(top == float("-inf"), 0.0)
        rescale = torch.exp(best - shift)
        weights = torch.exp(scores - shift)
        total = total * rescale + weights.sum(dim=-1, keepdim=True)
        out = out * rescale + weights @ v[..., start:end, :]
        best = top
    return out / total
