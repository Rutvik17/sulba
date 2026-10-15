import math

import numpy as np

PATH = "data/breast-cancer.csv"
# The checks' networks: the one checked for speed, and the one the other checks use.
BIG_HIDDEN, HIDDEN = 200, 4
# How the checks scale the loss, and how far one parameter's slope is off.
SMALL_SCALE, BIG_SCALE, ONE_OFF = 1e-6, 1e6, 0.01
# The solution's directions and tolerance, as a share of the gradient's length.
DIRECTIONS, TOLERANCE = 8, 1e-6


def power(value):
    """An exact power of 10 in TeX."""
    return f"10^{{{round(math.log10(value))}}}"


def tex(value, digits):
    """A number in TeX, as a multiple of a power of 10."""
    mantissa, exponent = f"{value:.{digits}e}".split("e")
    return f"{mantissa} \\times 10^{{{int(exponent)}}}"


def hidden_gradients(Z, y, theta, hidden):
    """The hidden layer's part of the gradient, with tanh's slope right and as 1 - A."""
    d = Z.shape[1]
    W1 = theta[: d * hidden].reshape(d, hidden)
    b1 = theta[d * hidden : d * hidden + hidden]
    w2, b2 = theta[d * hidden + hidden : -1], theta[-1]
    A = np.tanh(Z @ W1 + b1)
    ds = (np.exp(-np.logaddexp(0, -(A @ w2 + b2))) - y) / len(y)
    found = []
    for slope in (1 - A**2, 1 - A):
        dpre = np.outer(ds, w2) * slope
        found.append(np.concatenate([(Z.T @ dpre).ravel(), dpre.sum(axis=0)]))
    return found


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    d = X.shape[1]

    def size(hidden):
        return d * hidden + 2 * hidden + 1

    # The tanh mistake with the loss SMALL_SCALE times as large, along the directions the
    # solution draws in the check: how far it moves each slope.
    theta = np.random.default_rng(3).normal(0, 0.5, size(HIDDEN))
    right, wrong = hidden_gradients(Z, y, theta, HIDDEN)
    error = np.zeros(size(HIDDEN))
    error[: len(right)] = SMALL_SCALE * (wrong - right)
    rng = np.random.default_rng(4)
    shifts = []
    for _ in range(DIRECTIONS):
        v = rng.normal(size=size(HIDDEN))
        shifts.append(abs(error @ (v / np.sqrt(np.sum(v**2)))))
    # A fixed tolerance of TOLERANCE would pass this wrong gradient.
    assert max(shifts) < TOLERANCE
    return {
        "records": str(len(y)),
        "big_hidden": str(BIG_HIDDEN),
        "big_parameters": f"{size(BIG_HIDDEN):,}",
        "big_evaluations": f"{2 * size(BIG_HIDDEN):,}",
        "parameters": str(size(HIDDEN)),
        "one_off": f"{ONE_OFF:.0%}",
        "small_scale": power(SMALL_SCALE),
        "big_scale": power(BIG_SCALE),
        "directions": str(DIRECTIONS),
        "direction_evaluations": str(2 * DIRECTIONS),
        "tolerance": power(TOLERANCE),
        "largest_shift": tex(max(shifts), 1),
    }
