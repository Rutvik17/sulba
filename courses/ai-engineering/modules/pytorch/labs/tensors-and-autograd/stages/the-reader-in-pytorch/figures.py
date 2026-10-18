import math

import numpy as np
import torch
import torch.nn.functional as F

# The checks' target, and the NumPy reader's network and training.
TARGET = 0.95
HIDDEN, EPOCHS, BATCH, LR = 32, 20, 64, 0.1
DIGITS = 10


def numpy_reader(pixels, digits, rng):
    """The NumPy reader, trained as it trains: the digits it reads for a batch of pixels."""
    mean, spread = pixels.mean(axis=0), pixels.std(axis=0)
    spread = np.where(spread > 0, spread, 1.0)
    X = (pixels - mean) / spread
    layers = []
    for inputs, outputs in [(X.shape[1], HIDDEN), (HIDDEN, DIGITS)]:
        bound = 1 / np.sqrt(inputs)
        weight = rng.uniform(-bound, bound, size=(outputs, inputs))
        layers.append([weight, rng.uniform(-bound, bound, size=outputs)])

    def forward(batch):
        hidden = batch @ layers[0][0].T + layers[0][1]
        relu = np.where(hidden > 0, hidden, 0.0)
        return relu @ layers[1][0].T + layers[1][1], hidden, relu

    for _ in range(EPOCHS):
        order = rng.permutation(len(digits))
        for start in range(0, len(order), BATCH):
            rows = order[start : start + BATCH]
            z, hidden, relu = forward(X[rows])
            shifted = z - z.max(axis=1, keepdims=True)
            dz = np.exp(shifted) / np.exp(shifted).sum(axis=1, keepdims=True)
            dz[np.arange(len(rows)), digits[rows]] -= 1
            dz /= len(rows)
            dhidden = np.where(hidden > 0, dz @ layers[1][0], 0.0)
            gradients = [
                (dhidden.T @ X[rows], dhidden.sum(axis=0)),
                (dz.T @ relu, dz.sum(axis=0)),
            ]
            for layer, (dW, db) in zip(layers, gradients, strict=True):
                layer[0] = layer[0] - LR * dW
                layer[1] = layer[1] - LR * db
    return lambda batch: forward((batch - mean) / spread)[0].argmax(axis=1)


def torch_started(pixels, digits, rng):
    """The port started from torch.manual_seed(0) and nn.Linear's own weights, and trained as
    the NumPy reader trains: the digits it reads for a batch of pixels."""
    torch.manual_seed(0)
    layers = [torch.nn.Linear(pixels.shape[1], HIDDEN), torch.nn.Linear(HIDDEN, DIGITS)]
    params = [
        p.detach().double().requires_grad_()
        for layer in layers
        for p in layer.parameters()
    ]
    w1, b1, w2, b2 = params
    mean, spread = pixels.mean(dim=0), pixels.std(dim=0, correction=0)
    spread = torch.where(spread > 0, spread, 1.0)
    X = (pixels - mean) / spread

    def forward(batch):
        return torch.relu(batch @ w1.T + b1) @ w2.T + b2

    for _ in range(EPOCHS):
        order = torch.from_numpy(rng.permutation(len(digits)))
        for start in range(0, len(order), BATCH):
            rows = order[start : start + BATCH]
            F.cross_entropy(forward(X[rows]), digits[rows]).backward()
            with torch.no_grad():
                for param in params:
                    param -= LR * param.grad
                    param.grad = None
    return lambda batch: forward((batch - mean) / spread).argmax(dim=1)


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    read = numpy_reader(pixels[sets == 0], digits[sets == 0], np.random.default_rng(0))
    reads = read(pixels[sets == 2])
    accuracy = np.mean(reads == digits[sets == 2])
    training = int(np.sum(sets == 0))
    as_tensors = [
        torch.from_numpy(np.ascontiguousarray(pixels[sets == part])) for part in (0, 2)
    ]
    torch_read = torch_started(
        as_tensors[0], torch.from_numpy(digits[sets == 0]), np.random.default_rng(0)
    )
    with torch.no_grad():
        torch_reads = torch_read(as_tensors[1]).numpy()
    return {
        "epochs": str(EPOCHS),
        "lr": str(LR),
        "batch": str(BATCH),
        "hidden": str(HIDDEN),
        "training": f"{training:,}",
        "test": f"{np.sum(sets == 2):,}",
        "target": f"{TARGET:.0%}",
        "accuracy": f"{accuracy:.1%}",
        "steps": f"{EPOCHS * math.ceil(training / BATCH):,}",
        "torch_right": f"{np.mean(torch_reads == digits[sets == 2]):.1%}",
        "torch_differ": str(int(np.sum(torch_reads != reads))),
    }
