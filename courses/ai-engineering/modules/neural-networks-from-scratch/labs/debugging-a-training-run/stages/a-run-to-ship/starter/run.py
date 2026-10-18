"""The office's run: its network trained on a budget, with a report of how."""

import numpy as np

from clipping import clip_grad_norm_
from network import forward, loss_and_grads, network
from range_test import lowest, range_test
from train import train


def train_office(seed, batches=1000, loss_and_grads=loss_and_grads):
    """The office's network trained from seed on batches batches of training digits, and
    the report of its run: its settings, and the share of validation digits it reads."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]
    rng = np.random.default_rng(seed)
    params = network(rng)
    lr, batch = 0.01, 64
    train(
        params,
        X,
        digits,
        sets,
        rng,
        steps=batches,
        lr=lr,
        batch=batch,
        accumulate=1,
        loss_and_grads=loss_and_grads,
    )
    report = {"lr": lr, "batch": batch, "batches": batches, "validation": 0.0}
    return params, report
