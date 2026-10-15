"""Scores new samples and finds the records most like them, for the clinic's screen."""

import numpy as np


class Screen:
    """The clinic's screen, made from the records and their diagnoses."""

    def __init__(self, records, diagnoses):
        self.mean = records.mean(axis=0)
        self.std = records.std(axis=0)
        self.records = (records - self.mean) / self.std
        # The records' squared lengths, worked out once.
        self.lengths = np.sum(self.records**2, axis=1)
        mu0 = self.records[diagnoses == 0].mean(axis=0)
        mu1 = self.records[diagnoses == 1].mean(axis=0)
        # From the average benign record to the average malignant one.
        self.direction = (mu1 - mu0) / np.linalg.norm(mu1 - mu0)
        self.centre = (mu0 + mu1) / 2

    def scores(self, new):
        """How far each new sample lies past the midpoint of the two means, toward the
        malignant mean, in standard deviations."""
        z = (new - self.mean) / self.std
        return (z - self.centre) @ self.direction

    def nearest(self, new, k=5):
        """The row numbers of each new sample's k nearest records, nearest first, and
        their distances."""
        z = (new - self.mean) / self.std
        dots = z @ self.records.T
        squared = np.sum(z**2, axis=1)[:, None] + self.lengths[None, :] - 2 * dots
        near = np.argsort(squared, axis=1, kind="stable")[:, :k]
        return near, np.sqrt(np.maximum(np.take_along_axis(squared, near, axis=1), 0))
