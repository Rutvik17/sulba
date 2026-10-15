import numpy as np
from scipy.optimize import approx_fprime
from scipy.spatial.distance import cdist

PATH = "data/breast-cancer.csv"


def tex(value, digits):
    """A number in TeX, as a multiple of a power of 10."""
    mantissa, exponent = f"{value:.{digits}e}".split("e")
    return f"{mantissa} \\times 10^{{{int(exponent)}}}"


def length(v):
    return np.sqrt(np.sum(v**2))


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        names = [
            name.replace("_", " ") for name in file.readline().strip().split(",")[2:]
        ]
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    records, sample = (X - mean) / std, (table[new, 2:][0] - mean) / std
    record = records[np.argmin(cdist(sample[None, :], records)[0])]

    def distance(v):
        return np.sqrt(np.sum((v - record) ** 2))

    exact = (sample - record) / distance(sample)
    central = np.zeros(len(sample))
    for i in range(len(sample)):
        step = np.zeros(len(sample))
        step[i] = 1e-6
        central[i] = (distance(sample + step) - distance(sample - step)) / 2e-6
    forward = approx_fprime(sample.copy(), distance)
    order = np.argsort(-np.abs(exact))
    return {
        "measurements": str(len(sample)),
        "evaluations": str(2 * len(sample)),
        "top1_name": names[order[0]],
        "top1": f"{exact[order[0]]:.3f}",
        "top2_name": names[order[1]],
        "top2": f"{exact[order[1]]:.3f}",
        "central_error": tex(length(central - exact) / length(exact), 1),
        "forward_error": tex(length(forward - exact) / length(exact), 1),
    }
