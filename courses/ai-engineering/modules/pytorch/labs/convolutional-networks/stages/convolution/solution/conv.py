"""The shop's convolution and pooling, by hand, as PyTorch computes them."""

import torch
import torch.nn.functional as F


def pair(value):
    """An int or a pair as a pair: (height, width)."""
    return (value, value) if isinstance(value, int) else tuple(value)


def output_size(size, kernel, stride, padding, dilation):
    """The positions a kernel takes along one dimension of size pixels."""
    return (size + 2 * padding - dilation * (kernel - 1) - 1) // stride + 1


def span(start, step, count):
    """count positions, step apart from start, as a slice."""
    return slice(start, start + step * (count - 1) + 1, step)


def windows(x, kernel, stride, dilation):
    """What each kernel position sees: from a batch x (N, C, H, W), a tensor (N, C, kh, kw,
    H_out, W_out) whose [:, :, i, j] holds the pixels kernel position (i, j) covers at each of
    the output's positions."""
    (kh, kw), (sh, sw), (dh, dw) = kernel, stride, dilation
    h = output_size(x.shape[2], kh, sh, 0, dh)
    w = output_size(x.shape[3], kw, sw, 0, dw)
    rows = []
    for i in range(kh):
        row = [x[:, :, span(i * dh, sh, h), span(j * dw, sw, w)] for j in range(kw)]
        rows.append(torch.stack(row, dim=2))
    return torch.stack(rows, dim=2)


def conv2d(x, weight, bias=None, stride=1, padding=0, dilation=1, groups=1):
    """F.conv2d by hand: a batch x (N, C, H, W) convolved with weight (O, C / groups, kh, kw),
    plus bias (O,) if there is one. stride, padding and dilation are each an int or a pair."""
    out_channels, per_group, kh, kw = weight.shape
    ph, pw = pair(padding)
    seen = windows(F.pad(x, (pw, pw, ph, ph)), (kh, kw), pair(stride), pair(dilation))
    n, channels, _, _, h, w = seen.shape
    seen = seen.reshape(n, groups, channels // groups, kh, kw, h, w)
    weight = weight.reshape(groups, out_channels // groups, per_group, kh, kw)
    out = torch.einsum("ngcijhw,gocij->ngohw", seen, weight)
    out = out.reshape(n, out_channels, h, w)
    return out if bias is None else out + bias.reshape(1, -1, 1, 1)


def max_pool2d(x, kernel, stride=None):
    """F.max_pool2d by hand, without padding: the largest pixel of each kernel by kernel
    window of a batch x (N, C, H, W), the windows stride apart, or kernel apart unless given.
    kernel and stride are each an int or a pair. Each window's gradient goes to its first
    largest pixel, in reading order."""
    kernel = pair(kernel)
    stride = kernel if stride is None else pair(stride)
    seen = windows(x, kernel, stride, (1, 1))
    n, channels, kh, kw, h, w = seen.shape
    seen = seen.permute(0, 1, 4, 5, 2, 3).reshape(n, channels, h, w, kh * kw)
    return seen.max(dim=-1).values
