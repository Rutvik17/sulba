# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "torch==2.14.1"]
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# ///
"""Records PyTorch's results for the lab's tests, in float64, each case with its inputs.

linear.json holds torch.nn.functional.linear's outputs and, given the loss's gradient with
respect to them, the gradients with respect to its inputs, weight and bias. activations.json
holds torch.relu's and torch.nn.functional.cross_entropy's, and networks.json the loss and
every gradient of two networks of linear layers and ReLUs on a batch of digits.

    uv run make.py [folder]
"""

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import torch

PIXELS, DIGITS = 64, 10


def tensor(values):
    return torch.tensor(values, dtype=torch.float64, requires_grad=True)


def listed(t):
    return t.detach().numpy().tolist()


def linear_case(rng, samples, inputs, outputs):
    X, weight, bias = (
        rng.normal(size=(samples, inputs)),
        rng.normal(size=(outputs, inputs)),
        rng.normal(size=outputs),
    )
    dY = rng.normal(size=(samples, outputs))
    tX, tw, tb = tensor(X), tensor(weight), tensor(bias)
    Y = torch.nn.functional.linear(tX, tw, tb)
    Y.backward(torch.tensor(dY))
    return {
        "X": X.tolist(),
        "weight": weight.tolist(),
        "bias": bias.tolist(),
        "dY": dY.tolist(),
        "Y": listed(Y),
        "dX": listed(tX.grad),
        "dweight": listed(tw.grad),
        "dbias": listed(tb.grad),
    }


def relu_case(rng, samples, units):
    X = rng.normal(size=(samples, units))
    # Some inputs exactly 0, where ReLU has no derivative and PyTorch passes no gradient back.
    X[rng.random(size=X.shape) < 0.25] = 0.0
    dY = rng.normal(size=X.shape)
    tX = tensor(X)
    Y = torch.relu(tX)
    Y.backward(torch.tensor(dY))
    return {"X": X.tolist(), "dY": dY.tolist(), "Y": listed(Y), "dX": listed(tX.grad)}


def cross_entropy_case(rng, samples, scale):
    logits = scale * rng.normal(size=(samples, DIGITS))
    labels = rng.integers(0, DIGITS, size=samples)
    t = tensor(logits)
    loss = torch.nn.functional.cross_entropy(t, torch.tensor(labels))
    loss.backward()
    return {
        "logits": logits.tolist(),
        "labels": labels.tolist(),
        "loss": loss.item(),
        "dlogits": listed(t.grad),
    }


def network_case(rng, widths, samples):
    X = rng.integers(0, 17, size=(samples, PIXELS)) / 16
    labels = rng.integers(0, DIGITS, size=samples)
    layers = []
    for inputs, outputs in itertools.pairwise(widths):
        bound = 1 / np.sqrt(inputs)
        layers.append(
            (
                rng.uniform(-bound, bound, size=(outputs, inputs)),
                rng.uniform(-bound, bound, size=outputs),
            )
        )
    tX = tensor(X)
    params = [(tensor(weight), tensor(bias)) for weight, bias in layers]
    out = tX
    for number, (weight, bias) in enumerate(params):
        out = torch.nn.functional.linear(out, weight, bias)
        if number < len(params) - 1:
            out = torch.relu(out)
    loss = torch.nn.functional.cross_entropy(out, torch.tensor(labels))
    loss.backward()
    return {
        "X": X.tolist(),
        "labels": labels.tolist(),
        "layers": [{"weight": w.tolist(), "bias": b.tolist()} for w, b in layers],
        "logits": listed(out),
        "loss": loss.item(),
        "gradients": [
            {"weight": listed(w.grad), "bias": listed(b.grad)} for w, b in params
        ],
        "dX": listed(tX.grad),
    }


def main(folder: Path) -> None:
    versions = {"torch": torch.__version__, "numpy": np.__version__}
    rng = np.random.default_rng(0)
    linear = [
        linear_case(rng, *shape) for shape in [(1, 3, 2), (4, 5, 3), (8, PIXELS, 16)]
    ]
    relu = [relu_case(rng, 1, 5), relu_case(rng, 6, 16)]
    cross_entropy = [
        cross_entropy_case(rng, samples, scale)
        for samples, scale in [(1, 1.0), (8, 1.0), (32, 3.0), (4, 1000.0)]
    ]
    networks = [
        network_case(rng, widths, 8)
        for widths in [(PIXELS, 16, DIGITS), (PIXELS, 16, 16, DIGITS)]
    ]
    files = {
        "linear.json": {**versions, "cases": linear},
        "activations.json": {**versions, "relu": relu, "cross_entropy": cross_entropy},
        "networks.json": {**versions, "networks": networks},
    }
    for name, value in files.items():
        (folder / name).write_text(
            json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
