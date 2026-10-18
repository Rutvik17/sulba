"""The office's training run, saved after every epoch so that a stop doesn't lose it."""

import os

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from data import batches
from reader import Reader

EPOCHS, LR, MOMENTUM = 15, 0.05, 0.9


@torch.no_grad()
def validate(reader, digits):
    """The reader's mean loss on digits."""
    loss = 0.0
    for X, y in DataLoader(digits, batch_size=256):
        loss += F.cross_entropy(reader(X), y, reduction="sum").item()
    return loss / len(digits)


def save(path, reader, optimizer, loader, epochs):
    """Saves the run at path after epochs epochs."""
    checkpoint = {
        "reader": reader.state_dict(),
        "optimizer": optimizer.state_dict(),
        "generator": loader.generator.get_state(),
        "epochs": epochs,
    }
    torch.save(checkpoint, path)


def resume(path, reader, optimizer, loader):
    """Loads the run saved at path. Returns how many epochs it had done."""
    checkpoint = torch.load(path)
    reader.load_state_dict(checkpoint["reader"])
    return checkpoint["epochs"]


def run(path, train, validation, epochs=EPOCHS, seed=0):
    """Trains the office's reader on train for epochs epochs in all, saving the run at path
    after each, and goes on from the run saved there if there is one. Returns the reader, in
    evaluation mode, and its loss on validation after each epoch this call trained."""
    torch.manual_seed(seed)
    reader = Reader(train.pixels)
    optimizer = torch.optim.SGD(reader.parameters(), lr=LR, momentum=MOMENTUM)
    loader = batches(train, seed)
    done = resume(path, reader, optimizer, loader) if os.path.exists(path) else 0
    losses = []
    for epoch in range(done, epochs):
        reader.train()
        for X, y in loader:
            optimizer.zero_grad()
            F.cross_entropy(reader(X), y).backward()
            optimizer.step()
        losses.append(validate(reader, validation))
        save(path, reader, optimizer, loader, epoch)
    reader.eval()
    return reader, losses
