"""Rotary positions: each query and key turned by its position, pair by pair."""

import torch


def frequencies(dim, theta):
    """The angle each of a head's dim // 2 pairs turns through a position: theta ** (-2i / dim)
    for pair i, as a float64 tensor."""
    return theta ** (-torch.arange(0, dim, 2, dtype=torch.float64) / dim)


def rotate(x, positions, theta):
    """x (..., length, dim) with the row at each position turned by its angles, number i paired
    with number i + dim // 2. positions holds the position of each row, and its leading
    dimensions broadcast with x's. In x's dtype."""
    dim = x.shape[-1]
    angles = positions.to(torch.float64)[..., None] * frequencies(dim, theta)
    cos, sin = angles.cos().to(x.dtype), angles.sin().to(x.dtype)
    first, second = x[..., : dim // 2], x[..., dim // 2 :]
    return torch.cat([first * cos - second * sin, second * cos + first * sin], dim=-1)
