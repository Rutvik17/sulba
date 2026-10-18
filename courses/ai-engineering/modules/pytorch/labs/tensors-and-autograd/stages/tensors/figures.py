import math

import numpy as np


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, pixels = table[:, 0], table[:, 2:]
    train = pixels[sets == 0]
    numpy_spread, torch_spread = train.std(axis=0), train.std(axis=0, ddof=1)
    side = math.isqrt(pixels.shape[1])
    assert side * side == pixels.shape[1]
    return {
        "digits": f"{len(table):,}",
        "pixels": str(pixels.shape[1]),
        "side": str(side),
        "training": f"{len(train):,}",
        "factor": f"{math.sqrt(len(train) / (len(train) - 1)):.5f}",
        "gap": f"{np.max(torch_spread - numpy_spread):.4f}",
        "constant": str(int(np.sum(numpy_spread == 0))),
    }
