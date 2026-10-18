"""The office's training run: it keeps the epoch that validates best, and a stop, even while
it saves, loses nothing that the next run can't pick up."""

import copy
import os

import torch

from checkpoints import train_epoch
from data import batches, evaluate
from reader import Reader

EPOCHS, LR, MOMENTUM = 15, 0.05, 0.9


def run(path, train, validation, epochs=EPOCHS, seed=0):
    """Trains the office's reader on train for epochs epochs in all, saving the run at path
    after each, and goes on from the run saved there if there is one. Returns the reader with
    the state it had after the epoch with the lowest loss on validation, in evaluation mode."""
    raise NotImplementedError
