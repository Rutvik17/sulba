"""The office's digits as datasets, dealt in batches, and read in evaluation."""

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


class Digits(Dataset):
    """Digits as a map-style dataset: item i is digit i's pixels and the digit it shows."""

    def __init__(self, pixels, digits):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __getitem__(self, index):
        raise NotImplementedError


def sets(path):
    """The digits in the CSV file at path as three Digits: the training, validation and test
    sets, their pixels as float64 and their digits as int64."""
    raise NotImplementedError


def batches(digits, seed):
    """The office's training batches: a DataLoader that deals digits in batches of 64, in a
    new order each epoch, drawn from a generator of its own seeded with seed."""
    raise NotImplementedError


def evaluate(reader, digits):
    """(loss, right): the reader's mean cross-entropy over digits and how many of them it reads
    right, in evaluation mode. Leaves the reader in the mode it found it in."""
    raise NotImplementedError
