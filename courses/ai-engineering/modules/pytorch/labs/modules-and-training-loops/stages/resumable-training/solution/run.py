"""The office's training run: it keeps the epoch that validates best, and a stop, even while
it saves, loses nothing that the next run can't pick up."""

import copy
import os

import torch

from checkpoints import train_epoch
from data import batches, evaluate
from reader import Reader

EPOCHS, LR, MOMENTUM = 15, 0.05, 0.9


def write(path, checkpoint):
    """Saves checkpoint at path through a file beside it, so that a stop while saving leaves
    the last checkpoint whole: os.replace swaps the new one in only once it's all written."""
    partial = f"{path}.partial"
    torch.save(checkpoint, partial)
    os.replace(partial, path)


def run(path, train, validation, epochs=EPOCHS, seed=0):
    """Trains the office's reader on train for epochs epochs in all, saving the run at path
    after each, and goes on from the run saved there if there is one. Returns the reader with
    the state it had after the epoch with the lowest loss on validation, in evaluation mode."""
    torch.manual_seed(seed)
    reader = Reader(train.pixels)
    optimizer = torch.optim.SGD(reader.parameters(), lr=LR, momentum=MOMENTUM)
    loader = batches(train, seed)
    done, best = 0, None
    if os.path.exists(path):
        checkpoint = torch.load(path)
        reader.load_state_dict(checkpoint["reader"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        loader.generator.set_state(checkpoint["generator"])
        done, best = checkpoint["epochs"], checkpoint["best"]
    for epoch in range(done, epochs):
        train_epoch(reader, optimizer, loader)
        loss, _ = evaluate(reader, validation)
        if best is None or loss < best["loss"]:
            # state_dict() holds the reader's own tensors, which the next step changes.
            best = {"loss": loss, "reader": copy.deepcopy(reader.state_dict())}
        checkpoint = {
            "reader": reader.state_dict(),
            "optimizer": optimizer.state_dict(),
            "generator": loader.generator.get_state(),
            "epochs": epoch + 1,
            "best": best,
        }
        write(path, checkpoint)
    reader.load_state_dict(best["reader"])
    reader.eval()
    return reader
