import numpy as np

# The office's training batches.
BATCH = 64


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    training = int(np.sum(table[:, 0] == 0))
    full, last = divmod(training, BATCH)
    return {
        "batch": str(BATCH),
        "training": f"{training:,}",
        "full": str(full),
        "last": str(last),
    }
