import numpy as np
import pandas as pd

# The k compared, as the chart compares them.
KS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40]


def named(a, varieties, b, ks):
    """Each bean of b named by its k nearest of a, for each k of ks, as the brief describes."""
    order = [np.argsort(((a - bean) ** 2).sum(axis=1), kind="stable") for bean in b]
    out = {}
    for k in ks:
        chosen = []
        for row in order:
            names = list(varieties[row[:k]])
            most = max(names.count(name) for name in names)
            chosen.append(next(name for name in names if names.count(name) == most))
        out[k] = np.array(chosen)
    return out


def figures():
    table = pd.read_csv("data/beans.csv")
    # Every column after the set and the variety is a measurement.
    measurements = list(table.columns[2:])
    parts = [table[table["set"] == number] for number in (0, 1, 2)]
    a, b, c = (part[measurements].to_numpy() for part in parts)
    mean, sd = a.mean(axis=0), a.std(axis=0)
    a, b, c = (a - mean) / sd, (b - mean) / sd, (c - mean) / sd
    varieties, truth, test_truth = (part["variety"].to_numpy() for part in parts)
    shares = {k: (v == truth).mean() for k, v in named(a, varieties, b, KS).items()}
    best = min(k for k in KS if shares[k] == max(shares.values()))
    test = (named(a, varieties, c, [best])[best] == test_truth).mean()
    return {
        "one": f"{shares[1]:.1%}",
        "best": str(best),
        "best_share": f"{shares[best]:.1%}",
        "tries": str(len(KS)),
        "test": f"{test:.1%}",
    }
