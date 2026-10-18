"""The office's training an epoch at a time, and checkpoints a stopped run goes on from."""

import torch
import torch.nn.functional as F


def train_epoch(reader, optimizer, batches):
    """One epoch: a step of the optimizer on each batch that batches deals, in training mode.
    Returns the epoch's mean loss over its digits."""
    reader.train()
    total, count = 0.0, 0
    for X, digits in batches:
        optimizer.zero_grad()
        loss = F.cross_entropy(reader(X), digits)
        loss.backward()
        optimizer.step()
        total += loss.item() * len(digits)
        count += len(digits)
    return total / count


def save(path, reader, optimizer, batches, epochs):
    """Saves at path all a run needs to go on after epochs epochs: the reader's state, the
    optimizer's, and that of the generator batches draws its orders from."""
    checkpoint = {
        "reader": reader.state_dict(),
        "optimizer": optimizer.state_dict(),
        "generator": batches.generator.get_state(),
        "epochs": epochs,
    }
    torch.save(checkpoint, path)


def resume(path, reader, optimizer, batches):
    """Loads the run saved at path into reader, optimizer and batches. Returns how many epochs
    it had done."""
    checkpoint = torch.load(path)
    reader.load_state_dict(checkpoint["reader"])
    optimizer.load_state_dict(checkpoint["optimizer"])
    batches.generator.set_state(checkpoint["generator"])
    return checkpoint["epochs"]
