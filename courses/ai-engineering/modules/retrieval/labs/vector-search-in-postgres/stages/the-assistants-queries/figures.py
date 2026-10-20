import csv

import numpy as np

# Cosines are worked out in whole numbers, so that they are the same on every system:
# vectors of length 1 are rounded to this many steps for each unit.
STEPS = 2**20


def figures():
    with open("data/passage-vectors.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    passages = np.array([row[1:] for row in rows], dtype=np.int64)
    # Whole numbers below 2**53, which a float64 holds exactly, so every product and sum
    # here is exact.
    inner = passages.astype(np.float64) @ passages.T.astype(np.float64)
    lengths = np.sqrt((passages * passages).sum(axis=1, keepdims=True))
    units = np.rint(passages / lengths * STEPS)
    cosines = units @ units.T / STEPS**2
    each = np.arange(len(passages))
    # The first for `ORDER BY embedding <#> ... DESC`: the smallest inner product.
    np.fill_diagonal(inner, np.inf)
    least = np.argmin(inner, axis=1)
    np.fill_diagonal(inner, -np.inf)
    nearest = np.argmax(inner, axis=1)
    return {
        "passages": f"{len(passages):,}",
        "worst": f"{cosines[each, least].mean():.3f}",
        "best": f"{cosines[each, nearest].mean():.3f}",
    }
