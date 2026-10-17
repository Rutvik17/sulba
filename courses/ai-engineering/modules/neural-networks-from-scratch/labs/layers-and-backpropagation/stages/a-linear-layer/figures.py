import json

import numpy as np

# The office's network: a hidden layer of this many units, trained on batches of this many
# digits.
HIDDEN, BATCH = 64, 64


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1, dtype=np.int64)
    sets, pixels = table[:, 0], table[:, 2:]
    cases = json.loads(open("references/linear.json").read())["cases"]
    first, last = cases[0], cases[-1]
    side = int(np.sqrt(pixels.shape[1]))
    assert side * side == pixels.shape[1]
    return {
        "side": str(side),
        "pixels": str(pixels.shape[1]),
        "lowest": str(pixels.min()),
        "highest": str(pixels.max()),
        "digits": f"{len(table):,}",
        "training": f"{np.sum(sets == 0):,}",
        "validation": f"{np.sum(sets == 1):,}",
        "test": f"{np.sum(sets == 2):,}",
        "cases": str(len(cases)),
        "first_inputs": str(len(first["X"][0])),
        "last_samples": str(len(last["X"])),
        "hidden": str(HIDDEN),
        "batch": str(BATCH),
        "multiplications": f"{BATCH * HIDDEN * pixels.shape[1]:,}",
    }
