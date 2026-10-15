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
