"""The office's training an epoch at a time, and checkpoints a stopped run goes on from."""

import torch
import torch.nn.functional as F


def train_epoch(reader, optimizer, batches):
    """One epoch: a step of the optimizer on each batch that batches deals, in training mode.
    Returns the epoch's mean loss over its digits."""
    raise NotImplementedError


def save(path, reader, optimizer, batches, epochs):
    """Saves at path all a run needs to go on after epochs epochs: the reader's state, the
    optimizer's, and that of the generator batches draws its orders from."""
    raise NotImplementedError


def resume(path, reader, optimizer, batches):
    """Loads the run saved at path into reader, optimizer and batches. Returns how many epochs
    it had done."""
    raise NotImplementedError
