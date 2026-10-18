"""The office's training script: steps of SGD on the training digits, each from the
gradients of several batches, clipped together."""

import numpy as np

from clipping import clip_grad_norm_
from network import loss_and_grads


def shuffled(rng, X, digits, rows):
    """The pixels and the digits of rows, in a new random order."""
    order = rng.permutation(rows)
    return X[order], digits[order]


def train(
    params,
    X,
    digits,
    sets,
    rng,
    steps=300,
    lr=0.5,
    batch=32,
    accumulate=2,
    max_norm=1.0,
    loss_and_grads=loss_and_grads,
):
    """Trains params in place on the training digits for steps steps of SGD, each from the
    mean of the gradients of accumulate batches, as one batch of their combined size would
    give it, clipped together to max_norm. Returns the loss of each batch."""
    training = np.flatnonzero(sets == 0)
    pixels, labels = shuffled(rng, X, digits, training)
    start, losses = 0, []
    for _ in range(steps):
        total = [np.zeros_like(param) for param in params]
        for _ in range(accumulate):
            if start + batch > len(training):
                pixels, labels = shuffled(rng, X, digits, training)
                start = 0
            rows = slice(start, start + batch)
            start += batch
            loss, grads = loss_and_grads(params, pixels[rows], labels[rows])
            losses.append(loss)
            for summed, grad in zip(total, grads, strict=True):
                summed += grad / accumulate
        clip_grad_norm_(total, max_norm)
        for param, summed in zip(params, total, strict=True):
            param -= lr * summed
    return losses
