"""The office's run: its network trained on a budget, with a report of how."""

import numpy as np

from network import forward, loss_and_grads, network
from train import train

# About half the learning rate at the range test's lowest smoothed loss, in batches of
# BATCH, clipped to MAX_NORM.
LR, BATCH, MAX_NORM = 0.5, 64, 1.0


def train_office(seed, batches=1000, loss_and_grads=loss_and_grads):
    """The office's network trained from seed on batches batches of training digits, and
    the report of its run: its settings, and the share of validation digits it reads."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]
    rng = np.random.default_rng(seed)
    params = network(rng)
    train(
        params,
        X,
        digits,
        sets,
        rng,
        steps=batches,
        lr=LR,
        batch=BATCH,
        accumulate=1,
        max_norm=MAX_NORM,
        loss_and_grads=loss_and_grads,
    )
    validation = sets == 1
    read = forward(params, X[validation])[2].argmax(axis=1)
    report = {
        "lr": LR,
        "batch": BATCH,
        "batches": batches,
        "validation": float(np.mean(read == digits[validation])),
    }
    return params, report
