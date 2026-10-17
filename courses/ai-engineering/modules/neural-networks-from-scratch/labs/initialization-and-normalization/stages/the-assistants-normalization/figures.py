import json

import numpy as np

NORMS = json.loads(open("references/norms.json").read())
# PyTorch's defaults for BatchNorm1d.
EPS, MOMENTUM = 1e-5, 0.1


def biased_running_var(case):
    """The running variance after the case's training batches, with each batch's own
    variance mixed in, as the assistant mixed it."""
    var = np.ones(len(case["weight"]))
    for step in case["steps"]:
        var = (1 - MOMENTUM) * var + MOMENTUM * np.array(step["X"]).var(axis=0)
    return var


def backward_errors(case):
    """For each training batch, the assistant's gradient with respect to the batch,
    through each sample's own normalized value alone: its error as a share of PyTorch's
    gradient, and the largest of its sums over the batch."""
    weight = np.array(case["weight"])
    for step in case["steps"]:
        X, dX = np.array(step["X"]), np.array(step["dX"])
        found = np.array(step["dY"]) * weight / np.sqrt(X.var(axis=0) + EPS)
        error = np.linalg.norm(found - dX) / np.linalg.norm(dX)
        yield error, np.max(np.abs(found.sum(axis=0)))


def layer_norm_off(case):
    """The largest difference from PyTorch's outputs with each feature normalized over
    the batch, as the assistant normalized it."""
    X = np.array(case["X"])
    normalized = (X - X.mean(axis=0)) / np.sqrt(X.var(axis=0) + EPS)
    found = np.array(case["weight"]) * normalized + np.array(case["bias"])
    return np.max(np.abs(found - np.array(case["Y"])))


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    test = table[table[:, 0] == 2, 1].astype(np.int64)
    shares = np.bincount(test, minlength=10) / len(test)
    small = min(NORMS["batch_norm"], key=lambda case: len(case["steps"][0]["X"]))
    n = len(small["steps"][0]["X"])
    reached = biased_running_var(small) / np.array(small["steps"][-1]["running_var"])
    errors, sums = zip(
        *(found for case in NORMS["batch_norm"] for found in backward_errors(case)),
        strict=True,
    )
    return {
        "lone_low": f"{shares.min():.1%}",
        "lone_high": f"{shares.max():.1%}",
        "small": str(n),
        "small_batches": str(len(small["steps"])),
        "reached_low": f"{reached.min():.2f}",
        "reached_high": f"{reached.max():.2f}",
        "settled": f"{(n - 1) / n:.3g}",
        "stretch": f"{np.sqrt(n / (n - 1)):.2f}",
        "backward_low": f"{min(errors):.0%}",
        "backward_high": f"{max(errors):.0%}",
        "backward_sum": f"{max(sums):.1f}",
        "axis_off": f"{max(layer_norm_off(case) for case in NORMS['layer_norm']):.1f}",
    }
