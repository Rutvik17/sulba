import numpy as np

# The NumPy reader's network, and how closely the tests hold PyTorch to it.
HIDDEN = 32
RTOL_DIGITS = 12


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    pixels, classes = table.shape[1] - 2, int(table[:, 1].max()) + 1
    first, second = pixels * HIDDEN + HIDDEN, HIDDEN * classes + classes
    return {
        "hidden": str(HIDDEN),
        "classes": str(classes),
        "parameters": f"{first + second:,}",
        "first": f"{first:,}",
        "second": f"{second:,}",
        "digits": str(RTOL_DIGITS),
    }
