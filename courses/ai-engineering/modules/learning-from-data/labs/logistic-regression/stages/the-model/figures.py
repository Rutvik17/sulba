import math
import sys

import numpy as np


def figures():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    denominator = 1 + math.exp(-2)
    mantissa, exponent = f"{sys.float_info.max:.1e}".split("e+")
    return {
        "n_train": str(int((~test).sum())),
        "n_test": str(int(test.sum())),
        "n_features": str(table.shape[1] - 2),
        "denominator": f"{denominator:.4f}",
        "sigma_2": f"{1 / denominator:.4f}",
        "float_max": rf"{mantissa} \times 10^{{{int(exponent)}}}",
    }
