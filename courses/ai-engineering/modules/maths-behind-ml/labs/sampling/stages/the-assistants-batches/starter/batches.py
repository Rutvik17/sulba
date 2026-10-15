"""The batches the clinic's network trains on, and their averages."""

import numpy as np


class Batches:
    """Each epoch's batches of the row numbers 0 to n - 1, drawn from a seed."""

    def __init__(self, n, size, seed):
        self.n, self.size, self.seed = n, size, seed

    def epoch(self, number):
        """Epoch number's batches: every row once, in a random order, in batches of size."""
        rng = np.random.default_rng(self.seed)
        order = rng.choice(self.n, self.n)
        starts = range(0, self.n - self.size + 1, self.size)
        return [order[start : start + self.size] for start in starts]

    def average(self, per_record, batch):
        """The mean of per_record, such as each record's loss, over the rows in batch."""
        return per_record[batch].sum(axis=0) / self.size
