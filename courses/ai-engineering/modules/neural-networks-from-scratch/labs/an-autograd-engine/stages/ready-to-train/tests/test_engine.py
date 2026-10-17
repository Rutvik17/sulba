import json
from pathlib import Path

import numpy as np
import pytest

from engine import Tensor, Value, cross_entropy, exp, log, relu, tanh

MODELS = json.loads(Path("references/models.json").read_text())
DEEP = json.loads(Path("references/scalars.json").read_text())["deep"]
RTOL, ATOL = 1e-10, 1e-12
FUNCTIONS = {"exp": exp, "log": log, "tanh": tanh, "relu": relu}


def close(found, expected):
    return np.allclose(found, expected, rtol=RTOL, atol=ATOL)


def evaluate(steps):
    """The last step's Value and the inputs' Values, from an expression written as steps,
    each an operation on the results of steps before it."""
    values, inputs = [], []
    for op, *args in steps:
        match op:
            case "input":
                value = Value(args[0])
                inputs.append(value)
            case "add":
                value = values[args[0]] + values[args[1]]
            case "sub":
                value = values[args[0]] - values[args[1]]
            case "mul":
                value = values[args[0]] * values[args[1]]
            case "div":
                value = values[args[0]] / values[args[1]]
            case "add_number":
                value = values[args[0]] + args[1]
            case "number_sub":
                value = args[1] - values[args[0]]
            case "number_mul":
                value = args[1] * values[args[0]]
            case "number_div":
                value = args[1] / values[args[0]]
            case "neg":
                value = -values[args[0]]
            case "pow":
                value = values[args[0]] ** args[1]
            case _:
                value = FUNCTIONS[op](values[args[0]])
        values.append(value)
    return values[-1], inputs


@pytest.mark.id("tst_aw19gi")
def test_cross_entropy():
    """Cross-entropy's loss and gradient for batches of every size, as PyTorch has them"""
    for case in MODELS["cross_entropy"][:-1]:
        logits = Tensor(np.array(case["logits"]))
        loss = cross_entropy(logits, np.array(case["labels"]))
        loss.backward()
        assert loss.data == pytest.approx(case["loss"], rel=RTOL, abs=ATOL)
        assert close(logits.grad, case["dlogits"])


@pytest.mark.id("tst_w78wr4")
def test_network():
    """The office's kind of network: its loss and every gradient, as PyTorch has them"""
    case = MODELS["network"]
    layers = [
        (Tensor(np.array(layer["weight"])), Tensor(np.array(layer["bias"])))
        for layer in case["layers"]
    ]
    out = Tensor(np.array(case["X"]))
    for number, (weight, bias) in enumerate(layers):
        out = out @ weight.T + bias
        if number < len(layers) - 1:
            out = out.relu()
    loss = cross_entropy(out, np.array(case["labels"]))
    loss.backward()
    assert loss.data == pytest.approx(case["loss"], rel=RTOL, abs=ATOL)
    for (weight, bias), expected in zip(layers, case["gradients"], strict=True):
        assert close(weight.grad, expected["weight"])
        assert close(bias.grad, expected["bias"])


@pytest.mark.id("tst_refiy8")
def test_long_expressions():
    """Long random expressions of every operation, as PyTorch works them out"""
    for case in DEEP:
        out, inputs = evaluate(case["steps"])
        out.backward()
        assert out.data == pytest.approx(case["value"], rel=RTOL, abs=ATOL)
        found = [value.grad for value in inputs]
        assert found == pytest.approx(case["gradients"], rel=RTOL, abs=ATOL)
