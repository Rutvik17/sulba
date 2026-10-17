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
"""Records torch.optim's steps for the lab's tests, in float64, each case with its inputs.

Each case starts from random parameters, a weight and a bias, and gives the optimizer a
recorded gradient for each at every step, as a backward pass would. steps.json holds, for
torch.optim.SGD, Adam and AdamW, each case's settings, its parameters, its gradients and the
parameters after each step. A case with a list of learning rates sets the learning rate
before each step, as a schedule does.

    uv run make.py [folder]
"""

import json
import sys
from pathlib import Path

import numpy as np
import torch

OPTIMIZERS = {
    "sgd": torch.optim.SGD,
    "adam": torch.optim.Adam,
    "adamw": torch.optim.AdamW,
}
SHAPES = [(3, 4), (4,)]


def case(rng, kind, settings, steps, lrs=None, scale=1.0):
    """steps steps of one optimizer, its gradients scale times a standard normal's."""
    params = [rng.normal(size=shape) for shape in SHAPES]
    grads = [[scale * rng.normal(size=shape) for shape in SHAPES] for _ in range(steps)]
    tensors = [torch.tensor(p, dtype=torch.float64, requires_grad=True) for p in params]
    optimizer = OPTIMIZERS[kind](tensors, **settings)
    after = []
    for number, step in enumerate(grads):
        if lrs is not None:
            optimizer.param_groups[0]["lr"] = lrs[number]
        for tensor, grad in zip(tensors, step, strict=True):
            tensor.grad = torch.tensor(grad, dtype=torch.float64)
        optimizer.step()
        after.append([t.detach().numpy().tolist() for t in tensors])
    return {
        "settings": settings,
        "lrs": lrs,
        "params": [p.tolist() for p in params],
        "grads": [[g.tolist() for g in step] for step in grads],
        "after": after,
    }


def main(folder: Path) -> None:
    versions = {"torch": torch.__version__, "numpy": np.__version__}
    rng = np.random.default_rng(0)
    momentum = {"lr": 0.1, "momentum": 0.9}
    steps = {
        "sgd": [
            case(rng, "sgd", {"lr": 0.1}, 4),
            case(rng, "sgd", momentum, 8),
            case(rng, "sgd", {**momentum, "dampening": 0.5}, 8),
            case(rng, "sgd", {**momentum, "nesterov": True}, 8),
            case(rng, "sgd", {**momentum, "weight_decay": 0.01}, 8),
            # The learning rate divided by 10 after four steps.
            case(rng, "sgd", momentum, 10, lrs=[0.1] * 4 + [0.01] * 6),
        ],
        "adam": [
            case(rng, "adam", {}, 10),
            case(rng, "adam", {"lr": 0.01, "betas": (0.8, 0.99)}, 10),
            case(rng, "adam", {"lr": 0.01, "weight_decay": 0.1}, 10),
            # Gradients small enough that eps matters.
            case(rng, "adam", {"lr": 0.01, "eps": 0.001}, 10, scale=0.001),
        ],
        "adamw": [
            case(rng, "adamw", {}, 10),
            case(rng, "adamw", {"lr": 0.01, "weight_decay": 0.1}, 10),
            # Gradients of 0, so that only the weight decay moves the parameters.
            case(rng, "adamw", {"lr": 0.01, "weight_decay": 0.1}, 10, scale=0.0),
        ],
    }
    text = json.dumps({**versions, **steps}, separators=(",", ":")) + "\n"
    (folder / "steps.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
