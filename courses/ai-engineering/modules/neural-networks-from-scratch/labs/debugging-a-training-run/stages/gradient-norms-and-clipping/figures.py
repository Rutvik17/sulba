import json
import math

import numpy as np

WIDTHS = (64, 64, 32, 10)
# The chart's training, and the maximum norm it starts at.
LR, STEPS, BATCH, MAX_NORM = 3.0, 300, 64, 0.25


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


def grads_of(params, X, digits):
    """The mean cross-entropy's gradient with respect to each parameter."""
    before, logits = forward(params, X)
    inputs = [X] + [np.maximum(b, 0.0) for b in before]
    d = np.exp(logits - logits.max(axis=1, keepdims=True))
    d /= d.sum(axis=1, keepdims=True)
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    grads = [None] * len(params)
    for number in range(len(params) - 2, -1, -2):
        grads[number] = d.T @ inputs[number // 2]
        grads[number + 1] = d.sum(axis=0)
        if number:
            d = (d @ params[number]) * (before[number // 2 - 1] > 0)
    return grads


def run(X, digits, sets, max_norm):
    """The network after the chart's training, and how many of its steps were clipped."""
    rng = np.random.default_rng(0)
    params = network(rng)
    training, clipped = np.flatnonzero(sets == 0), 0
    for _ in range(STEPS):
        rows = rng.choice(training, size=BATCH, replace=False)
        grads = grads_of(params, X[rows], digits[rows])
        total = math.sqrt(sum(np.sum(grad**2) for grad in grads))
        scale = 1.0 if max_norm is None else min(max_norm / (total + 1e-6), 1.0)
        clipped += scale < 1.0
        for param, grad in zip(params, grads, strict=True):
            param -= LR * scale * grad
    return params, clipped


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]
    validation = sets == 1
    cases = json.loads(open("references/clipping.json").read())
    unclipped, _ = run(X, digits, sets, None)
    clipped, count = run(X, digits, sets, MAX_NORM)
    # The units of each hidden layer that are below 0 for every training digit.
    dead = [np.max(b, axis=0) <= 0 for b in forward(unclipped, X[sets == 0])[0]]

    def read(params):
        logits = forward(params, X[validation])[1]
        return f"{np.mean(logits.argmax(axis=1) == digits[validation]):.1%}"

    return {
        "cases": str(
            sum(
                len(cases[part])
                for part in ("total_norms", "clip_with_norm", "clip_norm")
            )
        ),
        "lr": f"{LR:g}",
        "steps": str(STEPS),
        "max_norm": f"{MAX_NORM:g}",
        "unclipped": read(unclipped),
        "first_dead": f"{np.mean(dead[0]):.0%}",
        "second_dead": f"{np.mean(dead[1]):.0%}",
        "clipped": read(clipped),
        "count": str(count),
        "length": f"{LR * MAX_NORM:g}",
    }
