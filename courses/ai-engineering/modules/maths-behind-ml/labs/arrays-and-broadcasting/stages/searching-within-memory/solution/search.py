"""Finds the records most like each new sample, for the clinic's system."""

import numpy as np


def rescale(X, reference):
    """X on the reference's scale: less the reference's mean, divided by its standard
    deviation."""
    mean = reference.mean(axis=0)
    std = reference.std(axis=0)
    std[std == 0] = 1
    return (X - mean) / std


def search(records, diagnoses, new, k=5):
    """For each new sample, the row numbers of its k nearest records, nearest first, their
    distances, and the share of them that are malignant."""
    scaled_new = rescale(new, records)
    scaled_records = rescale(records, records)
    diff = scaled_new[:, None, :] - scaled_records[None, :, :]
    D = np.sqrt(np.sum(diff**2, axis=-1))
    near = np.argsort(D, axis=1, kind="stable")[:, :k]
    share = diagnoses[near].mean(axis=1)
    return near, np.take_along_axis(D, near, axis=1), share


# The memory the search may use at once, in bytes.
BUDGET = 32_000_000


class Search:
    """The clinic's search, over records it standardizes once."""

    def __init__(self, records, diagnoses):
        self.mean = records.mean(axis=0)
        std = records.std(axis=0)
        std[std == 0] = 1
        self.std = std
        self.records = (records - self.mean) / std
        self.diagnoses = np.asarray(diagnoses)

    def nearest(self, scaled, k):
        """The k nearest records to each row of scaled, nearest first, and their
        distances. Its arrays are freed when it returns."""
        diff = scaled[:, None, :] - self.records[None, :, :]
        D = np.sqrt(np.sum(diff**2, axis=-1))
        near = np.argsort(D, axis=1, kind="stable")[:, :k]
        return near, np.take_along_axis(D, near, axis=1)

    def find(self, new, k=5):
        """For each new sample, its k nearest records, nearest first, their distances, and
        the share of them that are malignant, as search gives them, never holding more
        than BUDGET bytes of arrays at once."""
        scaled = (new - self.mean) / self.std
        n, d = self.records.shape
        # A chunk's differences and their squares are alive at the same time, with the
        # records and the rest: keep each to a quarter of the budget.
        rows = max(1, BUDGET // (4 * 8 * n * d))
        parts = [
            self.nearest(scaled[i : i + rows], k) for i in range(0, len(scaled), rows)
        ]
        near = np.concatenate([part[0] for part in parts])
        dist = np.concatenate([part[1] for part in parts])
        return near, dist, self.diagnoses[near].mean(axis=1)
