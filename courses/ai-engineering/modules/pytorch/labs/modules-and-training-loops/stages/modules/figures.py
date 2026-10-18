from itertools import pairwise

import numpy as np
from torch import nn

# The office's deep reader.
HIDDEN, WIDTH = 8, 32


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    pixels = table.shape[1] - 2
    widths = [pixels] + [WIDTH] * HIDDEN
    layers = [
        module
        for m, n in pairwise(widths)
        for module in (nn.Linear(m, n, bias=False), nn.BatchNorm1d(n))
    ]
    layers.append(nn.Linear(WIDTH, 10))
    reader = nn.Sequential(*layers)
    params = list(reader.parameters())
    # The scaling's mean and spread are buffers too.
    buffers = len(list(reader.buffers())) + 2
    return {
        "hidden": str(HIDDEN),
        "width": str(WIDTH),
        "tensors": str(len(params) + buffers),
        "parameter_tensors": str(len(params)),
        "parameters": f"{sum(param.numel() for param in params):,}",
        "buffers": str(buffers),
        "momentum": str(nn.BatchNorm1d(1).momentum),
    }
