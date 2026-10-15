import numpy as np

PATH = "data/breast-cancer.csv"
# The batch size and seed the checks use, and the epochs a record's batches are followed over.
SIZE, SEED, EPOCHS = 32, 0, 10


def epoch(n, number, same_order=False, replace=False, drop_last=False):
    """An epoch's batches as the fixed code draws them, or with one of the problems."""
    rng = np.random.default_rng(SEED if same_order else [SEED, number])
    order = rng.choice(n, n) if replace else rng.permutation(n)
    stop = n - SIZE + 1 if drop_last else n
    return [order[start : start + SIZE] for start in range(0, stop, SIZE)]


def mates(n, same_order):
    """How many other records each record shares a batch with over EPOCHS epochs, on
    average."""
    seen = [set() for _ in range(n)]
    for number in range(EPOCHS):
        for batch in epoch(n, number, same_order=same_order):
            for row in batch:
                seen[row].update(batch.tolist())
    return np.mean([len(rows) - 1 for rows in seen])


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    y = table[table[:, 0] == 0, 1]
    n = len(y)
    drawn = np.bincount(np.concatenate(epoch(n, 0, replace=True)), minlength=n)
    last = epoch(n, 0)[-1]
    return {
        "epochs": str(EPOCHS),
        "mates": f"{mates(n, True):.0f}",
        "shuffled_mates": f"{mates(n, False):.0f}",
        "records": str(n),
        "missed": str(int(np.sum(drawn == 0))),
        "missed_share": f"{np.mean(drawn == 0):.1%}",
        "most": str(int(drawn.max())),
        "size": str(SIZE),
        "full": str(n // SIZE),
        "left": str(n % SIZE),
        "last_malignant": str(int(y[last].sum())),
        "last_share": f"{y[last].mean():.1%}",
        "last_wrong": f"{y[last].sum() / SIZE:.1%}",
    }
