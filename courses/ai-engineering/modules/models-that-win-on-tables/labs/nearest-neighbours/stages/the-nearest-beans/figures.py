import numpy as np
import pandas as pd

# The neighbours of each validation bean in the comparison of the two ways to break a tie.
K = 2


def figures():
    table = pd.read_csv("data/beans.csv")
    # Every column after the set and the variety is a measurement.
    measurements = list(table.columns[2:])
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    a, b = train[measurements].to_numpy(), validation[measurements].to_numpy()
    mean, sd = a.mean(axis=0), a.std(axis=0)
    a, b = (a - mean) / sd, (b - mean) / sd
    varieties, truth = train["variety"].to_numpy(), validation["variety"].to_numpy()
    named = [
        varieties[np.argsort(((a - bean) ** 2).sum(axis=1), kind="stable")[:K]]
        for bean in b
    ]
    nearer, first, tied = [], [], 0
    for row in named:
        names, counts = np.unique(row, return_counts=True)
        winners = names[counts == counts.max()]
        tied += len(winners) > 1
        nearer.append(next(name for name in row if name in winners))
        first.append(winners[0])
    return {
        "tie_k": str(K),
        "tied": str(tied),
        "validation": str(len(validation)),
        "nearer": f"{(np.array(nearer) == truth).mean():.1%}",
        "first": f"{(np.array(first) == truth).mean():.1%}",
    }
