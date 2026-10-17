import json
import math
from pathlib import Path

import pytest

from engine import Value, exp, log, relu, tanh

CASES = json.loads(Path("references/scalars.json").read_text())["every_operation"]
# PyTorch's results and yours may differ in the last digits, from working in another order.
RTOL, ATOL = 1e-10, 1e-12
FUNCTIONS = {"exp": exp, "log": log, "tanh": tanh, "relu": relu}


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


@pytest.mark.id("tst_r5ltm5")
def test_subtraction_and_division_by_hand():
    """a - b and a / b, their values and gradients worked by hand"""
    a, b = Value(6.0), Value(2.0)
    assert (a - b).data == 4.0
    out = a / b
    out.backward()
    assert out.data == pytest.approx(3.0)
    assert a.grad == pytest.approx(0.5) and b.grad == pytest.approx(-1.5)


@pytest.mark.id("tst_3klp1g")
def test_numbers_on_either_side():
    """A number on either side of - and /"""
    a = Value(4.0)
    out = (1 - a) + (a - 1) + 8 / a + a / 2 - -a
    out.backward()
    assert out.data == pytest.approx(8.0)
    assert a.grad == pytest.approx(-0.5 + 0.5 + 1.0)


@pytest.mark.id("tst_stl6hh")
def test_powers():
    """Powers of 2, 1/2 and -1, with their derivatives"""
    for x, p, value, slope in [
        (3.0, 2, 9.0, 6.0),
        (4.0, 0.5, 2.0, 0.25),
        (2.0, -1, 0.5, -0.25),
    ]:
        a = Value(x)
        out = a**p
        out.backward()
        assert out.data == pytest.approx(value) and a.grad == pytest.approx(slope)


@pytest.mark.id("tst_8wlupm")
def test_functions():
    """log, tanh and relu, with their derivatives, relu's 0 at 0 among them"""
    a = Value(2.0)
    log(a).backward()
    assert a.grad == pytest.approx(0.5)
    b = Value(0.5)
    tanh(b).backward()
    assert b.grad == pytest.approx(1 - math.tanh(0.5) ** 2)
    for x, slope in [(-1.0, 0.0), (0.0, 0.0), (2.0, 1.0)]:
        c = Value(x)
        out = relu(c)
        out.backward()
        assert out.data == max(x, 0.0) and c.grad == slope


@pytest.mark.id("tst_8p8hlz")
def test_matches_pytorch():
    """The same value and gradients as PyTorch's, for each recorded expression"""
    for case in CASES:
        out, inputs = evaluate(case["steps"])
        out.backward()
        assert out.data == pytest.approx(case["value"], rel=RTOL, abs=ATOL)
        found = [value.grad for value in inputs]
        assert found == pytest.approx(case["gradients"], rel=RTOL, abs=ATOL)
