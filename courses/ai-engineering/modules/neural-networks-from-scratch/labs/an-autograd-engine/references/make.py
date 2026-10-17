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

scalars.json holds random expressions of numbers, and tensors.json expressions of arrays,
with broadcasting among them. Each is written as steps, each step one operation on the
results of steps before it, named by their places in the list, and PyTorch's autograd gives
the last step's value and its gradient with respect to every input. models.json holds parts
of networks, each with its inputs, its value and every gradient: a network of residual
blocks, a layer's loss with a weight penalty, a log-sum-exp with each row's largest logit
taken out, a tanh layer, torch.nn.functional.cross_entropy, and a network of linear layers
and a ReLU trained with it.

    uv run make.py [folder]
"""

import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

# Operations on one step's result, two steps' results, or a step's result and a number.
UNARY = ["neg", "exp", "log", "tanh", "relu", "pow"]
BINARY = ["add", "sub", "mul", "div"]
NUMBER = ["add_number", "number_sub", "number_mul", "number_div"]
POWERS = [2.0, 3.0, -1.0, 0.5]


def tensor(values):
    return torch.tensor(values, dtype=torch.float64, requires_grad=True)


def nested(t):
    """A tensor's numbers as nested lists."""
    return t.detach().numpy().tolist()


def scalar(op, a, b=None):
    """One step of a scalar expression, on floats or on PyTorch's tensors."""
    if isinstance(a, float):
        exp, log, tanh, relu = math.exp, math.log, math.tanh, lambda x: max(x, 0.0)
    else:
        exp, log, tanh, relu = torch.exp, torch.log, torch.tanh, torch.relu
    match op:
        case "add" | "add_number":
            return a + b
        case "sub":
            return a - b
        case "mul":
            return a * b
        case "div":
            return a / b
        case "number_sub":
            return b - a
        case "number_mul":
            return b * a
        case "number_div":
            return b / a
        case "neg":
            return -a
        case "exp":
            return exp(a)
        case "log":
            return log(a)
        case "tanh":
            return tanh(a)
        case "relu":
            return relu(a)
        case "pow":
            return a**b
    raise ValueError(op)


def allowed(op, x, b=None):
    """Whether a step stays where its operation is defined and its derivative is finite."""
    match op:
        case "exp":
            return abs(x) < 4
        case "log":
            return x > 0.2
        case "relu":
            return abs(x) > 1e-3
        case "pow":
            return (b != -1.0 or abs(x) > 0.3) and (b != 0.5 or x > 0.2)
        case "number_div":
            return abs(x) > 0.3
    return True


def scalar_case(rng, inputs, steps, ops):
    """A random expression of numbers that uses only ops."""
    values = [float(v) for v in rng.normal(size=inputs)]
    listed = [["input", v] for v in values]
    while len(listed) < inputs + steps:
        op = str(rng.choice(ops))
        a = int(rng.integers(len(values)))
        if op in BINARY:
            b = int(rng.integers(len(values)))
            if op == "div" and abs(values[b]) < 0.3:
                continue
            step, found = [op, a, b], scalar(op, values[a], values[b])
        elif op in NUMBER:
            number = round(float(rng.uniform(-2, 2)), 2)
            if not allowed(op, values[a]):
                continue
            step, found = [op, a, number], scalar(op, values[a], number)
        else:
            power = float(rng.choice(POWERS)) if op == "pow" else None
            if not allowed(op, values[a], power):
                continue
            step = [op, a] if power is None else [op, a, power]
            found = scalar(op, values[a], power)
        if abs(found) > 1e4:
            continue
        values.append(float(found))
        listed.append(step)
    return {"steps": listed, **autograd_scalar(listed)}


def autograd_scalar(steps):
    nodes, inputs = [], []
    for step in steps:
        if step[0] == "input":
            nodes.append(tensor(step[1]))
            inputs.append(nodes[-1])
        elif step[0] in BINARY:
            nodes.append(scalar(step[0], nodes[step[1]], nodes[step[2]]))
        else:
            nodes.append(scalar(step[0], nodes[step[1]], *step[2:]))
    nodes[-1].backward()
    return {
        "value": nodes[-1].item(),
        "gradients": [0.0 if x.grad is None else x.grad.item() for x in inputs],
    }


