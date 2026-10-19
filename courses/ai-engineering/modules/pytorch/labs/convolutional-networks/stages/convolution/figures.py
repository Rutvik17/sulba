import gzip

import torch
from torch import nn


def output_side(side, **options):
    """The side of the output a square photo gets from a 3 by 3 convolution with options."""
    conv = nn.Conv2d(1, 1, 3, **options)
    return conv(torch.zeros(1, 1, side, side)).shape[-1]


def figures():
    with gzip.open("data/t10k-images-idx3-ubyte.gz") as file:
        header = file.read(16)
    side = int.from_bytes(header[8:12], "big")
    with gzip.open("data/t10k-labels-idx1-ubyte.gz") as file:
        kinds = len(set(file.read()[8:]))
    half = nn.MaxPool2d(2)(torch.zeros(1, 1, side, side)).shape[-1]
    # Between 16 and 32 feature maps of the halved photo, a dense layer holds a weight for
    # every pair of their numbers, and a bias for each output.
    inputs, outputs = 16 * half * half, 32 * half * half
    dilation = 2
    return {
        "kinds": str(kinds),
        "side": str(side),
        "strided": str(output_side(side, padding=1, stride=2)),
        "span": str(dilation * (3 - 1) + 1),
        "dilated": str(output_side(side, dilation=dilation)),
        "conv": f"{sum(p.numel() for p in nn.Conv2d(16, 32, 3, padding=1).parameters()):,}",
        "half": str(half),
        "dense": f"{inputs * outputs + outputs:,}",
        "depthwise": str(
            sum(p.numel() for p in nn.Conv2d(16, 32, 3, groups=16).parameters())
        ),
    }
