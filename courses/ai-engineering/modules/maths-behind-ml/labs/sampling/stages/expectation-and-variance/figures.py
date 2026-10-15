import numpy as np

PATH = "data/breast-cancer.csv"
# The batch size the explanation works through, and one four times as large.
SIZE, LARGER = 32, 128


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    y = table[table[:, 0] == 0, 1]
    n = len(y)
    sigma = float(np.std(y))

    def spread(size, replace):
        """The standard deviation of a batch's share malignant."""
        correction = 1 if replace else (n - size) / (n - 1)
        return f"{sigma / np.sqrt(size) * np.sqrt(correction):.4f}"

    return {
        "records": str(n),
        "sigma": f"{sigma:.3f}",
        "size": str(SIZE),
        "larger": str(LARGER),
        "kept": str(n - SIZE),
        "less": str(n - 1),
        "correction": f"{(n - SIZE) / (n - 1):.3f}",
        "with": spread(SIZE, True),
        "without": spread(SIZE, False),
        "larger_with": spread(LARGER, True),
        "larger_without": spread(LARGER, False),
    }