def tensor_case(steps, *arrays):
    """A tensor expression: the inputs, then steps on them."""
    listed = [["input", array.tolist()] for array in arrays]
    listed.extend(steps)
    nodes, inputs = [], []
    for step in listed:
        op, *args = step
        if op == "input":
            nodes.append(tensor(args[0]))
            inputs.append(nodes[-1])
            continue
        a = nodes[args[0]]
        match op:
            case "add":
                found = a + nodes[args[1]]
            case "sub":
                found = a - nodes[args[1]]
            case "mul":
                found = a * nodes[args[1]]
            case "matmul":
                found = a @ nodes[args[1]]
            case "sum" | "mean":
                axis, keepdims = args[1], args[2]
                method = torch.sum if op == "sum" else torch.mean
                found = (
                    method(a) if axis is None else method(a, dim=axis, keepdim=keepdims)
                )
            case "T":
                found = a.T
            case "neg" | "exp" | "log" | "tanh" | "relu":
                found = {
                    "neg": lambda: -a,
                    "exp": lambda: torch.exp(a),
                    "log": lambda: torch.log(a),
                    "tanh": lambda: torch.tanh(a),
                    "relu": lambda: torch.relu(a),
                }[op]()
            case _:
                raise ValueError(op)
        nodes.append(found)
    nodes[-1].backward()
    return {
        "steps": listed,
        "value": nodes[-1].item(),
        "gradients": [
            np.zeros_like(x.detach().numpy()).tolist()
            if x.grad is None
            else x.grad.tolist()
            for x in inputs
        ],
    }


def tensor_cases(rng):
    normal = rng.normal
    n, k, h, classes = 6, 5, 4, 3
    onehot = np.eye(classes)[rng.integers(0, classes, size=n)]
    return [
        # A linear layer and a ReLU, the bias broadcast over the batch: relu(X Wᵀ + b), summed.
        tensor_case(
            [
                ["T", 1],
                ["matmul", 0, 3],
                ["add", 4, 2],
                ["relu", 5],
                ["sum", 6, None, False],
            ],
            normal(size=(n, k)),
            normal(size=(h, k)),
            normal(size=h),
        ),
        # Broadcasting a row and a column: tanh(A * B + C), its mean.
        tensor_case(
            [["mul", 0, 1], ["add", 3, 2], ["tanh", 4], ["mean", 5, None, False]],
            normal(size=(n, k)),
            normal(size=(1, k)),
            normal(size=(n, 1)),
        ),
        # Each column less its mean, squared, summed along the rows, then averaged.
        tensor_case(
            [
                ["mean", 0, 0, True],
                ["sub", 0, 1],
                ["mul", 2, 2],
                ["sum", 3, 1, False],
                ["mean", 4, None, False],
            ],
            normal(size=(n, k)),
        ),
        # Cross-entropy from logits Z and one-hot labels Y, without the largest logit taken
        # out: the mean of log(sum(exp(Z))) - sum(Z * Y) over the rows.
        tensor_case(
            [
                ["exp", 0],
                ["sum", 2, 1, False],
                ["log", 3],
                ["mul", 0, 1],
                ["sum", 5, 1, False],
                ["sub", 4, 6],
                ["mean", 7, None, False],
            ],
            normal(size=(n, classes)),
            onehot,
        ),
        # The office's kind of network: two linear layers with a ReLU between, and the same
        # cross-entropy.
        tensor_case(
            [
                ["T", 1],
                ["matmul", 0, 6],
                ["add", 7, 2],
                ["relu", 8],
                ["T", 3],
                ["matmul", 9, 10],
                ["add", 11, 4],
                ["exp", 12],
                ["sum", 13, 1, False],
                ["log", 14],
                ["mul", 12, 5],
                ["sum", 16, 1, False],
                ["sub", 15, 17],
                ["mean", 18, None, False],
            ],
            rng.integers(0, 17, size=(n, k)) / 16,
            rng.uniform(-0.5, 0.5, size=(h, k)),
            rng.uniform(-0.5, 0.5, size=h),
            rng.uniform(-0.5, 0.5, size=(classes, h)),
            rng.uniform(-0.5, 0.5, size=classes),
            onehot,
        ),
    ]


def uniform_layer(rng, inputs, outputs):
    """A weight and bias drawn as torch.nn.Linear draws them, from U(-1/sqrt(inputs), ...)."""
    bound = 1 / np.sqrt(inputs)
    return (
        rng.uniform(-bound, bound, size=(outputs, inputs)),
        rng.uniform(-bound, bound, size=outputs),
    )


def residual_case(rng, blocks, samples, width):
    """Residual blocks, each adding its input to a ReLU layer's output, x + relu(x Wᵀ + b),
    and the mean of the last block's output."""
    X = rng.normal(size=(samples, width))
    layers = [uniform_layer(rng, width, width) for _ in range(blocks)]
    tX = tensor(X)
    params = [(tensor(weight), tensor(bias)) for weight, bias in layers]
    x = tX
    for weight, bias in params:
        x = x + torch.relu(x @ weight.T + bias)
    out = x.mean()
    out.backward()
    return {
        "X": X.tolist(),
        "layers": [{"weight": w.tolist(), "bias": b.tolist()} for w, b in layers],
        "value": out.item(),
        "dX": nested(tX.grad),
        "gradients": [
            {"weight": nested(w.grad), "bias": nested(b.grad)} for w, b in params
        ],
    }


