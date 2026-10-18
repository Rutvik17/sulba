import math

import numpy as np

WIDTHS = (64, 64, 32, 10)
# The checks: a last layer started SCALE times too large, and a batch of BATCH digits
# learned by heart in STEPS steps of SGD at LR, its loss below BELOW.
SCALE, BATCH, STEPS, LR, BELOW = 30, 32, 300, 0.5, 0.01


def network(rng):
    params = []
    for inputs, outputs in zip(WIDTHS, WIDTHS[1:]):
        bound = 1 / math.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    return params


def loss_and_grads(params, X, digits, flipped=False):
    """The mean cross-entropy and its gradients, with each ReLU's mask flipped if asked."""
    inputs, before = [X], []
    for number in range(0, len(params), 2):
        out = inputs[-1] @ params[number].T + params[number + 1]
        if number + 2 < len(params):
            before.append(out)
            inputs.append(np.maximum(out, 0.0))
    shifted = out - out.max(axis=1, keepdims=True)
    log_sums = np.log(np.exp(shifted).sum(axis=1))
    loss = np.mean(log_sums - shifted[np.arange(len(digits)), digits])
    d = np.exp(shifted - log_sums[:, None])
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    grads = [None] * len(params)
    for number in range(len(params) - 2, -1, -2):
        grads[number] = d.T @ inputs[number // 2]
        grads[number + 1] = d.sum(axis=0)
        if number:
            mask = before[number // 2 - 1] > 0
            d = (d @ params[number]) * (~mask if flipped else mask)
    return loss, grads


def by_heart(X, digits, flipped=False):
    """The first step whose loss on the batch is below BELOW, counting from 1, or None."""
    params = network(np.random.default_rng(0))
    for step in range(1, STEPS + 1):
        loss, grads = loss_and_grads(params, X, digits, flipped)
        if loss < BELOW:
            return step
        for param, grad in zip(params, grads, strict=True):
            param -= LR * grad
    return None


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    training = table[:, 0] == 0
    X, digits = table[training, 2:] / 16, table[training, 1].astype(np.int64)
    params = network(np.random.default_rng(0))
    start = loss_and_grads(params, X, digits)[0]
    params[-2] *= SCALE
    params[-1] *= SCALE
    batch, labels = X[:BATCH], digits[:BATCH]
    shuffled = np.random.default_rng(1).permutation(labels)
    # With its backward pass broken, the loss never falls below the line.
    assert by_heart(batch, labels, flipped=True) is None
    return {
        "guess": f"{math.log(10):.2f}",
        "start": f"{start:.2f}",
        "scale": str(SCALE),
        "too_large": f"{loss_and_grads(params, X, digits)[0]:.2f}",
        "batch": str(BATCH),
        "steps": str(STEPS),
        "lr": f"{LR:g}",
        "below": f"{BELOW:g}",
        "by_heart": str(by_heart(batch, labels)),
        "shuffled": str(by_heart(batch, shuffled)),
        "parameters": f"{sum(p.size for p in network(np.random.default_rng(0))):,}",
    }
