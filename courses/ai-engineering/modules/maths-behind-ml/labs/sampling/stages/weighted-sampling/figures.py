import numpy as np

PATH = "data/breast-cancer.csv"
SIZE = 32
# Weights meant to add up to 1.
COUNT, WEIGHT = 10, 0.1


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    y = table[table[:, 0] == 0, 1]
    n, malignant = len(y), int(y.sum())
    # Their running total ends at the largest of the 2 ** 53 numbers rng.random gives.
    tenths = float(np.cumsum(np.full(COUNT, WEIGHT))[-1])
    assert tenths == np.nextafter(1.0, 0.0) == 1 - 2.0**-53
    odds = f"{2.0**53:.1e}".split("e")
    return {
        "share": f"{y.mean():.1%}",
        "size": str(SIZE),
        "plain": f"{SIZE * y.mean():.0f}",
        "half": str(SIZE // 2),
        "records": str(n),
        "malignant": str(malignant),
        "benign": str(n - malignant),
        "steps": str(int(np.ceil(np.log2(n + 1)))),
        "count": str(COUNT),
        "weight": str(WEIGHT),
        "tenths": repr(tenths),
        "odds": f"{odds[0]} \\times 10^{{{int(odds[1])}}}",
        "malignant_counts": f"{2 * malignant / n:.2f}",
        "benign_counts": f"{2 * (n - malignant) / n:.2f}",
    }
