"""The office's digits as datasets, dealt in batches, and read in evaluation."""

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

BATCH = 64


class Digits(Dataset):
    """Digits as a map-style dataset: item i is digit i's pixels and the digit it shows."""

    def __init__(self, pixels, digits):
        self.pixels, self.digits = pixels, digits

    def __len__(self):
        return len(self.digits)

    def __getitem__(self, index):
        return self.pixels[index], self.digits[index]


def sets(path):
    """The digits in the CSV file at path as three Digits: the training, validation and test
    sets, their pixels as float64 and their digits as int64."""
    table = torch.from_numpy(np.loadtxt(path, delimiter=",", skiprows=1))
    found = []
    for number in range(3):
        rows = table[table[:, 0] == number]
        found.append(Digits(rows[:, 2:].contiguous(), rows[:, 1].to(torch.int64)))
    return tuple(found)


def batches(digits, seed):
    """The office's training batches: a DataLoader that deals digits in batches of 64, in a
    new order each epoch, drawn from a generator of its own seeded with seed."""
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(digits, batch_size=BATCH, shuffle=True, generator=generator)


@torch.no_grad()
def evaluate(reader, digits):
    """(loss, right): the reader's mean cross-entropy over digits and how many of them it reads
    right, in evaluation mode. Leaves the reader in the mode it found it in."""
    was = reader.training
    reader.eval()
    loss, right = 0.0, 0
    for X, y in DataLoader(digits, batch_size=256):
        logits = reader(X)
        loss += F.cross_entropy(logits, y, reduction="sum").item()
        right += int((logits.argmax(dim=1) == y).sum())
    reader.train(was)
    return loss / len(digits), right
