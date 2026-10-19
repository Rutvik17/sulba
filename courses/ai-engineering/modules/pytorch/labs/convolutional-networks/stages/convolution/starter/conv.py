"""The shop's convolution and pooling, by hand, as PyTorch computes them."""

import torch
import torch.nn.functional as F


def conv2d(x, weight, bias=None, stride=1, padding=0, dilation=1, groups=1):
    """F.conv2d by hand: a batch x (N, C, H, W) convolved with weight (O, C / groups, kh, kw),
    plus bias (O,) if there is one. stride, padding and dilation are each an int or a pair."""
    raise NotImplementedError


def max_pool2d(x, kernel, stride=None):
    """F.max_pool2d by hand, without padding: the largest pixel of each kernel by kernel
    window of a batch x (N, C, H, W), the windows stride apart, or kernel apart unless given.
    kernel and stride are each an int or a pair. Each window's gradient goes to its first
    largest pixel, in reading order."""
    raise NotImplementedError
