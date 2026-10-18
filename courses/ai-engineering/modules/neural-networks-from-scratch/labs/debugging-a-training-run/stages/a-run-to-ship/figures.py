import math

import numpy as np

WIDTHS = (64, 64, 32, 10)
# The office's budget, its target, the run's seed, and the solution's clipping.
BUDGET, BATCH, TARGET, SEED, MAX_NORM = 1000, 64, 0.94, 0, 1.0
# The learning rates compared on the validation digits, the last of them the solution's.
LRS = (0.1, 0.3, 0.5)
# Stage 3's range test.
TEST_BATCHES, LR_MIN, LR_MAX, BETA, STOP = 300, 1e-3, 10.0, 0.98, 4.0


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


def run(X, digits, sets, lr):
    """The office's network after its budget at a learning rate, trained as stage 4's train
    trains it, a batch to a step, clipped to MAX_NORM."""
    rng = np.random.default_rng(SEED)
    params = network(rng)
    training = np.flatnonzero(sets == 0)
    order = rng.permutation(training)
    start = 0
    for _ in range(BUDGET):
        if start + BATCH > len(training):
            order = rng.permutation(training)
            start = 0
        rows = order[start : start + BATCH]
        start += BATCH
        _, grads = loss_and_grads(params, X[rows], digits[rows])
        scale = min(
            MAX_NORM / (math.sqrt(sum(np.sum(g**2) for g in grads)) + 1e-6), 1.0
        )
        for param, grad in zip(params, grads, strict=True):
            param -= lr * scale * grad
    return params


def lowest(X, digits, sets):
    """The learning rate at the lowest smoothed loss of stage 3's range test."""
    rng = np.random.default_rng(0)
    params = network(rng)
    training = np.flatnonzero(sets == 0)
    rows = [
        rng.choice(training, size=BATCH, replace=False) for _ in range(TEST_BATCHES)
    ]
    lrs = np.geomspace(LR_MIN, LR_MAX, TEST_BATCHES)
    average, smoothed = 0.0, []
    for step, (lr, batch) in enumerate(zip(lrs, rows, strict=True), start=1):
        loss, grads = loss_and_grads(params, X[batch], digits[batch])
        average = BETA * average + (1 - BETA) * loss
        smoothed.append(average / (1 - BETA**step))
        if not np.isfinite(smoothed[-1]) or smoothed[-1] > STOP * min(smoothed):
            break
        for param, grad in zip(params, grads, strict=True):
            param -= lr * grad
    return lrs[int(np.argmin(smoothed))]


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]

    def read(params, part):
        rows = sets == part
        return (
            f"{np.mean(forward(params, X[rows])[1].argmax(axis=1) == digits[rows]):.1%}"
        )

    runs = [run(X, digits, sets, lr) for lr in LRS]
    return {
        "budget": f"{BUDGET:,}",
        "batch": str(BATCH),
        "target": f"{TARGET:.0%}",
        "seed": str(SEED),
        "max_norm": f"{MAX_NORM:g}",
        "training": f"{np.sum(sets == 0):,}",
        "validation": str(np.sum(sets == 1)),
        "test": f"{np.sum(sets == 2):,}",
        "lowest": f"{lowest(X, digits, sets):.3g}",
        "low_lr": f"{LRS[0]:g}",
        "mid_lr": f"{LRS[1]:g}",
        "high_lr": f"{LRS[2]:g}",
        "low": read(runs[0], 1),
        "mid": read(runs[1], 1),
        "high": read(runs[2], 1),
        "chosen_test": read(runs[2], 2),
    }