def penalty_case(rng, samples, inputs, outputs, decay):
    """A ReLU layer's mean output plus a weight penalty: decay times the sum of the squared
    weights."""
    X = rng.normal(size=(samples, inputs))
    weight, bias = rng.normal(size=(outputs, inputs)), rng.normal(size=outputs)
    tX, tw, tb = tensor(X), tensor(weight), tensor(bias)
    out = torch.relu(tX @ tw.T + tb).mean() + (tw * tw).sum() * decay
    out.backward()
    return {
        "X": X.tolist(),
        "weight": weight.tolist(),
        "bias": bias.tolist(),
        "decay": decay,
        "value": out.item(),
        "dX": nested(tX.grad),
        "dweight": nested(tw.grad),
        "dbias": nested(tb.grad),
    }


def log_sum_exp_case(rng, samples, classes, scale):
    """The mean over the rows of log(sum(exp(z - m))), with m each row's largest logit,
    taken as a constant, as a stable softmax takes it out."""
    logits = scale * rng.normal(size=(samples, classes))
    t = tensor(logits)
    largest = torch.tensor(logits.max(axis=1, keepdims=True))
    out = torch.log(torch.exp(t - largest).sum(dim=1)).mean()
    out.backward()
    return {"logits": logits.tolist(), "value": out.item(), "dlogits": nested(t.grad)}


def tanh_case(rng, samples, inputs, outputs):
    """A tanh layer, Y = tanh(X Wᵀ + b), and, given the loss's gradient with respect to Y,
    the gradients with respect to its inputs, weight and bias."""
    X = rng.normal(size=(samples, inputs))
    weight, bias = rng.normal(size=(outputs, inputs)), rng.normal(size=outputs)
    dY = rng.normal(size=(samples, outputs))
    tX, tw, tb = tensor(X), tensor(weight), tensor(bias)
    Y = torch.tanh(tX @ tw.T + tb)
    Y.backward(torch.tensor(dY))
    return {
        "X": X.tolist(),
        "weight": weight.tolist(),
        "bias": bias.tolist(),
        "dY": dY.tolist(),
        "Y": nested(Y),
        "dX": nested(tX.grad),
        "dweight": nested(tw.grad),
        "dbias": nested(tb.grad),
    }


def cross_entropy_case(rng, samples, classes, scale):
    logits = scale * rng.normal(size=(samples, classes))
    labels = rng.integers(0, classes, size=samples)
    t = tensor(logits)
    loss = torch.nn.functional.cross_entropy(t, torch.tensor(labels))
    loss.backward()
    return {
        "logits": logits.tolist(),
        "labels": labels.tolist(),
        "loss": loss.item(),
        "dlogits": nested(t.grad),
    }


def network_case(rng, widths, samples):
    """Linear layers with a ReLU between each two, on a batch of digits' pixels, and the
    cross-entropy of the last layer's outputs against the digits."""
    X = rng.integers(0, 17, size=(samples, widths[0])) / 16
    labels = rng.integers(0, widths[-1], size=samples)
    layers = [uniform_layer(rng, i, o) for i, o in itertools.pairwise(widths)]
    params = [(tensor(weight), tensor(bias)) for weight, bias in layers]
    out = torch.tensor(X)
    for number, (weight, bias) in enumerate(params):
        out = out @ weight.T + bias
        if number < len(params) - 1:
            out = torch.relu(out)
    loss = torch.nn.functional.cross_entropy(out, torch.tensor(labels))
    loss.backward()
    return {
        "X": X.tolist(),
        "labels": labels.tolist(),
        "layers": [{"weight": w.tolist(), "bias": b.tolist()} for w, b in layers],
        "loss": loss.item(),
        "gradients": [
            {"weight": nested(w.grad), "bias": nested(b.grad)} for w, b in params
        ],
    }


def models(rng):
    return {
        "residual": residual_case(rng, 4, 6, 5),
        "penalty": penalty_case(rng, 6, 5, 4, 0.1),
        "log_sum_exp": log_sum_exp_case(rng, 6, 4, 3.0),
        "tanh": tanh_case(rng, 6, 5, 4),
        "cross_entropy": [
            cross_entropy_case(rng, samples, classes, scale)
            for samples, classes, scale in [
                (1, 3, 1.0),
                (8, 10, 1.0),
                (32, 10, 3.0),
                (5, 4, 2.0),
                (4, 10, 1000.0),
            ]
        ],
        "network": network_case(rng, (64, 16, 10), 8),
    }


def main(folder: Path) -> None:
    versions = {"torch": torch.__version__, "numpy": np.__version__}
    rng = np.random.default_rng(0)
    first = ["add", "mul", "add_number", "number_mul", "exp"]
    every = BINARY + NUMBER + UNARY
    scalars = {
        "first_operations": [scalar_case(rng, 3, 10, first) for _ in range(5)],
        "every_operation": [scalar_case(rng, 3, 15, every) for _ in range(10)],
        "deep": [scalar_case(rng, 4, 60, every) for _ in range(10)],
    }
    files = {
        "scalars.json": {**versions, **scalars},
        "tensors.json": {**versions, "cases": tensor_cases(rng)},
        "models.json": {**versions, **models(rng)},
    }
    for name, value in files.items():
        text = json.dumps(value, separators=(",", ":")) + "\n"
        (folder / name).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
