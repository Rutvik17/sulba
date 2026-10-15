import numpy as np
import pandas as pd

# The line's neighbours; how much longer than a Bombay bean each stone is, as the checks grow
# them; and the variety left out of training to stand for one the line has never seen.
K, LONGER, NEW = 12, 1.5, "HOROZ"
LENGTHS = ["Perimeter", "MajorAxisLength", "MinorAxisLength", "EquivDiameter"]
AREAS = ["Area", "ConvexArea"]


def nearest_squared(a, b):
    """The squared distance from each row of b to its nearest row of a."""
    return np.array([((a - bean) ** 2).sum(axis=1).min() for bean in b])


def reach_squared(a):
    """The farthest any row of a is from its nearest other, squared."""
    nearest_other = []
    for i, bean in enumerate(a):
        distances = ((a - bean) ** 2).sum(axis=1)
        distances[i] = np.inf
        nearest_other.append(distances.min())
    return max(nearest_other)


def figures():
    table = pd.read_csv("data/beans.csv")
    # Every column after the set and the variety is a measurement.
    measurements = list(table.columns[2:])
    train, validation, test = (table[table["set"] == n] for n in (0, 1, 2))
    raw = train[measurements].to_numpy()
    mean, sd = raw.mean(axis=0), raw.std(axis=0)
    a = (raw - mean) / sd
    varieties = train["variety"].to_numpy()
    b = (test[measurements].to_numpy() - mean) / sd
    truth = test["variety"].to_numpy()
    reach = reach_squared(a)
    valid = (validation[measurements].to_numpy() - mean) / sd

    named, top = [], []
    for bean in b:
        nearest = np.argsort(((a - bean) ** 2).sum(axis=1), kind="stable")[:K]
        names, counts = np.unique(varieties[nearest], return_counts=True)
        tied = names[counts == counts.max()]
        named.append(next(name for name in varieties[nearest] if name in tied))
        top.append(counts.max())
    right, split = np.array(named) == truth, np.array(top) * 2 <= K

    stones = test[test["variety"] == "BOMBAY"][measurements].to_numpy().copy()
    for name in LENGTHS:
        stones[:, measurements.index(name)] *= LONGER
    for name in AREAS:
        stones[:, measurements.index(name)] *= LONGER**2
    stones = (stones - mean) / sd

    others = train["variety"] != NEW
    kept = raw[others]
    kept_mean, kept_sd = kept.mean(axis=0), kept.std(axis=0)
    new = (test[test["variety"] == NEW][measurements].to_numpy() - kept_mean) / kept_sd
    kept = (kept - kept_mean) / kept_sd
    beyond = nearest_squared(kept, new) > reach_squared(kept)
    farthest = max(nearest_squared(a, valid).max(), nearest_squared(a, b).max())

    return {
        "k": str(K),
        "reach": f"{np.sqrt(reach):.2f}",
        "farthest": f"{np.sqrt(farthest):.2f}",
        "longer": f"{LONGER:g}",
        "stones": str(len(stones)),
        "nearest_stone": f"{np.sqrt(nearest_squared(a, stones).min()):.2f}",
        "test": str(len(b)),
        "split": str(int(split.sum())),
        "split_right": f"{right[split].mean():.0%}",
        "clear_right": f"{right[~split].mean():.1%}",
        "all_right": f"{right.mean():.1%}",
        "new": NEW,
        "new_beans": str(len(new)),
        "new_beyond": str(int(beyond.sum())),
    }
