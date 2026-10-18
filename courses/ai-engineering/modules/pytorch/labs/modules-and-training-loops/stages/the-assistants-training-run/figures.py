import copy
from itertools import pairwise

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

# The office's reader and its training, the epoch the stopped runs stop after, and the batches
# the assistant's validation reads.
HIDDEN, WIDTH, BATCH, EPOCHS, LR, MOMENTUM = 8, 32, 64, 15, 0.05, 0.9
STOP, VALIDATION_BATCH = 5, 256
# The ways a run of the assistant's could go wrong, each alone.
PICKING_UP = ("momentum", "order", "epoch")


class Scale(nn.Module):
    def __init__(self, train):
        super().__init__()
        spread = train.std(dim=0, correction=0)
        self.register_buffer("mean", train.mean(dim=0))
        self.register_buffer("spread", torch.where(spread > 0, spread, 1.0))

    def forward(self, pixels):
        return (pixels - self.mean) / self.spread


class Block(nn.Module):
    def __init__(self, inputs, outputs):
        super().__init__()
        self.linear = nn.Linear(inputs, outputs, bias=False, dtype=torch.float64)
        self.norm = nn.BatchNorm1d(outputs, dtype=torch.float64)

    def forward(self, X):
        return torch.relu(self.norm(self.linear(X)))


class Reader(nn.Module):
    def __init__(self, train):
        super().__init__()
        self.scale = Scale(train)
        widths = [train.shape[1]] + [WIDTH] * HIDDEN
        self.blocks = nn.Sequential(*(Block(m, n) for m, n in pairwise(widths)))
        self.output = nn.Linear(WIDTH, 10, dtype=torch.float64)

    def forward(self, pixels):
        return self.output(self.blocks(self.scale(pixels)))


def office():
    """The training, validation and test digits."""
    table = torch.from_numpy(np.loadtxt("data/digits.csv", delimiter=",", skiprows=1))
    parts = []
    for number in range(3):
        rows = table[table[:, 0] == number]
        parts.append(
            TensorDataset(rows[:, 2:].contiguous(), rows[:, 1].to(torch.int64))
        )
    return parts


def started(train):
    torch.manual_seed(0)
    reader = Reader(train.tensors[0])
    optimizer = torch.optim.SGD(reader.parameters(), lr=LR, momentum=MOMENTUM)
    generator = torch.Generator().manual_seed(0)
    return (
        reader,
        optimizer,
        DataLoader(train, BATCH, shuffle=True, generator=generator),
    )


@torch.no_grad()
def loss_on(reader, digits, mistake=None):
    """The mean loss on digits, read as the assistant's validate reads them."""
    if mistake != "training_mode":
        reader.eval()
    total = 0.0
    for X, y in DataLoader(digits, VALIDATION_BATCH):
        total += F.cross_entropy(reader(X), y, reduction="sum").item()
    return total / len(digits)


def run(train, validation, mistake=None):
    """The assistant's run fixed but for one of its mistakes, if any: trained for EPOCHS
    epochs from seed 0 or, for a mistake in picking up, stopped after STOP epochs and picked
    up. Returns the reader, in evaluation mode, and the validation losses the run reported."""
    reader, optimizer, loader = started(train)
    losses = []

    def epoch():
        reader.train()
        for X, y in loader:
            optimizer.zero_grad()
            F.cross_entropy(reader(X), y).backward()
            optimizer.step()
        losses.append(loss_on(reader, validation, mistake))

    for _ in range(STOP if mistake in PICKING_UP else EPOCHS):
        epoch()
    if mistake in PICKING_UP:
        saved = copy.deepcopy(
            {
                "reader": reader.state_dict(),
                "optimizer": optimizer.state_dict(),
                "generator": loader.generator.get_state(),
                # The epoch it was saved in, counted from 0, where it should be the epochs done.
                "epochs": STOP - 1 if mistake == "epoch" else STOP,
            }
        )
        reader, optimizer, loader = started(train)
        reader.load_state_dict(saved["reader"])
        if mistake != "momentum":
            optimizer.load_state_dict(saved["optimizer"])
        if mistake != "order":
            loader.generator.set_state(saved["generator"])
        for _ in range(saved["epochs"], EPOCHS):
            epoch()
    reader.eval()
    return reader, losses


@torch.no_grad()
def reads(reader, digits):
    return reader(digits.tensors[0]).argmax(dim=1)


def figures():
    train, validation, test = office()
    clean, clean_losses = run(train, validation)
    clean_reads = reads(clean, test)
    leaky, leaky_losses = run(train, validation, "training_mode")
    # The prose says validating in training mode left the weights as they were.
    assert all(
        torch.equal(found, param)
        for found, param in zip(leaky.parameters(), clean.parameters(), strict=True)
    )
    found = {}
    for mistake in PICKING_UP:
        reader, losses = run(train, validation, mistake)
        found[mistake] = int((reads(reader, test) != clean_reads).sum()), losses
    batches = -(-len(validation) // VALIDATION_BATCH)
    pull = nn.BatchNorm1d(1).momentum
    kept = (1 - pull) ** batches
    steps = -(-len(train) // BATCH)
    # The epoch trained again: the epochs after the stop, and the one before it.
    epochs = len(found["epoch"][1])
    assert epochs == EPOCHS + 1
    return {
        "batches": str(batches),
        "pull": f"{pull:.0%}",
        "share": f"{1 - kept:.0%}",
        "leaky": f"{loss_on(leaky, validation):.3f}",
        "clean": f"{clean_losses[-1]:.3f}",
        "reported": f"{leaky_losses[-1]:.3f}",
        "stop": str(STOP),
        "test": f"{len(test):,}",
        "momentum": str(found["momentum"][0]),
        "momentum_loss": f"{found['momentum'][1][-1]:.3f}",
        "order": str(found["order"][0]),
        "epochs": str(epochs),
        "steps": str(steps),
        "again": str(found["epoch"][0]),
    }
