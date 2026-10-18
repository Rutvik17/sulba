import math

import numpy as np

WIDTHS = (64, 64, 32, 10)
# The chart's range test, and the runs at fixed learning rates that follow it.
BATCHES, BATCH, LR_MIN, LR_MAX, BETA, STOP = 300, 64, 1e-3, 10.0, 0.98, 4.0
STEPS, TARGET = 300, 0.9


def network(rng):
    params = []
    for inputs, outputs in zip(WIDTHS, WIDTHS[1:]):
        bound = 1 / math.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    return params


def forward(params, X):
    """Each ReLU's input, and the logits."""
    before = []
    for number in range(0, len(params), 2):
        out = X @ params[number].T + params[number + 1]
        if number + 2 < len(params):
            before.append(out)
            X = np.maximum(out, 0.0)
    return before, out


def loss_and_grads(params, X, digits):
    before, logits = forward(params, X)
    inputs = [X] + [np.maximum(b, 0.0) for b in before]
    shifted = logits - logits.max(axis=1, keepdims=True)
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
            d = (d @ params[number]) * (before[number // 2 - 1] > 0)
    return loss, grads


def range_test(X, digits, training):
    """The chart's range test: its learning rates and smoothed losses."""
    rng = np.random.default_rng(0)
    params = network(rng)
    rows = [rng.choice(training, size=BATCH, replace=False) for _ in range(BATCHES)]
    lrs = np.geomspace(LR_MIN, LR_MAX, BATCHES)
    average, smoothed = 0.0, []
    for step, (lr, batch) in enumerate(zip(lrs, rows, strict=True), start=1):
        loss, grads = loss_and_grads(params, X[batch], digits[batch])
        average = BETA * average + (1 - BETA) * loss
        smoothed.append(average / (1 - BETA**step))
        if not np.isfinite(smoothed[-1]) or smoothed[-1] > STOP * min(smoothed):
            break
        for param, grad in zip(params, grads, strict=True):
            param -= lr * grad
    return lrs[: len(smoothed)], np.array(smoothed)


def read(X, digits, sets, lr):
    """The share of validation digits read after STEPS steps at a fixed learning rate."""
    rng = np.random.default_rng(0)
    params = network(rng)
    training = np.flatnonzero(sets == 0)
    for _ in range(STEPS):
        rows = rng.choice(training, size=BATCH, replace=False)
        _, grads = loss_and_grads(params, X[rows], digits[rows])
        for param, grad in zip(params, grads, strict=True):
            param -= lr * grad
    validation = sets == 1
    logits = forward(params, X[validation])[1]
    return np.mean(logits.argmax(axis=1) == digits[validation])


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]
    lrs, smoothed = range_test(X, digits, np.flatnonzero(sets == 0))
    lowest = lrs[int(np.argmin(smoothed))]
    # At the lowest point's own learning rate, training is so unsteady that the last digit
    # of a sum changes how many digits it reads, so the prose says only that it falls short.
    assert read(X, digits, sets, lowest) < TARGET
    return {
        "batches": str(BATCHES),
        "batch": str(BATCH),
        "lr_min": f"{LR_MIN:g}",
        "lr_max": f"{LR_MAX:g}",
        "beta": f"{BETA:g}",
        "memory": f"{1 / (1 - BETA):.0f}",
        "lowest": f"{lowest:.3g}",
        "steps": str(STEPS),
        "target": f"{TARGET:.0%}",
        "half": f"{read(X, digits, sets, lowest / 2):.1%}",
        "third": f"{read(X, digits, sets, lowest / 3):.1%}",
        "tenth": f"{read(X, digits, sets, lowest / 10):.1%}",
    }
