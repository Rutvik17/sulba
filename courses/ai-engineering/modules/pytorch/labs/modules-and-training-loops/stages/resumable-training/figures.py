from itertools import pairwise

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

# The office's reader and its training, the check that stops a run while it saves, and the
# share of new writers' digits the reader must read.
HIDDEN, WIDTH, BATCH, EPOCHS, LR, MOMENTUM = 8, 32, 64, 15, 0.05, 0.9
STOP, TARGET = 5, 0.95


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


@torch.no_grad()
def read(reader, digits):
    """The reader's mean loss on digits, and how many it reads right, in evaluation."""
    reader.eval()
    pixels, shown = digits.tensors
    logits = reader(pixels)
    return F.cross_entropy(logits, shown).item(), int(
        (logits.argmax(dim=1) == shown).sum()
    )


def figures():
    train, validation, test = office()
    torch.manual_seed(0)
    reader = Reader(train.tensors[0])
    optimizer = torch.optim.SGD(reader.parameters(), lr=LR, momentum=MOMENTUM)
    generator = torch.Generator().manual_seed(0)
    loader = DataLoader(train, BATCH, shuffle=True, generator=generator)
    epochs = []
    for _ in range(EPOCHS):
        reader.train()
        for X, y in loader:
            optimizer.zero_grad()
            F.cross_entropy(reader(X), y).backward()
            optimizer.step()
        epochs.append((read(reader, validation)[0], read(reader, test)[1]))
    best = min(range(EPOCHS), key=lambda epoch: epochs[epoch][0])
    # The checks stop runs before the best epoch and after it.
    assert STOP - 2 < best + 1 < EPOCHS - 1
    return {
        "lr": str(LR),
        "momentum": str(MOMENTUM),
        "epochs": str(EPOCHS),
        "target": f"{TARGET:.0%}",
        "test": f"{len(test):,}",
        "validation": f"{len(validation):,}",
        "best": str(best + 1),
        "best_loss": f"{epochs[best][0]:.4f}",
        "best_right": f"{epochs[best][1] / len(test):.1%}",
        "last_loss": f"{epochs[-1][0]:.4f}",
        "last_right": f"{epochs[-1][1] / len(test):.1%}",
        "stop": str(STOP),
    }
