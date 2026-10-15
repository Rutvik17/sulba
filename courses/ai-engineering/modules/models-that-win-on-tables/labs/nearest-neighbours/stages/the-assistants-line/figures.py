import numpy as np
import pandas as pd

# The line's neighbours, as the assistant set them.
K = 12


def named_by(varieties, nearest, nearer_wins):
    """The variety most of the nearest beans have, a tie going to the nearest of the tied or,
    as the assistant's line gave it, to the variety that sorts first."""
    named = varieties[nearest]
    names, counts = np.unique(named, return_counts=True)
    tied = names[counts == counts.max()]
    return next(name for name in named if name in tied) if nearer_wins else tied[0]


def sort(varieties, train_scaled, batch_scaled, k, nearer_wins=True):
    return np.array(
        [
            named_by(
                varieties,
                np.argsort(((train_scaled - bean) ** 2).sum(axis=1), kind="stable")[:k],
                nearer_wins,
            )
            for bean in batch_scaled
        ]
    )


def estimates(scaled, varieties, ks):
    """For each k of ks, the share of the training beans named right with each bean among its
    own neighbours, and with each named by the others."""
    itself, others = {k: 0 for k in ks}, {k: 0 for k in ks}
    for i, bean in enumerate(scaled):
        order = np.argsort(((scaled - bean) ** 2).sum(axis=1), kind="stable")
        without = order[order != i]
        for k in ks:
            itself[k] += named_by(varieties, order[:k], True) == varieties[i]
            others[k] += named_by(varieties, without[:k], True) == varieties[i]
    n = len(scaled)
    return {k: (itself[k] / n, others[k] / n) for k in ks}


def figures():
    table = pd.read_csv("data/beans.csv")
    # Every column after the set and the variety is a measurement.
    measurements = list(table.columns[2:])
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    a, b = train[measurements].to_numpy(), validation[measurements].to_numpy()
    varieties, truth = train["variety"].to_numpy(), validation["variety"].to_numpy()
    mean, sd = a.mean(axis=0), a.std(axis=0)
    a_scaled, b_scaled = (a - mean) / sd, (b - mean) / sd

    # Bombay beans are the largest, which the cost of the batch's statistics turns on.
    areas = table.groupby("variety")["Area"].mean()
    assert areas.idxmax() == "BOMBAY"
    bombay = b[truth == "BOMBAY"]
    own = (bombay - bombay.mean(axis=0)) / bombay.std(axis=0)
    named_own = sort(varieties, a_scaled, own, K)

    nearer = sort(varieties, a_scaled, b_scaled, K)
    first = sort(varieties, a_scaled, b_scaled, K, nearer_wins=False)

    first_k = named_by(varieties, np.arange(K), True)
    shares = estimates(a_scaled, varieties, [1, K])
    return {
        "k": str(K),
        "bombay": str(len(bombay)),
        "bombay_named": str(int((named_own == "BOMBAY").sum())),
        "itself_one": f"{shares[1][0]:.0%}",
        "others_one": f"{shares[1][1]:.1%}",
        "itself_k": f"{shares[K][0]:.1%}",
        "others_k": f"{shares[K][1]:.1%}",
        "changed": str(int((nearer != first).sum())),
        "nearer": f"{(nearer == truth).mean():.1%}",
        "first": f"{(first == truth).mean():.1%}",
        "first_k": first_k,
    }
