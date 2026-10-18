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
"""Records PyTorch's gradient norms and clipping for the lab's tests, in float64, each case
with its inputs.

clipping.json holds torch.nn.utils.get_total_norm for gradients of several shapes in
each norm type, clip_grads_with_norm_ given a total norm, and clip_grad_norm_'s total
norm and clipped gradients, for maximum norms above and below the gradients' norm.

    uv run make.py [folder]
"""

import json
import sys
from pathlib import Path

import numpy as np
import torch

SHAPES = [(3, 4), (4,), (2, 3, 2)]
NORM_TYPES = [2.0, 1.0, 3.0, "inf"]


def nested(t):
    """A tensor's numbers as nested lists."""
    return t.detach().numpy().tolist()


def gradients(rng, scale=1.0):
    """A gradient for each of SHAPES, as tensors."""
    return [torch.tensor(scale * rng.normal(size=shape)) for shape in SHAPES]


def norm_type(name):
    return float(name)


def total_norms(rng):
    cases = []
    for name in NORM_TYPES:
        grads = gradients(rng)
        total = torch.nn.utils.get_total_norm(grads, norm_type(name))
        cases.append(
            {
                "norm_type": name,
                "grads": [nested(g) for g in grads],
                "total": total.item(),
            }
        )
    return cases


def clip_with_norm(rng):
    """Gradients scaled for a total norm given to clip_grads_with_norm_."""
    cases = []
    for max_norm, total in [(1.0, 4.0), (2.0, 0.5)]:
        grads = gradients(rng)
        params = [torch.zeros_like(g, requires_grad=True) for g in grads]
        for param, grad in zip(params, grads, strict=True):
            param.grad = grad.clone()
        total_norm = torch.tensor(total, dtype=torch.float64)
        torch.nn.utils.clip_grads_with_norm_(params, max_norm, total_norm)
        cases.append(
            {
                "max_norm": max_norm,
                "total": total,
                "grads": [nested(g) for g in grads],
                "clipped": [nested(p.grad) for p in params],
            }
        )
    return cases


def clip_norm(rng):
    """clip_grad_norm_'s total norm and the gradients it leaves."""
    cases = []
    settings = [(1.0, 2.0, 1.0), (10.0, 2.0, 1.0), (0.5, "inf", 1.0), (2.0, 1.0, 1.0)]
    settings.append((1.0, 2.0, 0.0))
    for max_norm, name, scale in settings:
        grads = gradients(rng, scale)
        params = [torch.zeros_like(g, requires_grad=True) for g in grads]
        for param, grad in zip(params, grads, strict=True):
            param.grad = grad.clone()
        total = torch.nn.utils.clip_grad_norm_(params, max_norm, norm_type(name))
        cases.append(
            {
                "max_norm": max_norm,
                "norm_type": name,
                "grads": [nested(g) for g in grads],
                "total": total.item(),
                "clipped": [nested(p.grad) for p in params],
            }
        )
    return cases


def main(folder: Path) -> None:
    rng = np.random.default_rng(0)
    clipping = {
        "torch": torch.__version__,
        "numpy": np.__version__,
        "total_norms": total_norms(rng),
        "clip_with_norm": clip_with_norm(rng),
        "clip_norm": clip_norm(rng),
    }
    text = json.dumps(clipping, separators=(",", ":")) + "\n"
    (folder / "clipping.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
