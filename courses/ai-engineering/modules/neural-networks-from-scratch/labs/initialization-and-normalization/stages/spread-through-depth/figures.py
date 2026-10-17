import math

import numpy as np

# The office's deeper network: eight hidden layers of 32 ReLUs, started as nn.Linear starts,
# trained for STEPS steps of SGD on batches of BATCH digits.
WIDTHS, BATCH, STEPS, LR = (64,) + (32,) * 8 + (10,), 64, 200, 0.3
# The chart's depth, and how far its slider's ends take a start from Kaiming's.
LAYERS, OFF = 30, 0.1


def network(rng, widths):
    """A weight and a bias for each linear layer, drawn as torch.nn.Linear draws them."""
    params = []
    for inputs, outputs in zip(widths, widths[1:]):
        bound = 1 / np.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    return params


def batches(rng, rows, steps):
    """steps batches of BATCH rows, in an order shuffled for each pass over them."""
    order = []
    while len(order) < steps * BATCH:
        order.extend(rng.permutation(rows))
    return [np.array(order[i * BATCH : (i + 1) * BATCH]) for i in range(steps)]


def forward(params, X):
    """Each layer's input, each ReLU's input, and the logits."""
    inputs, before = [X], []
    for number in range(0, len(params), 2):
        out = inputs[-1] @ params[number].T + params[number + 1]
        if number + 2 == len(params):
            return inputs, before, out
        before.append(out)
        inputs.append(np.maximum(out, 0.0))


def gradients(params, X, digits):
    """The mean cross-entropy's gradient with respect to each parameter."""
    inputs, before, logits = forward(params, X)
    exps = np.exp(logits - logits.max(axis=1, keepdims=True))
    d = exps / exps.sum(axis=1, keepdims=True)
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    grads = [None] * len(params)
    for number in range(len(params) - 2, -1, -2):
        grads[number] = d.T @ inputs[number // 2]
        grads[number + 1] = d.sum(axis=0)
        if number:
            d = (d @ params[number]) * (before[number // 2 - 1] > 0)
    return grads


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]
    rng = np.random.default_rng(0)
    params = network(rng, WIDTHS)
    for rows in batches(rng, np.flatnonzero(sets == 0), STEPS):
        for param, grad in zip(
            params, gradients(params, X[rows], digits[rows]), strict=True
        ):
            param -= LR * grad
    validation = sets == 1
    logits = forward(params, X[validation])[2]
    shifted = logits - logits.max(axis=1, keepdims=True)
    log_sums = np.log(np.exp(shifted).sum(axis=1))
    loss = np.mean(log_sums - shifted[np.arange(len(logits)), digits[validation]])
    # Each layer of nn.Linear's start keeps a sixth of the mean square of its input through a
    # ReLU, and Xavier's keeps half of it in a layer as wide as its input.
    default, xavier = math.sqrt(1 / 6), math.sqrt(1 / 2)
    hidden = len(WIDTHS) - 2
    return {
        "hidden": str(hidden),
        "width": str(WIDTHS[1]),
        "steps": str(STEPS),
        "lr": f"{LR:g}",
        "read": f"{np.mean(logits.argmax(axis=1) == digits[validation]):.1%}",
        "loss": f"{loss:.2f}",
        "guess": f"{math.log(10):.2f}",
        "default": f"{default:.2f}",
        "after": f"{default**hidden:.4f}",
        "xavier": f"{xavier:.2f}",
        "layers": str(LAYERS),
        "off": f"{OFF:.0%}",
        "small": f"{(1 - OFF) ** LAYERS:.2f}",
        "large": f"{(1 + OFF) ** LAYERS:.0f}",
    }
