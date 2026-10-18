import math

import numpy as np

WIDTHS = (64, 64, 32, 10)
# The office's run: STEPS steps of SGD at LR, each from ACCUMULATE batches of BATCH digits,
# clipped to MAX_NORM.
STEPS, LR, BATCH, ACCUMULATE, MAX_NORM = 300, 0.5, 32, 2, 1.0


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


def norm(arrays):
    return math.sqrt(sum(np.sum(array**2) for array in arrays))


def clip(arrays, max_norm):
    """Scales the arrays in place together, as clip_grad_norm_ does."""
    scale = min(max_norm / (norm(arrays) + 1e-6), 1.0)
    for array in arrays:
        array *= scale


def angle(a, b):
    """The angle between two lists of arrays, as vectors, in degrees."""
    cos = sum(np.sum(x * y) for x, y in zip(a, b, strict=True)) / (norm(a) * norm(b))
    return math.degrees(math.acos(min(1.0, cos)))


def run(X, digits, sets, bug=None):
    """The script as the office asked for it, or with one of the assistant's bugs: the
    trained network, and each step's turn from its own batches' gradient and length."""
    rng = np.random.default_rng(1)
    params = network(np.random.default_rng(0))
    training = np.flatnonzero(sets != 1 if bug == "test" else sets == 0)

    def shuffled():
        order = rng.permutation(training)
        return X[order], digits[training if bug == "labels" else order]

    pixels, labels = shuffled()
    start, turns, lengths = 0, [], []
    total = [np.zeros_like(param) for param in params]
    for _ in range(STEPS):
        if bug != "zeroed":
            total = [np.zeros_like(param) for param in params]
        own = [np.zeros_like(param) for param in params]
        for _ in range(ACCUMULATE):
            if start + BATCH > len(training):
                pixels, labels = shuffled()
                start = 0
            rows = slice(start, start + BATCH)
            start += BATCH
            for summed, mine, grad in zip(
                total, own, grads_of(params, pixels[rows], labels[rows])
            ):
                summed += grad / ACCUMULATE
                mine += grad / ACCUMULATE
        if bug == "together":
            for summed in total:
                clip([summed], MAX_NORM)
        else:
            clip(total, MAX_NORM)
        turns.append(angle(total, own))
        lengths.append(norm(total))
        for param, summed in zip(params, total, strict=True):
            param -= LR * summed
    return params, turns, lengths


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]

    def read(params, part):
        rows = sets == part
        return np.mean(forward(params, X[rows])[1].argmax(axis=1) == digits[rows])

    correct = run(X, digits, sets)[0]
    leaked = run(X, digits, sets, "test")[0]
    zeroed, turns, _ = run(X, digits, sets, "zeroed")
    _, one_by_one, lengths = run(X, digits, sets, "together")
    arrays = len(correct)
    return {
        "steps": str(STEPS),
        "correct": f"{read(correct, 1):.1%}",
        "correct_test": f"{read(correct, 2):.1%}",
        "labels": f"{read(run(X, digits, sets, 'labels')[0], 1):.1%}",
        "test_count": f"{np.sum(sets == 2):,}",
        "leaked": f"{read(leaked, 2):.1%}",
        "points": f"{100 * (read(leaked, 2) - read(correct, 2)):.1f}",
        "turn": f"{np.median(turns):.0f}",
        "zeroed": f"{read(zeroed, 2):.1%}",
        "arrays": str(arrays),
        "bound": f"{math.sqrt(arrays):.2f}",
        "over": str(sum(length > MAX_NORM * (1 + 1e-9) for length in lengths)),
        "longest": f"{max(lengths) / MAX_NORM:.2f}",
        "largest_turn": f"{max(one_by_one):.0f}",
    }
