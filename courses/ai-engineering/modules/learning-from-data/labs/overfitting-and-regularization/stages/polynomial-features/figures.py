import math

import numpy as np


def row(values):
    """Numbers as a TeX row vector."""
    return (
        r"\begin{bmatrix} " + " & ".join(f"{v:g}" for v in values) + r" \end{bmatrix}"
    )


def figures():
    table = np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1)
    X = table[:, 3:]
    # The worked example: the first test's water and age, to degree 2.
    water, age = X[0, 3], X[0, 7]
    found = {
        "n_tests": f"{len(table):,}",
        "n_mixes": f"{len(np.unique(table[:, 1])):,}",
        "water": f"{water:g}",
        "age": f"{age:g}",
        "example": row([water, age, water**2, water * age, age**2]),
    }
    for degree in range(1, 5):
        found[f"count_{degree}"] = str(math.comb(X.shape[1] + degree, degree) - 1)
    return found
