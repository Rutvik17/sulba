"""Rotary positions: each query and key turned by its position, pair by pair."""

import torch


def frequencies(dim, theta):
    """The angle each of a head's dim // 2 pairs turns through a position: theta ** (-2i / dim)
    for pair i, as a float64 tensor."""
    raise NotImplementedError


def rotate(x, positions, theta):
    """x (..., length, dim) with the row at each position turned by its angles, number i paired
    with number i + dim // 2. positions holds the position of each row, and its leading
    dimensions broadcast with x's. In x's dtype."""
    raise NotImplementedError
