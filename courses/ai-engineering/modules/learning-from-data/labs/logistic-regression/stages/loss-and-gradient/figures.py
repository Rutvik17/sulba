import math

import numpy as np

# The gradient's worked example: two samples, two features, zero weights and bias.
X = np.array([[1.0, 2.0], [3.0, -1.0]])
y = np.array([1.0, 0.0])
w = np.zeros(2)
b = 0.0


def number(x):
    """A number as TeX shows it, without trailing zeros."""
    return f"{x + 0.0:g}"


def factor(x):
    """A number inside a product, in brackets when it is negative."""
    return f"({number(x)})" if x < 0 else number(x)


def matrix(rows):
    body = r" \\ ".join(" & ".join(row) for row in rows)
    return rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"


def column(values):
    return matrix([[number(value)] for value in values])


def figures():
    p = 1 / (1 + np.exp(-(X @ w + b)))
    error = p - y
    n = len(y)
    products = [
        [" + ".join(rf"{factor(a)} \times {factor(e)}" for a, e in zip(row, error))]
        for row in X.T
    ]
    return {
        "ln_2": f"{math.log(2):.4f}",
        "clipped_cost": f"{-math.log(1e-15):.4f}",
        "X": matrix([[number(a) for a in row] for row in X]),
        "y": column(y),
        "w": column(w),
        "b": number(b),
        "sigma_0": number(1 / (1 + math.exp(0))),
        "p": column(p),
        "error": column(error),
        "n": str(n),
        "X_T": matrix([[number(a) for a in row] for row in X.T]),
        "products": matrix(products),
        "dw": column(X.T @ error / n),
        "error_sum": " + ".join(
            number(e) if i == 0 else factor(e) for i, e in enumerate(error)
        ),
        "db": number(error.mean()),
    }
