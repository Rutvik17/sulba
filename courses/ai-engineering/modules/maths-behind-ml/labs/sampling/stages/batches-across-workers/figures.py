import numpy as np

PATH = "data/breast-cancer.csv"
# The checks' numbers of workers and batch sizes, the seeds and epochs they compare, and their
# cases with more workers than records.
FEWEST, MOST, SMALLEST, LARGEST, SEEDS = 1, 16, 8, 64, 10
FEW, MANY, ONE, FOUR = 3, 8, 1, 4
# The clinic's workers, and workers and a batch size where shares a record apart, without
# the order carried on, need different numbers of batches.
WORKERS, UNEVEN, UNEVEN_SIZE = 4, 8, 8


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    n = int(np.sum(table[:, 0] == 0))

    def again(workers):
        """How many records equal shares on workers use a second time."""
        return workers * -(-n // workers) - n

    big, small = -(-n // UNEVEN), n // UNEVEN
    big_batches, small_batches = -(-big // UNEVEN_SIZE), -(-small // UNEVEN_SIZE)
    assert big_batches != small_batches
    return {
        "records": str(n),
        "fewest": str(FEWEST),
        "most": str(MOST),
        "smallest": str(SMALLEST),
        "largest": str(LARGEST),
        "epochs": str(SEEDS),
        "last_seed": str(SEEDS - 1),
        "few": str(FEW),
        "many": str(MANY),
        "one": str(ONE),
        "four": str(FOUR),
        "workers": str(WORKERS),
        "again4": str(again(WORKERS)),
        "again16": str(again(MOST)),
        "share": str(-(-n // WORKERS)),
        "missed": f"{(1 - 1 / WORKERS) ** WORKERS:.1%}",
        "uneven": str(UNEVEN),
        "uneven_size": str(UNEVEN_SIZE),
        "big": str(big),
        "small": str(small),
        "big_batches": str(big_batches),
        "small_batches": str(small_batches),
    }
