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

init.json holds torch.nn.init.calculate_gain for each nonlinearity, and for each of
torch.nn.init's uniform starts, with its settings, the largest weight it drew in a large
weight, which is the bound of its range to within a few parts in a hundred thousand.
norms.json holds torch.nn.BatchNorm1d's outputs, gradients and running estimates through
batches in training, then its outputs in evaluation, and torch.nn.LayerNorm's outputs and
gradients, given the loss's gradient with respect to the outputs.

    uv run make.py [folder]
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

SHAPE = (256, 512)


def nested(t):
    """A tensor's numbers as nested lists."""
    return t.detach().numpy().tolist()


def gains():
    cases = [
        ("linear", None),
        ("sigmoid", None),
        ("tanh", None),
        ("relu", None),
        ("leaky_relu", None),
        ("leaky_relu", 0.2),
        ("selu", None),
    ]
    return [
        {
            "nonlinearity": name,
            "param": param,
            "gain": torch.nn.init.calculate_gain(name, param),
        }
        for name, param in cases
    ]


def largest(kind, settings):
    """The largest weight, in size, that kind draws for a weight of SHAPE."""
    torch.manual_seed(0)
    weight = torch.empty(SHAPE, dtype=torch.float64)
    getattr(torch.nn.init, f"{kind}_")(weight, **settings)
    return {
        "kind": kind,
        "settings": settings,
        "shape": list(SHAPE),
        "largest": weight.abs().max().item(),
    }


def batch_norm_case(rng, batches, samples, features):
    """Training batches, each with the loss's gradient, then a batch in evaluation."""
    layer = torch.nn.BatchNorm1d(features, dtype=torch.float64)
    weight, bias = rng.normal(size=features), rng.normal(size=features)
    with torch.no_grad():
        layer.weight.copy_(torch.tensor(weight))
        layer.bias.copy_(torch.tensor(bias))
    steps = []
    for _ in range(batches):
        X = rng.normal(loc=2.0, scale=3.0, size=(samples, features))
        dY = rng.normal(size=(samples, features))
        tX = torch.tensor(X, requires_grad=True)
        layer.zero_grad()
        Y = layer(tX)
        Y.backward(torch.tensor(dY))
        steps.append(
            {
                "X": X.tolist(),
                "dY": dY.tolist(),
                "Y": nested(Y),
                "dX": nested(tX.grad),
                "dweight": nested(layer.weight.grad),
                "dbias": nested(layer.bias.grad),
                "running_mean": nested(layer.running_mean),
                "running_var": nested(layer.running_var),
            }
        )
    layer.eval()
    X = rng.normal(loc=2.0, scale=3.0, size=(samples, features))
    return {
        "weight": weight.tolist(),
        "bias": bias.tolist(),
        "steps": steps,
        "evaluation": {"X": X.tolist(), "Y": nested(layer(torch.tensor(X)))},
    }


def layer_norm_case(rng, samples, features, constant_row=False):
    """A batch through layer normalization, and the gradients given the loss's gradient."""
    layer = torch.nn.LayerNorm(features, dtype=torch.float64)
    weight, bias = rng.normal(size=features), rng.normal(size=features)
    with torch.no_grad():
        layer.weight.copy_(torch.tensor(weight))
        layer.bias.copy_(torch.tensor(bias))
    X = rng.normal(loc=1.0, scale=2.0, size=(samples, features))
    if constant_row:
        # A row whose values are all the same, whose variance is 0.
        X[0] = 1.5
    dY = rng.normal(size=(samples, features))
    tX = torch.tensor(X, requires_grad=True)
    Y = layer(tX)
    Y.backward(torch.tensor(dY))
    return {
        "weight": weight.tolist(),
        "bias": bias.tolist(),
        "X": X.tolist(),
        "dY": dY.tolist(),
        "Y": nested(Y),
        "dX": nested(tX.grad),
        "dweight": nested(layer.weight.grad),
        "dbias": nested(layer.bias.grad),
    }


def main(folder: Path) -> None:
    versions = {"torch": torch.__version__, "numpy": np.__version__}
    rng = np.random.default_rng(0)
    starts = [
        largest("xavier_uniform", {}),
        largest("xavier_uniform", {"gain": 5 / 3}),
        largest("kaiming_uniform", {}),
        largest("kaiming_uniform", {"nonlinearity": "relu"}),
        largest("kaiming_uniform", {"mode": "fan_out"}),
        # As torch.nn.Linear starts its weights.
        largest("kaiming_uniform", {"a": math.sqrt(5)}),
    ]
    norms = {
        "batch_norm": [batch_norm_case(rng, 3, 8, 5), batch_norm_case(rng, 4, 32, 3)],
        "layer_norm": [layer_norm_case(rng, 4, 6), layer_norm_case(rng, 5, 8, True)],
    }
    files = {
        "init.json": {**versions, "gains": gains(), "starts": starts},
        "norms.json": {**versions, **norms},
    }
    for name, value in files.items():
        text = json.dumps(value, separators=(",", ":")) + "\n"
        (folder / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
