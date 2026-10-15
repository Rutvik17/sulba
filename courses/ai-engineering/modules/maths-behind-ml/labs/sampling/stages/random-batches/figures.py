import numpy as np

PATH = "data/breast-cancer.csv"
# The batch size the tests and the chart start from, and the chart's seed.
SIZE, SEED = 32, 0


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    y = table[table[:, 0] == 0, 1]
    n = len(y)
    order = np.random.default_rng(SEED).permutation(n)
    shares = [y[order[start : start + SIZE]].mean() for start in range(0, n, SIZE)]
    return {
        "records": str(n),
        "size": str(SIZE),
        "full": str(n // SIZE),
        "last": str(n % SIZE),
        "malignant": str(int(y.sum())),
        "share": f"{y.mean():.1%}",
        "low": f"{min(shares):.1%}",
        "high": f"{max(shares):.1%}",
    }
